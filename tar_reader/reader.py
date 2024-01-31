import io
import tarfile
from time import perf_counter
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import numpy as np

from tar_reader.consts import SupportedFormats, GRAYSCALE, KB


class TarRawImagesConverter:
    def __init__(self, target_format=SupportedFormats.PNG, **pillow_preferences):
        self.target_format = target_format
        self.pillow_preferences = pillow_preferences

    def convert_raw_image(self, raw_data: bytes, resolution: tuple[int, int], mode=GRAYSCALE):
        image = Image.frombytes(mode, resolution, raw_data)

        # Calculate average pixel value and standard deviation
        pixels = np.array(image).flatten()
        average_pixel = np.mean(pixels)
        std_dev_pixel = np.std(pixels)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format=self.target_format.name, **self.pillow_preferences)
        image_buffer.seek(0)

        return image_buffer, average_pixel, std_dev_pixel

    def process_member(self, member, tar, resolution):
        raw_data = tar.extractfile(member).read()
        png_buffer, average_pixel, std_dev_pixel = self.convert_raw_image(raw_data, resolution)
        statistics = {
            "average_pixel": average_pixel,
            "std_dev_pixel": std_dev_pixel,
            "new_name": self._get_new_image_name(member.name)
        }
        return statistics, png_buffer

    def convert_tar(self, input_tar_path, output_tar_path, resolution, image_list=None, bufsize=16 * KB):
        average_pixels = []
        std_dev_pixels = []
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
                    average_pixels.append(metadata["average_pixel"])
                    std_dev_pixels.append(metadata["std_dev_pixel"])
            print(f"Done. Converted {len(members_to_convert)} images.")
        print(f"Average pixel values: {average_pixels}")
        print(f"Standard deviation pixel values: {std_dev_pixels}")

    def _get_members_to_process(self, input_tar, image_list=None):
        if image_list is None:
            return [f for f in input_tar.getmembers()
                    if f.name.endswith(SupportedFormats.RAW.extension)]
        image_list = set(image_list)
        members_to_convert = []
        for member in input_tar.getmembers():
            if member.name in image_list:
                image_list.remove(member.name)
                members_to_convert.append(member)
        if image_list:
            raise ValueError(f"Could not find images in the provided tar file: {image_list}")
        return members_to_convert

    def _get_new_image_name(self, old_name):
        return old_name[:-4] + self.target_format.extension


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames_big.tar'
    output_path = '..\\output\\example_frames_big_converted.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as list_file:
        image_list = [f.strip() for f in list_file.readlines()]
    png_converter = TarRawImagesConverter(SupportedFormats.PNG, compress_level=0)
    print(f"Converting images in {tar_path} to {output_path}...")
    start_time = perf_counter()
    png_converter.convert_tar(tar_path, output_path, resolution_1280_720, image_list=image_list, bufsize=16 * KB)
    end_time = perf_counter()
    print(f"Done! Time taken: {end_time - start_time:.2f} seconds.")
