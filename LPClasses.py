from staticClasses import StaticData,  Settings
import math
from Auth import DataRequest
from blueprintClasses import * 
from pulp import *


########################################################################
class ModifiedManufacturingCost:
  """calculate manufacturing cost considering ME and other modifiers to material efficiency"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    self.blueprints = Blueprints(charID)
    self.riggedCategories = [] #categories for which a rig is present on the raitaru, provides 4.2% cost reduction
    
    
  #----------------------------------------------------------------------
  def _materialModifier(self, blueprintItem):
    """calculate the overall material modifier for a set of bpcs"""
    #calculate ME modifier
    MEModifier = 1 - (blueprintItem.ME / 100.0)
    raitaruModifier = 0.99
    if StaticData.categoryID(StaticData.productID(blueprintItem.typeID)) in self.riggedCategories:
      rigModifier = 0.958
    else:
      rigModifier = 1
      
    return MEModifier * raitaruModifier * rigModifier
  
  #----------------------------------------------------------------------
  def _BPCmaterialsCalculator(self, requiredRuns, blueprintItem):
    """determine modified manufacturing cost for N runs of one BPC"""
    baseCost = StaticData.baseManufacturingCost(blueprintItem.typeID)
    modMats = {}
    materialModifier = self._materialModifier(blueprintItem)
    
    for matID in baseCost:
      modmat = int(max(requiredRuns, math.ceil( round(baseCost[matID] * requiredRuns * materialModifier, 2) + 0.01 )))
      modMats[matID] = modmat
    
    return modMats
  
  #----------------------------------------------------------------------
  def requiredComponents(self, typeID):
    """return the component materials needed for an item"""
    typeID = int(typeID)
    if typeID in self.blueprints.blueprints and self.blueprints.blueprints[typeID].t1Priority[0] == 'manufacture':
      blueprint = self.blueprints.blueprints[typeID]
      manufSize = blueprint.manufSize
      totalMaterialCost = self.t1MaterialCost(manufSize, blueprint)        
      return totalMaterialCost
    elif StaticData.originatorBp(typeID) in self.blueprints.blueprints: 
      blueprint = self.blueprints.blueprints[StaticData.originatorBp(typeID)]
      inventedIndex = ''
      for idx, i in enumerate(blueprint.T2.inventedIDs):
        if typeID == i:
          inventedIndex = int(idx)
      if blueprint.t2Priority[inventedIndex][0] == 'manufacture':
        totalMaterialCost = {}
        manufSize = blueprint.manufSize
        
        #logic that decides which bpc to use given the amount of things to produce
        sortedBPCs = sorted(blueprint.T2.items[inventedIndex], key=lambda x: x.TE)
        
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
      else:
        raise TypeError("wrong. {}".format(StaticData.idName(typeID)))      

      
    
  #----------------------------------------------------------------------
  def _componentsMaterialsCalculator(self, requiredRuns, BPO):
    """calculate materials required by components bpo"""
    baseCost = StaticData.baseManufacturingCost(BPO.typeID)
    modMats = {}
    materialModifier = self._materialModifier(BPO)
    
    for matID in baseCost:
      modmat = int(max(requiredRuns, math.ceil( round(baseCost[matID] * requiredRuns * materialModifier, 2) + 0.01 )))
      modMats[matID] = modmat
    
    return modMats
  
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
      bpTypeID = StaticData.producerID(component)
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

########################################################################
class MatsBreakDown:
  """deconvolve and print nested dictionaries produced by requiredBaseMaterials"""

  #----------------------------------------------------------------------
  def __init__(self, breakDownDict, bpTypeID, runs, componentsDict):
    """Constructor"""
    self.breakDownDict = breakDownDict
    self.name = StaticData.idName(bpTypeID)
    self.runs = runs
    self.componentsDict = componentsDict
    
  #----------------------------------------------------------------------
  def printBreakDown(self):
    """nicely print the breakdown of the required materials"""
    print "Material Breakdown for {} runs of {}:".format(self.runs, self.name)
    for i in self.breakDownDict:
      if  isinstance(self.breakDownDict[i], dict):
        print "  {} units of {} require:".format(self.componentsDict[i], StaticData.idName(i))
        for a in self.breakDownDict[i]:
          print "    {}\t{}".format(StaticData.idName(a), self.breakDownDict[i][a])
      else:
        print "  {}\t{}".format(StaticData.idName(i), self.breakDownDict[i])
        
  #----------------------------------------------------------------------
  def printTotalMats(self):
    """nicely print the total mats irrespective of their origin"""
    totalMats = self.totalMats()
    print "Total Material Breakdown for {}:".format(self.name)    
    StaticData.printDict(totalMats)
  #----------------------------------------------------------------------
  def totalMats(self):
    """produce dictionary of total base mats required"""
    totalMats = {}
    for i in self.breakDownDict:
      if  isinstance(self.breakDownDict[i], dict):
        for a in self.breakDownDict[i]:
          if a in totalMats:
            totalMats[a] += self.breakDownDict[i][a]
          else:
            totalMats[a] = self.breakDownDict[i][a]
      else:
        if i in totalMats:
          totalMats[i] += self.breakDownDict[i]
        else:
          totalMats[i] = self.breakDownDict[i]
          
    return totalMats
    
    
    
  
          
          
          

#DEPRECATED FOR NOW
########################################################################
class TotalMaterialCost:
  """calculate total material cost for a group of items."""

  #----------------------------------------------------------------------
  def __init__(self, ESI):
    """Constructor"""
    
    self.esi = ESI
    
    
  #----------------------------------------------------------------------
  def calculate(self):
    """"""
    totMats = {}
    ratios = self.calcVolumeRatio()
    BPOList = open("allBPOs.txt")
    
    for i in BPOList:
      i = i.strip()
      CopySize, manufSize, minMarketSize = StaticData.marketSize(StaticData.idName(i))
      a = StaticData.baseManufacturingCost(StaticData.idName(i))
      
      for mat in a:
        if mat in totMats:
          totMats[mat] += a[mat] * manufSize * ratios[StaticData.idName(i)]
        else:
          totMats[mat] = a[mat] * manufSize * ratios[StaticData.idName(i)]
          
          
    return totMats
      
  #----------------------------------------------------------------------
  def calcVolumeRatio(self):
    """"""
    returnDict = {}
    BPOList = open("allBPOs.txt")
    for i in BPOList:
      i = i.strip()
      CopySize, manufSize, minMarketSize = StaticData.marketSize(StaticData.idName(i))
      
      a = self.esi.getMarketHistory(StaticData.productID(StaticData.idName(i)))
      daysPerManuf = manufSize / a.medianVolume(90)
      
      returnDict[StaticData.idName(i)] =  10 / daysPerManuf #/ 
      
      

      
    return returnDict
  
  
########################################################################
class DatacoresReq:
  """determines the required datacores to run all remaining invention jobs"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    self.charID = charID
    blueprints = Blueprints(self.charID)
    typeIDs = blueprints.blueprints.keys() #sort the itemIDs by corresponding names
    self.datacoresDict = {}
    
    for typeID in typeIDs:
      bpContainer = blueprints.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if  bpContainer.t2Priority[index][0] == 'invention' and bpContainer.BPO.component == 0:
            tempDict = StaticData.datacoreRequirements(typeID)
            for datacore in tempDict:
              if datacore in self.datacoresDict:
                self.datacoresDict[datacore] += tempDict[datacore] * bpContainer.t2Priority[index][1]
              else:
                self.datacoresDict[datacore] = tempDict[datacore] * bpContainer.t2Priority[index][1]
                
                
  #----------------------------------------------------------------------
  def notInAssets(self):
    """subtract owned datacores from the total required"""
    materialStore = DataRequest.getAssets(self.charID).materials()
    notInAssetsDict = {}
    for typeID in self.datacoresDict:
      if typeID in materialStore:
        remaining = int(self.datacoresDict[typeID]) - int(materialStore[typeID])
        if remaining <= 0:
          continue
        else:
            notInAssetsDict[typeID] = remaining
      else:
        notInAssetsDict[typeID] = int(self.datacoresDict[typeID])
         
    return notInAssetsDict
    
    
    
  
    
