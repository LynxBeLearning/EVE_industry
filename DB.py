from staticClasses import StaticData, Settings
import API
import sqlite3
import datetime
import scipy
import time
import os
import re

########################################################################
class DBUpdate:
  """Push data returned from the API to the playerDB"""
  _database = sqlite3.connect(os.path.join(Settings.dataFolder, Settings.charDBName))
  
  #----------------------------------------------------------------------
  @classmethod
  def _updateBlueprints(cls):
    """get blueprint data from the API and """
    for charID in Settings.charIDList:
      insertList =  []
      xmlBlueprints = API.DataRequest.getBlueprints(charID)
      
        
      for apiRow in xmlBlueprints.blueprints._rows:
        itemID = apiRow[0] #unique id of the item, should not change if item changes location
        locationID = apiRow[1] #id of the place where the item is, containers count as different locations and have ids that depend on the station or citadel
        typeID = apiRow[2] #id of the item type
        name = apiRow[3] #actual name of the item
        flag = apiRow[4] #
        if apiRow[5] == -1: #not really a quantity, -1 for bpo, -2 for bpc
          bpClass = 0
        elif apiRow[5] == -2:
          if typeID in StaticData.T2toT1:
            bpClass = 2
          else:
            bpClass =  1
        TE = apiRow[6]
        ME = apiRow[7]
        if apiRow[8] < 0: #-1 for infinite in the api, 0 for infinet in the db
          runs = 0
        else:
          runs = apiRow[8]

        insertList.append((itemID, charID, Settings.charConfig[charID]["NAME"] , locationID, typeID, StaticData.idName(typeID), bpClass, ME, TE, runs, StaticData.productID(typeID), StaticData.idName(StaticData.productID(typeID))))
          
      cls._database.executemany('INSERT INTO Blueprints VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', insertList)
      cls._database.commit()
      
  #----------------------------------------------------------------------
  @classmethod
  def _DBWipe(cls):
    """wipe the database of all entries"""
    tableNames = [x[0] for x in _database.execute("SELECT name FROM sqlite_master WHERE type='table';")] #_database.execute returns a list of tuples with only one element, hence the list comprehension
    cls._database.executemany("DELETE FROM ?", tableNames)
    cls._database.commit()
    
  #----------------------------------------------------------------------
  @classmethod
  def _DBDump(cls):
    """dump the database in a txt file for future restoration if needed"""
    #dumping current db
    with open('dump{}.sql'.format(time.time()), 'w') as f:
      for line in cls._database.iterdump():
        f.write('{}\n'.format(line))
    
    #deleting too old dumps
    oldDumps = [x for x in os.listdir(Settings.dbfolder) if x.startswith('dump')]
    if len(oldDumps > 3):
      oldDumps.sort()
      os.remove(os.path.join(Settings.dbfolder, oldDumps[0]))
      
  #----------------------------------------------------------------------
  def _DBRestore(self):
    """read a dump file and restore old databases"""
    pass
    

class Assets:
  """Parse json ESI output for character assets"""

  #----------------------------------------------------------------------
  def __init__(self, jsonList):
    """Constructor"""
    self.assets = []
    for idx in range(len(jsonList)):
      self.assets.append(jsonList[idx])
      
    #this conditional prints asset name and location that are not in the known locations, useful when you need to know which containers to allow.
    #for item in self.assets:
    #  if item["location_id"] not in Settings.materialsLocations:
    #    print "{}\t{}".format(StaticData.idName(item["type_id"]), item['location_id'])    
    
  #----------------------------------------------------------------------
  def materials(self):
    """"""
    
    mats = {}
    for item in self.assets:
      itemLocationID = item["location_id"]
      itemTypeID = item['type_id']
      
      #this conditional prints asset name and location that are not in the known locations, useful when you need to know which containers to allow.
      #if item["location_id"] not in Settings.materialsLocations:
        #print "{}\t{}".format(StaticData.idName(item["type_id"]), item['location_id'])
        
      if itemLocationID in Settings.materialsLocations:
        if itemTypeID not in mats:
          mats[itemTypeID] =  item['quantity']
        else:
          mats[itemTypeID] += item['quantity']
          
    return mats
          
          
########################################################################
class Skills:
  """store information on character skills"""

  #----------------------------------------------------------------------
  def __init__(self, jsonDict):
    """Constructor"""
    self.totalSP = jsonDict['total_sp']
    self.skills = {}
    for skill in jsonDict['skills']:
      self.skills[skill['skill_id']] = skill['current_skill_level']
      
  #----------------------------------------------------------------------
  def skillLevel(self, skillID):
    """return the level of the supplied skill"""
    default = 4
    if skillID in self.skills:
      return self.skills[skillID]
    else:
      print "WARNING: ESI seems to be having problems? skill\"{}\" was not found. returning default (4)".format(StaticData.idName(skillID))
      return default
    
    

    
########################################################################
class MarketHistory:
  """store market order history information"""

  #----------------------------------------------------------------------
  def __init__(self, jsonList):
    """Constructor"""
    self.history = jsonList
    
  #----------------------------------------------------------------------
  def medianVolume(self, daysBack):
    """calculate """
    volumeList = []
    for dayItems in self.history:
      year, month, day = [int(x) for x in dayItems['date'].split("-")]
      dayDate = datetime.date(year, month, day)
      delta = datetime.date.today() - dayDate
      if delta.days <= daysBack:
        volumeList.append(dayItems['volume'])
        
    return scipy.median(volumeList)    
    
    
########################################################################
class MarketOrders:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, marketOrders):
    """Constructor"""
    self.marketOrders = marketOrders
    
    
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
      orderState = row[6]
      if stationID == Settings.marketStationID and typeID == StaticData.productID(blueprintTypeID) and bid == 0 and orderState == 0:
        returnValue = remainingItems
        break

    return returnValue
  
  
  #----------------------------------------------------------------------
  def ordersList(self): 
    """"""  
    for row in self.marketOrders._rows:
      stationID = row[2]
      typeID = row[7]
      bid = row[13] 
      volEntered=row[3]
      remainingItems = row[4]
    
      if stationID == Settings.marketStationID and bid == 0 and remainingItems != 0:
        print "{}\t{}/{}".format(StaticData.idName(typeID), remainingItems, volEntered)


    

########################################################################
class IndustryJobs:
  """stores structured data about industry jobs and who is performing them"""

  #----------------------------------------------------------------------
  def __init__(self, industryJobsXml):
    """Constructor"""
    
    
    
    
  
  
  
  
    
    
  
    
    
  

    
  