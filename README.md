# TAR Converter
## Overview
TAR Converter is a Python package for converting RAW images within a TAR file to various image formats.  
It provides a flexible and easy-to-use interface for converting images and extracting statistical information about pixel values.

## Installation
```bash
pip install tar-converter
```

## Usage
### Import
```python
from tar_converter import TarRawImagesConverter, SupportedFormats 
```

### Create a converter instance
```python
png_converter = TarRawImagesConverter(SupportedFormats.PNG)  # use compress_level=0 for faster conversion
png_no_compression_converter = TarRawImagesConverter(SupportedFormats.PNG, compress_level=0)  # use compress_level=0 for faster conversion
jpg_converter = TarRawImagesConverter(SupportedFormats.JPEG)
```

### Convert images in a TAR file
```python
input_tar_path = "path/to/input.tar"
output_tar_path = "path/to/output.tar"
resolution = (width, height)
converter.convert_tar(input_tar_path, output_tar_path, resolution)
```

## Supported Formats
The `SupportedFormats` enum in `consts.py` defines the supported output formats, including `RAW`, `PNG`, and `JPEG`.
