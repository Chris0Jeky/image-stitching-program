import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

import compose


class ComposeOrientationTests(unittest.TestCase):
    def test_exif_orientation_is_applied_before_scaling_and_height_alignment(self):
        rotations = {3: Image.Transpose.ROTATE_180,
                     6: Image.Transpose.ROTATE_270,
                     8: Image.Transpose.ROTATE_90}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            photo = root / "camera.jpg"
            upright = root / "upright.jpg"
            with Image.new("RGB", (120, 60), "blue") as image:
                image.save(upright)

            for orientation in (None, 1, 3, 6, 8):
                with Image.new("RGB", (60, 120), "white") as image:
                    image.paste("red", (0, 0, 60, 20))
                    image.paste("green", (0, 20, 15, 120))
                    exif = Image.Exif()
                    if orientation is not None:
                        exif[274] = orientation
                    image.save(photo, exif=exif)

                for target_height in (1200, 30):
                    with self.subTest(orientation=orientation, target_height=target_height), \
                            patch.object(compose, "TARGET_HEIGHT", target_height):
                        frames = compose.load_and_normalise([photo, upright])
                        try:
                            height = min(60, target_height)
                            width = (2 * height if orientation in (6, 8) else height // 2)
                            self.assertEqual([frame.size for frame in frames],
                                             [(width, height), (2 * height, height)])
                            with Image.open(photo) as source:
                                expected = source.convert("RGB")
                            if orientation in rotations:
                                rotated = expected.transpose(rotations[orientation])
                                expected.close()
                                expected = rotated
                            with expected:
                                with expected.resize((width, height), Image.LANCZOS) as resized:
                                    with ImageChops.difference(frames[0], resized) as difference:
                                        self.assertIsNone(difference.getbbox())
                            self.assertIn(frames[0].getexif().get(274), (None, 1))
                            with Image.open(upright) as source:
                                with source.resize(frames[1].size, Image.LANCZOS) as expected_upright, \
                                        ImageChops.difference(frames[1], expected_upright) as difference:
                                    self.assertIsNone(difference.getbbox())
                        finally:
                            for frame in frames:
                                frame.close()


if __name__ == "__main__":
    unittest.main()
