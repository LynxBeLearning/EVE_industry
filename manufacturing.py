import math
import utils

#----------------------------------------------------------------------
def baseMaterials(typeID):
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
    engComplexModifier = 0.99
    #commented code below is used to implement rigged categories on engineering complexes
    #not used for the moment.
    #if StaticData.categoryID(StaticData.productID(blueprintItem.typeID)) in self.riggedCategories:
    #  rigModifier = 0.958
    #else:
    #  rigModifier = 1

    return MEModifier * engComplexModifier  #* rigModifier

#----------------------------------------------------------------------
def modifiedMaterials(typeID, requiredRuns, ME):
    """determine modified manufacturing cost for N runs of one BPC"""
    baseCost = baseMaterials(typeID)
    matMod = materialModifier(ME)

    modMats = {}
    for matID in baseCost:
        modmat = int(max(requiredRuns, math.ceil( round(baseCost[matID] * requiredRuns * matMod, 2) + 0.01 )))
        modMats[matID] = modmat

    return modMats


#----------------------------------------------------------------------
def requiredMaterials(typeID, componentsOnly = False):
    """return the component materials needed for manufSize number of items"""
    bpItems = utils.getBlueprintsItems(typeID)
    manufSize = utils.size(typeID)[1]

    #modify runs if they are negative (i.e, if a bpo is available)
    for bp in bpItems:
        ME = bp[0]
        runs = bp[1]
        if runs == -1:  #bpos have -1 runs
            bpItems = [[ME, 10000000]]
            break

    #logic that decides which bpc to use given the amount of things to produce
    sortedBPCs = sorted(bpItems, key=lambda x: x[0], reverse= True)

    totalMaterialCost = {}
    for BP in sortedBPCs:
        ME = BP[0]
        runs = BP[1]
        if manufSize - runs > 0:
            modMaterialCost = modifiedMaterials(typeID, runs, ME)
            for matID in modMaterialCost:
                if componentsOnly and not utils.buildable(matID):
                    continue
                elif matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            manufSize = manufSize - runs
        elif manufSize - runs == 0:
            modMaterialCost = modifiedMaterials(typeID, runs, ME)
            for matID in modMaterialCost:
                if componentsOnly and not utils.buildable(matID):
                    continue
                elif matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break
        elif manufSize - runs < 0:
            modMaterialCost = modifiedMaterials(typeID, manufSize, ME)
            for matID in modMaterialCost:
                if componentsOnly and not utils.buildable(matID):
                    continue
                elif matID in totalMaterialCost:
                    totalMaterialCost[matID] += modMaterialCost[matID]
                else:
                    totalMaterialCost[matID] = modMaterialCost[matID]
            break

    return totalMaterialCost

#----------------------------------------------------------------------
def itemChooser():
    """query db for produceable stuff and applies whatever
    filter, return list of typeIDs"""

#----------------------------------------------------------------------
def productionBreakdown():
    """choses items, calculates materials, presents results"""


a = requiredMaterials(956)
pls = "efw"