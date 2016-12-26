from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading
import urlparse
import base64
import os
import webbrowser
import json
import csv
import requests
import grequests
import time
import pubsub
import locale
import eveapi
from eveapi import MyCacheHandler
import tempfile
import cPickle
import math
import zlib
import re
import datetime
from os.path import join, exists
from Auth import Settings,  AuthOperations
from staticClasses import StaticData



########################################################################
class BlueprintItem:
  """"""
  #----------------------------------------------------------------------
  def __init__(self, apiRow):
    """Constructor"""
    self.itemID = apiRow[0] #unique id of the item, changes if item changes location
    self.locationID = apiRow[1] #id of the place where the item is, containers count as different locations and have ids that depend on the station or citadel
    self.typeID = apiRow[2] #id of the item type
    self.name = apiRow[3] #actual name of the item
    self.flag = apiRow[4] #
    if apiRow[5] == -1: #not really a quantity, -1 for bpo, -2 for bpc
      self.bpo = 1
      self.bpc = 0
    elif apiRow[5] == -2:
      self.bpo = 0
      self.bpc = 1
    else:
      self.bpo = 0
      self.bpc = 0
    self.TE = apiRow[6]
    self.ME = apiRow[7]
    self.runs = apiRow[8] #-1 for infinite
    
########################################################################
class BlueprintItemParser:
  """parse raw api blueprint output into data structures."""

  #----------------------------------------------------------------------
  def __init__(self, blueprintApiObj):
    """Constructor"""
    self.rawBlueprints = {}
    for row in blueprintApiObj.blueprints._rows:
      itemID = row[0]
      self.rawBlueprints[itemID] = BlueprintItem(row)
      
  #----------------------------------------------------------------------
  def removeItems(self, keys):
    """remove items from the dictionary as they are incorporated in the BlueprintOriginal class"""
    try:
      for key in keys:
        del self.rawBlueprints[key]
    except TypeError:    
      del self.rawBlueprints[keys]
  
########################################################################
class BpContainer:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, blueprintItemObj, blueprintItemParserObj, marketData):
    """Constructor"""
    self.CopySize, self.manufSize, self.minMarketSize = StaticData.marketSize(blueprintItemObj.typeID) #the copy time for bp is used as a measure of how difficult it is to manufacture and as a consequence how many should be on the market. i hope to implement real volume data to supplant this
    #set variables for bpo, bpc and t2
    self.BPO = BPO(blueprintItemObj, blueprintItemParserObj)
    self.BPC = BPC(self.BPO, blueprintItemParserObj)
    self.T2 = T2(self.BPO, blueprintItemParserObj)
    
    #calculating priority for this bp family, t1 item
    self.t1MarketOK = 0
    self.t1Priority = []
    remainingItems = marketData.remainingItems(self.BPO.typeID)
    if remainingItems >= self.minMarketSize:
      self.t1MarketOK = 1
      if self.BPC.totalRuns >= self.manufSize:
        self.t1Priority = ['ready', 0]
    elif self.BPC.totalRuns >= self.manufSize:
      self.t1Priority = ['manufacture', self.manufSize]
    else:
      copyNumber = math.ceil(((self.CopySize * 4) - self.BPC.totalRuns) / self.CopySize)
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
        if remainingItems >= self.minMarketSize:
          self.t2MarketOK[index] = 1
          if self.T2.totalRuns[index] >= self.manufSize:
            self.t2Priority[index] = ['ready', 0]
          else:
            #TODO: calculate how many things i should invent based on how many t2 bpc i have and how many are needed to get to 5 or more, use fixed probability of 45% for success
            self.t2Priority[index] = ['invention', 15]
        elif self.T2.totalRuns[index] >= self.manufSize:
          self.t2Priority[index] = ["manufacture", self.manufSize]
        elif self.BPC.totalRuns >= 15:
          self.t2Priority[index] = ['invention', 15]
        else: 
          copyNumber = math.ceil(((self.CopySize * 4) - self.BPC.totalRuns) / self.CopySize)
          self.t2Priority[index] = ['copy', copyNumber]

########################################################################
class BPO:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, blueprintItemObj, blueprintItemParserObj):
    """Constructor"""
    self.name = blueprintItemObj.name
    self.typeID = blueprintItemObj.typeID
    self.bpoItem = blueprintItemObj
    self.ME = blueprintItemObj.ME
    self.TE = blueprintItemObj.TE
    self.locationID = blueprintItemObj.locationID
    self.rawItem = [blueprintItemObj]
    if blueprintItemObj.locationID == 1022946515289:
      self.component = 1
    else:
      self.component = 0
    blueprintItemParserObj.removeItems(blueprintItemObj.itemID)    
    
########################################################################
class BPC:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, bpo, blueprintItemParserObj):
    """Constructor"""
    parentID = bpo.typeID
    self.totalRuns = 0
    self.totalBPCs = 0
    self.rawItems = []
    
    itemIDs = blueprintItemParserObj.rawBlueprints.keys()
    

    for ItemID in itemIDs:
      if blueprintItemParserObj.rawBlueprints[ItemID].typeID == parentID and blueprintItemParserObj.rawBlueprints[ItemID].bpc == 1:
        self.totalBPCs += 1
        self.totalRuns += blueprintItemParserObj.rawBlueprints[ItemID].runs
        self.rawItems.append(blueprintItemParserObj.rawBlueprints[ItemID])
        blueprintItemParserObj.removeItems(ItemID)
        

    
