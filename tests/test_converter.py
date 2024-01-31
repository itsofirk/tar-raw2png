import unittest
from unittest.mock import Mock, patch
from tarfile import TarInfo
from tar_converter.converter import _process_member, convert_raw_image, _get_members_to_process


class TarRawImagesConverterTests(unittest.TestCase):
    def test_convert_raw_image(self):
        raw_image_path = "resources/test_image.raw"
        expected_image_path = "resources/test_image.png"

        resolution = (1280, 720)
        mode = "L"  # mode for 8-bit images

        with open(raw_image_path, "rb") as f:
            raw_data = f.read()
        with open(expected_image_path, "rb") as f:
            expected_data = f.read()

        image_buffer, _, _ = convert_raw_image(raw_data, resolution, mode)

        # Assertions
        self.assertEqual(image_buffer.getvalue(), expected_data)

    @patch("tar_converter.converter.convert_raw_image")
    def test_process_member(self, mock_convert_raw_image):
        mock_tar = Mock()
        mock_member = Mock()
        mock_member.name = "test_image.raw"
        mock_tar.extractfile.return_value.read.return_value = b"raw_data"

        mock_convert_raw_image.return_value = (b"png_data", 45.6, 12.3)

        statistics, png_buffer = _process_member(mock_member, mock_tar, None)

        # Assertions
        expected_statistics = {
            "average_pixel": 45.6,
            "std_dev_pixel": 12.3,
            "new_name": "test_image.png"
        }
        self.assertEqual(statistics, expected_statistics)
        self.assertEqual(png_buffer, b"png_data")

    def test_get_members_to_process_with_image_list(self):
        input_tar_mock = Mock()

        members = [TarInfo("image1.raw"), TarInfo("image2.jpg"), TarInfo("image3.raw")]
        input_tar_mock.getmembers.return_value = members
        image_list = ["image1.raw", "image3.raw"]

        members_to_convert = _get_members_to_process(input_tar_mock, image_list)

        expected_members_to_convert = [members[0], members[2]]

        # Assertions
        self.assertEqual(members_to_convert, expected_members_to_convert)

    def test_get_members_to_process_without_image_list(self):
        input_tar_mock = Mock()

        members = [TarInfo("image1.raw"), TarInfo("image2.jpg"), TarInfo("image3.raw")]
        input_tar_mock.getmembers.return_value = members

        members_to_convert = _get_members_to_process(input_tar_mock)

        expected_members_to_convert = [members[0], members[2]]
        self.assertEqual(members_to_convert, expected_members_to_convert)

    def test_get_members_to_process_with_missing_images(self):
        input_tar_mock = Mock()

        members = [TarInfo("image1.raw"), TarInfo("image2.jpg"), TarInfo("image3.raw")]
        input_tar_mock.getmembers.return_value = members
        image_list = ["image1.raw", "image4.raw"]

        # Assertions
        with self.assertRaises(ValueError):
            _get_members_to_process(input_tar_mock, image_list)


if __name__ == '__main__':
    unittest.main()
