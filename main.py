import pysftp
import json
import paramiko
from base64 import decodebytes
import os
import exifread
import re
import zipfile


path_to_photos = r'/home/andweste/AshleyPictures/'
temp_photo_repo = 'photo_temp/'
local_photo_repo = 'Photos/'
log_file = 'log.txt'
year_regex = '20[0-2][0-9]'


class Server:
    def __init__(self, json_string):
        self.__dict__ = json.loads(json_string)


def get_new_photos() -> list[str]:
    # Compile any new photos added by checking local storage for same name
    # This is safer than adding any in the last 24h b/c the app may crash at some point
    new_photo_files = []
    log = open(log_file, 'a')
    dir_contents = sftp.execute(f"cd {path_to_photos} && ls")
    for file in dir_contents:
        file = file.strip().decode('utf-8')
        if file not in os.listdir(temp_photo_repo):
            sftp.get(remotepath=f'{path_to_photos}{file}', localpath=f'{temp_photo_repo}{file}')
            new_photo_files.append(file)
    log.write(f'\nDownloaded {len(new_photo_files)} new photos')
    return new_photo_files


def get_exif_year(file_path: str) -> str | None:
    # First just try to grab the date from the file name
    year_search = re.search(year_regex, file_path)
    if year_search:
        return year_search.group()

    # Didn't have the year in the file name. Try EXIF data if it's a JPG/Jpeg
    if not file_path.lower().endswith(('jpg', 'jpeg')):
        return None
    file = open(file_path, 'rb')
    tags = exifread.process_file(file, details=True)
    for tag, val in tags.items():
        if "date" in str(tag).lower():
            year_search = re.search(year_regex, str(val))
            if year_search:
                return year_search.group()

    return None



def archive_new_photo(photo_name: str, photo_year: str):
    # Archive the photo into the zip corresponding to the year it was taken
    # Also make the zip if it doesn't exist yet
    zip_file = f'Photos/{photo_year}.zip'
    with zipfile.ZipFile(zip_file, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(f'{temp_photo_repo}{photo_name}', photo_name)


if __name__ == '__main__':
    # Set up directories
    if not os.path.isdir(temp_photo_repo):
        os.makedirs(temp_photo_repo)
    if not os.path.isdir(local_photo_repo):
        os.makedirs(local_photo_repo)

    # Connect SFTP, navigate to the photo directory
    server = Server(open('config.json').read())
    host_key = open("hostkey.ppk").read()
    host_key = str.encode(host_key)
    host_key = paramiko.RSAKey(data=decodebytes(host_key))
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys.add(server.Host, 'ssh-rsa', host_key)

    with pysftp.Connection(server.Host, username=server.User, private_key="private_key.ppk", port=server.Port,
                           cnopts=cnopts) as sftp:
        photos = get_new_photos()
        for photo in photos:
            photo_file_path = f'{temp_photo_repo}{photo}'
            year = get_exif_year(photo_file_path)
            archive_new_photo(photo, year)
