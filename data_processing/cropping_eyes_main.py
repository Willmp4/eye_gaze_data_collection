import os
import cv2
import numpy as np
import json
from image_processing import ImageProcessor
from multiprocessing import Pool
import pandas as pd
import dlib
import os
from glob import glob
import pandas as pd
import pickle
import cv2

# Global initialization
global_detector = dlib.get_frontal_face_detector()
global_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
global_sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
global_sr_model.readModel("EDSR_x4.pb")
global_sr_model.setModel("edsr", 4)
ImageProcessor = ImageProcessor(global_detector, global_predictor, global_sr_model)

def main():
    local_base_dir = './data'
    X, Y = process_images_parallel(local_base_dir)

    print(f"Processed {len(X)} items.")

    # Save the processed data
    with open('./pickel_files/calibration_processed_data_buffer.pkl', 'wb') as f:
        pickle.dump((X,Y), f)

def get_combined_eyes(frame, global_sr_model, global_detector, global_predictor, target_size=(40, 48)):
    """
    Detects, enhances, and combines the eye regions from the frame using the extract_eye_region method.
    Args:
        frame: The input image frame.
        global_sr_model: Super-resolution model.
        global_detector: Face detector.
        global_predictor: Landmark predictor.
        target_size: Target size for resizing each eye region.
    Returns:
        The combined eye regions, or None if not detected.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = global_detector(gray)

    for face in faces:
        landmarks = global_predictor(gray, face)

        left_eye_points = [36, 37, 38, 39, 40, 41]
        right_eye_points = [42, 43, 44, 45, 46, 47]

        # Preprocess each eye region
        left_eye_region, _ = ImageProcessor.extract_eye_region(frame, landmarks, left_eye_points)
        right_eye_region, _ = ImageProcessor.extract_eye_region(frame, landmarks, right_eye_points)

        # Enhance image resolution and normalize
        left_eye_super_res = ImageProcessor.enhance_image_resolution(left_eye_region, global_sr_model).astype(np.float32) / 255.0
        right_eye_super_res = ImageProcessor.enhance_image_resolution(right_eye_region, global_sr_model).astype(np.float32) / 255.0

        # Resize images to the target size
        left_eye_resized = cv2.resize(left_eye_super_res, target_size, interpolation=cv2.INTER_AREA)
        right_eye_resized = cv2.resize(right_eye_super_res, target_size, interpolation=cv2.INTER_AREA)

        # Combine the eyes side by side
        combined_eyes = np.hstack([left_eye_resized, right_eye_resized])
        
        return combined_eyes

    return None

def normalize_head_pose(head_pose_data, rotation_scale=180, translation_max_displacement=None):
    """
    Normalizes the head pose data.
    Args:
        head_pose_data: List containing the head pose data (rotation and translation vectors).
        rotation_scale: Maximum value for the rotation vector components (180 for degrees, np.pi for radians).
        translation_max_displacement: A tuple (max_x, max_y, max_z) representing the maximum displacement in each axis. If None, standard deviation normalization will be used.

    Returns:
        Normalized head pose data.
    """
    # Normalize rotation vectors
    normalized_rotation = np.array(head_pose_data[:3]) / rotation_scale

    # Normalize translation vectors
    if translation_max_displacement:
        max_x, max_y, max_z = translation_max_displacement
        normalized_translation = np.array(head_pose_data[3:]) / np.array([max_x, max_y, max_z])
    else:
        # Standard deviation normalization
        translation_vector = np.array(head_pose_data[3:])
        std_dev = np.std(translation_vector)
        mean_val = np.mean(translation_vector)
        normalized_translation = (translation_vector - mean_val) / std_dev

    return np.concatenate([normalized_rotation, normalized_translation]).tolist()


# Assuming normalize_head_pose and get_combined_eyes are defined as before
def get_screen_size(metadata_file_path):
    with open(metadata_file_path, 'r') as f:
        metadata = json.load(f)

        # Check if 'screenData' is a key in the metadata
        if 'screenData' in metadata:
            metadata = metadata['screenData']

        # Otherwise, assume the metadata is already at the top level
        screen_width = metadata.get('screenWidth')
        screen_height = metadata.get('screenHeight')

        if screen_width is None or screen_height is None:
            raise ValueError("Screen size not found in metadata")

        return screen_width, screen_height

def parse_head_pose_data(row):
    # Split the strings and convert to float
    rotation_str, translation_str = row['head_pose'], row['head_translation']
    rotation = [float(x) for x in rotation_str.strip('"').split(',')]
    translation = [float(x) for x in translation_str.strip('"').split(',')]
    return rotation + translation  # Combine into a single list

def process_row(data, metadata_file_path, local_base_dir):
    screen_width, screen_height = get_screen_size(metadata_file_path)

    # Unpack your data
    image_path, cursor_x, cursor_y, *eye_box_pupil_data, head_pose, head_translation = data
    
    full_image_path = os.path.join(image_path)
    image = cv2.imread(full_image_path)
    if image is None:
        print(f"Image not found: {full_image_path}")
        return None
    
    combined_eyes = get_combined_eyes(image, global_sr_model, global_detector, global_predictor)
    if combined_eyes is None:
        return None
    
    # Normalize eye box pupil data
    normalized_eye_box_pupil_data = [float(coord) / screen_width if i % 2 == 0 else float(coord) / screen_height for i, coord in enumerate(eye_box_pupil_data)]

    # Parse and normalize head pose and translation data
    head_pose_data = [float(x) for x in head_pose.strip('"').split(',')]
    head_translation_data = [float(x) for x in head_translation.strip('"').split(',')]
    normalized_head_pose_data = normalize_head_pose(head_pose_data + head_translation_data)
    
    # Normalize cursor positions
    normalized_cursor_x = float(cursor_x) / screen_width
    normalized_cursor_y = float(cursor_y) / screen_height
    
    # Prepare X and Y
    # X: Combined eyes image
    # Y: Cursor position, eye box pupil data, head pose data
    X = combined_eyes
    Y = [normalized_cursor_x, normalized_cursor_y] + normalized_eye_box_pupil_data + normalized_head_pose_data
    return X, Y

def process_images_parallel(base_dir):
    subdirs = glob(os.path.join(base_dir, '*/'))
    
    with Pool(processes=6) as pool:  # Use context manager to handle pool closure
        results = []

        for subdir in subdirs:
            print(f"Processing images in {subdir}")
            metadata_file_path = os.path.join(subdir, 'metadata.json')
            csv_files = glob(os.path.join(subdir, '*.csv'))

            csv_files = [csv_file for csv_file in csv_files if 'calibration' in csv_file]
            
            for csv_file in csv_files:
                print(f"Processing file: {csv_file}")
                dataset = pd.read_csv(csv_file, header=None)
                # Update here: Remove extra parentheses to correctly unpack arguments
                data_rows = [(tuple(row), metadata_file_path, base_dir) for index, row in dataset.iterrows()]
                
                processed_data = pool.starmap(process_row, data_rows)
                results.extend(processed_data)

    X = [result[0] for result in results if result is not None]
    Y = [result[1] for result in results if result is not None]

    return X, Y


if __name__ == '__main__':
    main()
