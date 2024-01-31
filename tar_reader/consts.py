from enum import Enum


class SupportedFormats(Enum):
    PNG = "PNG"
    # JPEG = "JPEG"


KB = 1024

RAW = '.raw'
TAR = '.tar'
PNG = '.png'

NEW_TAR_SUFFIX = '_converted.tar'

GRAYSCALE = "L"  # mode for 8-bit images

