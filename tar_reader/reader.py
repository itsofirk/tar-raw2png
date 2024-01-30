import io
import tarfile
from time import perf_counter
from PIL import Image
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from functools import partial

GRAYSCALE = "L"  # mode for 8-bit images


class SupportedFormats(Enum):
    PNG = "PNG"
    # JPEG = "JPEG"


class TarRawImagesConverter:
    def __init__(self, target_format=SupportedFormats.PNG, **pillow_preferences):
        self.target_format = target_format.value
        self.pillow_preferences = pillow_preferences

    def convert_raw_image(self, raw_data: bytes, resolution: tuple[int, int], mode=GRAYSCALE):
        image = Image.frombytes(mode, resolution, raw_data)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format=self.target_format, **self.pillow_preferences)
        image_buffer.seek(0)

        return image_buffer

    def process_member(self, member, tar, resolution):
        raw_data = tar.extractfile(member).read()
        png_buffer = self.convert_raw_image(raw_data, resolution)
        return self._get_new_image_name(member.name), png_buffer

    def convert_tar(self, input_tar_path, resolution, image_list=None, output_tar_path=None):
        if output_tar_path is None:
            output_tar_path = self._get_output_name(input_tar_path)
        with (tarfile.open(input_tar_path, 'r') as input_tar,
              tarfile.open(output_tar_path, 'w') as output_tar):
            members_to_convert = self._get_members_to_process(input_tar, image_list)

            _process_image = partial(self.process_member, tar=input_tar, resolution=resolution)
            with ThreadPoolExecutor() as executor:
                for png_name, png_buffer in executor.map(_process_image, members_to_convert):
                    png_member = tarfile.TarInfo(name=png_name)
                    png_member.size = len(png_buffer.getvalue())
                    output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))

    def _get_members_to_process(self, input_tar, image_list=None):
        if image_list is None:
            return input_tar.getmembers()
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
        return input_tar_path.replace('.tar', '_converted.tar')

    def _get_new_image_name(self, old_name):
        return f'{old_name[:-4]}.{self.target_format.lower()}'


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames.tar'
    output_path = '..\\output\\example_frames.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as f:
        image_list = [f.strip() for f in f.readlines()]
    png_converter = TarRawImagesConverter(SupportedFormats.PNG, compress_level=0)
    print(f"Processing {len(image_list)} files...")
    start_time = perf_counter()
    png_converter.convert_tar(tar_path, resolution_1280_720, image_list, output_path)
    end_time = perf_counter()
    print(f"Done! Time taken: {end_time - start_time:.2f} seconds.")
