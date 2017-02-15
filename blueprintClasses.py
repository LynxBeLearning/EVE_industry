from os.path import join, exists
from Auth import DataRequest
from staticClasses import StaticData,  Settings
from scipy.stats import binom as binomial
import math


########################################################################
class Blueprints:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, charID):
    """Constructor"""
    #getting required data
    bpItems = DataRequest.getBlueprints(charID)
    marketData = DataRequest.getMarketOrders(charID)
    charSkills = DataRequest.getSkills(charID)      
    
    #processing
    self.blueprints = {}
    bpoList = self._listOfBpos(bpItems)
    for bpo in bpoList:
      typeID = bpo.typeID
      self.blueprints[typeID] = BpContainer(bpo, bpItems, marketData, charSkills)
  
  #----------------------------------------------------------------------
  def _listOfBpos(self, blueprintItemParserObj):
    """"""
    bpos = []
    for key in blueprintItemParserObj.rawBlueprints:
      #check to see if i have unaccounted for bps in unknown containers
      if blueprintItemParserObj.rawBlueprints[key].locationID not in Settings.blueprintLocations and blueprintItemParserObj.rawBlueprints[key].locationID not in Settings.knownLocations:
        print "WARNING: NEW BLUEPRINT LOCATION DETECTED: BPO: {}, BPC: {}, LOCATIONID: {}, NAME: {}".format(blueprintItemParserObj.rawBlueprints[key].bpo,
                                                                                                            blueprintItemParserObj.rawBlueprints[key].bpc,
                                                                                                            blueprintItemParserObj.rawBlueprints[key].locationID,
                                                                                                            StaticData.idName(blueprintItemParserObj.rawBlueprints[key].typeID))
      if blueprintItemParserObj.rawBlueprints[key].bpo == 1 and blueprintItemParserObj.rawBlueprints[key].locationID in Settings.blueprintLocations:
        if blueprintItemParserObj.rawBlueprints[key].typeID in [x.typeID for x in bpos]:
          print 'WARNING: DUPLICATE DETECTED, {}'.format(StaticData.idName(blueprintItemParserObj.rawBlueprints[key].typeID))
          continue
        bpos.append(blueprintItemParserObj.rawBlueprints[key])
    return bpos

  #----------------------------------------------------------------------
  def printPriority(self):
    """"""
    sortedTypeIDs = [x[0] for x in sorted(self.blueprints.items(), key= lambda x: StaticData.idName(x[0]))] #sort the itemIDs by corresponding names
    
    print "T1 MANUFACTURING\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.t1MarketOK == 0 and bpContainer.t1Priority[0] == 'manufacture' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  bpContainer.t1Priority[1])
    
    print "\n\nT1 COPYING\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.t1MarketOK == 0 and bpContainer.t1Priority[0] == 'copy' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  int(bpContainer.t1Priority[1]))
        
    print "\n\nT1 COPYING (low priority)\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.t1MarketOK == 1 and bpContainer.t1Priority[0] == 'copy' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  int(bpContainer.t1Priority[1])) 
        
    print "\n\nT1 DONE\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.t1MarketOK == 1 and bpContainer.t1Priority[0] == 'ready' and bpContainer.BPO.component == 0:
        print "{}".format(StaticData.idName(typeID)) 
        
    
    print "\n\nT2 MANUFACTURING\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 0 and bpContainer.t2Priority[index][0] == 'manufacture' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))
            
            
    print "\n\nT2 INVENTING\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 0 and bpContainer.t2Priority[index][0] == 'invention' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))      
    
    print "\n\nT2 INVENTING (low priority)\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 1 and bpContainer.t2Priority[index][0] == 'invention' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))
            
           
    print "\n\nT2 DONE\n"
    for typeID in sortedTypeIDs:
      bpContainer = self.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 1 and bpContainer.t2Priority[index][0] == 'ready' and bpContainer.BPO.component == 0:
            print "{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]))
            
            
  #----------------------------------------------------------------------
  def printBPCRuns(self):
    """print a list of BP sorted by available runs"""
    sortedTypeIDs = [x[0] for x in sorted(self.blueprints.items(), key= lambda x: self.blueprints[x[0]].BPC.totalRuns/self.blueprints[x[0]].manufSize)] #sort the itemIDs by BPC runs
    for i in sortedTypeIDs:
      if self.blueprints[i].BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(i), self.blueprints[i].BPC.totalRuns/self.blueprints[i].manufSize)


  
