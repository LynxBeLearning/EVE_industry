from http.server import BaseHTTPRequestHandler,HTTPServer
import threading
import os
import webbrowser
import json
import requests
import time
from pubsub import pub

import pickle
import urllib
import os
from base64 import  b64encode
from os.path import join, exists
from staticClasses import StaticData, settings, configFile

########################################################################
class DataRequest:
  """request data to APIs, either ESI or XML"""

  #----------------------------------------------------------------------
  @classmethod
  def getAssets(cls, charID):
    """query esi for asset data"""
    cacheName = str(charID) + "Assets.cache"
    objIdentifier = str(charID) + "Assets"

    #checking existance of object
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
    #checking existance and age
      try:
        lastModified = time.time() - os.path.getmtime("cache/"+cacheName)
      except:
        lastModified = 999999999999

      #obtaining data
      if lastModified < 3600:
        #loading cache
        pickleIn = open("cache/"+cacheName, 'rb')
        assets = pickle.load(pickleIn)
        pickleIn.close()
        return assets
      else:
        #getting data from api
        esi = ESI(charID)
        assetUrl = 'https://esi.tech.ccp.is/latest/characters/{}/assets/'.format(charID)
        r = requests.get(assetUrl, headers=esi.authHeader)
        assets = r.json()

        #saving cache
        if not os.path.isdir('cache'):
          os.mkdir('cache')
        pickleOut = open("cache/"+cacheName, 'wb')
        pickle.dump(assets, pickleOut)

        #settings.DataObjectStorage[objIdentifier] = assets
        return assets

  #----------------------------------------------------------------------
  @classmethod
  def getSkills(cls, charID):
    """query esi for skill data"""
    cacheName = str(charID) + "Skill.cache"
    objIdentifier = str(charID) + "Skill"

    #checking existance of object
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
      #checking existance and age
      try:
        lastModified = time.time() - os.path.getmtime("cache/"+cacheName)
      except:
        lastModified = 999999999999

      #obtaining data
      if lastModified < 3600:
        pickleIn = open("cache/"+cacheName, 'rb')
        skills = pickle.load(pickleIn)
        return skills
      else:
        #getting data from api
        esi = ESI(charID)
        skillsUrl = 'https://esi.tech.ccp.is/latest/characters/{}/skills/?datasource=tranquility'.format(charID)
        r = requests.get(skillsUrl, headers=esi.authHeader)
        skills = Skills(r.json())

        #saving cache
        if not os.path.isdir('cache'):
          os.mkdir('cache')
        pickleOut = open("cache/"+cacheName, 'wb')
        pickle.dump(skills, pickleOut)

        settings.DataObjectStorage[objIdentifier] = skills
        return skills

  #----------------------------------------------------------------------
  @classmethod
  def getMarketHistory(cls, charID, typeID):
    """query esi for market history data"""
    cacheName = str(charID) + "marketHistory" + str(typeID)+ ".cache"
    objIdentifier = str(charID) + "marketHistory" + str(typeID)

    #checking existance of object
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
      #checking existance and age
      try:
        lastModified = time.time() - os.path.getmtime("cache/"+cacheName)
      except:
        lastModified = 999999999999

      #obtaining data
      if lastModified < 3600:
        #lastModified = os.path.getmtime("cache/"+cacheName)
        pickleIn = open("cache/"+cacheName, 'rb')
        marketHistory = pickle.load(pickleIn)
        return marketHistory
      else:
        #getting data from api
        esi = ESI(charID)
        marketHistoryUrl = 'https://esi.tech.ccp.is/latest/markets/{}/history/?type_id={}'.format(settings.fadeID, typeID)
        r = requests.get(marketHistoryUrl, headers=esi.authHeader)
        marketHistory = MarketHistory(r.json())

        #saving cache
        if not os.path.isdir('cache'):
          os.mkdir('cache')
        pickleOut = open("cache/"+cacheName, 'wb')
        pickle.dump(marketHistory, pickleOut)

        settings.DataObjectStorage[objIdentifier] = marketHistory
        return marketHistory

  #----------------------------------------------------------------------
  @classmethod
  def getBlueprints(cls, charID):
    """"""
    objIdentifier = str(charID) + "blueprints"
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
      keyID = settings.charConfig[charID]['KEYID']
      vCode = settings.charConfig[charID]['VCODE']

      cachedApi = EVEAPIConnection(cacheHandler=MyCacheHandler(debug=settings.debug))
      xml = cachedApi.auth(keyID=keyID, vCode=vCode).character(charID)
      return xml.Blueprints()

  #----------------------------------------------------------------------
  @classmethod
  def getMarketOrders(cls, charID):
    """obtain data about market orders for given character"""
    objIdentifier = str(charID) + "marketOrders"
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
      keyID = settings.charConfig[charID]['KEYID']
      vCode = settings.charConfig[charID]['VCODE']

      cachedApi = eveapi.EVEAPIConnection(cacheHandler=eveapi.MyCacheHandler(debug=settings.debug))
      xml = cachedApi.auth(keyID=keyID, vCode=vCode).character(charID)
      marketOrders = MarketOrders(xml.MarketOrders().orders)

      settings.DataObjectStorage[objIdentifier] = marketOrders
      return marketOrders


  #----------------------------------------------------------------------
  @classmethod
  def getIndustryJobs(cls, charID):
    """obtain data about market orders for given character"""
    objIdentifier = str(charID) + "Jobs"
    if objIdentifier in settings.DataObjectStorage:
      return settings.DataObjectStorage[objIdentifier]
    else:
      keyID = settings.charConfig[charID]['KEYID']
      vCode = settings.charConfig[charID]['VCODE']

      cachedApi = EVEAPIConnection(cacheHandler=MyCacheHandler(debug=settings.debug))
      xml = cachedApi.auth(keyID=keyID, vCode=vCode).character(charID)
      ind = xml.IndustryJobs()

      return ind





########################################################################
class ESI:
  """take care of login and authentication operations for the ESI interface"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor, perform credentials operations and handles the code returned by the api"""
    self.charID = charID
    if hasattr(settings, "accessToken"):
      self.authHeader = {'Authorization':'Bearer '+ settings.accessToken,
                         'User-Agent': settings.userAgent}
    elif hasattr(settings, 'refreshToken'):
      self._refresh()
      self.authHeader = {'Authorization':'Bearer ' + settings.accessToken,
                         'User-Agent': settings.userAgent}
    else:
      self._credentials()
      self._login()
      self.authHeader = {'Authorization':'Bearer '+ settings.accessToken,
                         'User-Agent': settings.userAgent}

  #----------------------------------------------------------------------
  def _credentials(self):
    """"""
    scopes = "esi-assets.read_assets.v1%20esi-planets.manage_planets.v1%20publicData%20esi-wallet.read_character_wallet.v1%20esi-skills.read_skillqueue.v1%20esi-skills.read_skills.v1"

    server = HTTPServer(('', int(settings.port)), CodeHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.daemon = True
    serverThread.start()
    webbrowser.open('https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http://localhost:'+settings.port+'/&client_id='+settings.clientID+'&scope='+scopes+'&state=')

    while 1:
      time.sleep(2)
      if hasattr(settings, 'code'):
        server.shutdown()
        break

  #----------------------------------------------------------------------
  def _login(self):
    """"""
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
    """handle token refresh requests"""
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
    settingDict.pop('accessToken', None)


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

if __name__ == "__main__":
  #a = ESI(1004487144)
  a = DataRequest.getAssets(1004487144)
  print('lae')