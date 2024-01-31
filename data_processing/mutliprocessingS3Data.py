import boto3
from multiprocessing import Pool
import json
import os
from image_processing import detect_pupil,extract_eye_region, get_head_pose, is_image_blurry, eye_aspect_ratio
import dlib
import cv2
import pandas as pd
import numpy as np

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
sr_model_path = "EDSR_x4.pb"  # Change to the path of the model
sr_model.readModel(sr_model_path)
sr_model.setModel("edsr", 4)  # You can change the model and scale as needed
def get_camera_info(camera_info):
    camera_matrix = np.array(camera_info[0], dtype='double')
    dist_coeffs = np.array(camera_info[1], dtype='double')
    return camera_matrix, dist_coeffs

def pre_process_image(image):        
    # Initialize variables
    left_eye_info = right_eye_info = left_eye_bbox = right_eye_bbox = None

    # Quality Assessment: Check if the image is blurry
    if is_image_blurry(image):
        print("Image is too blurry")
        return None

    dlib_faces = detector(image)
    processed_data = []
    for dlib_face in dlib_faces:
        shape = predictor(image, dlib_face)

        for (i, (start, end)) in enumerate([(36,42), (42,48)]):
            eye_landmarks = [(shape.part(point).x, shape.part(point).y) for point in range(start, end)]
            
            # Skip if eye is closed
            if eye_aspect_ratio(eye_landmarks) < 0.2:
                print("Eye is closed")
                continue

            eye_image, (eye_min_x, eye_min_y, eye_max_x, eye_max_y) = extract_eye_region(image, shape, range(start, end))

            pupil_center, pupil_contour = detect_pupil(eye_image, sr_model)
            # After detecting the pupil in the cropped eye image:
            if pupil_center:
                # Scale the pupil center coordinates down to the original image size
                pupil_center_original = (pupil_center[0] / 4, pupil_center[1] / 4)
                # Transform these coordinates to the global space of the original image
                pupil_center_global = (int(pupil_center_original[0]) + eye_min_x, int(pupil_center_original[1]) + eye_min_y)
    
                pupil_center_global = tuple(pc.item() if isinstance(pc, np.generic) else pc for pc in pupil_center_global)


                bounding_box = (eye_min_x, eye_min_y, eye_max_x - eye_min_x, eye_max_y - eye_min_y)
                bounding_box = tuple(bb.item() if isinstance(bb, np.generic) else bb for bb in bounding_box)

                eye_data = {
                    'eye_position': 'left' if i == 0 else 'right',
                    'pupil_center': pupil_center_global,
                    'bounding_box': bounding_box
                }
                processed_data.append(eye_data)

        # Processed data for each eye
    for eye_data in processed_data:
        if eye_data['eye_position'] == 'left':
            left_eye_info = eye_data['pupil_center']
            left_eye_bbox = eye_data['bounding_box']
        else:
            right_eye_info = eye_data['pupil_center']
            right_eye_bbox = eye_data['bounding_box']
    
    # Check if any eye information was detected
    if left_eye_info is None and right_eye_info is None:
        print("No eye information detected")
        return None

    return processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape
def format_calibration_data_row(calibratoin_points, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose):
    rotation_vector, translation_vector = head_pose if head_pose else (np.zeros((3, 1)), np.zeros((3, 1)))

    rotation_vector_str = ','.join(map(str, rotation_vector.flatten()))

    translation_vector_str = ','.join(map(str, translation_vector.flatten()))
    data_row = [
        calibratoin_points[0], calibratoin_points[1],
        left_eye_info[0], left_eye_info[1],
        *left_eye_bbox,
        right_eye_info[0], right_eye_info[1],
        *right_eye_bbox,
        rotation_vector_str, translation_vector_str
    ]
    return data_row

def format_eye_gaze_data_row(cursors_position, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose):
    rotation_vector, translation_vector = head_pose if head_pose else (np.zeros((3, 1)), np.zeros((3, 1)))

    rotation_vector_str = ','.join(map(str, rotation_vector.flatten()))
    translation_vector_str = ','.join(map(str, translation_vector.flatten()))

    data_row = [
        cursors_position[0], cursors_position[1],
        left_eye_info[0], left_eye_info[1],
        *left_eye_bbox,
        right_eye_info[0], right_eye_info[1],
        *right_eye_bbox,
        rotation_vector_str, translation_vector_str
    ]
    return data_row
