from staticClasses import StaticData,  Settings
import math
import Auth

########################################################################
class ModifiedManufacturingCost:
  """calculate manufacturing cost considering ME and other modifiers to material efficiency"""

  #----------------------------------------------------------------------
  def __init__(self, blueprints):
    """Constructor"""
    self.blueprints = blueprints
    self.riggedCategories = [] #categories for which a rig is present on the raitaru, provides 4.2% cost reduction
    
    
  #----------------------------------------------------------------------
  def _materialModifier(self, BPC):
    """calculate the overall material modifier for a set of bpcs"""
    #calculate ME modifier
    TEModifier = 1 - (BPC.ME / 100.0)
    raitaruModifier = 0.99
    if StaticData.categoryID(StaticData.productID(BPC.typeID)) in self.riggedCategories:
      rigModifier = 0.958
    else:
      rigModifier = 1
      
    return TEModifier * raitaruModifier * rigModifier
  
  #----------------------------------------------------------------------
  def _materialsCalculator(self, runs, BPC):
    """determine modified manufacturing cost for one blueprint witn N runs"""
    baseCost = StaticData.baseManufacturingCost(BPC.typeID)
    modMats = {}
    materialModifier = self._materialModifier(BPC)
    
    for matID in baseCost:
      modmat = int(max(runs, math.ceil( round(baseCost[matID] * runs * materialModifier, 2) + 0.01 )))
      modMats[matID] = modmat
    
    return modMats
  
  #----------------------------------------------------------------------
  def requiredComponents(self, typeID):
    """"""
    typeID = int(typeID)
    if typeID in self.blueprints.blueprints and self.blueprints.blueprints[typeID].t1Priority[0] == 'manufacture':
      blueprint = self.blueprints.blueprints[typeID]
      manufSize = blueprint.manufSize
      totalMaterialCost = {}
      #logic that decides which bpc to use given the amount of things to produce
      sortedBPCs = sorted(blueprint.BPC.rawItems, key=lambda x: x.TE)
      
      for BPC in sortedBPCs:
        if manufSize - BPC.runs > 0:
          modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
          for matID in modMaterialCost:
            if matID in totalMaterialCost:
              totalMaterialCost[matID] += modMaterialCost[matID]
            else:
              totalMaterialCost[matID] = modMaterialCost[matID]
          manufSize = manufSize - BPC.runs
        elif manufSize - BPC.runs == 0:
          modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
          for matID in modMaterialCost:
            if matID in totalMaterialCost:
              totalMaterialCost[matID] += modMaterialCost[matID]
            else:
              totalMaterialCost[matID] = modMaterialCost[matID]
          break
        elif manufSize - BPC.runs < 0:
          modMaterialCost = self._materialsCalculator(manufSize, BPC)
          for matID in modMaterialCost:
            if matID in totalMaterialCost:
              totalMaterialCost[matID] += modMaterialCost[matID]
            else:
              totalMaterialCost[matID] = modMaterialCost[matID]
          break
        
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
            modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
            for matID in modMaterialCost:
              if matID in totalMaterialCost:
                totalMaterialCost[matID] += modMaterialCost[matID]
              else:
                totalMaterialCost[matID] = modMaterialCost[matID]
            manufSize = manufSize - BPC.runs
          elif manufSize - BPC.runs == 0:
            modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
            for matID in modMaterialCost:
              if matID in totalMaterialCost:
                totalMaterialCost[matID] += modMaterialCost[matID]
              else:
                totalMaterialCost[matID] = modMaterialCost[matID]
            break
          elif manufSize - BPC.runs < 0:
            modMaterialCost = self._materialsCalculator(manufSize, BPC)
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
  def requiredBaseMaterials(self):
    """"""
    pass




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
class datacoresReq:
  """determines the required datacores to run all remaining invention jobs"""

  #----------------------------------------------------------------------
  def __init__(self, blueprints):
    """Constructor"""
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
  def notInAssets(self, assets):
    """subtract owned datacores from the total required"""
    materialStore = assets.materials()
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
    
    
    
  
    
    
    
 # for i in returnDict:
 #   print "{}\t{}".format(StaticData.idName(i), returnDict[i])