########################################################################
class T2:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, bpo, blueprintItemParserObj):
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
      
      itemIDs = blueprintItemParserObj.rawBlueprints.keys()
      
      for inventedCounter, inventedID in enumerate(self.inventedIDs):
        for itemID in itemIDs:
          if blueprintItemParserObj.rawBlueprints[itemID].typeID == inventedID:
            self.totalBPCs[inventedCounter] += 1
            self.totalRuns[inventedCounter] += blueprintItemParserObj.rawBlueprints[itemID].runs
            self.items[inventedCounter].append(blueprintItemParserObj.rawBlueprints[itemID])
            blueprintItemParserObj.removeItems(itemID)
    
    
  
  
  

########################################################################
class Blueprints:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, blueprintItemParserObj, marketData):
    """Constructor"""
    self.blueprints = {}
    bpoList = self._listOfBpos(blueprintItemParserObj)
    for bpo in bpoList:
      typeID = bpo.typeID
      self.blueprints[typeID] = BpContainer(bpo, blueprintItemParserObj, marketData)
  
  #----------------------------------------------------------------------
  def _listOfBpos(self, blueprintItemParserObj):
    """"""
    bpos = []
    for key in blueprintItemParserObj.rawBlueprints:
      #check to see if i have unaccounted for bps in unknown containers
      if blueprintItemParserObj.rawBlueprints[key].locationID not in settings.allowedLocations and blueprintItemParserObj.rawBlueprints[key].locationID not in settings.knownLocations:
        print "WARNING: NEW BLUEPRINT LOCATION DETECTED: BPO: {}, BPC: {}, LOCATIONID: {}, NAME: {}".format(blueprintItemParserObj.rawBlueprints[key].bpc,
                                                                                                            blueprintItemParserObj.rawBlueprints[key].bpo,
                                                                                                            blueprintItemParserObj.rawBlueprints[key].locationID,
                                                                                                            StaticData.idName(blueprintItemParserObj.rawBlueprints[key].typeID))
      if blueprintItemParserObj.rawBlueprints[key].bpo == 1 and blueprintItemParserObj.rawBlueprints[key].locationID in settings.allowedLocations:
        bpos.append(blueprintItemParserObj.rawBlueprints[key])
    return bpos

  #----------------------------------------------------------------------
  def calculatePriority(self):
    """"""
    #
    print "T1 PRIORITY FOR MANUFACTURING\n"
    print "priorities (not on market)\n"
    print "BP_NAME\tUNITS"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.t1MarketOK == 0 and bpContainer.t1Priority[0] == 'manufacture' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  bpContainer.t1Priority[1])
    
    print "\n\nT1 PRIORITY FOR COPYING\n"
    print "BP_NAME\tUNITS"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.t1MarketOK == 0 and bpContainer.t1Priority[0] == 'copy' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  int(bpContainer.t1Priority[1]))
        
    print "\n\nT1 LOW PRIORITY FOR COPYING\n"
    print "BP_NAME\tUNITS"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.t1MarketOK == 1 and bpContainer.t1Priority[0] == 'copy' and bpContainer.BPO.component == 0:
        print "{}\t{}".format(StaticData.idName(typeID),  int(bpContainer.t1Priority[1]))   
    
    print "\n\nT2 PRIORITY FOR MANUFACTURING\n"
    print "BP_NAME\tUNITS"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 0 and bpContainer.t2Priority[index][0] == 'manufacture' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))
            
            
    print "\n\nT2 PRIORITY FOR INVENTING\n"
    print "BP_NAME\tUNITS"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 0 and bpContainer.t2Priority[index][0] == 'invention' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))      
    
    print "\n LOW PRIORITY (on market already)"
    for typeID in bp.blueprints:
      bpContainer = bp.blueprints[typeID]
      if bpContainer.T2.inventable == 1:
        for index in range(len(bpContainer.T2.inventedIDs)):
          if bpContainer.t2MarketOK[index] == 1 and bpContainer.t2Priority[index][0] == 'invention' and bpContainer.BPO.component == 0:
            print "{}\t{}".format(StaticData.idName(bpContainer.T2.inventedIDs[index]),  int(bpContainer.t2Priority[index][1]))     

########################################################################
class MarketOrders:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, apiObj):
    """Constructor"""
    self.marketOrders = joltanXml.MarketOrders().orders
    
    
  #----------------------------------------------------------------------
  def remainingItems(self, blueprintTypeID): #blueprint or object typeID? need converter of bp to object
    """"""

    blueprintTypeID = int(blueprintTypeID)
    returnValue = 0
    
    for row in self.marketOrders._rows:
      stationID = row[2]
      typeID = row[7]
      bid = row[13]
      remainingItems = row[4]
      if stationID == settings.marketStationID and typeID == StaticData.productID(blueprintTypeID) and bid == 0:
        returnValue = remainingItems
        break

    return returnValue
    
      
      
    
    
  

settings = Settings()
cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=settings.keyID, vCode=settings.vCode).character(1004487144)
bps = joltanXml.Blueprints()
BlueprintItemParserO = BlueprintItemParser(bps)
marketData = MarketOrders(joltanXml)
bp = Blueprints(BlueprintItemParserO, marketData)
bp.calculatePriority()



    
    
  


print "aa"



