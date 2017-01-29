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
    return self.skills[skillID]
    
    

    
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
    
    
  
    
  