from staticClasses import StaticData, Settings


class Assets:
  """Parse json ESI output for character assets"""

  #----------------------------------------------------------------------
  def __init__(self, jsonList):
    """Constructor"""
    self.materials = {}
    for idx in range(len(jsonList)):
      item = jsonList[idx]
      itemLocationID = item["location_id"]
      itemTypeID = item['type_id']
      
      #this conditional prints asset name and location that are not in the known locations, useful when you need to know which containers to allow.
      #if item["location_id"] not in Settings.materialsLocations:
        #print "{}\t{}".format(StaticData.idName(item["type_id"]), item['location_id'])
        
      if itemLocationID in Settings.materialsLocations:
        if itemTypeID not in self.materials:
          self.materials[itemTypeID] =  item['quantity']
        else:
          self.materials[itemTypeID] += item['quantity']
        
          
          
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
    
    

    
    
    
  