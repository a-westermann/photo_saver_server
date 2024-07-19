import pysftp
import json
import paramiko
from base64 import decodebytes
import os
import exifread
import re
import zipfile


path_to_photos = r'/home/andweste/AshleyPictures/'
local_photo_repo = 'photo_temp/'
log_file = 'log.txt'
year_regex = '20[0-2][0-9]'


class Server:
    def __init__(self, json_string):
        self.__dict__ = json.loads(json_string)


def get_new_photos():
    # Compile any new photos added by checking local storage for same name
    # This is safer than adding any in the last 24h b/c the app may crash at some point
    new_photo_files = []
    log = open(log_file, 'a')
    dir_contents = sftp.execute(f"cd {path_to_photos} && ls")
    for file in dir_contents:
        file = file.strip().decode('utf-8')
        if file not in os.listdir(local_photo_repo):
            sftp.get(remotepath=f'{path_to_photos}{file}', localpath=f'{local_photo_repo}{file}')
            new_photo_files.append(file)
    log.write(f'\nDownloaded {len(new_photo_files)} new photos')


def get_exif_year(file_path: str) -> str | None:
    # First just try to grab the date from the file name
    year_search = re.search(year_regex, file_path)
    if year_search:
        return year_search.group()

    # Didn't have the year in the file name. Try EXIF data
    file = open(file_path, 'rb')
    tags = exifread.process_file(file, details=True)#, stop_tag='DateTimeOriginal')
    for tag, val in tags.items():
        if "date" in str(tag).lower():
            year_search = re.search(year_regex, str(val))
            if year_search:
                return year_search.group()

    return None



# def archive_new_photos():



if __name__ == '__main__':
    # Connect SFTP, navigate to the photo directory
    server = Server(open('config.json').read())
    host_key = open("hostkey.ppk").read()
    host_key = str.encode(host_key)
    host_key = paramiko.RSAKey(data=decodebytes(host_key))
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys.add(server.Host, 'ssh-rsa', host_key)

    with pysftp.Connection(server.Host, username=server.User, private_key="private_key.ppk", port=server.Port,
                           cnopts=cnopts) as sftp:
        get_new_photos()
        # archive_new_photos()
        get_exif_year('photo_temp/ashleyw-2.jpg')
