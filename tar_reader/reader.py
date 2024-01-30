import io
import struct
import tarfile
from PIL import Image
from enum import Enum

GRAYSCALE = "L"  # "L" mode for 8-bit images


class SupportedFormats(Enum):
    PNG = "PNG"
    # JPEG = "JPEG"


def convert_raw_to_png(raw_data, resolution=(1280, 720), target_format=SupportedFormats.PNG):
    # pixel_format = f"{resolution[0]}x{resolution[1]}B"
    pixel_format = "B" * resolution[0] * resolution[1]
    unpacked_data = struct.unpack(pixel_format, raw_data)

    image = Image.new(GRAYSCALE, resolution)
    image.putdata(unpacked_data)

    image_buffer = io.BytesIO()
    image.save(image_buffer, format=target_format.value)
    image_buffer.seek(0)

    return image_buffer


def process_tar_file(input_tar_path, output_tar_path, resolution, image_list):
    with (tarfile.open(input_tar_path, 'r') as input_tar,
          tarfile.open(output_tar_path, 'w') as output_tar):
        for raw_name in image_list:
            if raw_name not in input_tar.getnames():
                print(f"Warning: {raw_name} not found in the TAR file.")
                continue

            raw_data = input_tar.extractfile(raw_name) \
                                .read()

            png_buffer = convert_raw_to_png(raw_data, resolution)

            png_name = raw_name.replace('.raw', '.png')
            png_member = tarfile.TarInfo(name=png_name)
            png_member.size = len(png_buffer.getvalue())
            output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames.tar'
    output_path = '..\\output\\example_frames.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as f:
        image_list = [f.strip() for f in f.readlines()]

    process_tar_file(tar_path, output_path, resolution_1280_720, image_list)
