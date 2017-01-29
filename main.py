from Auth import ESI
from staticClasses import StaticData,  Settings
from blueprintClasses import * 
import eveapi
import LPClasses

#connect to esi, the ESI class contains methods to obtain data (e.g. getMaterials). 
joltanESI = ESI()
joltanAssets = joltanESI.getAssets()
joltanSkills = joltanESI.getSkills()
#marketHistory = joltanESI.getMarketHistory(34)
#a = LPClasses.TotalMaterialCost(joltanESI).calculate()

#connecting and caching the xml api for joltan (only supported character for now)
cachedApi = eveapi.EVEAPIConnection(cacheHandler=eveapi.MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=Settings.keyID, vCode=Settings.vCode).character(Settings.joltanID)
#gather data about blueprints from xml api 
BlueprintItemParserO = BlueprintItemParser(joltanXml.Blueprints())
#gather market data through the xml api 
marketData = MarketOrders(joltanXml)
# represent blueprint data in the Blueprint class, market data are used to calculate priorities
bp = Blueprints(BlueprintItemParserO, marketData, joltanSkills)

n = joltanAssets.materials()
x = LPClasses.datacoresReq(bp)

h = LPClasses.ModifiedManufacturingCost(bp.blueprints[976])
z = h.requiredComponents()

#after the setup above, we can calculate useful stuff:
#outputs priority list, bpc run list or market order lists
bp.printPriority()
bp.printBPCRuns()
marketData.ordersList()


#calculate manufacturing cost of any item
a = StaticData.baseManufacturingCost(StaticData.idName("Ice Harvester II Blueprint"))
StaticData.inventionProb(joltanSkills, StaticData.idName('Incursus Blueprint'))

