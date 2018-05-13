import math
import utils
import random
import market
import operator

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
def requiredMaterials(typeID, componentsOnly = False, manufSize = None):
    """return the component materials needed for manufSize number of items"""
    bpItems = utils.getBlueprintsItems(typeID)
    if not manufSize:
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
                totalMaterialCost = utils.integrate(totalMaterialCost,
                                                    matID,
                                                    modMaterialCost[matID])
            manufSize = manufSize - runs
        elif manufSize - runs == 0:
            modMaterialCost = modifiedMaterials(typeID, runs, ME)
            for matID in modMaterialCost:
                if componentsOnly and not utils.buildable(matID):
                    continue
                totalMaterialCost = utils.integrate(totalMaterialCost,
                                                    matID,
                                                    modMaterialCost[matID])
            break
        elif manufSize - runs < 0:
            modMaterialCost = modifiedMaterials(typeID, manufSize, ME)
            for matID in modMaterialCost:
                if componentsOnly and not utils.buildable(matID):
                    continue
                totalMaterialCost = utils.integrate(totalMaterialCost,
                                                    matID,
                                                    modMaterialCost[matID])
            break

    return totalMaterialCost

#----------------------------------------------------------------------
def marketChooser(typeIDs):
    """chose items on the basis of expected profit"""
    profits = {}
    for typeID in typeIDs:
        print(f'calculating profits for {utils.idName(typeID)}...')
        manufSize = typeIDs[typeID]
        productID = utils.productID(typeID)
        itemSellPrice = market.avgSellPrice(productID) * manufSize

        matsToBuild = manufactureItems(disregardOwnedMats=True,
                                      report=False,
                                      typeIDs={typeID: manufSize,})

        totalMatCost = 0
        for mat in matsToBuild:
            numMats = matsToBuild[mat]
            matCost = market.avgSellPrice(mat) * numMats
            totalMatCost += matCost

        profits[typeID] = itemSellPrice - totalMatCost
        print(f'expected profits {market.millify(profits[typeID])}!')

    return profits

#----------------------------------------------------------------------
def chooseItems(mode = 'random', nItems = 10):
    """query db for produceable stuff and applies whatever
    filter, return list of typeIDs"""
    command = (f'SELECT "typeID", "manufSize" '
               f'FROM "BlueprintPriority" '
               f'WHERE "priority" = "manufacturing" ')

    typeIDs = utils.dbQuery(utils.currentDb, command, fetchAll=True)
    typeIDs = dict(typeIDs)

    if mode == 'random':
        chosen = random.sample(typeIDs.keys(), nItems)
        return {typeID: typeIDs[typeID] for typeID in typeIDs if typeID in chosen}
    elif mode == 'market':
        profits = marketChooser(typeIDs)
        sortedProfits = sorted(profits.items(), key=operator.itemgetter(1), reverse= True)
        print(f"expected total profit: {market.millify(sum(x[1] for x in sortedProfits[1:nItems]))}")
        return {typeID[0]: typeIDs[typeID[0]] for typeID in sortedProfits[1:nItems]}
#----------------------------------------------------------------------
def materialReport(items, components, materials):
    """prints list of items and required components and materials"""
    print("TO BUILD ITEMS:\n")
    utils.printDict(items)
    print("\nCOMPONENTS REQUIRED:\n")
    utils.printDict(components)
    print("\nRAW MATERIALS REQUIRED:\n")
    utils.printDict(materials)


#----------------------------------------------------------------------
def manufactureItems(mode = 'market', nItems = 10, disregardOwnedMats = False,
                     report = True, typeIDs = None):
    """choses items, calculates materials, presents results"""
    if not typeIDs:
        typeIDs = chooseItems(mode=mode, nItems=nItems)

    #calculate total components and additional raw materials needed for typeID production
    materials = {}
    components = {}
    for typeID in typeIDs:
        reqMats = requiredMaterials(typeID)
        for matID in reqMats:
            if utils.buildable(matID):
                components = utils.integrate(components,
                                             matID,
                                             reqMats[matID])
            else:
                materials = utils.integrate(materials,
                                            matID,
                                            reqMats[matID])

    #subtract already owned components from the list
    if not disregardOwnedMats:
        ownedMats = utils.getOwnedMaterials()
        components, ownedMats = utils.dictSubtraction(components,
                                                  ownedMats)


    #further break down components into raw materials
    for componentID in components:
        producerID = utils.producerID(componentID)
        reqMats = requiredMaterials(producerID, manufSize= components[componentID])
        for matID in reqMats:
            materials = utils.integrate(materials,
                                        matID,
                                        reqMats[matID])

    #subtract already owned raw materials from the list
    if not disregardOwnedMats:
        materials, ownedMats = utils.dictSubtraction(materials, ownedMats)

    #final report
    if report:
        materialReport(typeIDs, components, materials)
    else:
        return materials

if __name__ == "__main__":

    manufactureItems()
