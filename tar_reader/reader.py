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
    pixel_format = f"{resolution[0]}x{resolution[1]}B"
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
        for image_name in image_list:
            tar_member = input_tar.getmember(image_name)
            tar_member = next((m for m in input_tar.getmembers() if m.name == image_name), None)

            if tar_member:
                # Read raw data from the tar file
                raw_data = input_tar.extractfile(tar_member).read()

                # Convert raw data to PNG format
                png_buffer = convert_raw_to_png(raw_data, resolution)

                # Add the PNG image to the output tar file
                png_member = tarfile.TarInfo(name=image_name.replace('.raw', '.png'))
                png_member.size = len(png_buffer.getvalue())
                output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))


if __name__ == '__main__':
    tar_path = '..\\resources\\example_frames.tar'
    output_path = '..\\output\\example_frames.tar'
    resolution_1280_720 = (1280, 720)
    with open('..\\resources\\example_frames.lst') as f:
        image_list = f.readlines()

    process_tar_file(tar_path, output_path, resolution_1280_720, image_list)
