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
  """take care of login and authentication operations"""

  #----------------------------------------------------------------------
  def __init__(self):
    """Constructor, perform credentials operations and handles the code returned by the api"""

    
    if Settings.refreshToken:
      self._refresh()
    else:
      self._credentials()
      self._login()
    
    self.authHeader = {'Authorization':'Bearer '+ Settings.accessToken,'User-Agent': Settings.userAgent}
    self.chrID = self._getCharID()
  #----------------------------------------------------------------------
  def _credentials(self):
    """"""
    scopes = "esi-assets.read_assets.v1%20esi-planets.manage_planets.v1%20publicData%20esi-wallet.read_character_wallet.v1%20esi-skills.read_skillqueue.v1%20esi-skills.read_skills.v1 %20"

    server = HTTPServer(('', int(Settings.port)), CodeHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.daemon = True
    serverThread.start()  
    webbrowser.open('https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http://localhost:'+Settings.port+'/&client_id='+Settings.clientID+'&scope='+scopes+'&state=') #%20%20%20%20%20%20%20%20%20%20%20%20%20%20  %20%20%20%20
    Settings.updateCode()         
      
  #----------------------------------------------------------------------
  def _login(self):
    """"""
    headers = {'User-Agent':Settings.userAgent}
    query = {'grant_type':'authorization_code','code': Settings.code}
    r = requests.get(Settings.esiEndpointsUrl, headers=headers) 
    Settings.esiEndpoints=r.json() 
    headers = {'Authorization':'Basic '+ base64.b64encode(Settings.clientID+':'+Settings.secret),'User-Agent':Settings.userAgent}
    r = requests.post(Settings.authUrl,params=query,headers=headers) 
    response = r.json()
    Settings.accessToken=response['access_token']
    Settings.refreshToken=response['refresh_token']
    Settings.expires=time.time()+float(response['expires_in'])-20
    self._saveRefreshToken()
 
    
    #self.load_base_data()
    
  #----------------------------------------------------------------------
  def _refresh(self):
    """handle token refresh requests"""
    headers = {'Authorization':'Basic '+ base64.b64encode(Settings.clientID+':'+Settings.secret),'User-Agent':Settings.userAgent}
    query = {'grant_type':'refresh_token','refresh_token':Settings.refreshToken}
    r = requests.post(Settings.authUrl,params=query,headers=headers)
    response = r.json()
    Settings.accessToken=response['access_token']
    Settings.refreshToken=response['refresh_token']
    Settings.expires=time.time()+float(response['expires_in'])-20
    #get endpoints
    r = requests.get(Settings.esiEndpointsUrl, headers=headers) 
    Settings.esiEndpoints=r.json()
    #save refresh token
    self._saveRefreshToken()
  
  #----------------------------------------------------------------------
  def _saveRefreshToken(self):
    """save the refresh token to config.ini"""
    #save refresh token
    if Settings.refreshToken:
      settingsFile = open("config.ini")
      lines = settingsFile.readlines()
      settingsFile.close()
      
      settingsFileWrite = open("config.ini", 'w')
      for line in lines:
        if line.startswith("REFRESHTOKEN"):
          pass
        else:
          settingsFileWrite.write(line)
      settingsFileWrite.write("REFRESHTOKEN = {}".format(Settings.refreshToken))
      
  def _getCharID(self):
    """queries server for char ID"""
    r = requests.get("https://login.eveonline.com/oauth/verify/", headers=self.authHeader)
    return r.json()["CharacterID"]
  
  
  #----------------------------------------------------------------------
  def getMaterials(self): 
    """query esi for asset data"""
    assetUrl = 'https://esi.tech.ccp.is/latest/characters/{}/assets/'.format(self.chrID)
    r = requests.get(assetUrl, headers=self.authHeader)
    assets = Materials(r.json())
    return assets
  
  #----------------------------------------------------------------------
  def getSkills(self):
    """query esi for skill data"""
    skillsUrl = 'https://esi.tech.ccp.is/latest/characters/{}/skills/'.format(self.chrID)
    r = requests.get(skillsUrl, headers=self.authHeader)
    skills = Skills(r.json())
    return skills    
      

        





 
  
