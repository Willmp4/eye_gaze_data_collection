import json
from flask import Flask, request, jsonify
import cv2
import dlib
import io
import os 
import csv
import numpy as np
from flask_cors import CORS
import logging
from image_processing import detect_pupil, extract_eye_region, convert_eye_to_binary, capture_and_save, get_head_pose
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})



detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

def pre_process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dlib_faces = detector(gray)

    processed_data = []

    for dlib_face in dlib_faces:
        shape = predictor(gray, dlib_face)


        for (i, (start, end)) in enumerate([(36,42), (42,48)]):
            eye_image, (eye_min_x, eye_min_y, eye_max_x, eye_max_y) = extract_eye_region(gray, shape, range(start, end))
            eye_image_b = convert_eye_to_binary(eye_image)
            pupil_center, _ = detect_pupil(eye_image_b)

            if pupil_center:
                pupil_center_global = (pupil_center[0] + eye_min_x, pupil_center[1] + eye_min_y)
                pupil_center_global = tuple(pc.item() if isinstance(pc, np.generic) else pc for pc in pupil_center_global)
                bounding_box = (eye_min_x, eye_min_y, eye_max_x - eye_min_x, eye_max_y - eye_min_y)
                bounding_box = tuple(bb.item() if isinstance(bb, np.generic) else bb for bb in bounding_box)


                eye_data = {
                    'eye_position': 'left' if i == 0 else 'right',
                    'pupil_center': pupil_center_global,
                    'bounding_box': bounding_box
                }
                processed_data.append(eye_data)

                left_eye_info = None
                right_eye_info = None
                left_eye_bbox = None
                right_eye_bbox = None

                for eye_data in processed_data:
                    if eye_data['eye_position'] == 'left':
                        left_eye_info = eye_data['pupil_center']
                        left_eye_bbox = eye_data['bounding_box']
                    else:
                        right_eye_info = eye_data['pupil_center']
                        right_eye_bbox = eye_data['bounding_box']
        break
    return processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape

@app.route('/')
def index():
    return "Pupil Detection API"

@app.route('/calibrate', methods=['POST'])
def calibrate():
    user_id = request.form.get('userId')
    calibration_points = json.loads(request.form.get('calibrationPoints')) 
    screen_data = json.loads(request.form.get('screenData')) if request.form.get('screenData') else None
    camera_matrix_str = request.form.get('cameraMatrix')
    dist_coeffs_str = request.form.get('distCoeffs')
    
    # Parse camera matrix and distortion coefficients as numpy arrays
    camera_matrix = np.array(json.loads(camera_matrix_str)) if camera_matrix_str else None
    dist_coeffs = np.array(json.loads(dist_coeffs_str)) if dist_coeffs_str else None


    file = request.files['image']

    if file.filename == '':
        return jsonify({'message': "No image found!", "data": {}}), 400

    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)  # Fixed typo here
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)

    processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape = pre_process_image(image)
    rotation_vector, translation_vector = get_head_pose(shape, camera_matrix, dist_coeffs)

    if left_eye_info and right_eye_info:
        additional_data = [calibration_points, screen_data, (rotation_vector, translation_vector)]
        capture_and_save(user_id, image, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, additional_data, 'calibration')
        logging.info("Eye-gaze data saved successfully!")

    return jsonify({'message': "Calibration image processed successfully!", "data": processed_data})

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'message': "No image found!", "data": {}}), 400
    
    file = request.files['image']

    if file.filename == '':
        return jsonify({'message': "No image found!", "data": {}}), 400
    
    user_id = request.form.get('userId')
    camera_matrix_str = request.form.get('cameraMatrix')
    dist_coeffs_str = request.form.get('distCoeffs')
    
    # Parse camera matrix and distortion coefficients as numpy arrays
    camera_matrix = np.array(json.loads(camera_matrix_str)) if camera_matrix_str else None
    dist_coeffs = np.array(json.loads(dist_coeffs_str)) if dist_coeffs_str else None

    cursor_position = json.loads(request.form.get('cursorPosition')) if request.form.get('cursorPosition') else None
    screen_data = json.loads(request.form.get('screenData')) if request.form.get('screenData') else None
    
    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
    color_image_flag = 1
    image = cv2.imdecode(data, color_image_flag)

    processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape = pre_process_image(image)
    rotation_vector, translation_vector = get_head_pose(shape, camera_matrix, dist_coeffs)
    if left_eye_info and right_eye_info:
        additional_data = [cursor_position['x'], cursor_position['y'], screen_data, (rotation_vector, translation_vector)]
        capture_and_save(user_id, image, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, additional_data, 'eye-gaze')
        logging.info("Image saved successfully!")

    return jsonify({'message': "Image processed successfully!", "data": processed_data})



if __name__ == '__main__':
    app.run()