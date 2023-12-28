import dlib
import cv2
import numpy as np
import boto3
import time
import csv
import json
import logging
from io import BytesIO, StringIO

logging.basicConfig(level=logging.DEBUG)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

def extract_eye_region(image, landmarks, eye_points):
    # Extract the coordinates of the eye points
    region = np.array([(landmarks.part(point).x, landmarks.part(point).y) for point in eye_points])
    # Create a mask with zeros
    height, width = image.shape[:2]
    mask = np.zeros((height, width), np.uint8)
    # Fill the mask with the polygon defined by the eye points
    cv2.fillPoly(mask, [region], 255)
    # Bitwise AND operation to isolate the eye region
    eye = cv2.bitwise_and(image, image, mask=mask)
    # Cropping the eye region
    (min_x, min_y) = np.min(region, axis=0)
    (max_x, max_y) = np.max(region, axis=0)
    cropped_eye = eye[min_y:max_y, min_x:max_x]
    return cropped_eye, (min_x, min_y, max_x, max_y)


def detect_pupil(eye_image):
    # Apply Gaussian Blur
    blurred_eye = cv2.GaussianBlur(eye_image, (7, 7), 0)
    # Adaptive thresholding to binarize the image
    thresholded_eye = cv2.adaptiveThreshold(blurred_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed_eye = cv2.morphologyEx(thresholded_eye, cv2.MORPH_CLOSE, kernel, iterations=2)
    # Find contours which will give us the pupil
    contours, _ = cv2.findContours(morphed_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Assume the largest contour is the pupil
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    if contours:
        # Calculate the centroid of the pupil
        M = cv2.moments(contours[0])
        if M['m00'] != 0:
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            return (cx, cy), contours[0]
    contours, _ = cv2.findContours(morphed_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        # Approximate the contour to reduce the number of points
        approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
        area = cv2.contourArea(approx)
        # Assume the pupil will be the largest, roughly circular contour
        if len(approx) > 5 and area > 100:  # Adjust threshold as needed
            (x, y), radius = cv2.minEnclosingCircle(approx)
            center = (int(x), int(y))
            radius = int(radius)
            if radius > 1:  # Avoid tiny contours
                return center, contour
    return None, None


def convert_eye_to_binary(eye_image):
    # Convert to grayscale if the image is not already
    if len(eye_image.shape) == 3:
        gray_eye = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)
    else:
        gray_eye = eye_image
    
    # Apply Gaussian Blur
    blurred_eye = cv2.GaussianBlur(gray_eye, (7, 7), 0)
    
    # Apply a binary adaptive threshold to the image
    binary_eye = cv2.adaptiveThreshold(
        blurred_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    return binary_eye

s3_client = boto3.client('s3')
bucket_name = 'eye-gaze-data'

def capture_and_save(user_id, original_frame, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, additional_data, data_type='eye_gaze'):
    user_data_dir = f'data/{user_id}/'
    metadata_file = f'{user_data_dir}metadata.json'

    if data_type == 'calibration':
        img_dir = f'{user_data_dir}calibration_images/'
        csv_name = f'{user_data_dir}calibration_data.csv'
        calibration_points, screen_data = additional_data
        head_pose = None
        rotation_vector, translation_vector = head_pose if head_pose else (np.zeros((3,1)), np.zeros((3,1)))
        rotation_vector_str = ','.join(map(str, rotation_vector.flatten()))
        translation_vector_str = ','.join(map(str, translation_vector.flatten()))

        data_row = [
            calibration_points[0], calibration_points[1],  # X, Y coordinates of calibration point
            left_eye_info[0], left_eye_info[1],
            left_eye_bbox[0], left_eye_bbox[1], left_eye_bbox[2], left_eye_bbox[3],
            right_eye_info[0], right_eye_info[1],
            right_eye_bbox[0], right_eye_bbox[1], right_eye_bbox[2], right_eye_bbox[3],
            rotation_vector_str, translation_vector_str
        ]
    else:
        img_dir = f'{user_data_dir}images/'
        csv_name = f'{user_data_dir}data.csv'
        cursor_x, cursor_y, screen_data, head_pose = additional_data
        rotation_vector, translation_vector = head_pose if head_pose else (np.zeros((3,1)), np.zeros((3,1)))
        rotation_vector_str = ','.join(map(str, rotation_vector.flatten()))
        translation_vector_str = ','.join(map(str, translation_vector.flatten()))

        
        data_row = [
            cursor_x, cursor_y,
            left_eye_info[0], left_eye_info[1],
            left_eye_bbox[0], left_eye_bbox[1], left_eye_bbox[2], left_eye_bbox[3],
            right_eye_info[0], right_eye_info[1],
            right_eye_bbox[0], right_eye_bbox[1], right_eye_bbox[2], right_eye_bbox[3],
            rotation_vector_str, translation_vector_str
        ]
    
    if screen_data_changed(bucket_name, metadata_file, screen_data, s3_client):
        # Handle the change here, like updating the metadata in S3
        if screen_data != None and len(screen_data) > 0 and screen_data !='null':
            try:
                s3_client.put_object(Body=json.dumps(screen_data), Bucket=bucket_name, Key=metadata_file)
                logging.info("Successfully updated metadata in S3.")
            except Exception as e:
                logging.error(f"Error updating metadata in S3: {e}")


    img_name = f'{img_dir}{user_id}_{int(time.time())}.png'
    data_row.insert(0, img_name)  # Insert the image name at the beginning of the row
    
    _, buffer = cv2.imencode('.png', original_frame)
    img_bytes = BytesIO(buffer)

    # Upload image to S3
    try:
        s3_client.upload_fileobj(img_bytes, bucket_name, img_name)
        logging.info(f"Successfully uploaded {img_name} to S3.")
    except Exception as e:
        logging.error(f"Error uploading to S3: {e}")

    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(data_row)
    csv_data.seek(0)

    # Append to existing CSV file or create a new one if it doesn't exist
    try:
        existing_data = ''
        try:
            existing_data = s3_client.get_object(Bucket=bucket_name, Key=csv_name)['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            logging.info("CSV file does not exist. A new file will be created.")

        all_data = existing_data + csv_data.getvalue()
        s3_client.put_object(Body=all_data, Bucket=bucket_name, Key=csv_name)
        logging.info("Successfully appended to CSV in S3.")
    except Exception as e:
        logging.error(f"Error updating CSV in S3: {e}")


def screen_data_changed(bucket_name, metadata_file, screen_data, s3_client):
    """
    Check if the metadata file in the S3 bucket is different from the provided screen_data.
    """
    try:
        # Download the metadata file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=metadata_file)
        existing_data = json.load(response['Body'])
        return existing_data != screen_data
    except s3_client.exceptions.NoSuchKey:
        # File does not exist in the bucket
        return True
    except Exception as e:
        logging.error(f"Error accessing S3: {e}")
        return True

