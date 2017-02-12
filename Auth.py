from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading
import urlparse
import base64
import os
import webbrowser
import json
import csv
import requests
import grequests
import time
import pubsub
import locale
#from ESIRequests import Assets
from staticClasses import StaticData, Settings
from ESIClasses import *
import pickle



  

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
    parsed_path = urlparse.urlparse(self.path)
    parts=urlparse.parse_qs(parsed_path.query)
    self.send_response(200)
    self.end_headers()
    self.wfile.write('Login successful. you can close this window now')
    pubsub.publish('code', str(parts['code'][0]))
    self.finish()
    self.connection.close()    
  def log_message(self, format, *args):
    return


########################################################################
class ESI:
  """take care of login and authentication operations for the ESI interface"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor, perform credentials operations and handles the code returned by the api"""
    self.charID = charID
    if Settings.config.has_option(charID, 'ACCESSTOKEN'):
      self.authHeader = {'Authorization':'Bearer '+ Settings.charConfig[charID]['ACCESSTOKEN'],'User-Agent': Settings.userAgent}
    elif Settings.charConfig[charID]['REFRESHTOKEN']:
      self._refresh()
      self.authHeader = {'Authorization':'Bearer '+ Settings.charConfig[charID]['ACCESSTOKEN'],'User-Agent': Settings.userAgent}
    else:
      self._credentials()
      self._login()
      self.authHeader = {'Authorization':'Bearer '+ Settings.charConfig[charID]['ACCESSTOKEN'],'User-Agent': Settings.userAgent}
    
  #----------------------------------------------------------------------
  def _credentials(self):
    """"""
    scopes = "esi-assets.read_assets.v1%20esi-planets.manage_planets.v1%20publicData%20esi-wallet.read_character_wallet.v1%20esi-skills.read_skillqueue.v1%20esi-skills.read_skills.v1"

    server = HTTPServer(('', int(Settings.port)), CodeHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.daemon = True
    serverThread.start()  
    webbrowser.open('https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http://localhost:'+Settings.port+'/&client_id='+Settings.clientID+'&scope='+scopes+'&state=') #%20%20%20%20%20%20%20%20%20%20%20%20%20%20  %20%20%20%20
    Settings.updateCode(self.charID)         
      
  #----------------------------------------------------------------------
  def _login(self):
    """"""
    headers = {'User-Agent':Settings.userAgent}
    query = {'grant_type':'authorization_code','code': Settings.charConfig[self.charID]['CODE']}
    headers = {'Authorization':'Basic '+ base64.b64encode(Settings.clientID+':'+Settings.secret),'User-Agent':Settings.userAgent}
    r = requests.post(Settings.authUrl,params=query,headers=headers) 
    response = r.json()
    Settings.charConfig[self.charID]['ACCESSTOKEN'] = response['access_token']
    Settings.charConfig[self.charID]['REFRESHTOKEN'] = response['refresh_token']  
    self._saveRefreshToken()
    
  #----------------------------------------------------------------------
  def _refresh(self):
    """handle token refresh requests"""
    refreshToken = Settings.charConfig[self.charID]['REFRESHTOKEN']
    headers = {'Authorization':'Basic '+ base64.b64encode(Settings.clientID+':'+Settings.secret),'User-Agent':Settings.userAgent}
    query = {'grant_type':'refresh_token','refresh_token':refreshToken}
    r = requests.post(Settings.authUrl,params=query,headers=headers)
    response = r.json()
    Settings.charConfig[self.charID]['ACCESSTOKEN'] = response['access_token']
    Settings.charConfig[self.charID]['REFRESHTOKEN'] = response['refresh_token']  
    #save refresh token
    self._saveRefreshToken()
  
  #----------------------------------------------------------------------
  def _saveRefreshToken(self):
    """save the refresh token to config.ini"""
    #save refresh token
    refreshToken = Settings.charConfig[self.charID]['REFRESHTOKEN']
    Settings.config.set(str(self.charID), 'REFRESHTOKEN', refreshToken)
    fileHandle = open(Settings.iniPath, 'w')
    Settings.config.write(fileHandle)
    fileHandle.close()
      
      
      
      
########################################################################
class DataRequest:
  """request data to APIs, either ESI or XML"""
  
  #----------------------------------------------------------------------
  @classmethod
  def getAssets(cls, charID): 
    """query esi for asset data"""
    cacheName = str(charID) + "Assets.cache"
    
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
      assets = Assets(r.json())
      
      #saving cache
      if not os.path.isdir('cache'):
        os.mkdir('cache')
      pickleOut = open("cache/"+cacheName, 'wb')
      pickle.dump(assets, pickleOut) 
  
      return assets
  
  #----------------------------------------------------------------------
  @classmethod
  def getSkills(cls, charID):
    """query esi for skill data"""
    cacheName = str(charID) + "Skill.cache"

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
      
      return skills
  
  #----------------------------------------------------------------------
  @classmethod
  def getMarketHistory(cls, charID, typeID): 
    """query esi for market history data"""
    cacheName = str(charID) + "marketHistory" + str(typeID)+ ".cache"
    
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
      marketHistoryUrl = 'https://esi.tech.ccp.is/latest/markets/{}/history/?type_id={}'.format(Settings.fadeID, typeID)
      r = requests.get(marketHistoryUrl, headers=esi.authHeader)
      marketHistory = MarketHistory(r.json())
      
      #saving cache
      if not os.path.isdir('cache'):
        os.mkdir('cache')
      pickleOut = open("cache/"+cacheName, 'wb')
      pickle.dump(marketHistory, pickleOut)            
      
      return marketHistory    
      

        





 
  
