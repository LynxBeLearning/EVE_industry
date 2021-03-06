from staticClasses import StaticData,  Settings
import DB


DB.DBUpdate._updateBlueprints()

#connect to esi, the ESI class contains methods to obtain data (e.g. getMaterials). 
 #joltanAssets = DataRequest.getAssets(1004487144)
 #joltanSkills = DataRequest.getSkills(718731811)
#marketHistory = joltanESI.getMarketHistory(34)
#a = LPClasses.TotalMaterialCost(joltanESI).calculate()
bp = Blueprints(1004487144) #

bp.printPriority()

a = DataRequest.getAssets(1004487144)

produceableItems = LPClasses.ProduceableItems(1004487144)
agg = produceableItems.T2Produceables()
agg.printTotMats()

z = LPClasses.InventableItems(1004487144).T2Inventables()
z.printTotMats()
h = IndustryJobs()
#a = Blueprints(charID=1004487144)


LPClasses.TotalMatRequirements(1004487144)
# represent blueprint data in the Blueprint class, market data are used to calculate priorities


StaticData.printDict(LPClasses.DatacoresReq(1004487144).notInAssets())
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





