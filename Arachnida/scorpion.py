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
    """
    Load the image and print its basic information.
    """
    with Image.open(img_path) as img:
        print(f"Name: {img.filename}")
        print(f"Size: {os.path.getsize(img.filename)} bytes")
        print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(img.filename))}")
        print(f"Format: {img.format}")
        print(f"Dim: {img.size[0]}x{img.size[1]} px")

def dms_to_decimal(dms, direction):
    """
    Convert degrees, minutes, seconds to decimal degrees.
    """
    d, m, s = [float(x) for x in dms]
    direction = direction.decode() if isinstance(direction, bytes) else direction
    deg = d + m/60 + s/3600
    return -deg if direction in ('S', 'W') else deg

def read_exif(img_file):
    """
    Read and print EXIF data from the image file.
    """
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
                lat_direction = gps_info.get(1)
                lat = gps_info.get(2)
                lon_direction = gps_info.get(3)
                lon = gps_info.get(4)
                
                if lat_direction and lat:
                    print(f"Latitude: {dms_to_decimal(lat, lat_direction):4f}° {lat_direction}")

                if lon_direction and lon:
                    print(f"Longitude: {dms_to_decimal(lon, lon_direction):4f}° {lon_direction}")

def main():
    """
    Main function to parse command line arguments and process the image files.
    """
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
