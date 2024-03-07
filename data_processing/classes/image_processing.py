from classes.blink_detector import BlinkDetector
import cv2
import numpy as np
import matplotlib.pyplot as plt

class ImageProcessor:
    def __init__(self, detector, predictor):
        self.detector = detector
        self.predictor = predictor

    def extract_eye_region(self, image, landmarks, left_eye_points, right_eye_points, nose_bridge_points, forehead_points):
        # Combine the eye, nose bridge, and forehead points
        eye_points = left_eye_points + right_eye_points
        all_points = eye_points + nose_bridge_points + forehead_points

        # Extract the coordinates of the combined points
        region = np.array([(landmarks.part(point).x, landmarks.part(point).y) for point in all_points])

        # Find the bounding box coordinates
        min_x = np.min(region[:, 0])
        max_x = np.max(region[:, 0])
        min_y = np.min(region[:, 1])
        max_y = np.max(region[:, 1])

        # Crop the region to create a rectangle
        cropped_region = image[min_y:max_y, min_x:max_x]

        return cropped_region, (min_x, min_y, max_x, max_y)

    def detect_pupil(self, eye_image):
        # Enhance resolution
        eye_image = self.enhance_image_resolution(eye_image, self.sr_model)

        gray = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)

        gray = cv2.equalizeHist(gray)  # Histogram Equalization
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)  # Gaussian Blur

        # Find contours
        contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Sort contours by area and filter
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.circle(eye_image, (cX, cY), 7, (255, 255, 255), -1)
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
                eye_center = np.mean(eye_landmarks, axis=0).astype(int)  # Ensure you have integers for the center
                eye_image, (eye_min_x, eye_min_y, eye_max_x, eye_max_y) = self.extract_eye_region(image, shape, range(start, end))
    
                pupil_center, pupil_contour = self.detect_pupil(eye_image, eye_center)
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
    
    def get_combined_eyes(self, frame, global_detector, global_predictor, target_size=(200, 100)):
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
            left_eye_landmarks = [36, 37, 38, 39, 40, 41]
            right_eye_landmarks = [42, 43, 44, 45, 46, 47]
            nose_bridge_points = [27, 28, 29]

            blink_detctor = BlinkDetector()
            
            if blink_detctor.detect_blink(landmarks, left_eye_landmarks, right_eye_landmarks):
                print("Blink Detected")

            combined_eye_region, _ = self.extract_eye_region(
                frame, landmarks, left_eye_landmarks, right_eye_landmarks, nose_bridge_points, forehead_points)

            if isinstance(combined_eye_region, np.ndarray):

                # Apply super-resolution
                # combined_eye_super_res = ImageProcessor.enhance_image_resolution(combined_eye_region, global_sr_model)

                # Resize to the final target size
                combined_eye_final_resized = cv2.resize(combined_eye_region, target_size, interpolation=cv2.INTER_AREA)

                # combined_eye_final_resized = cv2.cvtColor(combined_eye_final_resized, cv2.COLOR_BGR2GRAY)
                combined_eye_final_resized = combined_eye_final_resized.astype(np.float32) / 255.0

                return combined_eye_final_resized

        return None
        
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
