import pysftp
import json
import paramiko
from base64 import decodebytes
import os


path_to_photos = 'home/andweste/Ashley Pictures/'

class Server:
    def __init__(self, json_string):
        self.__dict__ = json.loads(json_string)


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
        sftp.cd(path_to_photos)

    # Compile any new photos added by checking local storage for same name
    # This is safer than adding any in the last 24h b/c the app may crash at some point

