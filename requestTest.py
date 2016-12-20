#from bravado.requests_client import RequestsClient
#from bravado.client import SwaggerClient
import requests
import json
import csv
from Auth import Settings,  AuthOperations

########################################################################
class requestUrls:
  """return correct urls to submit requests"""

  #----------------------------------------------------------------------
  def __init__(self, characterID):
    """Constructor"""
    
    self.assetsUrl = 'https://esi.tech.ccp.is/latest/characters/{}/assets/'.format(characterID)
    

########################################################################
class getAssets:
  """get asset data from ESI"""

  #----------------------------------------------------------------------
  def __init__(self,  assetUrl, authHeader):
    """Constructor"""
    
    r = requests.get(assetUrl, headers=authHeader)
    self.assets = r.json()
    
    
  




settings = Settings()
joltan = AuthOperations(settings)
joltanUrls = requestUrls(joltan.chrID)
joltanAssets = getAssets(joltanUrls.assetsUrl, joltan.authHeader)




print "kaorlghj"