########################################################################
class BpContainer:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, BpoItem, blueprintItems, marketData, charSkills):
    """Constructor"""
    #getting base parameters
    self.CopySize, self.manufSize, self.minMarketSize = StaticData.marketSize(BpoItem.typeID) #the copy time for bp is used as a measure of how difficult it is to manufacture and as a consequence how many should be on the market. i hope to implement real volume data to supplant this
    self.t1ProductionSize = StaticData.productAmount(BpoItem.typeID)
    
    #set variables for bpo, bpc and t2
    self.BPO = BPO(BpoItem, blueprintItems)
    self.BPC = BPC(self.BPO, blueprintItems)
    self.T2 = T2(self.BPO, blueprintItems)
    
    #calculating priority for this bp family, t1 item
    self.t1MarketOK = 0
    self.t1Priority = []
    remainingItems = marketData.remainingItems(self.BPO.typeID)
    if remainingItems >= self.minMarketSize:
      self.t1MarketOK = 1
      if self.BPC.totalRuns <= self.manufSize:
        copyNumber = math.ceil(((self.CopySize * 8) - self.BPC.totalRuns) / self.CopySize)
        self.t1Priority = ['copy', copyNumber]        
      elif self.BPC.totalRuns  >= self.manufSize:
        self.t1Priority = ['ready', 0]
    elif self.BPC.totalRuns  >= self.manufSize:
      self.t1Priority = ['manufacture', self.manufSize] 
    else:
      copyNumber = math.ceil(((self.CopySize * 8) - self.BPC.totalRuns) / self.CopySize)
      self.t1Priority = ['copy', copyNumber]
    
    
    #calculating priority for this bp family, t2 item if present
    if self.T2.inventable == 0:
      self.t2MarketOK = None
      self.t2Priority = None
    else:
      self.t2MarketOK = [0] * len(self.T2.inventedIDs)
      self.t2Priority = [""] * len(self.T2.inventedIDs)      
      for index in range(len(self.T2.inventedIDs)):
        remainingItems = marketData.remainingItems(self.T2.inventedIDs[index])
        if remainingItems > self.minMarketSize:
          self.t2MarketOK[index] = 1
          if self.T2.totalRuns[index]  >= self.manufSize:
            self.t2Priority[index] = ['ready', 0]
          else:
            runs = self._inventionCalculator( 5 - self.T2.totalBPCs[index], 
                                            StaticData.inventionProb(charSkills, StaticData.producerID(self.T2.inventedIDs[index])), 
                                            0.95)
            self.t2Priority[index] = ['invention', runs]
        elif self.T2.totalRuns[index]  >= self.manufSize:
          self.t2Priority[index] = ["manufacture", self.manufSize]
        elif self.BPC.totalRuns >= 25:
          runs = self._inventionCalculator( 5 - self.T2.totalBPCs[index], 
                                            StaticData.inventionProb(charSkills, StaticData.producerID(self.T2.inventedIDs[index])), 
                                            0.95)
          self.t2Priority[index] = ['invention', runs]          
        else: 
          copyNumber = math.ceil(((self.CopySize * 10) - self.BPC.totalRuns) / self.CopySize)
          self.t2Priority[index] = ['copy', copyNumber]
          
  #----------------------------------------------------------------------
  def _inventionCalculator(self, successNumber, successProbability, alpha):
    """calculate the number of invention runs necessary to have alpha probability of successNumber successes"""
    for i in range(50):
      prob = 1-binomial.cdf(successNumber, i, successProbability)
      if prob > alpha:
        return i
      

########################################################################
class BPO:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, BpoItem, blueprintItems):
    """Constructor"""
    self.name = BpoItem.name
    self.typeID = BpoItem.typeID
    self.bpoItem = BpoItem
    self.ME = BpoItem.ME
    self.TE = BpoItem.TE
    self.locationID = BpoItem.locationID
    self.rawItem = [BpoItem]
    if BpoItem.locationID == Settings.componentsBpoContainer:
      self.component = 1
    else:
      self.component = 0
    blueprintItems.removeItems(BpoItem.itemID)    
    
########################################################################
class BPC:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, bpo, blueprintItems):
    """Constructor"""
    parentID = bpo.typeID
    self.totalRuns = 0
    self.totalBPCs = 0
    self.rawItems = []
    
    itemIDs = blueprintItems.rawBlueprints.keys()
    

    for ItemID in itemIDs:
      if blueprintItems.rawBlueprints[ItemID].typeID == parentID and blueprintItems.rawBlueprints[ItemID].bpc == 1 and blueprintItems.rawBlueprints[ItemID].locationID in Settings.blueprintLocations:
        self.totalBPCs += 1
        self.totalRuns += blueprintItems.rawBlueprints[ItemID].runs
        self.rawItems.append(blueprintItems.rawBlueprints[ItemID])
        blueprintItems.removeItems(ItemID)
        

    
########################################################################
class T2:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, bpo, blueprintItems):
    """Constructor"""
    if bpo.typeID not in StaticData.T1toT2:
      self.inventable = 0
    elif bpo.typeID in StaticData.T1toT2:
      self.inventable = 1
      self.inventedIDs = StaticData.T1toT2[bpo.typeID]
      self.names = [StaticData.idName(x) for x in self.inventedIDs]
      self.totalBPCs = [0] * len(self.inventedIDs)
      self.totalRuns = [0] * len(self.inventedIDs)
      self.items = [[] for x in range(len(self.inventedIDs))]
      self.t2ProductionSize = [StaticData.productAmount(x) for x in self.inventedIDs]
      
      itemIDs = blueprintItems.rawBlueprints.keys()
      
      for inventedCounter, inventedID in enumerate(self.inventedIDs):
        for itemID in itemIDs:
          if blueprintItems.rawBlueprints[itemID].typeID == inventedID and blueprintItems.rawBlueprints[itemID].locationID in Settings.blueprintLocations:
            self.totalBPCs[inventedCounter] += 1
            self.totalRuns[inventedCounter] += blueprintItems.rawBlueprints[itemID].runs
            self.items[inventedCounter].append(blueprintItems.rawBlueprints[itemID])
            #blueprintItemParserObj.removeItems(itemID)
    
    
  
  
  


    
    
  







