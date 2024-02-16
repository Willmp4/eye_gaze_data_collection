import os
import cv2
import pickle
import h5py
import numpy as np
from multiprocessing import Pool, cpu_count
from pathlib import Path

def preprocess_frame(frame, target_size=(200, 100)):
    """
    Preprocesses a frame for gaze prediction.
    Args:
    - frame: The input image frame (assumed to be in BGR format as per OpenCV standard)
    - target_size: The target size to which the frame should be resized (width, height)

    Returns:
    - Preprocessed frame
    """
    # Check if image is loaded correctly
    if frame is None:
        raise ValueError("Invalid input frame")

    # Convert to grayscale
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to get a binary image
    _, binary_image = cv2.threshold(gray_image, 1, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found in the frame")

    # Find the largest contour based on area
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the bounding box of the largest contour
    x, y, w, h = cv2.boundingRect(largest_contour)

    # Crop the image using the bounding box
    cropped_image = frame[y:y+h, x:x+w]

    # Resize the cropped image to the target size
    resized_image = cv2.resize(cropped_image, target_size)
 
    # Convert to float and normalize
    preprocessed_image = resized_image.astype(np.float32) / 255.0

    return preprocessed_image

def get_h5_file_path(subdir):
    try:
        print('logging', subdir)

        # Extract the parent directory of the 'subdir' to get the user's data directory
        user_data_dir = os.path.dirname(subdir)
        
        # Construct the path to the 'Calibration' directory
        calibration_dir = os.path.join(user_data_dir, 'Calibration')
        
        # Assuming there's only one .h5 file per user in the 'Calibration' directory
        for file in os.listdir(calibration_dir):
            if file.endswith('.h5'):
                if 'screenSize' in file:
                    return os.path.join(calibration_dir, file)
    except Exception as e:
        print(f"Error while getting h5 file path: {e}")
        return None


def ask_to_continue(current_dir, processed_dirs_count, subdir_limit=5):
    if processed_dirs_count % subdir_limit == 0:
        answer = input(f"Processed {processed_dirs_count} directories up to {current_dir}. Continue? [y/n]: ")
        if answer.lower() != 'y':
            return False
    return True

def read_h5(h5_file_path):
    try:
        with h5py.File(h5_file_path, 'r') as h5_file:
            h5_data = {key: h5_file[key][:] for key in h5_file.keys()}
        return h5_data
    except Exception as e:
        print(f"Error while reading h5 file: {e}")
        return None
    
def normalize_annotations(annotation, width_pixel, height_pixel):
    normalized_x = float(annotation[0]) / width_pixel
    normalized_y = float(annotation[1]) / height_pixel
    return [normalized_x, normalized_y]

def append_to_pickle(data, filename):
    try:
        with open(filename, 'rb') as file:
            existing_data = pickle.load(file)
    except FileNotFoundError:
        existing_data = {'X': [], 'Y': []}

    existing_data['X'].extend(data['X'])
    existing_data['Y'].extend(data['Y'])

    try:
        with open(filename, 'wb') as file:
            pickle.dump(existing_data, file)
    except Exception as e:
        print(f"Error while writing to pickle file: {e}")

def process_directory(subdir_info):
    try:
        subdir, base_path = subdir_info
        X, Y = [], []  # Initialize X and Y locally within the function

        # Assuming get_h5_file_path and other support functions are defined globally
        h5_file_path = get_h5_file_path(subdir)
        if not Path(h5_file_path).exists():
            print(f"No .h5 file found for user in {subdir}. Skipping.")
            return None  # Skip this directory

        h5_data = read_h5(h5_file_path)
        if h5_data is None:
            print(f"Error reading h5 file for user in {subdir}. Skipping.")
            return None  # Skip this directory
        width_pixel, height_pixel = h5_data['width_pixel'][0], h5_data['height_pixel'][0]
        print(f"Processing directory {subdir} with width_pixel={width_pixel} and height_pixel={height_pixel}")

        annotation_file = os.path.join(subdir, 'annotation.txt')
        if not os.path.exists(annotation_file):
            print(f"No annotation file found for directory {subdir}. Skipping.")
            return None  # Skip this directory

        with open(annotation_file, 'r') as ann_file:
            annotations = [line.strip().split() for line in ann_file]

        for file in os.listdir(subdir):
            if file.endswith('.jpg'):
                image_path = os.path.join(subdir, file)
                image_index = int(file.split('.')[0])  # Assuming files are named like "index.jpg"
                if image_index < len(annotations):
                    annotation = normalize_annotations(annotations[image_index][24:26], width_pixel, height_pixel)
                    image = cv2.imread(image_path)
                    if image is not None:
                        preprocessed_image = preprocess_frame(image)
                        X.append(preprocessed_image)
                        Y.append(annotation)
        return {'X': X, 'Y': Y}
    
    except Exception as e:
        print(f"Error while processing directory {subdir}: {e}")
        return None

def process_images_and_annotations_parallel(base_path,start = 0, max_dirs = 50, batch_size=500):
    # List all subdirectories containing .jpg files
    subdirs = [(os.path.join(subdir), base_path) for subdir, _, files in os.walk(base_path) if any(file.endswith('.jpg') for file in files)]

    # Limit the number of directories to process to prevent excessive memory usage
    subdirs = subdirs[start:max_dirs]

    # Initialize multiprocessing Pool
    with Pool() as pool:
        results = pool.map(process_directory, subdirs)

    # Filter out None results if any directory was skipped
    results = [result for result in results if result is not None]

    # Merge results from all directories
    all_X, all_Y = [], []
    for result in results:
        all_X.extend(result['X'])
        all_Y.extend(result['Y'])

    append_to_pickle({'X': all_X, 'Y': all_Y}, 'image_batch0.pkl')

# create main function
def main():
    process_images_and_annotations_parallel('../MPIIGaze/Data/Original')

# call main function
if __name__ == '__main__':
    main()