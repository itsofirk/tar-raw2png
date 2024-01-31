import io
import tarfile
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import numpy as np

from tar_converter.consts import SupportedFormats, GRAYSCALE, KB


def convert_raw_image(raw_data: bytes,
                      resolution: tuple[int, int],
                      mode=GRAYSCALE,
                      target_format=SupportedFormats.PNG,
                      **pillow_preferences):
    """
    Converts a RAW image to one of the supported formats and returns the image.
    The function also returns the average and standard deviation of the pixel values.

    :param raw_data: raw image data
    :param resolution: the image resolution
    :param mode: the image mode. for further information, see https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    :param target_format: the target format to convert to
    :param pillow_preferences: keyword arguments to pass to Pillow's Image.save
    :return: the converted image in a BytesIO object, the average pixel value, and the standard deviation
    """
    image = Image.frombytes(mode, resolution, raw_data)

    # Calculate statistics
    pixels = np.array(image).flatten()
    average_pixel = np.mean(pixels)
    std_dev_pixel = np.std(pixels)

    # Convert to target format
    image_buffer = io.BytesIO()
    image.save(image_buffer, format=target_format.name, **pillow_preferences)
    image_buffer.seek(0)

    return image_buffer, average_pixel, std_dev_pixel


def _process_member(member: tarfile.TarInfo,
                    tar: tarfile.TarFile,
                    resolution: tuple[int, int],
                    mode=GRAYSCALE,
                    target_format=SupportedFormats.PNG,
                    **pillow_preferences):
    """
    Processes a single member of the tar file.
    """
    raw_data = tar.extractfile(member).read()
    png_buffer, average_pixel, std_dev_pixel = convert_raw_image(raw_data, resolution, mode, target_format,
                                                                 **pillow_preferences)
    statistics = {
        "average_pixel": average_pixel,
        "std_dev_pixel": std_dev_pixel,
        "new_name": _get_new_image_name(member.name, target_format),
    }
    return statistics, png_buffer


def convert_tar(input_tar_path: str,
                output_tar_path: str,
                resolution: tuple[int, int],
                image_list: list[str] = None,
                image_mode=GRAYSCALE,
                target_format=SupportedFormats.PNG,
                buffer_size=16 * KB):
    """
    Converts images in a tar file to another format and saves the images in a new tar file.
    :param input_tar_path: the path to the input tar file
    :param output_tar_path: the path to the output tar file
    :param resolution: a tuple of the resolution of the images
    :param image_list: a specific list of images to convert. if not provided, all images will be converted.
    :param image_mode: the images' mode. for further information, see https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    :param target_format: the target format to convert to. use SupportedFormats to get a list of supported formats.
    :param buffer_size: the buffer size to use when reading from the tar file.
    :return: the path to the output tar file, the average pixel value per image, and the standard deviation per image
    """
    average_pixels = []
    std_dev_pixels = []
    with (tarfile.open(input_tar_path, 'r', bufsize=buffer_size) as input_tar,
          tarfile.open(output_tar_path, 'w', bufsize=buffer_size) as output_tar):
        members_to_convert = _get_members_to_process(input_tar, image_list)
        _process_image = partial(_process_member, tar=input_tar, resolution=resolution, mode=image_mode,
                                 target_format=target_format)
        print(f"Converting {len(members_to_convert)} images...")
        with ThreadPoolExecutor() as executor:
            for metadata, png_buffer in executor.map(_process_image, members_to_convert):
                png_member = tarfile.TarInfo(name=metadata["new_name"])
                png_member.size = len(png_buffer.getvalue())
                output_tar.addfile(png_member, io.BytesIO(png_buffer.getvalue()))
                average_pixels.append(metadata["average_pixel"])
                std_dev_pixels.append(metadata["std_dev_pixel"])
        print(f"Done. Converted {len(members_to_convert)} images.")
    return output_tar_path, average_pixels, std_dev_pixels


def _get_members_to_process(input_tar, image_list=None):
    """
    A helper function to get the list of members to process.
    """
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


def _get_new_image_name(old_name, target_format=SupportedFormats.PNG):
    """
    A helper function to get the new name of the image.
    """
    return old_name[:-4] + target_format.extension
