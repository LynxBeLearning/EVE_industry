import socket
import swagger_client
from Auth import authenticate
from swagger_client.rest import ApiException
from utils import settings, configFile


#generating the proper swagger_client configuration
_apiConfig = swagger_client.api_client.ApiClient()
_apiConfig.configuration.access_token = settings.accessToken
_apiConfig.default_headers = {'User-Agent': settings.userAgent}

#----------------------------------------------------------------------
def _refreshCredentials(apiObject):
  """force a refresh of the access token and set the appropriate value to api client"""
  #authenticate again to refresh keys...
  authenticate()
  #...modify the access token of the object in question...
  apiObject.api_client.configuration.access_token = settings.accessToken
  #...and change the global configuration so later calls will work too!
  _apiConfig.configuration.access_token = settings.accessToken

  return apiObject

#----------------------------------------------------------------------
def _apiCall(apiObject, methodName, *args, **kwargs):
  """"""
  requestMethod = getattr(apiObject, methodName)
  exception = ''

  try:
    returnJson = requestMethod(*args, **kwargs)
  except ApiException as exp:
    exception = exp
    #retry
    apiObject = _refreshCredentials(apiObject)
    requestMethod = getattr(apiObject, methodName)
    returnJson = requestMethod(*args, **kwargs)  #this second try might give an unhandled exception. I think this is what i want to happen, but there might be a better way.

  return returnJson

#----------------------------------------------------------------------
def getAssets():
  """query esi for asset data"""
  assetsApi = swagger_client.AssetsApi(_apiConfig)
  methodName = "get_corporations_corporation_id_assets"

  assets = _apiCall(assetsApi, methodName, settings.corpID)

  return assets


#----------------------------------------------------------------------
def getSkills( ):
  """query esi for skill data"""
  skillsApi = swagger_client.SkillsApi(_apiConfig)
  methodName = "get_characters_character_id_skills"

  skills = _apiCall(skillsApi, methodName, settings.ceoID)

  return skills

#----------------------------------------------------------------------
def getBlueprints():
  """"""
  corpApi = swagger_client.CorporationApi(_apiConfig)
  methodName = "get_corporations_corporation_id_blueprints"

  blueprints = _apiCall(corpApi, methodName, settings.corpID)

  return blueprints

#----------------------------------------------------------------------
def getMarketOrders():
  """obtain data about market orders for given corp"""
  marketApi = swagger_client.MarketApi(_apiConfig)
  methodName = "get_corporations_corporation_id_orders"

  marketOrders = _apiCall(marketApi, methodName, settings.corpID)

  return marketOrders


#----------------------------------------------------------------------
def getIndustryJobs():
  """obtain data about market orders for given character"""
  industryApi = swagger_client.IndustryApi(_apiConfig)
  methodName = "get_corporations_corporation_id_industry_jobs"

  industryJobs = _apiCall(industryApi, methodName, settings.corpID)

  return industryJobs

#----------------------------------------------------------------------
def getAdjustedPrices():
  """"""
  marketApi = swagger_client.MarketApi(_apiConfig)
  methodName = "get_markets_prices"

  adjustedPrices = _apiCall(marketApi, methodName)

  return adjustedPrices


#----------------------------------------------------------------------
def getSystemIndexes():
  """"""
  industryApi = swagger_client.IndustryApi(_apiConfig)
  methodName = "get_industry_systems"

  adjustedPrices = _apiCall(industryApi, methodName)

  return adjustedPrices

#----------------------------------------------------------------------
def getJournal():
  """"""
  walletApi = swagger_client.WalletApi(_apiConfig)
  methodName = "get_corporations_corporation_id_wallets_division_journal"

  corpJournal = _apiCall(walletApi, methodName, settings.corpID, 1)

  return corpJournal

#----------------------------------------------------------------------
def getName(charID):
  """"""
  characterApi = swagger_client.CharacterApi(_apiConfig)
  methodName = "get_characters_names"

  charName = _apiCall(characterApi, methodName, [charID])

  return charName

#----------------------------------------------------------------------
def getMarketTransactions():
  """"""
  walletApi = swagger_client.WalletApi(_apiConfig)
  methodName = "get_corporations_corporation_id_wallets_division_transactions"

  corpTransactions = _apiCall(walletApi, methodName, settings.corpID, 1)

  return corpTransactions


def networkConnectivity(host="8.8.8.8", port=53, timeout=3):
  """
  Host: 8.8.8.8 (google-public-dns-a.google.com)
  OpenPort: 53/tcp
  Service: domain (DNS/TCP)
  """
  try:
    socket.setdefaulttimeout(timeout)
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    return True
  except Exception as ex:
    print(ex)
    return False

if __name__ == "__main__":

  #authenticate()  #forceLogin = True
  #assets = DataRequest.getAssets()
  #adjustedP = DataRequest.getAdjustedPrices()
  #indJobs = DataRequest.getIndustryJobs()
  #bp = DataRequest.getBlueprints()
  #skills = DataRequest.getSkills()
  #marketOrders = DataRequest.getMarketOrders()
  #sysInd = DataRequest.getSystemIndexes()
  #Auth(forceLogin= True)
  #journal = DataRequest.getJournal()



  print('lae')
  pass