from staticClasses import StaticData


class Materials:
  """Parse json ESI output for character assets"""

  #----------------------------------------------------------------------
  def __init__(self, jsonList):
    """Constructor"""
    self.materials = {}
    for idx in range(len(jsonList)):
      item = jsonList[idx]
      itemLocationID = item["location_id"]
      itemTypeID = item['type_id']
      
      #this loop prints asset name and location, useful when you need to know which containers to allow.
      #if item["location_id"] not in Settings.materialsLocations:
        #print "{}\t{}".format(StaticData.idName(item["type_id"]), item['location_id'])
        
      if itemLocationID in Settings.materialsLocations:
        if itemTypeID not in self.materials:
          self.materials[itemTypeID] =  item['quantity']
        else:
          self.materials[itemTypeID] += item['quantity']