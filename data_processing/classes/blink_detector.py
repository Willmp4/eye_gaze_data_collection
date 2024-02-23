import math
import numpy as np

class BlinkDetector:
    def __init__(self, eye_aspect_ratio_threshold=5.7, consecutive_frames_threshold=2):
        self.eye_aspect_ratio_threshold = eye_aspect_ratio_threshold
        self.consecutive_frames_threshold = consecutive_frames_threshold
        self.blink_count = 0
        self.blinking = False

    def _midpoint(self, point1, point2):
        return (point1.x + point2.x) / 2, (point1.y + point2.y) / 2

    def _euclidean_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def _get_blink_ratio(self, eye_points, facial_landmarks):
        corner_left = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
        corner_right = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
        center_top = self._midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
        center_bottom = self._midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))
        horizontal_length = self._euclidean_distance(corner_left, corner_right)
        vertical_length = self._euclidean_distance(center_top, center_bottom)
        return horizontal_length / vertical_length

    def detect_blink(self, facial_landmarks, left_eye_points, right_eye_points):
        left_eye_ratio = self._get_blink_ratio(left_eye_points, facial_landmarks)
        right_eye_ratio = self._get_blink_ratio(right_eye_points, facial_landmarks)
        blink_ratio = (left_eye_ratio + right_eye_ratio) / 2

        if blink_ratio > self.eye_aspect_ratio_threshold:
            self.blinking = True
            self.blink_count += 1
            print("Blink Detected")
        else:
            self.blinking = False
