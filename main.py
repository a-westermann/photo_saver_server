import pysftp
import json
import paramiko
from base64 import decodebytes
import os


path_to_photos = r'/home/andweste/AshleyPictures/'
local_photo_repo = "Photos/"

class Server:
    def __init__(self, json_string):
        self.__dict__ = json.loads(json_string)


def get_new_photo_names() -> list[str]:
    new_photo_files = []
    dir_contents = sftp.execute(f"cd {path_to_photos} && ls")
    for file in dir_contents:
        file = file.strip().decode('utf-8')
        if file not in os.listdir(local_photo_repo):
            sftp.get(remotepath=f'{path_to_photos}{file}', localpath=f'{local_photo_repo}{file}')
    print(f'Downloaded {len(new_photo_files)} new photos')




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
        new_photo_names = get_new_photo_names()

        # Compile any new photos added by checking local storage for same name
        # This is safer than adding any in the last 24h b/c the app may crash at some point

