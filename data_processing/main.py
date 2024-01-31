import os
import cv2
import numpy as np
import json
import DataHandler
import ImageProcessor
import CSVManager
from multiprocessing import Pool
import pandas as pd

def main():
    bucket_name = 'eye-gaze-data'
    local_base_dir = './'
    data_handler = DataHandler.DataHandler(bucket_name, local_base_dir)

    image_processor = ImageProcessor.ImageProcessor()

    csv_manager = CSVManager.CSVManager(local_base_dir)

    # Pass instances to process_data_if_needed
    data_handler.process_s3_bucket_data(bucket_name, local_base_dir, process_data_if_needed, data_handler, image_processor, csv_manager)

def process_data_if_needed(key_prefix, local_base_dir, s3_client, bucket_name, data_handler, image_processor, csv_manager):
    # Retrieve metadata and determine if processing is needed
    metadata_key = f"{key_prefix}metadata.json"
    metadata_object = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
    metadata_content = metadata_object['Body'].read().decode('utf-8')
    metadata = json.loads(metadata_content)

    # If cameraInfo is present in metadata, process the data
    if 'cameraInfo' in metadata:
        print(f"Processing data in {key_prefix}")
        camera_matrix, dist_coeffs = data_handler.get_camera_info(metadata['cameraInfo'])
        
        # Get the list of image paths that need processing
        calibration_image_paths = data_handler.get_image_paths(bucket_name, key_prefix, 'calibration_images/', s3_client)
        eye_gaze_image_paths = data_handler.get_image_paths(bucket_name, key_prefix, 'eye_gaze_images/', s3_client)
        
        subdir_prefix = key_prefix.rstrip('/')  # Ensure the prefix doesn't end with a '/'
        
        # Process calibration images
        if calibration_image_paths:
            process_images(calibration_image_paths, local_base_dir, subdir_prefix, 'calibration_data.csv', data_handler, image_processor, csv_manager, camera_info=(camera_matrix, dist_coeffs))
        
        # Process eye gaze images
        if eye_gaze_image_paths:
            process_images(eye_gaze_image_paths, local_base_dir, subdir_prefix, 'eye_gaze_data.csv',  data_handler, image_processor, csv_manager, camera_info=(camera_matrix, dist_coeffs),)
        
    else:
        print(f"No processing needed for {key_prefix}")

def process_single_image(image_path, existing_data, local_base_dir, subdirectory, csv_file_name, camera_info, csv_manager):
    image_processor = ImageProcessor.ImageProcessor()
    image_processor.ensure_sr_model_loaded()
    try:
        # Construct the full path to the image
        full_image_path = os.path.join(local_base_dir, image_path)
        image = cv2.imread(full_image_path)

        # Process the image
        processed_data = image_processor.pre_process_image(image)
        if processed_data is None:
            return None
        processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape = processed_data

        # Get head pose data
        camera_matrix, dist_coeffs = camera_info
        head_pose = image_processor.get_head_pose(shape, camera_matrix, dist_coeffs)

        # Determine cursor or calibration data based on the file path
        if existing_data is not None:
            cursor_or_calibration = existing_data  # Use existing data for this image
        else:
            print(f"Skipping image {image_path} because no cursor or calibration data was found")
            cursor_or_calibration = [np.nan, np.nan]  # Replace with your actual data source

        # Format the data row for CSV, including the existing data
        if left_eye_bbox is None or right_eye_bbox is None:
            print(f"Skipping image {image_path} because no eyes were detected")
            return None
        if right_eye_info is None and left_eye_info is None:
            print(f"Skipping image {image_path} because no eyes were detected")
            return None

        if 'calibration' in image_path:
            data_row = csv_manager.format_calibration_data_row(cursor_or_calibration, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose)
        else:
            data_row = csv_manager.format_eye_gaze_data_row(cursor_or_calibration, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose)

        # Return the processed data for this image
        return [image_path] + data_row
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None
    
def process_images(image_paths, local_base_dir, subdirectory, csv_file_name, data_handler, image_processor, csv_manager, camera_info):
    image_data = []

    # Path to the current CSV file
    current_csv_path = os.path.join(local_base_dir, subdirectory, csv_file_name)

    # Read existing data if CSV exists
    if os.path.exists(current_csv_path):
        current_data_df = pd.read_csv(current_csv_path, header=None)
        existing_data = current_data_df.iloc[:, 1:3].values.tolist()
    else:
        existing_data = None  # No existing data

    # Create a pool of worker processes
    with Pool(processes=8) as pool:
        print(f"Processing {len(image_paths)} images")
        
        # Prepare arguments for each process, including existing data
        # Now include image_processor and csv_manager in the arguments
        args = [(path, existing_data[idx] if existing_data else None, local_base_dir, subdirectory, csv_file_name, camera_info, csv_manager) for idx, path in enumerate(image_paths)]

        # Map each image to a worker process
        try:
            results = pool.starmap(process_single_image, args)
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

        # Collect results from each worker
        for result in results:
            if result is not None:
                print(result)
                image_data.append(result)

    # Create and replace the CSV file with the new data
    csv_manager.create_and_replace_csv(local_base_dir, subdirectory, csv_file_name, image_data)

if __name__ == '__main__':
    main()


