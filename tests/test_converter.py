import unittest
from tar_converter.converter import TarRawImagesConverter


class TarRawImagesConverterTests(unittest.TestCase):
    def setUp(self):
        self.converter = TarRawImagesConverter()

    def test_convert_raw_image(self):
        raw_image_path = "resources/test_image.raw"
        expected_image_path = "resources/test_image.png"

        resolution = (1280, 720)
        mode = "L"  # mode for 8-bit images

        with open(raw_image_path, "rb") as f:
            raw_data = f.read()
        with open(expected_image_path, "rb") as f:
            expected_data = f.read()

        image_buffer, _, _ = self.converter.convert_raw_image(raw_data, resolution, mode)

        self.assertEqual(image_buffer.getvalue(), expected_data)

    def test_process_member(self):
        # TODO: Implement test for process_member method
        pass

    def test_get_new_image_name(self):
        # TODO: Implement test for _get_new_image_name method
        pass

    def test_get_members_to_process(self):
        # TODO: Implement test for _get_members_to_process method
        pass

    def test_convert_tar(self):
        # TODO: Implement test for convert_tar method
        pass


if __name__ == '__main__':
    unittest.main()
