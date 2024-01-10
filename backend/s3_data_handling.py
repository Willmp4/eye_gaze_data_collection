import boto3
import csv
import cv2
import json
import logging
import numpy as np
import uuid
from io import BytesIO, StringIO

logging.basicConfig(level=logging.DEBUG)

def capture_and_save(user_id, original_frame, additional_data, data_type='eye_gaze', s3_client=boto3.client('s3'), bucket_name='eye-gaze-data'):
    user_data_dir = f'data/{user_id}/'
    metadata_file = f'{user_data_dir}metadata.json'
    img_dir = f'{user_data_dir}{data_type}_images/'
    csv_name = f'{user_data_dir}{data_type}_data.csv'

    img_name, data_row = prepare_data_and_image(user_id, original_frame, additional_data, img_dir, data_type)
    upload_image_to_s3(s3_client, bucket_name, f'{img_dir}{img_name}', original_frame)
    append_data_to_csv(s3_client, bucket_name, csv_name, data_row)
    if data_type == 'calibration':
        # Assuming additional_data[1] is screen_data and additional_data[2:] is camera_info
        metadata = {
            "screenData": additional_data[1] if len(additional_data) > 1 else None,
            "cameraInfo": additional_data[2:] if len(additional_data) > 2 else None
        }
        update_metadata_if_changed(s3_client, bucket_name, metadata_file, metadata)

def prepare_data_and_image(user_id, original_frame, additional_data, img_dir, data_type):
    unique_id = uuid.uuid4()
    img_name = f'{user_id}_{unique_id}.png'
    data_row = format_data_row(additional_data, f'{img_dir}{img_name}', data_type)
    return img_name, data_row

def format_data_row(additional_data, img_path, data_type):
    if data_type == 'eye_gaze':
        cursor_pos = additional_data[0] if len(additional_data) > 0 else ('', '')
        return [img_path, cursor_pos['x'], cursor_pos['y']]
    elif data_type == 'calibration':
        calibration_point = additional_data[0] if len(additional_data) > 0 else ('', '')
        return [img_path, calibration_point[0], calibration_point[1]]
    else:
        # Handle other data types if needed
        return [img_path]

def upload_image_to_s3(s3_client, bucket_name, img_path, original_frame):
    try:
        _, buffer = cv2.imencode('.png', original_frame)
        img_bytes = BytesIO(buffer)
        s3_client.upload_fileobj(img_bytes, bucket_name, img_path)
        logging.info(f"Successfully uploaded {img_path} to S3.")
    except Exception as e:
        logging.error(f"Error uploading to S3: {e}")

def append_data_to_csv(s3_client, bucket_name, csv_name, data_row):
    try:
        existing_data = get_existing_csv_data(s3_client, bucket_name, csv_name)
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        writer.writerow(data_row)
        all_data = existing_data + csv_data.getvalue()
        s3_client.put_object(Body=all_data, Bucket=bucket_name, Key=csv_name)
        logging.info("Successfully appended to CSV in S3.")
    except Exception as e:
        logging.error(f"Error updating CSV in S3: {e}")

def update_metadata_if_changed(s3_client, bucket_name, metadata_file, camera_info):
    if camera_info:
        try:
            # Ensure all NumPy arrays are converted to lists
            camera_info_serializable = convert_numpy_arrays_to_lists(camera_info)

            s3_client.put_object(Body=json.dumps(camera_info_serializable), Bucket=bucket_name, Key=metadata_file)
            logging.info("Successfully updated metadata in S3.")
        except Exception as e:
            logging.error(f"Error updating metadata in S3: {e}")

def convert_numpy_arrays_to_lists(data):
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, dict):
        return {key: convert_numpy_arrays_to_lists(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_arrays_to_lists(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(convert_numpy_arrays_to_lists(item) for item in data)
    return data

def get_existing_csv_data(s3_client, bucket_name, csv_name):
    try:
        return s3_client.get_object(Bucket=bucket_name, Key=csv_name)['Body'].read().decode('utf-8')
    except s3_client.exceptions.NoSuchKey:
        logging.info("CSV file does not exist. A new file will be created.")
        return ''
