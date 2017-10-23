import swagger_client
import threading
import webbrowser
import json
import requests
import time
import pickle
import urllib
import os
from pubsub import pub
from base64 import  b64encode
from os.path import join, exists
from swagger_client.rest import ApiException
from http.server import BaseHTTPRequestHandler,HTTPServer
from staticClasses import StaticData, settings, configFile

########################################################################
class Auth:
  """manage of login and authentication operations for the ESI interface"""

  #----------------------------------------------------------------------
  def __init__(self, forceLogin = False, forceRefresh = False) :
    """Constructor, perform credentials operations and handles the code returned by the api"""

    if forceLogin:
      self._credentials()
      self._login()
    elif forceRefresh:
      self._refresh()
    else:
      fresh = self._validateAccessToken()
      if not fresh:
        self._refresh()

  #----------------------------------------------------------------------
  def _validateAccessToken(self, ):
    """"""
    apiConfig = swagger_client.api_client.ApiClient()
    apiConfig.configuration.access_token = settings.accessToken
    apiConfig.default_headers = {'User-Agent': settings.userAgent}

    assetsApi = swagger_client.CharacterApi(apiConfig)

    try:
      name = assetsApi.get_characters_character_id_standings(1004487144)
      return True
    except ApiException:
      return False


  #----------------------------------------------------------------------
  def _credentials(self):
    """open a login window in the default browser so the user can authenticate"""
    scopes = ("publicData%20"
              "esi-skills.read_skills.v1%20"
              "esi-assets.read_corporation_assets.v1%20"
              "esi-corporations.read_blueprints.v1%20"
              "esi-markets.read_corporation_orders.v1%20"
              "esi-industry.read_corporation_jobs.v1%20"
              "esi-characters.read_blueprints.v1"
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
  def _login(self):
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
  def _refresh(self):
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
  def _saveRefreshToken(self):
    """save the refresh token to config.json"""
    #save refresh token
    settingDict = settings.__dict__.copy()
    settingDict.pop('code', None)
    #settingDict.pop('accessToken', None)


    with open(configFile, 'w') as config:
      json.dump(settingDict, config)

##########################################################################
#This class is engineered as a handler for BaseHTTPRequest,
#it catches the authentication token after login.
#the original (and mostly unmodified) template from this
#comes from CREST-market-downloader from fuzzworks.
#note: i think this class inherits from BaseHTTPServer.BaseHTTPRequestHandler
class CodeHandler(BaseHTTPRequestHandler):
  """retrieve authentication token from localhost redirect after login"""
  def do_GET(self):
    if self.path == "/favicon.ico":
      return;
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



########################################################################
class DataRequest:
  """request data to the ESI api"""
  #swagger_client setup
  Auth()
  apiConfig = swagger_client.api_client.ApiClient()
  apiConfig.configuration.access_token = settings.accessToken
  apiConfig.default_headers = {'User-Agent': settings.userAgent}

  #----------------------------------------------------------------------
  def _refreshCredentials(cls, apiObject):
    """force a refresh of the access token and set the appropriate value to api client"""
    Auth(forceRefresh = True)
    apiObject.configuration.access_token = settings.accessToken
    cls.apiConfig.configuration.access_token = settings.accessToken

  #----------------------------------------------------------------------
  @classmethod
  def getAssets(cls):
    """query esi for asset data"""
    assetsApi = swagger_client.AssetsApi(cls.apiConfig)

    try:
      assets = assetsApi.get_corporations_corporation_id_assets(settings.corpID)
    except ApiException:
      assetsApi = cls._refreshCredentials(assetsApi)
      assets = assetsApi.get_corporations_corporation_id_assets(settings.corpID)
    finally:
      if not assets:
        raise ApiException("sum tin wong")

    return assets

  #----------------------------------------------------------------------
  @classmethod
  def getSkills(cls, ):
    """query esi for skill data"""
    skillsApi = swagger_client.SkillsApi(cls.apiConfig)

    try:
      skills = skillsApi.get_characters_character_id_skills(settings.ceoID)
    except ApiException:
      skillsApi = cls._refreshCredentials(skillsApi)
      skills = skillsApi.get_characters_character_id_skills(settings.ceoID)
    finally:
      if not skills:
        raise ApiException('sum tin wong')

    return skills

  #----------------------------------------------------------------------
  @classmethod
  def getBlueprints(cls):
    """"""
    corpApi = swagger_client.CorporationApi(cls.apiConfig)

    try:
      blueprints = corpApi.get_corporations_corporation_id_blueprints(settings.corpID)
    except ApiException:
      corpApi = cls._refreshCredentials(corpApi)
      blueprints = corpApi.get_corporations_corporation_id_blueprints(settings.corpID)
    finally:
      if not blueprints:
        raise ApiException('sum tin wong')

    return blueprints

  #----------------------------------------------------------------------
  @classmethod
  def getMarketOrders(cls):
    """obtain data about market orders for given corp"""
    marketApi = swagger_client.MarketApi(cls.apiConfig)

    try:
      marketOrders = marketApi.get_corporations_corporation_id_orders(settings.corpID)
    except ApiException:
      marketApi = cls._refreshCredentials(marketApi)
      marketOrders = marketApi.get_corporations_corporation_id_orders(settings.corpID)
    finally:
      if not marketOrders:
        raise ApiException('sum tin wong')

    return marketOrders


  #----------------------------------------------------------------------
  @classmethod
  def getIndustryJobs(cls):
    """obtain data about market orders for given character"""
    industryApi = swagger_client.IndustryApi(cls.apiConfig)

    try:
      industryJobs = industryApi.get_corporations_corporation_id_industry_jobs(settings.corpID)
    except ApiException:
      industryApi = cls._refreshCredentials(industryApi)
      industryJobs = industryApi.get_corporations_corporation_id_industry_jobs(settings.corpID)
    finally:
      if not industryJobs:
        raise ApiException('sum tin wong')

    return industryJobs

  #----------------------------------------------------------------------
  @classmethod
  def getAdjustedPrices(cls):
    """"""
    marketApi = swagger_client.MarketApi(cls.apiConfig)

    try:
      adjustedPrices = marketApi.get_markets_prices()
    except ApiException:
      marketApi = cls._refreshCredentials(marketApi)
      adjustedPrices = marketApi.get_markets_prices()
    finally:
      if not adjustedPrices:
        raise ApiException('sum tin wong')

    return adjustedPrices

  #----------------------------------------------------------------------
  @classmethod
  def getSystemIndexes(cls):
    """"""
    industryApi = swagger_client.IndustryApi(cls.apiConfig)

    try:
      systemIndexes = industryApi.get_industry_systems()
    except ApiException:
      industryApi = cls._refreshCredentials(industryApi)
      systemIndexes = industryApi.get_industry_systems()
    finally:
      if not systemIndexes:
        raise ApiException('sum tin wong')

    return systemIndexes

  #----------------------------------------------------------------------
  @classmethod
  def getSystemIndexes(cls):
    """"""
    industryApi = swagger_client.IndustryApi(cls.apiConfig)

    try:
      systemIndexes = industryApi.get_industry_systems()
    except ApiException:
      industryApi = cls._refreshCredentials(industryApi)
      systemIndexes = industryApi.get_industry_systems()
    finally:
      if not systemIndexes:
        raise ApiException('sum tin wong')

    return systemIndexes

if __name__ == "__main__":
  #a = ESI(1004487144)
  #assets = DataRequest.getAssets()
  #adjustedP = DataRequest.getAdjustedPrices()
  #indJobs = DataRequest.getIndustryJobs()
  #bp = DataRequest.getBlueprints()
  #skills = DataRequest.getSkills()
  #marketOrders = DataRequest.getMarketOrders()
  #sysInd = DataRequest.getSystemIndexes()
  #Auth()
  print('lae')
  pass