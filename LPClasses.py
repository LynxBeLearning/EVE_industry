from staticClasses import StaticData,  Settings
import math

########################################################################
class ModifiedManufacturingCost:
  """calculate manufacturing cost considering ME and other modifiers to material efficiency"""

  #----------------------------------------------------------------------
  def __init__(self, blueprint):
    """Constructor"""
    self.riggedCategories = [7] #categories for which a rig is present on the raitaru, provides 4.2% cost reduction
    self.manufSize = blueprint.manufSize
    self.totalMaterialCost = {}
        
    #logic that decides which bpc to use given the amount of things to produce
    sortedBPCs = sorted(blueprint.BPC.rawItems, key=lambda x: x.TE)
    
    for BPC in sortedBPCs:
      if self.manufSize - BPC.runs > 0:
        modMaterialCost = self.materialsCalculator(BPC.runs, BPC)
        for matID in modMaterialCost:
          if matID in self.totalMaterialCost:
            self.totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            self.totalMaterialCost[matID] = modMaterialCost[matID]
        self.manufSize = self.manufSize - BPC.runs
      elif self.manufSize - BPC.runs == 0:
        modMaterialCost = self.materialsCalculator(BPC.runs, BPC)
        for matID in modMaterialCost:
          if matID in self.totalMaterialCost:
            self.totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            self.totalMaterialCost[matID] = modMaterialCost[matID]
        break
      elif self.manufSize - BPC.runs < 0:
        modMaterialCost = self.materialsCalculator(BPC.runs - self.manufSize, BPC)
        for matID in modMaterialCost:
          if matID in self.totalMaterialCost:
            self.totalMaterialCost[matID] += modMaterialCost[matID]
          else:
            self.totalMaterialCost[matID] = modMaterialCost[matID]
        break
   
    
  #----------------------------------------------------------------------
  def materialModifier(self, BPC):
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
  def materialsCalculator(self, runs, BPC):
    """determine modified manufacturing cost for one blueprint witn N runs"""
    baseCost = StaticData.baseManufacturingCost(BPC.typeID)
    modMats = {}
    materialModifier = self.materialModifier(BPC)
    
    for matID in baseMats:
      modmat = max(runs, math.ceil( round(baseMats[matID] * runs * materialModifier, 2) + 0.01 ))
      modMats[matID] = modmat
    
    return modMats
  
########################################################################
class BaseModifiedManufacturingCost:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, modifiedManufacturingCostObject):
    """Constructor"""
    a = 1
    
    
  