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

########################################################################
class Settings: #TURN THIS INTO STATIC CLASS?
  """read and hold settings variables"""

  #----------------------------------------------------------------------
  def __init__(self):
    """Constructor"""
    settingsDict = {}
    settingsFile = open("config.ini")
    for line in settingsFile:
      tempList = line.strip().split(" = ")
      settingsDict[tempList[0]] = tempList[1]
    settingsFile.close()
    
    #code listener
    self._listener = pubsub.subscribe("code")
    
    #variables
    self.crestUrl = settingsDict['CRESTURL']
    self.esiUrl = settingsDict['ESIURL']
    self.esiEndpointsUrl = settingsDict['ESIENDPOINTS']
    self.userAgent = settingsDict['USERAGENT']
    self.port = settingsDict['PORT']
    self.clientID = settingsDict['CLIENTID']
    self.secret = settingsDict['SECRET']
    self.authUrl = settingsDict['AUTHTOKEN']
    self.keyID = settingsDict['KEYID']
    self.vCode = settingsDict['VCODE']    
    self.code = ''
    self.esiEndpoints = ''
    self.accessToken = ''
    
    self.expires = ''
    if "REFRESHTOKEN" in settingsDict:
      self.refreshToken = settingsDict['REFRESHTOKEN']
    else:
      self.refreshToken = ''
      
    #locations, ADD THESE TO A CONFIG FILE
    self.allowedLocations = {
      1022771210683 : "zansha mining, bpc container", #zansha mining, bpc container
      1022832888095 : "zansha neuro, researched bpo container", #zansha neuro, researched bpo container
      1022946515289 : "dunk's workshop, component bpos",  #zansha mining, components bpos container
      1022756068998 : "zansha neuro, hangar",  #zansha neuro, hangar
      1022946509438: "dunk's workshop, T2 bpc container",
      1022946637486: "dunk's workshop, t1 bpc container",
      1022975749725: "zansha neuro, BPO container",
      
    }
    
    self.knownLocations = {
      1019684069461: "amarr, manufacturing container",
      60006142 : "yehnifi station hangar",
      1022975868749L: "DO6 fortizar, low priority blueprint container",
      1022975750208L: "zansha neuro, unreaserched BPOs",
      1022946551363L: "fortizar misc container",
      1019684069479L: "amarr misc container",
      
     
    }
    self.marketStationID = 61000990 # DO6 STATION, 60008494 is for amarr station
    
  #----------------------------------------------------------------------
  def updateCode(self):
    """listen for code broadcasts and set the variable."""
    self.code = self._listener.listen().next()['data']
      
  

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
class AuthOperations:
  """take care of login and authentication operations"""

  #----------------------------------------------------------------------
  def __init__(self, settingsObj):
    """Constructor, perform credentials operations and handles the code returned by the api"""
    self.settings = settingsObj
    
    if self.settings.refreshToken:
      self.refresh()
    else:
      self.credentials()
      self.login()
    
    self.authHeader = {'Authorization':'Bearer '+ self.settings.accessToken,'User-Agent':self.settings.userAgent}
    self.chrID = self.getCharID()
  #----------------------------------------------------------------------
  def credentials(self):
    """"""
    server = HTTPServer(('', int(self.settings.port)), CodeHandler)
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.daemon = True
    serverThread.start()  
    webbrowser.open('https://login.eveonline.com/oauth/authorize?response_type=code&redirect_uri=http://localhost:'+self.settings.port+'/&client_id='+self.settings.clientID+'&scope=esi-assets.read_assets.v1%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20esi-planets.manage_planets.v1%20%20%20%20%20&state=')
    self.settings.updateCode()         
      
  #----------------------------------------------------------------------
  def login(self):
    """"""
    headers = {'User-Agent':self.settings.userAgent}
    query = {'grant_type':'authorization_code','code': self.settings.code}
    r = requests.get(self.settings.esiEndpointsUrl, headers=headers) 
    self.settings.esiEndpoints=r.json() 
    headers = {'Authorization':'Basic '+ base64.b64encode(self.settings.clientID+':'+self.settings.secret),'User-Agent':self.settings.userAgent}
    r = requests.post(self.settings.authUrl,params=query,headers=headers) 
    response = r.json()
    self.settings.accessToken=response['access_token']
    self.settings.refreshToken=response['refresh_token']
    self.settings.expires=time.time()+float(response['expires_in'])-20
    self.saveRefreshToken()
 
    
    #self.load_base_data()
    
  #----------------------------------------------------------------------
  def refresh(self):
    """handle token refresh requests"""
    headers = {'Authorization':'Basic '+ base64.b64encode(self.settings.clientID+':'+self.settings.secret),'User-Agent':self.settings.userAgent}
    query = {'grant_type':'refresh_token','refresh_token':self.settings.refreshToken}
    r = requests.post(self.settings.authUrl,params=query,headers=headers)
    response = r.json()
    self.settings.accessToken=response['access_token']
    self.settings.refreshToken=response['refresh_token']
    self.settings.expires=time.time()+float(response['expires_in'])-20
    #get endpoints
    r = requests.get(self.settings.esiEndpointsUrl, headers=headers) 
    self.settings.esiEndpoints=r.json()
    #save refresh token
    self.saveRefreshToken()
  
  #----------------------------------------------------------------------
  def saveRefreshToken(self):
    """save the refresh token to config.ini"""
    #save refresh token
    if self.settings.refreshToken:
      settingsFile = open("config.ini")
      lines = settingsFile.readlines()
      settingsFile.close()
      
      settingsFileWrite = open("config.ini", 'w')
      for line in lines:
        if line.startswith("REFRESHTOKEN"):
          pass
        else:
          settingsFileWrite.write(line)
      settingsFileWrite.write("REFRESHTOKEN = {}".format(self.settings.refreshToken))
    
  #----------------------------------------------------------------------
  def getCharID(self):
    """queries server for char ID"""
    r = requests.get("https://login.eveonline.com/oauth/verify/", headers=self.authHeader)
    return r.json()["CharacterID"]
      
 





#print "lala"
  
