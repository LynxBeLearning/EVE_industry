import sqlite3
import pubsub


########################################################################
class StaticData():
  """"""

  __database = sqlite3.connect('static_ascension.sqlite')  
  T1toT2, T2toT1 = {}, {}

  #----------------------------------------------------------------------
  @classmethod
  def _inventablesFetcher(cls):
    """create dictionaries of inventables"""
    T1toT2 = {} 
    T2toT1 = {}

    T1T2 = cls.__database.execute('SELECT "typeID","productTypeID" FROM "industryActivityProducts" where "activityID" = 8')
    for row in T1T2:
      if row[0] in T1toT2:
        T1toT2[row[0]].append(row[1])
      else:
        T1toT2[row[0]] = [row[1]]

      if row[1] in T2toT1:
        T2toT1[row[1]].append(row[0])
      else:
        T2toT1[row[1]] = [row[0]]      

    return (T1toT2, T2toT1) #dictionary values are LISTS of INTEGERS

  #----------------------------------------------------------------------
  @classmethod
  def idName(cls, idOrName):
    """return id if name is provided and vice versa"""
    try:
      idOrName = int(idOrName)
      selected = cls.__database.execute('SELECT "typeName" FROM "invTypes" WHERE "typeID" = ?', (idOrName, )) #note that parameters of execute must be a tuple, even if only contains only one element
      nameTuple = selected.fetchone()
      return str(nameTuple[0]) #[0] is required because fetchone returns a tuple      
    except ValueError:
      selected = cls.__database.execute('SELECT "typeID" FROM "invTypes" WHERE "typeName" = ?', (idOrName, ))
      nameTuple = selected.fetchone()
      return str(nameTuple[0]) 



  #----------------------------------------------------------------------
  @classmethod
  def originatorBp(cls, rawBlueprint):
    """return the id of the bpo that is used to derive the blueprint (copy or invent)"""

    if rawBlueprint.bpo == 1:
      return rawBlueprint.typeID
    elif rawBlueprint.typeID in cls.T2toT1:
      return T2toT1[rawBlueprint.typeID]
    else:
      return rawBlueprint.typeID

  @classmethod
  def productID(cls, ID):
    """return id if name is provided and vice versa"""
    ID = int(ID)
    selected = cls.__database.execute('SELECT "productTypeID" FROM "industryActivityProducts" WHERE "typeID" = ?', (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    productTuple = selected.fetchone()
    if productTuple is not None:
      return int(productTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      return None

  @classmethod
  def producerID(cls, ID):
    """return id if name is provided and vice versa"""
    ID = int(ID)
    selected = cls.__database.execute('SELECT "typeID" FROM "industryActivityProducts" WHERE "productTypeID" = ?', (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    producerTuple = selected.fetchone()
    if producerTuple is not None:
      return str(producerTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      return None 

  @classmethod
  def marketSize(cls, typeID):
    """estimate quantity of things to put on the market on the basis of how long the bpo takes to copy. trust me, it works. maybe."""
    typeID = int(typeID)
    selected = cls.__database.execute('SELECT "time" FROM "industryActivity" WHERE "TypeID" = ? and "activityID" = 5' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    copyTimeTuple = selected.fetchone()
    if copyTimeTuple[0]:
      copyTime = copyTimeTuple[0] #[0] is required because fetchone returns a tuple
      if copyTime <= 240:
        return [300, 100, 20] #returns 3 things in this order: bpc copy runs, quantity to manufacture when below threshold, minimum market threshold before manufacturing again.
      elif copyTime <= 720:
        return [100, 50, 20]
      elif copyTime <= 1440:
        return [50, 50, 10]
      elif copyTime <= 4800:
        return [10, 5, 2]
      elif copyTime > 4800:
        return [5, 1, 0]

    else:
      raise("{} does not have copy time. maybe it's not a bpo".format(StaticData.idName(typeID)))

  #----------------------------------------------------------------------
  @classmethod
  def baseManufacturingCost(cls, typeID):
    """calculate the manufacturing cost of an item"""
    typeID = int(typeID)
    returnDict = {}
    selected = cls.__database.execute('SELECT "materialTypeID", "quantity" FROM "industryActivityMaterials" WHERE "TypeID" = ? and "activityID" = 1' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    resultsList = selected.fetchall()

    if len(resultsList) > 0:
      for resultTuple in resultsList:
        #print "{} {}".format(cls.idName(tup[0]), tup[1]) #print material name and cost
        returnDict[resultTuple[0]] = resultTuple[1]
        
    else:
      return None

    return returnDict

  #----------------------------------------------------------------------
  @classmethod
  def inventionProb(cls, charSkills, bpID): 
    """calculate invention probability based on skill levels"""
    encryptionSkillsID = [21791,23087,21790,23121]
    baseProb = cls.__database.execute('SELECT "probability" FROM "industryActivityProbabilities" WHERE "TypeID" = ? and "activityID" = 8' , (bpID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    reqSkills = cls.__database.execute('SELECT "skillID" FROM "industryActivitySkills" WHERE "TypeID" = ? and "activityID" = 8' , (bpID, )) #note that parameters of execute must be a tuple, even if only contains only one element
  
    baseProb = float(baseProb.fetchone()[0])
    reqSkills = reqSkills.fetchall()
  
    encryptionSkill = ''
    scienceSkills = []

    if len(reqSkills) > 0:
      for resultTuple in reqSkills:
        if resultTuple[0] in encryptionSkillsID:
          encryptionSkill = float(charSkills.skillLevel(resultTuple[0]))
        else:
          scienceSkills.append(float(charSkills.skillLevel(resultTuple[0])))

    modifiedProb = round(baseProb * (1.0 + ( (scienceSkills[0] + scienceSkills[1] ) / 30 + (encryptionSkill / 40) ) ), 3)
    return modifiedProb
  
  #----------------------------------------------------------------------
  @classmethod
  def categoryID(cls, typeID):
    """return the category to which an item belongs"""
    itemGroup = cls.__database.execute('SELECT "groupID" FROM "invTypes" WHERE "TypeID" = ?' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    itemGroup = itemGroup.fetchone()[0]
    itemCategory = cls.__database.execute('SELECT "categoryID" FROM "invGroups" WHERE "groupID" = ?' , (itemGroup, )) #note that parameters of execute must be a tuple, even if only contains only one element
    itemCategory = int(itemCategory.fetchone()[0])
    return itemCategory






#necessary patch to updata static variables from internal methods
StaticData.T1toT2, StaticData.T2toT1 = StaticData._inventablesFetcher()



########################################################################
class Settings: # NEED TO IMPLEMENT MULTI CHARACTER PARSING AND STORING OF SETTINGS
  """read and hold settings variables"""

  blueprintLocations = {
    1022771210683 : "zansha mining, bpc container", #zansha mining, bpc container
    1022832888095 : "zansha neuro, researched bpo container", #zansha neuro, researched bpo container
    1022946515289 : "dunk's workshop, component bpos",  #zansha mining, components bpos container
    1022756068998 : "zansha neuro, hangar",  #zansha neuro, hangar
    1022946509438: "dunk's workshop, T2 bpc container",
    1022946637486: "dunk's workshop, t1 bpc container",
    1022975749725: "zansha neuro, BPO container",
    1022946512073: 'zansha mining, t2 bpc container',
    1022980573793: 'la fistiniere, bpc container'

  }

  materialsLocations = {
    1022771185137: "invention, zansha mining",
    1022946657877: 'dunks raw mats',
    1022840070781: 'dunks components',
  }

  knownLocations = {
    1019684069461: "amarr, manufacturing container",
    60006142 : "yehnifi station hangar",
    1022975868749L: "DO6 fortizar, low priority blueprint container",
    1022975750208L: "zansha neuro, unreaserched BPOs",
    1022946551363L: "fortizar misc container",
    1019684069479L: "amarr misc container",
  }  



  settingsDict = {}
  settingsFile = open("config.ini")
  for line in settingsFile:
    tempList = line.strip().split(" = ")
    settingsDict[tempList[0]] = tempList[1]
  settingsFile.close()

  #code listener
  _listener = pubsub.subscribe("code")

  #variables
  crestUrl = settingsDict['CRESTURL']
  esiUrl = settingsDict['ESIURL']
  esiEndpointsUrl = settingsDict['ESIENDPOINTS']
  userAgent = settingsDict['USERAGENT']
  port = settingsDict['PORT']
  clientID = settingsDict['CLIENTID']
  secret = settingsDict['SECRET']
  authUrl = settingsDict['AUTHTOKEN']
  keyID = settingsDict['KEYID']
  vCode = settingsDict['VCODE']    
  code = ''
  esiEndpoints = ''
  accessToken = ''

  expires = ''
  if "REFRESHTOKEN" in settingsDict:
    refreshToken = settingsDict['REFRESHTOKEN']
  else:
    refreshToken = ''


  marketStationID = 61000990 # DO6 STATION, 60008494 is for amarr station
  componentsBpoContainer = 1022946515289 #all bpos in here will be flagged as components and require no copying or inventing.
  joltanID = 1004487144

  #----------------------------------------------------------------------
  @classmethod
  def updateCode(cls):
    """listen for code broadcasts and set the variable."""
    cls.code = cls._listener.listen().next()['data']





