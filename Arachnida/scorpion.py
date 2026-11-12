import argparse
from pathlib import Path
from PIL import Image, UnidentifiedImageError, ExifTags
from datetime import datetime
import os

def validate_path(file_path):
    """
    Validate the provided file path.
    """
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File {file_path} not found!")
        return False
    
    if not path.is_file():
        print(f"Error: {file_path} is not a regular file!")
        return False

    return True

def validate_extension(file_path):
    """
    Validate the provided file extension.
    """
    path = Path(file_path)

    if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
        print(f"Error: {file_path} has an unsupported extension!")
        return False

    return True

def load_image(img_path):
    with Image.open(img_path) as img:
        print(f"Name: {img.filename}")
        print(f"Size: {os.path.getsize(img.filename)} bytes")
        print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(img.filename))}")
        print(f"Format: {img.format}")
        print(f"Dim: {img.size[0]}x{img.size[1]} px")

def read_exif(img_file):
    with Image.open(img_file) as img:
        img_exif = img.getexif()

        if not img_exif:
            print(f"Image {img_file} contains no EXIF data.")
        else:
            for key, value in img_exif.items():
                tag_name = ExifTags.TAGS.get(key, f"Unknown tag {key}")
                print(f"{tag_name}: {value}")

            gps_info = img_exif.get_ifd(ExifTags.IFD.GPSInfo)
            if gps_info:
                for key, value in gps_info.items():
                    print(f"GPS {key}: {value}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

    args = parser.parse_args()
    
    for file in args.files:
        if validate_path(file):
            if validate_extension(file):
                try:
                    load_image(file)
                    read_exif(file)
                except UnidentifiedImageError as e:
                    print(f"Error identifying image {file}: {e}")
                except OSError as e:
                    print(f"Error loading image {file}: {e}")

if __name__ == "__main__":
    main()
