import io
import tarfile
from time import perf_counter
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import numpy as np

from tar_reader.consts import SupportedFormats, RAW, GRAYSCALE, KB, NEW_TAR_SUFFIX, TAR


class TarRawImagesConverter:
    def __init__(self, target_format=SupportedFormats.PNG, **pillow_preferences):
        self.target_format = target_format.value
        self.pillow_preferences = pillow_preferences

    def convert_raw_image(self, raw_data: bytes, resolution: tuple[int, int], mode=GRAYSCALE):
        image = Image.frombytes(mode, resolution, raw_data)

        # Calculate average pixel value and standard deviation
        pixel_values = np.array(image).flatten()
        average_pixel_value = np.mean(pixel_values)
        std_dev_pixel_value = np.std(pixel_values)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format=self.target_format, **self.pillow_preferences)
        image_buffer.seek(0)

        return image_buffer, average_pixel_value, std_dev_pixel_value

    def process_member(self, member, tar, resolution):
        raw_data = tar.extractfile(member).read()
        png_buffer, average_pixel_value, std_dev_pixel_value = self.convert_raw_image(raw_data, resolution)
        statistics = {
            "average_pixel_value": average_pixel_value,
            "std_dev_pixel_value": std_dev_pixel_value,
            "new_name": self._get_new_image_name(member.name)
        }
        return statistics, png_buffer

    def convert_tar(self, input_tar_path, resolution, image_list=None, output_tar_path=None, bufsize=16 * 1024):
        if output_tar_path is None:
            output_tar_path = self._get_output_name(input_tar_path)
        average_pixel_values = []
        std_dev_pixel_values = []
        with (tarfile.open(input_tar_path, 'r', bufsize=bufsize) as input_tar,
              tarfile.open(output_tar_path, 'w', bufsize=bufsize) as output_tar):
            members_to_convert = self._get_members_to_process(input_tar, image_list)
            _process_image = partial(self.process_member, tar=input_tar, resolution=resolution)
            print(f"Converting {len(members_to_convert)} images...")
            with ThreadPoolExecutor() as executor:
                for metadata, png_buffer in executor.map(_process_image, members_to_convert):
                    png_member = tarfile.TarInfo(name=metadata["new_name"])
                    png_member.size = len(png_buffer.getvalue())
                    output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))
                    average_pixel_values.append(metadata["average_pixel_value"])
                    std_dev_pixel_values.append(metadata["std_dev_pixel_value"])
            print(f"Done. Converted {len(members_to_convert)} images.")
        print(f"Average pixel values: {average_pixel_values}")
        print(f"Standard deviation pixel values: {std_dev_pixel_values}")

    def _get_members_to_process(self, input_tar, image_list=None):
        if image_list is None:
            return [f for f in input_tar.getmembers() if f.name.endswith(RAW)]
        image_list = set(image_list)
        members_to_convert = []
        for member in input_tar.getmembers():
            if member.name in image_list:
                image_list.remove(member.name)
                members_to_convert.append(member)
        if image_list:
            raise ValueError(f"Could not find images in the provided tar file: {image_list}")
        return members_to_convert

    def _get_output_name(self, input_tar_path):
        return input_tar_path.replace(TAR, NEW_TAR_SUFFIX)

    def _get_new_image_name(self, old_name):
        return f'{old_name[:-4]}.{self.target_format.lower()}'


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames.tar'
    output_path = '..\\output\\example_frames_converted.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as list_file:
        image_list = [f.strip() for f in list_file.readlines()]
    png_converter = TarRawImagesConverter(SupportedFormats.PNG, compress_level=0)
    print(f"Converting images in {tar_path} to {output_path}...")
    start_time = perf_counter()
    png_converter.convert_tar(tar_path, resolution_1280_720, bufsize=16 * KB, image_list=image_list, output_tar_path=output_path)
    end_time = perf_counter()
    print(f"Done! Time taken: {end_time - start_time:.2f} seconds.")
