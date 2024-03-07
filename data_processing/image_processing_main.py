import sys
from pathlib import Path
parent_dir = Path.cwd().parent.parent
sys.path.append(str(parent_dir))

import os
import cv2
import numpy as np
from classes.data_handelr import DataHandler
from classes.image_processing import ImageProcessor
from classes.csv_manager import CSVManager
from multiprocessing import Pool
import pandas as pd
import dlib


# Global initialization
global_detector = dlib.get_frontal_face_detector()
global_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
global_sr_model = cv2.dnn_superres.DnnSuperResImpl_create()

def main():
    bucket_name = 'eye-gaze-data'
    local_base_dir = './'
    data_handler = DataHandler(bucket_name, local_base_dir)
    csv_manager = CSVManager(local_base_dir)

    data_handler.process_s3_bucket_data(bucket_name, local_base_dir, process_images, csv_manager)

def process_single_image(image_path, existing_data, local_base_dir, subdirectory, csv_file_name, camera_info, csv_manager):
    image_processor = ImageProcessor(global_detector, global_predictor)

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
        print(f"Processed image {image_path}")
        return [image_path] + data_row
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None
    
def process_images(image_paths, local_base_dir, subdirectory, csv_file_name, csv_manager, camera_info):
    image_data = []

    # Path to the current CSV file
    current_csv_path = os.path.join(local_base_dir, subdirectory, csv_file_name)

    # Create a mapping of image paths to existing data
    existing_data_map = {}
    if os.path.exists(current_csv_path):
        print(f"Reading existing data from {current_csv_path}")
        current_data_df = pd.read_csv(current_csv_path, header=None)
        for idx, row in current_data_df.iterrows():
            image_path = row[0]
            existing_data_map[image_path] = row[1:3].values.tolist()

    with Pool() as pool:
        print(f"Processing {len(image_paths)} images")
        
        # Prepare arguments for each process
        args = []
        for image_path in image_paths:
            existing_data = existing_data_map.get(image_path, [np.nan, np.nan])  # Use mapped data or default
            args.append((image_path, existing_data, local_base_dir, subdirectory, csv_file_name, camera_info, csv_manager))

        # Map each image to a worker process
        try:
            results = pool.starmap(process_single_image, args)
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

        # Collect results from each worker
        for result in results:
            if result is not None:
                image_data.append(result)

    # Create and replace the CSV file with the new data
    csv_manager.create_and_replace_csv(local_base_dir, subdirectory, csv_file_name, image_data)


if __name__ == '__main__':
    main()
