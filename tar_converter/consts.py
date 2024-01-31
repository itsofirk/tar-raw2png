from enum import Enum


class SupportedFormats(Enum):
    RAW = ".raw"
    PNG = ".png"
    JPEG = ".jpg"

    @property
    def extension(self):
        return self.value


KB = 1024

GRAYSCALE = "L"  # mode for 8-bit images

