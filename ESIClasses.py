from staticClasses import StaticData, Settings
import datetime
import scipy


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

    
  