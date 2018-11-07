import sys
import os
import requests
import urllib2
import urlparse
import json
import oauth2
import pprint
import shutil
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


RTOKEN_URL = 'https://api.twitter.com/oauth/request_token?oauth_callback=oob'
ATOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTH_URL = 'https://api.twitter.com/oauth/authorize'
VERIFY_URL = 'https://api.twitter.com/1.1/account/verify_credentials.json?' \
             'include_entities=false&skip_status=true'
PERI_LOGIN_URL = 'https://api.periscope.tv/api/v2/loginTwitter?build=v1.0.2'
PERI_VERIFY_URL = 'https://api.periscope.tv/api/v2/verifyUsername'
PERI_VALIDATE_URL = 'https://api.periscope.tv/api/v2/validateUsername'


class HTTPError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)
        requests.HTTPError(str(args))


class Config(dict):
    def __init__(self):
        dict.__init__(self)
        self.config_file = os.path.join(os.path.expanduser('~'), "peri.conf")
        if os.path.isfile(self.config_file):
            self.load()

    def load(self):
        with open(self.config_file, "r") as reader:
            self.update(json.load(reader))

    def write(self):
        temp_file = self.config_file+".tmp"
        try:
            with open(temp_file, "w") as reader:
                json.dump(self, reader, indent=2)
            try:
                os.unlink(self.config_file)
            except Exception as error:
                print error
            shutil.move(temp_file, self.config_file)
        finally:
            try:
                os.unlink(temp_file)
            except Exception as error:
                print error


class Login(requests.Session):

    def __init__(self):
        requests.Session.__init__(self)
        config = self.config = Config()

        self.headers.update(
                                {
                                'User-Agent': 'Periscope/3313 (iPhone; iOS 7.1.1; Scale/2.00)',
                                "Accept-Encoding": "gzip, deflate",
                                }
                            )
        
        cookie = config.get("cookie",  None)
        if not cookie:
            cookie = self.authenticate()
        self.cookie = cookie
        self.uid = config.get("uid")
        self.name = config.get("name")

        if not self.cookie:
            raise HTTPError("Cannot get cookies")

    def authenticate(self):

        config = self.config
        consumer_key = config.get("consumer_key")
        consumer_secret = config.get("consumer_secret")

        consumer_auth = oauth2.Consumer(consumer_key, consumer_secret)
        client = oauth2.Client(consumer=consumer_auth)
        response, content = client.request(RTOKEN_URL, "GET")

        if response.get('status') != '200':
            raise HTTPError("Could not initilize authentication process")

        request_token = dict(urlparse.parse_qsl(content.decode('utf-8')))
        os.startfile('{0}?oauth_token={1}'.format(AUTH_URL, request_token['oauth_token']))

        oauth_varifier = input('input those digits here')
        token = oauth2.Token(request_token.get('oauth_token'), 
                            request_token.get('oauth_token_secret'))
        token.set_verifier(oauth_varifier)


        client = oauth2.Client(consumer_auth, token)
        response, content = client.request(ATOKEN_URL, 'POST')
        if response.get('status') != '200':
            raise HTTPError("Could not complete authentication process")

        access_token = dict(urlparse.parse_qsl(content.decode('utf-8')))
        token = oauth2.Token(access_token.get('oauth_token'),
                            access_token.get('oauth_token_secret'))

        client = oauth2.Client(consumer_auth, token)
        response, content = client.request(VERIFY_URL, 'GET')

        if response.get('status') != '200':
            raise HTTPError("Cannot complete authencation process")

        user_info = json.loads(content.decode('utf-8'))
        config['token'] = access_token.get('oauth_token')
        config['token_secret'] = access_token.get('oauth_token_secret')
        config['twitter_name'] = user_info.get('screen_name')
        config['uid'] = user_info.get('id_str')

        pprint.pprint("access {}".format(access_token))
        pprint.pprint("user_info {}".format(user_info))

        login_payload = {
                            'session_secret': config.get('token_secret'),
                            'session_key': config.get('token'),
                            'user_id': config.get('uid'),
                            'user_name': config.get('twitter_name'),
                            'phone_number': '',
                            'vendor_id': '81EA8A9B-2950-40CD-9365-40535404DDE4',
                            'bundle_id': 'com.bountylabs.periscope',
                        }

        response = self.post(PERI_LOGIN_URL, json=login_payload)
        if response.status_code != 200:
            raise HTTPError("Cannot complete authentication")

        cookie = config['cookie'] = response.json().get('cookie')
        config['name'] = response.json().get('user').get('username')
        config['pubid'] = response.json().get('user').get('id')

        test_payload = {'user_id': config.get('pubid')}

        try:
            response = self.post('https://api.periscope.tv/api/v2/following', json=test_payload)
        except Exception as error:
            raise HTTPError("Failed while testing payload cuz {}".format(error))


        while not config.get('username_validated'):

            validate_payload = {
                                    'session_secret': config.get("token_secret"),
                                    'session_key': config.get("token"),
                                    'username': config.get("name"),
                                    'cookie': config.get("cookie")
                                }

            try:
                response = self.post(PERI_VALIDATE_URL, json=validate_payload)
            except:
                raise HTTPError("could not complete authentication")

            verify_payload = {
                                'session_secret': config["token_secret"],
                                'session_key': config["token"],
                                'username': config["name"],
                                'display_name': config["name"],
                                'cookie': config["cookie"]
                             }

            try:
                response = self.post(PERI_VERIFY_URL, json=verify_payload)
            except:
                raise IOError('Could not complete authentication with Periscope')

            if response.json().get("success"):
                config["username_validated"] = True

        config.write()
        return cookie



login = Login()
data = Config()
cookie = data.get('cookie')
session = requests.Session()
data = session.post("https://api.periscope.tv/api/v2/rankedBroadcastFeed", json=data)
sorted_data = sorted(data.json(), reverse=True, key=lambda x: x.get('n_total_watching'))

# with open ("brodcast_details.json", "w") as writer:
#     json.dump(sorted_data, writer, indent=2)

# for i in sorted_data:
#     pprint.pprint(i)
#     break
#     date = datetime.datetime.strptime(i.get("start").split("T")[0], "%Y-%m-%d").date()
#     time = datetime.datetime.strptime(i.get("start").split("T")[-1].split(".")[0], "%H:%M:%S").time()
#     total_time = datetime.datetime.now() - datetime.datetime.combine(date, time)
#     passed_time = datetime.timedelta(seconds=total_time.total_seconds())
#     print "user is live from {} long and have {} viewers".format(str(passed_time), i.get("n_total_watching" ))
#     os.startfile(i.get('image_url'))