def create_and_replace_csv(local_base_dir, subdirectory, csv_file_name, image_data):
    # Path for the CSV file within the subdirectory
    csv_dir_path = os.path.join(local_base_dir, subdirectory)
    os.makedirs(csv_dir_path, exist_ok=True)  # Ensure the subdirectory exists
    csv_path = os.path.join(csv_dir_path, csv_file_name)
    
    # Create a new DataFrame for the CSV data
    new_data_df = pd.DataFrame(image_data)
    
    # Write the new DataFrame to the CSV file, overwriting the old data
    new_data_df.to_csv(csv_path, index=False, header=False)

def get_image_paths(bucket_name, key_prefix, subdirectory, s3_client):
    paginator = s3_client.get_paginator('list_objects_v2')
    image_paths = []

    # List objects within a specific subdirectory
    for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{key_prefix}{subdirectory}"):
        for obj in page.get('Contents', []):
            # Skip directories
            if obj['Key'].endswith('/'):
                continue
            image_paths.append(obj['Key'])

    return image_paths
def process_single_image(image_path, existing_data, local_base_dir, subdirectory, csv_file_name, camera_info):
    try:
        # Construct the full path to the image
        full_image_path = os.path.join(local_base_dir, image_path)
        image = cv2.imread(full_image_path)

        # Process the image
        processed_data = pre_process_image(image)
        if processed_data is None:
            return None
        processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape = processed_data

        # Get head pose data
        camera_matrix, dist_coeffs = camera_info
        head_pose = get_head_pose(shape, camera_matrix, dist_coeffs)

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
            data_row = format_calibration_data_row(cursor_or_calibration, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose)
        else:
            data_row = format_eye_gaze_data_row(cursor_or_calibration, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose)

        # Return the processed data for this image
        return [image_path] + data_row
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None
    
def process_images(image_paths, local_base_dir, subdirectory, csv_file_name, camera_info):
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
        print(existing_data)
        args = [(path, existing_data[idx] if existing_data else None, local_base_dir, subdirectory, csv_file_name, camera_info) for idx, path in enumerate(image_paths)]

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
    create_and_replace_csv(local_base_dir, subdirectory, csv_file_name, image_data)
from botocore.exceptions import ClientError

def get_metadata(bucket_name, metadata_file_key, s3_client):
    try:
        metadata_object = s3_client.get_object(Bucket=bucket_name, Key=metadata_file_key)
        metadata_content = metadata_object['Body'].read().decode('utf-8')
        metadata = json.loads(metadata_content)
        return metadata
    except Exception as e:
        print(f"Error retrieving metadata from S3: {e}")
        return None
def download_data(key_prefix, local_base_dir, s3_client, bucket_name):
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name, Prefix=key_prefix):
        print(f"Downloading data from {key_prefix}")
        for obj in page.get('Contents', []):
            s3_object_key = obj['Key']
            if s3_object_key.endswith('/'):
                continue
            local_file_path = os.path.join(local_base_dir, s3_object_key)
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            try:
                local_file_info = os.stat(local_file_path)
                s3_object_info = s3_client.head_object(Bucket=bucket_name, Key=s3_object_key)
                if local_file_info.st_size == s3_object_info['ContentLength']:
                    continue
            except (FileNotFoundError, ClientError):
                pass

            s3_client.download_file(bucket_name, s3_object_key, local_file_path)
            
