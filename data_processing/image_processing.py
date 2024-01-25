
import cv2
import numpy as np

def extract_eye_region(image, landmarks, eye_points, buffer= 5):
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
    min_x = max(min_x - buffer, 0)
    min_y = max(min_y - buffer, 0)
    max_x = min(max_x + buffer, width)
    max_y = min(max_y + buffer, height)
    cropped_eye = eye[min_y:max_y, min_x:max_x]
    return cropped_eye, (min_x, min_y, max_x, max_y)

def detect_pupil(eye_image):
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed_eye = cv2.morphologyEx(eye_image, cv2.MORPH_CLOSE, kernel, iterations=2)
    # Find contours which will give us the pupil
    contours, _ = cv2.findContours(morphed_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Assume the largest contour is the pupil
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    contours = [c for c in contours if cv2.contourArea(c) > 0]

    # Check contours
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * (area / (perimeter ** 2))

        # Check if contour is circular enough and of reasonable area
        if 0.1 < circularity < 1.1 and 7 < area < 500:
            M = cv2.moments(contour)
            if M['m00'] != 0:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                return (cx, cy), contour
        else:
            print(area, circularity)


    return None, None

def equalize_adaptive_histogram(image):
    # Convert to grayscale if the image is not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    return equalized

def apply_noise_reduction(image, method='gaussian', kernel_size=5):
    if method == 'gaussian':
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif method == 'median':
        return cv2.medianBlur(image, kernel_size)
    else:
        return image  # No noise reduction applied

def eye_aspect_ratio(eye_points):
    A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
    B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
    C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
    ear = (A + B) / (2.0 * C)
    return ear


def is_image_blurry(image, threshold=10):
    # Calculate the Laplacian of the image and then the focus
    # measure, which is the variance of the Laplacian
    variance_of_laplacian = cv2.Laplacian(image, cv2.CV_64F).var()
    return variance_of_laplacian < threshold


# Apply bilateral filter to an eye region
def apply_bilateral_filter(image, d=9, sigmaColor=75, sigmaSpace=75):
    return cv2.bilateralFilter(image, d, sigmaColor, sigmaSpace)

def convert_eye_to_binary(eye_image, blur_ksize=7, threshold_block_size=11, threshold_C=2):    
    # Convert to grayscale if the image is not already
    if len(eye_image.shape) == 3:
        gray_eye = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)
    else:
        gray_eye = eye_image
    
    # Apply bilateral filter instead of Gaussian blur
    blurred_eye = apply_bilateral_filter(gray_eye, d=9, sigmaColor=75, sigmaSpace=75)
    
    # Apply a binary adaptive threshold to the image
    binary_eye = cv2.adaptiveThreshold(
        blurred_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 
        threshold_block_size, threshold_C)
    
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


