import swagger_client
from swagger_client.rest import ApiException
from staticClasses import settings, configFile
from Auth import authenticate

########################################################################
class ApiRequest:
  """request data to the ESI api"""
  # token and swagger_client setup
  authenticate()
  apiConfig = swagger_client.api_client.ApiClient()
  apiConfig.configuration.access_token = settings.accessToken
  apiConfig.default_headers = {'User-Agent': settings.userAgent}

  #----------------------------------------------------------------------
  @classmethod
  def _refreshCredentials(cls, apiObject):
    """force a refresh of the access token and set the appropriate value to api client"""
    authenticate(forceRefresh = True)
    apiObject.api_client.configuration.access_token = settings.accessToken
    cls.apiConfig.configuration.access_token = settings.accessToken

    return apiObject

  #----------------------------------------------------------------------
  @classmethod
  def _apiCall(cls, apiObject, methodName, *args, **kwargs):
    """"""
    requestMethod = getattr(apiObject, methodName)
    exception = ''

    try:
      returnJson = requestMethod(*args, **kwargs)
    except ApiException as exp:
      exception = exp
      #retry
      apiObject = cls._refreshCredentials(apiObject)
      requestMethod = getattr(apiObject, methodName)
      returnJson = requestMethod(*args, **kwargs)  #this second try might give an unhandled exception. I think this is what i want to happen, but there might be a better way.

    return returnJson

  #----------------------------------------------------------------------
  @classmethod
  def getAssets(cls):
    """query esi for asset data"""
    assetsApi = swagger_client.AssetsApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_assets"

    assets = cls._apiCall(assetsApi, methodName, settings.corpID)

    return assets

  #----------------------------------------------------------------------
  @classmethod
  def getSkills(cls, ):
    """query esi for skill data"""
    skillsApi = swagger_client.SkillsApi(cls.apiConfig)
    methodName = "get_characters_character_id_skills"

    skills = cls._apiCall(skillsApi, methodName, settings.ceoID)

    return skills

  #----------------------------------------------------------------------
  @classmethod
  def getBlueprints(cls):
    """"""
    corpApi = swagger_client.CorporationApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_blueprints"

    blueprints = cls._apiCall(corpApi, methodName, settings.corpID)

    return blueprints

  #----------------------------------------------------------------------
  @classmethod
  def getMarketOrders(cls):
    """obtain data about market orders for given corp"""
    marketApi = swagger_client.MarketApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_orders"

    marketOrders = cls._apiCall(marketApi, methodName, settings.corpID)

    return marketOrders


  #----------------------------------------------------------------------
  @classmethod
  def getIndustryJobs(cls):
    """obtain data about market orders for given character"""
    industryApi = swagger_client.IndustryApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_industry_jobs"

    industryJobs = cls._apiCall(industryApi, methodName, settings.corpID)

    return industryJobs

  #----------------------------------------------------------------------
  @classmethod
  def getAdjustedPrices(cls):
    """"""
    marketApi = swagger_client.MarketApi(cls.apiConfig)
    methodName = "get_markets_prices"

    adjustedPrices = cls._apiCall(marketApi, methodName)

    return adjustedPrices


  #----------------------------------------------------------------------
  @classmethod
  def getSystemIndexes(cls):
    """"""
    industryApi = swagger_client.IndustryApi(cls.apiConfig)
    methodName = "get_industry_systems"

    adjustedPrices = cls._apiCall(industryApi, methodName)

    return adjustedPrices

  #----------------------------------------------------------------------
  @classmethod
  def getJournal(cls):
    """"""
    walletApi = swagger_client.WalletApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_wallets_division_journal"

    corpJournal = cls._apiCall(walletApi, methodName, settings.corpID, 1)

    return corpJournal

  #----------------------------------------------------------------------
  @classmethod
  def getName(cls, charID):
    """"""
    characterApi = swagger_client.CharacterApi(cls.apiConfig)
    methodName = "get_characters_names"

    charName = cls._apiCall(characterApi, methodName, [charID])

    return charName

  #----------------------------------------------------------------------
  @classmethod
  def getMarketTransactions(cls):
    """"""
    walletApi = swagger_client.WalletApi(cls.apiConfig)
    methodName = "get_corporations_corporation_id_wallets_division_transactions"

    corpTransactions = cls._apiCall(walletApi, methodName, settings.corpID, 1)

    return corpTransactions

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