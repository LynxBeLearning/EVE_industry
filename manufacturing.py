import math
import utils

#----------------------------------------------------------------------
def baseManufacturingCost(typeID):
    """calculate the manufacturing cost of an item"""
    typeID = int(typeID)
    returnDict = {}
    command = (f'SELECT "materialTypeID", "quantity" '
             f'FROM "industryActivityMaterials" '
               f'WHERE "TypeID" = {typeID} '
               f'AND "activityID" = 1')

    materials = utils.dbQuery(utils.staticDb, command, fetchAll=True)

    if len(materials) > 0:
        for materialTuple in materials:
            returnDict[materialTuple[0]] = materialTuple[1]
    else:
        return None

    return returnDict

#----------------------------------------------------------------------
def materialModifier(ME):
    """calculate the overall material modifier for a set of bpcs"""
    #calculate ME modifier
    MEModifier = 1 - (ME / 100.0)
    raitaruModifier = 0.99
    #commented code below is used to implement rigged categories on engineering complexes
    #not used for the moment.
    #if StaticData.categoryID(StaticData.productID(blueprintItem.typeID)) in self.riggedCategories:
    #  rigModifier = 0.958
    #else:
    #  rigModifier = 1

    return MEModifier * raitaruModifier  #* rigModifier

#----------------------------------------------------------------------
def BPCmaterialsCalculator(typeID, requiredRuns, ME):
    """determine modified manufacturing cost for N runs of one BPC"""
    baseCost = baseManufacturingCost(typeID)
    matMod = materialModifier(ME)

    modMats = {}
    for matID in baseCost:
        modmat = int(max(requiredRuns, math.ceil( round(baseCost[matID] * requiredRuns * matMod, 2) + 0.01 )))
        modMats[matID] = modmat

    return modMats


#----------------------------------------------------------------------
def requiredComponents(typeID):
    """return the component materials needed for an item"""
    bpItems = utils.getBlueprintsItems(typeID)
    manufSize = utils.size(typeID)[1]

    #logic that decides which bpc to use given the amount of things to produce
    sortedBPCs = sorted(bpItems, key=lambda x: x[0])

    totalMaterialCost = {}
    for BPC in sortedBPCs:
        ME = BPC[0]
        runs = BPC[1]
        if manufSize - runs > 0:
            modMaterialCost = BPCmaterialsCalculator(typeID, runs, ME)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            manufSize = manufSize - runs
        elif manufSize - runs == 0:
            modMaterialCost = BPCmaterialsCalculator(typeID, runs, ME)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break
        elif manufSize - BPC.runs < 0:
            modMaterialCost = BPCmaterialsCalculator(typeID, manufSize, ME)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break

    return totalMaterialCost




#----------------------------------------------------------------------
def t1MaterialCost(self, runs, bpContainer):
    """"""
    blueprint = bpContainer
    manufSize = runs
    totalMaterialCost = {}
    #logic that decides which bpc to use given the amount of things to produce
    sortedBPCs = sorted(blueprint.BPC.rawItems, key=lambda x: x.TE)

    for BPC in sortedBPCs:
        if manufSize - BPC.runs > 0:
            modMaterialCost = self._BPCmaterialsCalculator(BPC.runs, BPC)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            manufSize = manufSize - BPC.runs
        elif manufSize - BPC.runs == 0:
            modMaterialCost = self._BPCmaterialsCalculator(BPC.runs, BPC)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break
        elif manufSize - BPC.runs < 0:
            modMaterialCost = self._BPCmaterialsCalculator(manufSize, BPC)
            for matID in modMaterialCost:
                if matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break

    return totalMaterialCost

#----------------------------------------------------------------------
def requiredBaseMaterials(self, typeID):
    """return the total base materials needed for a given item"""
    components = self.requiredComponents(typeID)

    breakDownDict = {}

    for component in components:
        bpTypeID = utils.producerID(component)
        if bpTypeID: #this stupid conditional is needed because producerID returns strings but i need int, but if producerID returns null int throws an error.
            bpTypeID = int(bpTypeID)
        if not bpTypeID:
            breakDownDict[component] = components[component]
            continue
        elif bpTypeID in self.blueprints.blueprints:
            if self.blueprints.blueprints[bpTypeID].BPO.component == 1:
                mats = self._componentsMaterialsCalculator(components[component], self.blueprints.blueprints[bpTypeID].BPO)
                breakDownDict[component] = mats
            elif self.blueprints.blueprints[bpTypeID].BPO.component == 0:
                mats = self.t1MaterialCost(components[component], self.blueprints.blueprints[bpTypeID])
                breakDownDict[component] = mats

    try:
        return MatsBreakDown(breakDownDict, typeID, self.blueprints.blueprints[typeID].manufSize, components)
    except KeyError:
        t1TypeID = StaticData.originatorBp(typeID)
        return MatsBreakDown(breakDownDict, typeID, self.blueprints.blueprints[t1TypeID].manufSize, components)

a = requiredComponents(11175)
pls = "efw"