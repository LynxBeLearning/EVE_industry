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
import zlib
import re
import datetime
from os.path import join, exists
from Auth import Settings,  AuthOperations
from staticClasses import StaticData

locations = {
  1022771210683 : "zansha mining, bpc container", #zansha mining, bpc container
  1022832888095 : "zansha neuro, researched bpo container", #zansha neuro, researched bpo container
  1022771182111 : "zansha mining, component bpos",  #zansha mining, components bpos container
  1022756068998 : "zansha neuro, hangar",  #zansha neuro, hangar
}

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
  def __init__(self, blueprintItemObj, blueprintItemParserObj):
    """Constructor"""
    #set variables for the bpo
    self.BPO = BPO(blueprintItemObj, blueprintItemParserObj)
    #set variables for the bpcs
    self.BPC = BPC(self.BPO, blueprintItemParserObj)
    #set variables for the t2
    self.T2 = T2(self.BPO, blueprintItemParserObj)
    

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
  def __init__(self, blueprintItemParserObj):
    """Constructor"""
    self.blueprints = {}
    bpoList = self.listOfBpos(blueprintItemParserObj)
    for bpo in bpoList:
      typeID = bpo.typeID
      self.blueprints[typeID] = BpContainer(bpo, blueprintItemParserObj)
  
  #----------------------------------------------------------------------
  def listOfBpos(self, blueprintItemParserObj):
    """"""
    bpos = []
    for key in blueprintItemParserObj.rawBlueprints:
      if blueprintItemParserObj.rawBlueprints[key].bpo == 1 and blueprintItemParserObj.rawBlueprints[key].locationID in locations:
        bpos.append(blueprintItemParserObj.rawBlueprints[key])
    return bpos

  #----------------------------------------------------------------------
  def calculatePriority(self):
    """"""
    



settings = Settings()
cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=settings.keyID, vCode=settings.vCode).character(1004487144)
bps = joltanXml.Blueprints()
BlueprintItemParserO = BlueprintItemParser(bps)
bp = Blueprints(BlueprintItemParserO)


print "aa"


