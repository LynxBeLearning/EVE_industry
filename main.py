from Auth import DataRequest
from staticClasses import StaticData,  Settings
from blueprintClasses import * 
import eveapi
import LPClasses

#connect to esi, the ESI class contains methods to obtain data (e.g. getMaterials). 
 #joltanAssets = DataRequest.getAssets(1004487144)
 #joltanSkills = DataRequest.getSkills(718731811)
#marketHistory = joltanESI.getMarketHistory(34)
#a = LPClasses.TotalMaterialCost(joltanESI).calculate()

#connecting and caching the xml api for joltan (only supported character for now)
 #cachedApi = eveapi.EVEAPIConnection(cacheHandler=eveapi.MyCacheHandler(debug=True))
 #joltanXml = cachedApi.auth(keyID=Settings.keyID, vCode=Settings.vCode).character(Settings.joltanID)
#gather data about blueprints from xml api 
 #BlueprintItemParserO = BlueprintItemParser(joltanXml.Blueprints())
#gather market data through the xml api 
 #marketData = MarketOrders(joltanXml)
# represent blueprint data in the Blueprint class, market data are used to calculate priorities
bp = Blueprints(1004487144)

#n = joltanAssets.materials()
#x = LPClasses.datacoresReq(bp)

#h  = LPClasses.ModifiedManufacturingCost(1004487144)
#a = h.requiredBaseMaterials(StaticData.idName("Scimitar Blueprint"))
#a.printBreakDown()
#a.printTotalMats()

produceableItems = LPClasses.ProduceableItems(1004487144)
agg = produceableItems.T2Produceables()
agg.printTotMats()

#a = LPClasses.ModifiedManufacturingCost(bp)
#g = a.requiredComponents(StaticData.idName("Deflection Shield Emitter Blueprint"))
#StaticData.printDict(g)

#after the setup above, we can calculate useful stuff:
#outputs priority list, bpc run list or market order lists
bp.printPriority()
bp.printBPCRuns()



#calculate manufacturing cost of any item
a = StaticData.baseManufacturingCost(StaticData.idName("Ice Harvester II Blueprint"))
StaticData.inventionProb(joltanSkills, StaticData.idName('Incursus Blueprint'))

