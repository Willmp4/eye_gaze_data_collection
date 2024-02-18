import os
import cv2
import numpy as np
import json
from image_processing import ImageProcessor
from multiprocessing import Pool
import pandas as pd
import dlib
import os
import glob
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
    with open('./pickel_files/all_data_200_100_head_pose.pkl', 'wb') as f:
        pickle.dump((X,Y), f)


def get_combined_eyes(frame, global_detector, global_predictor, target_size=(200, 100)):
    """
    Detects, enhances, and combines the eye regions including the nose bridge from the frame.
    Args:
        frame: The input image frame.
        global_detector: Face detector.
        global_predictor: Landmark predictor.
        target_size: Target size for resizing the combined eye region.
    Returns:
        The combined eye regions including the nose bridge, or None if not detected.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = global_detector(gray)

    # super resolution image
    for face in faces:
        landmarks = global_predictor(gray, face)

        forehead_points = [20, 21, 22, 23, 0 ,16]
        left_eye_points = [36, 37, 38, 39, 40, 41]
        right_eye_points = [42, 43, 44, 45, 46, 47]
        nose_bridge_points = [27, 28, 29]  # Adjust if necessary for your landmarks

        # Extract the combined region of both eyes including the nose bridge
        # Make sure to only use the first returned value (the image)

        combined_eye_region, _ = ImageProcessor.extract_eye_region(
            frame, landmarks, left_eye_points, right_eye_points, nose_bridge_points, forehead_points)

        if isinstance(combined_eye_region, np.ndarray):

            # Apply super-resolution
            # combined_eye_super_res = ImageProcessor.enhance_image_resolution(combined_eye_region, global_sr_model)

            # Resize to the final target size
            combined_eye_final_resized = cv2.resize(combined_eye_region, target_size, interpolation=cv2.INTER_AREA)

            # combined_eye_final_resized = cv2.cvtColor(combined_eye_final_resized, cv2.COLOR_BGR2GRAY)


            # Normalize if necessary
            combined_eye_final_resized = combined_eye_final_resized.astype(np.float32) / 255.0

            return combined_eye_final_resized
    return None

def compute_global_stats(base_dir):
    all_head_pose_data = []
    for csv_file in glob.glob(os.path.join(base_dir, '**', '*.csv'), recursive=True):
        data = pd.read_csv(csv_file, usecols=[15, 16])
        for _, row in data.iterrows():
            head_pose_data = [float(x) for x in row.iloc[0].strip('"').split(',')]
            head_translation_data = [float(x) for x in row.iloc[1].strip('"').split(',')]
            all_head_pose_data.append(head_pose_data + head_translation_data)
    all_head_pose_data = np.array(all_head_pose_data)
    min_vals = np.min(all_head_pose_data, axis=0)
    max_vals = np.max(all_head_pose_data, axis=0)
    return  min_vals, max_vals

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

def process_row(data, metadata_file_path, local_base_dir, min_vals, max_vals):
    screen_width, screen_height = get_screen_size(metadata_file_path)
    data = data[0]
    data = data[0]
    image_path = data[0]
    cursor_x = data[1]
    cursor_y = data[2]
    eye_box_pupil_data = data[3:15]
    head_pose = data[15]
    head_translation = data[16]
    # Unpack the row data
    # image_path, cursor_x, cursor_y, *eye_box_pupil_data, head_pose, head_translation = data
    eye_gaze_image_path = os.path.join(image_path)
    calibration_image_path = os.path.join(image_path)

    if os.path.exists(eye_gaze_image_path):
        full_image_path = eye_gaze_image_path
    elif os.path.exists(calibration_image_path):
        full_image_path = calibration_image_path
    else:
        print(f"Image not found: {image_path}")
        return None 
    
    full_image_path = os.path.join(image_path)
    image = cv2.imread(full_image_path)
    if image is None:
        print(f"Image not found: {full_image_path}")
        return None
    
    combined_eyes = get_combined_eyes(image, global_detector, global_predictor)
    if combined_eyes is None:
        return None
    
    # Normalize eye box pupil data
    # normalized_eye_box_pupil_data = [float(coord) / screen_width if i % 2 == 0 else float(coord) / screen_height for i, coord in enumerate(eye_box_pupil_data)]

    head_pose_data = [float(x) for x in head_pose.strip('"').split(',')]
    head_translation_data = [float(x) for x in head_translation.strip('"').split(',')]
    
    head_pose_data = np.array(head_pose_data + head_translation_data)
    normalized_head_pose_data = (head_pose_data - min_vals) / (max_vals - min_vals)
    
    # Normalize cursor positions
    normalized_cursor_x = float(cursor_x) / screen_width
    normalized_cursor_y = float(cursor_y) / screen_height
    
    # Prepare X and Y
    # X: Combined eyes image
    # Y: Cursor position, eye box pupil data, head pose data
    X = combined_eyes
# Assuming normalized_eye_box_pupil_data and normalized_head_pose_data are numpy arrays
    Y = [normalized_cursor_x, normalized_cursor_y, full_image_path] +  normalized_head_pose_data.tolist()
    return X, Y

def process_images_parallel(base_dir):
    subdirs = glob.glob(os.path.join(base_dir, '*/'))
    min_vals, max_vals = compute_global_stats(base_dir)
    
    with Pool() as pool:
        results = []
        for subdir in subdirs:
            print(f"Processing images in {subdir}")
            metadata_file_path = os.path.join(subdir, 'metadata.json')
            csv_files = glob.glob(os.path.join(subdir, '*.csv'))  # Correctly use glob.glob() here as well

            # csv_files = [csv_file for csv_file in csv_files if 'calibration' in csv_file]
            
            for csv_file in csv_files:
                print(f"Processing file: {csv_file}")
                dataset = pd.read_csv(csv_file, header=None)
                data_rows = [([row.values], metadata_file_path, base_dir, min_vals, max_vals) for index, row in dataset.iterrows()]
                                
                processed_data = pool.starmap(process_row, [(row, metadata_file_path, base_dir, min_vals, max_vals) for row in data_rows])
                results.extend(processed_data)

    X = [result[0] for result in results if result is not None]
    Y = [result[1] for result in results if result is not None]

    return X, Y

if __name__ == '__main__':
    main()