def process_data_if_needed(key_prefix, local_base_dir, s3_client, bucket_name):
    # Retrieve metadata and determine if processing is needed
    metadata_key = f"{key_prefix}metadata.json"
    metadata_object = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
    metadata_content = metadata_object['Body'].read().decode('utf-8')
    metadata = json.loads(metadata_content)

    # If cameraInfo is present in metadata, process the data
    if 'cameraInfo' in metadata:
        print(f"Processing data in {key_prefix}")
        camera_matrix, dist_coeffs = get_camera_info(metadata['cameraInfo'])
        
        # Get the list of image paths that need processing
        calibration_image_paths = get_image_paths(bucket_name, key_prefix, 'calibration_images/', s3_client)
        eye_gaze_image_paths = get_image_paths(bucket_name, key_prefix, 'eye_gaze_images/', s3_client)
        
        subdir_prefix = key_prefix.rstrip('/')  # Ensure the prefix doesn't end with a '/'
        
        # Process calibration images
        if calibration_image_paths:
            process_images(calibration_image_paths, local_base_dir, subdir_prefix, 'calibration_data.csv', camera_info=(camera_matrix, dist_coeffs))
        
        # Process eye gaze images
        if eye_gaze_image_paths:
            process_images(eye_gaze_image_paths, local_base_dir, subdir_prefix, 'eye_gaze_data.csv', camera_info=(camera_matrix, dist_coeffs))
        
    else:
        print(f"No processing needed for {key_prefix}")
def get_all_metadata_keys(bucket_name, s3_client):
    metadata_keys = []
    paginator = s3_client.get_paginator('list_objects_v2')
    print(f"Looking for metadata files in bucket {bucket_name}")
    for page in paginator.paginate(Bucket=bucket_name, Prefix='data/'):
        for content in page.get('Contents', []):
            key = content['Key']
            if key.endswith('metadata.json'):
                metadata_keys.append(key)
    print(f"Found {len(metadata_keys)} metadata files")
    return metadata_keys

def process_s3_bucket_data(bucket_name, local_base_dir):
    s3_client = boto3.client('s3')
    
    # First, get a list of all metadata files
    metadata_keys = get_all_metadata_keys(bucket_name, s3_client)
    
    # Now process each metadata and its associated directory
    for metadata_key in metadata_keys:
        subdir_prefix = '/'.join(metadata_key.split('/')[:-1]) + '/'
        print(f"Processing data in {subdir_prefix}")
        download_data(subdir_prefix, local_base_dir, s3_client, bucket_name)
        process_data_if_needed(subdir_prefix, local_base_dir, s3_client, bucket_name)


import boto3
from multiprocessing import Pool
import json
import os
# process_s3_bucket_data(bucket_name, local_base_dir)
def get_local_image_paths(local_image_dir):
    # Get all file names in the local image directory
    return [os.path.join(f) for f in os.listdir(local_image_dir) if os.path.isfile(os.path.join(local_image_dir, f))]

def process_local_data(local_base_dir, image_dir_name, csv_file_name, camera_info):
    image_paths = get_local_image_paths(os.path.join(local_base_dir, image_dir_name))
    print(image_paths)
    process_images(image_paths, local_base_dir, image_dir_name, csv_file_name, camera_info)
# Import other libraries and functions as needed

def main():
    # Your code here
    bucket_name = 'eye-gaze-data'
    local_base_dir = './'
    os.makedirs(local_base_dir, exist_ok=True)

    process_s3_bucket_data(bucket_name, local_base_dir)

    # # Assuming the local_base_dir is the current directory ('./')
    # local_base_dir = './data/WilliamOld'
    # image_dir_name = 'images'
    # csv_file_name = 'data1.csv'

    # # The camera information, as you specified
    # camera_matrix = np.array([[560, 0, 320], [0, 560, 240], [0, 0, 1]], dtype='double')
    # dist_coeffs = np.array([0, 0, 0, 0, 0], dtype='double')

    # # Process the local data
    # process_local_data(local_base_dir, image_dir_name, csv_file_name, (camera_matrix, dist_coeffs))

if __name__ == "__main__":
    main()

# bucket_name = 'eye-gaze-data'
# local_base_dir = './'
# os.makedirs(local_base_dir, exist_ok=True)



# # The camera information, as you specified
# camera_matrix = np.array([[560, 0, 320], [0, 560, 240], [0, 0, 1]], dtype='double')
# dist_coeffs = np.array([0, 0, 0, 0, 0], dtype='double')

# # Assuming the local_base_dir is the current directory ('./')
# local_base_dir = './data/WilliamOld'
# image_dir_name = 'images'
# csv_file_name = 'data1.csv'

# # Process the local data
# process_local_data(local_base_dir, image_dir_name, csv_file_name, (camera_matrix, dist_coeffs))
