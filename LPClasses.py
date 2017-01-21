from staticClasses import StaticData,  Settings
import math
import Auth

########################################################################
class ModifiedManufacturingCost:
  """calculate manufacturing cost considering ME and other modifiers to material efficiency"""

  #----------------------------------------------------------------------
  def __init__(self, blueprintObject):
    """Constructor"""
    self.BPC = blueprint
    self.riggedCategories = [7] #categories for which a rig is present on the raitaru, provides 4.2% cost reduction
    self.manufSize = blueprint.manufSize
    
        

    
  #----------------------------------------------------------------------
  def _materialModifier(self, BPC):
    """calculate the overall material modifier for a set of bpcs"""
    #calculate ME modifier
    TEModifier = 1 - (BPC.TE / 100.0)
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
    
    for matID in baseMats:
      modmat = max(runs, math.ceil( round(baseMats[matID] * runs * materialModifier, 2) + 0.01 ))
      modMats[matID] = modmat
    
    return modMats
  
  #----------------------------------------------------------------------
  def requiredComponents(self, ):
    """"""
    totalMaterialCost = {}
    #logic that decides which bpc to use given the amount of things to produce
    sortedBPCs = sorted(self.blueprint.BPC.rawItems, key=lambda x: x.TE)
    
    for BPC in sortedBPCs:
      if self.manufSize - BPC.runs > 0:
        modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
        for matID in modMaterialCost:
          if matID in totalMaterialCost:
            totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            totalMaterialCost[matID] = modMaterialCost[matID]
        self.manufSize = self.manufSize - BPC.runs
      elif self.manufSize - BPC.runs == 0:
        modMaterialCost = self._materialsCalculator(BPC.runs, BPC)
        for matID in modMaterialCost:
          if matID in totalMaterialCost:
            totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            totalMaterialCost[matID] = modMaterialCost[matID]
        break
      elif self.manufSize - BPC.runs < 0:
        modMaterialCost = self._materialsCalculator(BPC.runs - self.manufSize, BPC)
        for matID in modMaterialCost:
          if matID in totalMaterialCost:
            totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            totalMaterialCost[matID] = modMaterialCost[matID]
        break
      
      return totalMaterialCost
    
  
  
  #----------------------------------------------------------------------
  def requiredBaseMaterials(self):
    """"""
    pass




########################################################################
class TotalMaterialCost:
  """calculate total material cost for a group of items"""

  #----------------------------------------------------------------------
  def __init__(self, marketHistory, ESI):
    """Constructor"""
    
    self.marketHistory = marketHistory
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
  
  
    
    
    
    
 # for i in returnDict:
 #   print "{}\t{}".format(StaticData.idName(i), returnDict[i])