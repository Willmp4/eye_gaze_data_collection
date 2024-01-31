import os
import pandas as pd
import numpy as np
class CSVManager:
    def __init__(self, local_base_dir):
        self.local_base_dir = local_base_dir

    def format_calibration_data_row(self, calibratoin_points, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose):
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

    def format_eye_gaze_data_row(self, cursors_position, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, head_pose):
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

    def create_and_replace_csv(self, local_base_dir, subdirectory, csv_file_name, image_data):
        # Path for the CSV file within the subdirectory
        csv_dir_path = os.path.join(local_base_dir, subdirectory)
        os.makedirs(csv_dir_path, exist_ok=True)  # Ensure the subdirectory exists
        csv_path = os.path.join(csv_dir_path, csv_file_name)
        
        # Create a new DataFrame for the CSV data
        new_data_df = pd.DataFrame(image_data)
        
        # Write the new DataFrame to the CSV file, overwriting the old data
        new_data_df.to_csv(csv_path, index=False, header=False)