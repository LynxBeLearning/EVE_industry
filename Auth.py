import time
import json
import urllib
import requests
import threading
import webbrowser
import swagger_client
from pubsub import pub
from base64 import b64encode
from staticClasses import settings, configFile
from http.server import BaseHTTPRequestHandler, HTTPServer


#----------------------------------------------------------------------
def authenticate(forceLogin = False, forceRefresh = False) :
    """perform credentials operations and handles the code returned by the api"""

    if forceLogin:
        _credentials()
        _login()
    elif forceRefresh:
        _refresh()
    else:
        fresh = _validateAccessToken()
        if not fresh:
            _refresh()

#----------------------------------------------------------------------
def _validateAccessToken():
    """"""
    apiConfig = swagger_client.api_client.ApiClient()
    apiConfig.configuration.access_token = settings.accessToken
    apiConfig.default_headers = {'User-Agent': settings.userAgent}

    walletApi = swagger_client.WalletApi(apiConfig)

    try:
        walletApi.get_characters_character_id_wallet(1004487144)
        return True
    except ApiException:
        return False


#----------------------------------------------------------------------
def _credentials():
    """open a login window in the default browser so the user can authenticate"""
    scopes = ("publicData%20"
          "esi-skills.read_skills.v1%20"
          "esi-assets.read_corporation_assets.v1%20"
          "esi-corporations.read_blueprints.v1%20"
          "esi-markets.read_corporation_orders.v1%20"
          "esi-industry.read_corporation_jobs.v1%20"
          "esi-characters.read_blueprints.v1%20"
          "esi-wallet.read_corporation_wallets.v1%20"
          "esi-wallet.read_character_wallet.v1"
          )

    server = HTTPServer(('', int(settings.port)), CodeHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.daemon = True
    serverThread.start()
    webbrowser.open( (f'https://login.eveonline.com/oauth/authorize?'
                  f'response_type=code&'
                  f'redirect_uri=http://localhost:{settings.port}/&'
                  f'client_id={settings.clientID}&'
                  f'scope={scopes}&'
                  f'state=evesso') )

    while 1:
        time.sleep(2)
        if hasattr(settings, 'code'):
            server.shutdown()
            break

#----------------------------------------------------------------------
def _login():
    """query ESI to retrieve access and refresh tokens"""
    headers = {'User-Agent':settings.userAgent}
    query = {'grant_type':'authorization_code','code': settings.code}
    secretEncoded = b64encode((settings.clientID+':'+settings.secret).encode()).decode()
    headers = {'Authorization':'Basic '+ secretEncoded,'User-Agent':settings.userAgent}
    r = requests.post(settings.authUrl,params=query,headers=headers)
    response = r.json()
    settings.accessToken = response['access_token']
    settings.refreshToken = response['refresh_token']
    self._saveRefreshToken()

#----------------------------------------------------------------------
def _refresh():
    """query ESI to refresh an access token"""
    refreshToken = settings.refreshToken
    secretEncoded = b64encode((settings.clientID+':'+settings.secret).encode()).decode()
    headers = {'Authorization':'Basic '+ secretEncoded,'User-Agent':settings.userAgent}
    query = {'grant_type':'refresh_token','refresh_token':refreshToken}
    r = requests.post(settings.authUrl,params=query,headers=headers)
    response = r.json()
    settings.accessToken = response['access_token']
    settings.refreshToken = response['refresh_token']

    #save refresh token
    self._saveRefreshToken()

#----------------------------------------------------------------------
def _saveRefreshToken():
    """save the refresh token to config.json"""
    #save refresh token
    settingDict = settings.__dict__.copy()
    settingDict.pop('code', None)


    with open(configFile, 'w') as config:
        json.dump(settingDict, config)

#This class is engineered as a handler for BaseHTTPRequest,
#it catches the authentication token after login.
#the original (and mostly unmodified) template from this
#comes from CREST-market-downloader from fuzzworks.
#note: i think this class inherits from BaseHTTPServer.BaseHTTPRequestHandler
class CodeHandler(BaseHTTPRequestHandler):
    """retrieve authentication token from localhost redirect after login"""
    def do_GET(self):
        if self.path == "/favicon.ico":
            return
        parsed_path = urllib.parse.urlparse(self.path)
        parts=urllib.parse.parse_qs(parsed_path.query)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Login successful. you can close this window now')
        pub.sendMessage('code', code = str(parts['code'][0]) )
        self.finish()
        self.connection.close()
    def log_message(self, format, *args):
        return

