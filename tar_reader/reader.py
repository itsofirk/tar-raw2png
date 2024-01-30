import io
import tarfile
from time import perf_counter
from PIL import Image
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from functools import partial

GRAYSCALE = "L"  # "L" mode for 8-bit images


class SupportedFormats(Enum):
    PNG = "PNG"
    # JPEG = "JPEG"


def convert_raw_image(raw_data, resolution=(1280, 720), target_format=SupportedFormats.PNG):
    image = Image.frombytes(GRAYSCALE, resolution, raw_data)

    image_buffer = io.BytesIO()
    image.save(image_buffer, format=target_format.value)
    image_buffer.seek(0)

    return image_buffer


def process_tar_raw_member(member, tar, resolution, target_format=SupportedFormats.PNG):
    raw_data = tar.extractfile(member).read()
    png_buffer = convert_raw_image(raw_data, resolution, target_format)
    return member.name.replace('.raw', f'.{target_format.value}'), png_buffer


def process_tar_file(input_tar_path, output_tar_path, resolution, image_list):
    image_list = set(image_list)
    with (tarfile.open(input_tar_path, 'r') as input_tar,
          tarfile.open(output_tar_path, 'w') as output_tar):

        members_to_convert = []
        for member in input_tar.getmembers():
            if member.name in image_list:
                image_list.remove(member.name)
                members_to_convert.append(member)
        if image_list:
            raise ValueError(f"Could not find images in the provided tar file: {image_list}")

        _process_image = partial(process_tar_raw_member, tar=input_tar, resolution=resolution)
        with ThreadPoolExecutor() as executor:
            for png_name, png_buffer in executor.map(_process_image, members_to_convert):
                png_member = tarfile.TarInfo(name=png_name)
                png_member.size = len(png_buffer.getvalue())
                output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames.tar'
    output_path = '..\\output\\example_frames.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as f:
        image_list = [f.strip() for f in f.readlines()]

    print(f"Processing {len(image_list)} files...")
    start_time = perf_counter()
    process_tar_file(tar_path, output_path, resolution_1280_720, image_list)
    end_time = perf_counter()
    print(f"Done! Time taken: {end_time - start_time:.2f} seconds.")
