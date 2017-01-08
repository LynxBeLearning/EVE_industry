from Auth import ESI
from staticClasses import StaticData,  Settings
from blueprintClasses import * 

#connecting and caching the xml api for joltan (only supported character for now)
cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=Settings.keyID, vCode=Settings.vCode).character(1004487144)
#gather data about blueprints from xml api and represent it in the Blueprint class
BlueprintItemParserO = BlueprintItemParser(joltanXml.Blueprints())
bp = Blueprints(BlueprintItemParserO, marketData)
#gather market data through the xml api 
marketData = MarketOrders(joltanXml)
#connect to esi, the ESI class contains methods to obtain data (e.g. getMaterials). 
joltanESI = ESI()
a = joltan.getMaterials()

#after the setup above, we can calculate useful stuff:
#calculate manufacturing cost of any item
a = StaticData.manufacturingCost(StaticData.idName("Ice Harvester II Blueprint"))
#outputs priority list, bpc run list or market order lists
bp.printPriority()
bp.printBPCRuns()
marketData.ordersList()





