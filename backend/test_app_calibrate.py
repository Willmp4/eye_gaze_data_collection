import unittest
import requests
import json

class TestS3BucketIntegration(unittest.TestCase):
    def test_post_to_process_image_endpoint(self):
        # URL of your Flask app's /process-image endpoint
        url = 'http://localhost:5000/calibrate'

        # Prepare the test data with JSON strings
        data = {
            'userId': 'test_user',
            'calibrationPoints': '[80, 9]',  # Convert list to JSON string
            'screenData': '[1080, 1780]', # Convert list to JSON string
            'cameraMatrix': '[[560,0,320],[0,560,240],[0,0,1]]',
            'distCoeffs': '[0,0,0,0,0]',

        }

        # Prepare the test file - Ensure the file exists at the specified path
        files = {
            'image': ('eye_head_capture_1702669188.0753756.png', open('./eye_head_capture_1702669188.0753756.png', 'rb'))
        }

        # Make the POST request to the /process-image endpoint
        response = requests.post(url, data=data, files=files)

        # Assert the response status code and any other expected behavior
        self.assertEqual(response.status_code, 200)
        # Additional assertions can be added as needed

        # Clean up: Close the file
        files['image'][1].close()

if __name__ == '__main__':
    unittest.main()
