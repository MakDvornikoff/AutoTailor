import unittest
import numpy as np
from autotailor.processor import rotate_image, clean_background_grayscale

class TestProcessor(unittest.TestCase):
    def test_rotate(self):
        # Create a dummy 3-channel image (height=100, width=200)
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        # Rotate 90 degrees
        rotated = rotate_image(img, 90)
        self.assertEqual(rotated.shape[0], 200)
        self.assertEqual(rotated.shape[1], 100)

    def test_clean_grayscale(self):
        # Create a dummy white image (height=100, width=100)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cleaned = clean_background_grayscale(img)
        self.assertEqual(cleaned.shape, (100, 100))

if __name__ == '__main__':
    unittest.main()
