'''
TODOS:
make broadcast previewer
'''

import sys  
import os
import re
import urllib2
import requests
import json
import subprocess

FFMPEG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ffmpeg.exe"))


class URL(object):
    def __init__(self, url):
        object.__init__(self)
        self.url = url

    def validate_url(self):

        if "periscope" not in self.url and "pscp" not in self.url:
            raise TypeError ("Input URL {} is invalid.".format(self.url))
        try:
            urllib2.urlopen(self.url)
        except Exception as error:
            raise TypeError ("Input URL {} is not accessable due to {}".format(self.url, error))

        return True

    def find_token_id(self):
        pattern = re.search(".tv/w/[a-zA-Z0-9]{13}", self.url)
        if not pattern:
            raise TypeError ("Input URL {} is invalid.".format(self.url))
        
        return pattern.group().split(".tv/w/")[-1]

    def request_broadcast_details(self, token_id):
        
        api_request_uri = "https://api.periscope.tv/api/v2/getAccessPublic?token={}".format(token_id)
        request = requests.get(url=api_request_uri)
        if request.status_code is 404:
            raise WindowsError ("Cannot find the broadcast info..") 
        broadcast_data = request.json()
        return broadcast_data

    def get_broadcast_replay(self):
        '''
        REPLAY_ACCESS = "https://api.periscope.tv/api/v2/replayPlaylist.m3u8?broadcast_id={}&cookie={}"

        '''
        pass

    def grab_scope(self, download_url, output_path, broadcast_id):
        output_mov = "{}/{}.mov".format(output_path, broadcast_id)
        if not os.path.exists(os.path.dirname(output_mov)):
            os.makedirs(os.path.dirname(output_mov))
        command = "{ffmpeg} -y -i {url} -bsf:a aac_adtstoasc -codec copy {output_mov}".format(
                                            ffmpeg=FFMPEG_PATH, url=download_url, output_mov=output_mov)

        print command
        process = subprocess.Popen(command, shell=False)
        process.wait()
        return output_mov


url = URL("https://www.pscp.tv/w/1yNGaXLQeYjKj")
if url.validate_url():
    token_id = url.find_token_id()
    details = url.request_broadcast_details(token_id)
    download_url = details.get('hls_url', details.get('replay_url'))
    __import__("pprint").pprint(details)
    output_path = "C:/Temp/new/"
    url.grab_scope(download_url, output_path, token_id)


 