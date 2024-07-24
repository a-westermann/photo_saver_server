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


def get_new_photos() -> dict[str, str]:
    # Compile any new photos added by checking local storage for same name
    # This is safer than adding any in the last 24h b/c the app may crash at some point
    new_photo_files = dict()
    log = open(log_file, 'a')
    dir_contents = sftp.execute(f"cd {path_to_photos} && ls")
    for file in dir_contents:
        file = file.strip().decode('utf-8')
        if sftp.isdir(f'{path_to_photos}{file}'):
            # someone moved a folder/gallery onto the server
            # I could add logic to iterate through directories (galleries) until finding the photos
            # For now, just log the event and move on
            log.write(f'\nError: A directory was added to the server: {file}. Right now only individual photos '
                      f'are supported. Please remove the gallery and upload the photos inside instead.')
            continue
        # Grab the year of the photo so we know which zip to check. And which to add it to if it's a new photo
        photo_year = get_exif_year(f'{path_to_photos}{file}')

        download_photo = False
        if not os.path.isfile(f'{local_photo_repo}/{photo_year}.zip'):
            # Archive for this year doesn't exist yet. Photo is good to download
            download_photo = True
        else:
            with zipfile.ZipFile(f'{local_photo_repo}/{photo_year}.zip', 'r') as year_zip:
                if file not in year_zip.namelist():
                    # Archive for this year exists and this photo is not in it yet. Download it
                    download_photo = True

        if download_photo:
            sftp.get(remotepath=f'{path_to_photos}{file}', localpath=f'{temp_photo_repo}{file}',
                     callback=lambda x, y: delete_photo(f'{path_to_photos}{file}', x, y))
            new_photo_files[file] = photo_year

    log.write(f'\nDownloaded {len(new_photo_files)} new photos')
    return new_photo_files


def delete_photo(path: str, progressBytes: int, totalSize: int) -> None:
    if progressBytes % totalSize == 0:
        sftp.remove(path)

def get_exif_year(file_path: str) -> str | None:
    # First just try to grab the date from the file name
    year_search = re.search(year_regex, file_path)
    if year_search:
        return year_search.group()

    # Didn't have the year in the file name. Try EXIF data if it's a JPG/Jpeg
    if not (file_path.lower().__contains__('jpg') or file_path.lower().__contains__('jpeg')):
        return None
    file = sftp.open(file_path, 'rb')
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
    zip_file = f'{local_photo_repo}/{photo_year}.zip'
    with zipfile.ZipFile(zip_file, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(f'{temp_photo_repo}{photo_name}', photo_name, compress_type=zipfile.ZIP_DEFLATED)


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
    cnopts = pysftp.CnOpts(knownhosts=None)
    cnopts.hostkeys.add(server.Host, 'ssh-rsa', host_key)

    with pysftp.Connection(server.Host, username=server.User, private_key="private_key.ppk", port=server.Port,
                           cnopts=cnopts) as sftp:
        photo_year_dict = get_new_photos()
        for photo, year in photo_year_dict.items():
            archive_new_photo(photo, year)

    # clean up the temp directory
    for temp_file in os.listdir(temp_photo_repo):
        os.remove(f'{temp_photo_repo}{temp_file}')