########################################################################
class ProduceableItems:
  """calculate the maximum amount of items that can be produced with current materials"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    self.blueprints = Blueprints(charID)
    self.materials = DataRequest.getAssets(charID).materials()
    self.modmanCosts = ModifiedManufacturingCost(charID)
    self.results = {}
    
    
  #----------------------------------------------------------------------
  def T2Produceables(self):
    """determine produceable T2 items"""
    #vars
    items = [] #list of all items    
    objectiveFunction = {} #names of items, this is the objective function "name": 1
    matsDict = {} #a dict containing another dict for every resource. the latter contains the amount of that resource required for every object    
    
    #determine total resources
    for blueprintID in self.blueprints.blueprints:
      bpContainer = self.blueprints.blueprints[blueprintID]
      if bpContainer.BPO.component == 1 or bpContainer.T2.inventable == 0:
        continue
      for idx in range(len(bpContainer.T2.inventedIDs)):
        if not bpContainer.t2Priority[idx][0] == 'manufacture':
          continue
        matsRequired = self.modmanCosts.requiredBaseMaterials(bpContainer.T2.inventedIDs[idx])
        matsRequired = matsRequired.totalMats()
        items.append(bpContainer.T2.inventedIDs[idx])
        objectiveFunction[bpContainer.T2.inventedIDs[idx]] = 1
        for mat in matsRequired:
          if mat not in matsDict:
            matsDict[mat] = {}   
    
    
    for blueprintID in self.blueprints.blueprints:
      bpContainer = self.blueprints.blueprints[blueprintID]
      if bpContainer.BPO.component == 1 or bpContainer.T2.inventable == 0:
        continue
      for idx in range(len(bpContainer.T2.inventedIDs)):
        bpTypeID = bpContainer.T2.inventedIDs[idx]
        if not bpContainer.t2Priority[idx][0] == 'manufacture':
          continue
        matsRequired = self.modmanCosts.requiredBaseMaterials(bpContainer.T2.inventedIDs[idx])
        matsRequired = matsRequired.totalMats()
        
        for resource in matsDict:
          if resource in matsRequired:
            matsDict[resource][bpTypeID] = matsRequired[resource]
          else:
            matsDict[resource][bpTypeID] = 0
          
    prob = LpProblem("t2 produceable items",LpMaximize)
    itemVars = LpVariable.dicts("items",items,0, 1, LpInteger)
    
    prob += lpSum([objectiveFunction[i]*itemVars[i] for i in items]), "all items, this represents the objective function"

    for i in matsDict:
      if i in self.materials:
        ownedMat = self.materials[i]
      else:
        ownedMat = 0
      prob += lpSum([matsDict[i][x] * itemVars[x] for x in items]) <= ownedMat, StaticData.idName(i)
      
    prob.solve()
  
    #for v in prob.variables():
    #  print(v.name, "=", v.varValue)
    
    
    
    return OptimizedAggregator(prob.variables(), self.modmanCosts, self.materials)

  
########################################################################
class OptimizedAggregator:
  """aggregates needed components of buildable items, takes results of simplex optimization as arguments"""

  #----------------------------------------------------------------------
  def __init__(self, optimizedResults, modManCosts,  materials):
    """Constructor"""
    self.finalDict = {}
    self.itemList = []
    self.materials = materials
    self.optimizedResults = optimizedResults
    self.modManCosts = modManCosts
    
    for item in optimizedResults:
      if item.varValue == 1:
        bpTypeID = int(item.name[6:])
        self.itemList.append(bpTypeID)
        matsRequired = self.modManCosts.requiredComponents(bpTypeID)
        
        for i in matsRequired:
          if i in self.finalDict:
            self.finalDict[i] += matsRequired[i]
          else:
            self.finalDict[i] = matsRequired[i]
            
            
  #----------------------------------------------------------------------
  def printTotMats(self):
    """print the total mats required for the optimized items"""
    print "ITEMS BUILDABLE WITH CURRENT RESOURCES:"
    for i in self.itemList:
      print "{}".format(StaticData.idName(StaticData.productID(i)))
    print "\n"
    print "TOTAL REQUIRED COMPONENTS:"
    for key in self.finalDict:
      print "{}\t{}".format(StaticData.idName(key), self.finalDict[key])    
    print "\n"
    print "MISSING COMPONENTS:"
    remainingMinerals, requiredMats = StaticData.materialSubtraction(self.materials, self.finalDict)                                                             
    for key in requiredMats:
      if StaticData.producerID(key):
        print "{}\t{}".format(StaticData.idName(key), self.finalDict[key])
    
    
########################################################################
class TotalMatRequirements:
  """calculate material requirements for all item with production priority"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    self.charID = charID
    self.blueprints = Blueprints(self.charID)
    self.materials = DataRequest.getAssets(self.charID).materials()
    self.modMatCost = ModifiedManufacturingCost(self.charID)
    self.result = {}
    
    
    for blueprintID in self.blueprints.blueprints:
      blueprint = self.blueprints.blueprints[blueprintID]
      if not blueprint.T2.inventable:
        continue
      for idx in range(len(blueprint.T2.inventedIDs)):
        if blueprint.t2Priority[idx][0] == "manufacture":
          matsBreakdown = self.modMatCost.requiredBaseMaterials(blueprint.T2.inventedIDs[idx])
          totalMats = matsBreakdown.totalMats()
          self.result = StaticData.materialAddition(self.result, totalMats)
    
    print "TOTAL REQUIRED:\n"
    StaticData.printDict(self.result)
    print "\n\nNOT OWNED:\n"
    StaticData.printDict(StaticData.materialSubtraction(self.result, self.materials)[0])
  

