import dlib
import cv2
import numpy as np
import logging
from io import BytesIO, StringIO


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

def get_head_pose(shape, camera_matrix, dist_coeffs):
    # Define the model points (the points in a generic 3D model face)
    model_points = np.array([
           (0.0, 0.0, 0.0),             # Nose tip
           (0.0, -330.0, -65.0),        # Chin
           (-225.0, 170.0, -135.0),     # Left eye left corner
           (225.0, 170.0, -135.0),      # Right eye right corne
           (-150.0, -150.0, -125.0),    # Left Mouth corner
           (150.0, -150.0, -125.0)      # Right mouth corner
       ])
   # 2D image points from the facial landmark detection
    image_points = np.array([
            (shape.part(30).x, shape.part(30).y),     # Nose tip
            (shape.part(8).x, shape.part(8).y),       # Chin
            (shape.part(36).x, shape.part(36).y),     # Left eye left corner
            (shape.part(45).x, shape.part(45).y),     # Right eye right corner
            (shape.part(48).x, shape.part(48).y),     # Left Mouth corner
            (shape.part(54).x, shape.part(54).y)      # Right mouth corner
        ], dtype="double")


    (success, rotation_vector, translation_vector) = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)

    return rotation_vector, translation_vector


