import json
from flask import Flask, request, jsonify
import io
import numpy as np
from flask_cors import CORS
import logging
from s3_data_handling import capture_and_save
import cv2

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
        return jsonify({'message': "No image found!", 'data': {}}), 400

    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)

    # Capture and save data to S3
    additional_data = [calibration_points, screen_data, camera_matrix, dist_coeffs]
    capture_and_save(user_id, image, additional_data, 'calibration')

    return jsonify({'message': "Calibration image saved successfully!"})

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'message': "No image found!", 'data': {}}), 400
    
    user_id = request.form.get('userId')
    file = request.files['image']
    cursor_position = json.loads(request.form.get('cursorPosition')) if request.form.get('cursorPosition') else None
    screen_data = json.loads(request.form.get('screenData')) if request.form.get('screenData') else None

    if file.filename == '':
        return jsonify({'message': "No image found!", 'data': {}}), 400

    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)

    # Capture and save data to S3
    additional_data = [cursor_position]
    capture_and_save(user_id, image, additional_data, 'eye-gaze')

    return jsonify({'message': "Image saved successfully!"})

if __name__ == '__main__':
    app.run()