########################################################################
class InventableItems:
  """calculate the maximum amount of items that can be produced with current materials"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    self.blueprints = Blueprints()
    self.materials = DataRequest.getAssets(charID).materials()
    self.modmanCosts = ModifiedManufacturingCost(charID)
    self.results = {}
    
    
  #----------------------------------------------------------------------
  def T2Inventables(self):
    """determine inventable T2 items"""
    #vars
    items = [] #list of all blueprints    
    objectiveFunction = {} #names of items, this is the objective function "name": required invention runs
    datacoresDict = {} #a dict containing another dict for every resource. the latter contains the amount of that resource required for every object    
    
    #determine total resources
    for blueprintID in self.blueprints.blueprints:
      bpContainer = self.blueprints.blueprints[blueprintID]
      if not bpContainer.T2.inventable:
        continue
      for idx in range(len(bpContainer.T2.inventedIDs)):
        if not bpContainer.t2Priority[idx][0] == 'invention':
          continue
        
        reqDatacores = StaticData.datacoreRequirements(StaticData.originatorBp(bpContainer.T2.inventedIDs[idx]))
        items.append(bpContainer.T2.inventedIDs[idx])
        objectiveFunction[bpContainer.T2.inventedIDs[idx]] = 1
        for datacore in reqDatacores:
          if datacore not in datacoresDict:
            datacoresDict[datacore] = {}   
    
    
    for blueprintID in self.blueprints.blueprints:
      bpContainer = self.blueprints.blueprints[blueprintID]
      if not bpContainer.T2.inventable:
        continue
      for idx in range(len(bpContainer.T2.inventedIDs)):
        bpTypeID = bpContainer.T2.inventedIDs[idx]
        if not bpContainer.t2Priority[idx][0] == 'invention':
          continue
        reqDatacores = StaticData.datacoreRequirements(StaticData.originatorBp(bpTypeID))
        
        for datacore in datacoresDict:
          if datacore in reqDatacores:
            datacoresDict[datacore][bpTypeID] = reqDatacores[datacore] * bpContainer.t2Priority[idx][1]
          else:
            datacoresDict[datacore][bpTypeID] = 0
          
    prob = LpProblem("t2 inventable items",LpMaximize)
    itemVars = LpVariable.dicts("items",items,0, 1, LpInteger)
    
    prob += lpSum([objectiveFunction[i]*itemVars[i] for i in items]), "all items, this represents the objective function"

    for datacore in datacoresDict:
      if datacore in self.materials:
        ownedMat = self.materials[datacore]
      else:
        ownedMat = 0
      prob += lpSum([datacoresDict[datacore][x] * itemVars[x] for x in items]) <= ownedMat, StaticData.idName(datacore)
      
    prob.solve()
  
    #for v in prob.variables():
    #  print(v.name, "=", v.varValue)
    
    
    
    return DatacoreOptimizedAggregator(prob.variables(), self.blueprints, self.materials)
        
      
  
########################################################################
class DatacoreOptimizedAggregator:
  """aggregates needed components of inventable items, takes results of simplex optimization as arguments"""

  #----------------------------------------------------------------------
  def __init__(self, optimizedResults, blueprints, materials):
    """Constructor"""
    self.finalDict = {}
    self.itemList = []
    self.materials = materials
    self.optimizedResults = optimizedResults
    self.blueprints = blueprints
    
    for item in optimizedResults:
      if item.varValue == 1:
        bpTypeID = int(item.name[6:])
        self.itemList.append(bpTypeID)
        
        
        
        
            
            
  #----------------------------------------------------------------------
  def printTotMats(self):
    """print the total mats required for the optimized items"""
    print "ITEMS INVENTABLE WITH CURRENT RESOURCES:"
    for i in self.itemList:
      idx = self.blueprints.blueprints[StaticData.originatorBp(i)].T2.inventedIDs.index(i)
      print "{}\t{}".format(StaticData.idName(i), self.blueprints.blueprints[StaticData.originatorBp(i)].t2Priority[idx][1])
