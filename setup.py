from setuptools import setup, find_packages

setup(
    name='tar_converter',
    version='1.0.0',
    description='A library for converting RAW images in a tar file to PNG images',
    packages=find_packages(),
    install_requires=[
        'Pillow==10.2.0',
        'numpy==1.26.3',
    ],
)