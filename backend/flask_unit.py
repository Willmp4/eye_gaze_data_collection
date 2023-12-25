import unittest
import json
from app import app

class FlaskTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True 

    def test_process_image(self):
        with open('../test_images/eye_head_capture_1702669170.120304.png', 'rb') as img:
            response = self.app.post('/process-image',
                                     content_type='multipart/form-data',
                                     data={'image': img})

        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], "Image processed successfully!")

if __name__ == "__main__":
    unittest.main()