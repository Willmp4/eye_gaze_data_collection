import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, detector, predictor, sr_model):
        self.detector = detector
        self.predictor = predictor
        self.sr_model = sr_model

    # Rest of your methods, utilizing the passed-in resources

    
    def enhance_image_resolution(self, image, sr_model):
        # Enhance the resolution of the image using the preloaded model
        enhanced_image = sr_model.upsample(image)
        return enhanced_image

    def extract_eye_region(self, image, landmarks, eye_points, buffer=3):
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

    def detect_pupil(self, eye_image):
        # Enhance resolution
        eye_image = self.enhance_image_resolution(eye_image, self.sr_model)

        # Preprocessing
        gray = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)  # Histogram Equalization
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)  # Gaussian Blur

        # Edge detection
        edged = cv2.Canny(blurred, 50, 100)

        # Find contours
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area and filter
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        # Find contours
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area and filter
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for contour in contours:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)

            # The pupil will be the first contour that is sufficiently circular
            area = cv2.contourArea(contour)
            if area > 30:  # You may need to adjust this threshold
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    return (cX, cY), contour

        return None, None
    
    def pre_process_image(self, image):        
        # Initialize variables
        left_eye_info = right_eye_info = left_eye_bbox = right_eye_bbox = None

        dlib_faces = self.detector(image)
        processed_data = []
        for dlib_face in dlib_faces:
            shape = self.predictor(image, dlib_face)

            for (i, (start, end)) in enumerate([(36,42), (42,48)]):
                eye_landmarks = [(shape.part(point).x, shape.part(point).y) for point in range(start, end)]

                eye_image, (eye_min_x, eye_min_y, eye_max_x, eye_max_y) = self.extract_eye_region(image, shape, range(start, end))

                pupil_center, pupil_contour = self.detect_pupil(eye_image)
                # After detecting the pupil in the cropped eye image:
                if pupil_center:
                    # Scale the pupil center coordinates down to the original image size
                    pupil_center_original = (pupil_center[0] / 4, pupil_center[1] / 4)
                    # Transform these coordinates to the global space of the original image
                    pupil_center_global = (int(pupil_center_original[0]) + eye_min_x, int(pupil_center_original[1]) + eye_min_y)
        
                    pupil_center_global = tuple(pc.item() if isinstance(pc, np.generic) else pc for pc in pupil_center_global)

                    bounding_box = (eye_min_x, eye_min_y, eye_max_x - eye_min_x, eye_max_y - eye_min_y)
                    bounding_box = tuple(bb.item() if isinstance(bb, np.generic) else bb for bb in bounding_box)

                    eye_data = {
                        'eye_position': 'left' if i == 0 else 'right',
                        'pupil_center': pupil_center_global,
                        'bounding_box': bounding_box
                    }
                    processed_data.append(eye_data)

            # Processed data for each eye
        for eye_data in processed_data:
            if eye_data['eye_position'] == 'left':
                left_eye_info = eye_data['pupil_center']
                left_eye_bbox = eye_data['bounding_box']
            else:
                right_eye_info = eye_data['pupil_center']
                right_eye_bbox = eye_data['bounding_box']
        
        # Check if any eye information was detected
        if left_eye_info is None and right_eye_info is None:
            print("No eye information detected")
            return None

        return processed_data, left_eye_info, right_eye_info, left_eye_bbox, right_eye_bbox, shape
    
    def get_head_pose(self, shape, camera_matrix, dist_coeffs):
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