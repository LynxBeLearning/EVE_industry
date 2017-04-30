from os.path import join, exists
from Auth import DataRequest
from staticClasses import StaticData,  Settings
from scipy.stats import binom as binomial
import math
import time


########################################################################
class Blueprints:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, charID = Settings.charIDList):
    """Constructor"""
    #getting required data
    if isinstance(charID, list):
      for idx, ID in enumerate(charID):
        if idx: #do not execute on the first iteration
          bpItems.rawBlueprints.update(DataRequest.getBlueprints(ID).rawBlueprints)
        else:
          bpItems = DataRequest.getBlueprints(ID)
    else:
      bpItems = DataRequest.getBlueprints(charID)
    
    marketData = DataRequest.getMarketOrders(1004487144)
    charSkills = DataRequest.getSkills(1004487144)
    indyJobs = IndustryJobs()
    
    #processing
    self.blueprints = {}
    bpoList = self._listOfBpos(bpItems)
    for bpo in bpoList:
      typeID = bpo.typeID
      self.blueprints[typeID] = BpContainer(bpo, bpItems, marketData, charSkills, indyJobs)
  
  #----------------------------------------------------------------------
  def _listOfBpos(self, blueprintItems):
    """"""
    bpos = []
    for key in blueprintItems.rawBlueprints:
      #check to see if i have unaccounted for bps in unknown containers
      if blueprintItems.rawBlueprints[key].locationID not in Settings.blueprintLocations and blueprintItems.rawBlueprints[key].locationID not in Settings.knownLocations and Settings.debug:
        print "WARNING: NEW BLUEPRINT LOCATION DETECTED: ME: {} TE {} BPO: {}, BPC: {}, LOCATIONID: {}, NAME: {}".format(blueprintItems.rawBlueprints[key].ME,
                                                                                                                         blueprintItems.rawBlueprints[key].TE,
                                                                                                                         blueprintItems.rawBlueprints[key].bpo,
                                                                                                                         blueprintItems.rawBlueprints[key].bpc,
                                                                                                                         blueprintItems.rawBlueprints[key].locationID,
                                                                                                                         StaticData.idName(blueprintItems.rawBlueprints[key].typeID))
      if blueprintItems.rawBlueprints[key].bpo == 1 and blueprintItems.rawBlueprints[key].locationID in Settings.blueprintLocations:
        if blueprintItems.rawBlueprints[key].typeID in [x.typeID for x in bpos]:
          print 'WARNING: DUPLICATE DETECTED, {}'.format(StaticData.idName(blueprintItems.rawBlueprints[key].typeID))
          continue
        bpos.append(blueprintItems.rawBlueprints[key])
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
  def __init__(self, BpoItem, blueprintItems, marketData, charSkills, industryJobs):
    """Constructor"""
    #getting base parameters
    self.CopySize, self.manufSize, self.minMarketSize = StaticData.marketSize(BpoItem.typeID) #these sizes are established based on the type of BP, ammo, frigate, module, etc.
    self.t1ProductionSize = StaticData.productAmount(BpoItem.typeID) #how much of it gets produced every run
    
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
            runs = self._inventionCalculator( self.manufSize / self.T2.inventionSize - math.floor(self.T2.totalRuns[index] / self.T2.inventionSize), 
                                            StaticData.inventionProb(charSkills, StaticData.producerID(self.T2.inventedIDs[index])), 
                                            0.95)
            self.t2Priority[index] = ['invention', runs]
        elif self.T2.totalRuns[index]  >= self.manufSize:
          self.t2Priority[index] = ["manufacture", self.manufSize]
        elif self.BPC.totalRuns >= 30:
          runs = self._inventionCalculator( self.manufSize / self.T2.inventionSize - math.floor(self.T2.totalRuns[index] / self.T2.inventionSize), 
                                            StaticData.inventionProb(charSkills, StaticData.producerID(self.T2.inventedIDs[index])), 
                                            0.95)
          self.t2Priority[index] = ['invention', runs]          
        else: 
          copyNumber = math.ceil(((self.CopySize * 10) - self.BPC.totalRuns) / self.CopySize)
          self.t2Priority[index] = ['copy', copyNumber]
          
  #----------------------------------------------------------------------
  def _inventionCalculator(self, successNumber, successProbability, alpha):
    """calculate the number of invention runs necessary to have alpha probability of successNumber successes"""
    for i in range(200):
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
      self.inventionSize = StaticData.t2BlueprintAmount(bpo.typeID)
      
      itemIDs = blueprintItems.rawBlueprints.keys()
      
      for inventedCounter, inventedID in enumerate(self.inventedIDs):
        for itemID in itemIDs:
          if blueprintItems.rawBlueprints[itemID].typeID == inventedID and blueprintItems.rawBlueprints[itemID].locationID in Settings.blueprintLocations:
            self.totalBPCs[inventedCounter] += 1
            self.totalRuns[inventedCounter] += blueprintItems.rawBlueprints[itemID].runs
            self.items[inventedCounter].append(blueprintItems.rawBlueprints[itemID])
    
#INDUSTRY CLASSES
########################################################################
class IndustryJobs:
  """parse raw industry jobs api output into data structures"""

  #----------------------------------------------------------------------
  def __init__(self, charID=Settings.charIDList):
    """Constructor"""
    #getting required data
    apiRows = {}
    if isinstance(charID, list):
      for ID in charID:
        indyJobs = DataRequest.getIndustryJobs(ID)
        apiRows[ID] = indyJobs._rows        
    else:
      indyJobs = DataRequest.getIndustryJobs(charID)
      apiRows[charID] = indyJobs._rows     
    
    
    self.typeIDJobs = {}
    self.activityJobs = {}
    for activity in ["manufacturing", 'inventing', 'researching', 'copying', 'reverse engineering']:
      self.activityJobs[activity] = {}
      
    for ID in charID:
      for apiRow in apiRows[ID]:
        if apiRow[7] == 1:
          activity = "manufacturing"
        elif apiRow[7] == 8:
          activity = 'inventing'
        elif apiRow[7] == 3 or apiRow[7] == 4:
          activity = 'researching'
        elif apiRow[7] == 5:
          activity = 'copying'
        elif apiRow[7] == 7:
          activity = 'reverse engineering'
        bpID = apiRow[9]
        
        if bpID not in self.activityJobs[activity]:
          self.activityJobs[activity][bpID] = [IndustryJobItem(apiRow)]
        else:
          self.activityJobs[activity][bpID].append(IndustryJobItem(apiRow))
          
        #filling typeIDJobs
        if bpID not in self.typeIDJobs:
          self.typeIDJobs[bpID] = [IndustryJobItem(apiRow)]
        else:
          self.typeIDJobs[bpID].append(IndustryJobItem(apiRow))
    
########################################################################
class IndustryJobItem:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, apiRow):
    """Constructor"""
    self.installerID = apiRow[1]
    self.installerName = apiRow[2]
    if apiRow[7] == 1:
      self.activity = "manufacturing"
    elif apiRow[7] == 8:
      self.activity = 'inventing'
    elif apiRow[7] == 3 or apiRow[7] == 4:
      self.activity = 'researching'
    elif apiRow[7] == 5:
      self.activity = 'copying'
    elif apiRow[7] == 7:
      self.activity = 'reverse engineering'
    else:
      raise TypeError("wtf are you doing with this blueprint? {}".format(StaticData.idName(self.bpID)))
    self.bpID = apiRow[9]
    self.bpLocation = apiRow[11]
    self.runs = apiRow[13]
    self.productID = apiRow[18]
    self.timeRemaining = (apiRow[24] - time.time()) / 3600



    
    
  







