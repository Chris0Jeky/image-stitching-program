import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import compose


class ComposeLimitsTests(unittest.TestCase):
    def test_unused_corrupt_fifth_image_is_never_opened(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "images"
            images.mkdir()
            photos = [images / f"{n}.jpg" for n in range(1, 5)]
            for n, photo in enumerate(photos):
                with Image.new("RGB", (12 + n, 8 + n), (n * 60, 80, 120)) as image:
                    image.save(photo)

            with patch.object(compose, "IMAGES_DIR", images), \
                    patch.object(compose, "LOGO_PATH", root / "missing.png"), \
                    patch("builtins.print"):
                control = root / "control"
                with patch.object(compose, "OUTPUT_DIR", control):
                    compose.main()
                expected = {f"collage_{n}.jpg": (control / f"collage_{n}.jpg").read_bytes()
                            for n in (2, 3, 4)}

                (images / "5.jpg").write_bytes(b"corrupt unused photo")
                output = root / "output"
                with patch.object(compose, "OUTPUT_DIR", output), \
                        patch.object(compose.Image, "open", wraps=Image.open) as decoder:
                    compose.main()
                self.assertEqual([call.args[0] for call in decoder.call_args_list], photos)
                self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()},
                                 expected)

    def test_source_pixel_limit_is_checked_before_decode_and_closes_file(self):
        with tempfile.TemporaryDirectory() as directory:
            photo = Path(directory) / "photo.png"
            with Image.new("RGB", (4, 3)) as image:
                image.save(photo)
            with patch.object(compose, "MAX_IMAGE_PIXELS", 12, create=True):
                frames = compose.load_and_normalise([photo])
                self.assertEqual(frames[0].size, (4, 3))
                frames[0].close()

            source = Image.open(photo)
            file_handle = source.fp
            try:
                with patch.object(compose, "MAX_IMAGE_PIXELS", 11, create=True), \
                        patch.object(compose.Image, "open", return_value=source), \
                        patch.object(source, "load", side_effect=AssertionError("decoded oversized image")):
                    with self.assertRaisesRegex(ValueError, "pixel limit"):
                        compose.load_and_normalise([photo])
                self.assertTrue(file_handle.closed)
            finally:
                source.close()

    def test_canvas_pixel_limit_is_checked_before_allocation(self):
        with Image.new("RGB", (4, 3)) as frame, \
                patch.object(compose, "MAX_COLLAGE_PIXELS", 24, create=True):
            with compose.stitch_row([frame, frame]) as canvas:
                self.assertEqual(canvas.size, (8, 3))
            with patch.object(compose, "MAX_COLLAGE_PIXELS", 23), \
                    patch.object(compose.Image, "new", side_effect=AssertionError("allocated oversized canvas")):
                with self.assertRaisesRegex(ValueError, "pixel limit"):
                    compose.stitch_row([frame, frame])


if __name__ == "__main__":
    unittest.main()
