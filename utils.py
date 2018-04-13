import sqlite3
import os
import json
from types import SimpleNamespace
from pubsub import pub

activityID2Name = {8: "invention",
                   1: "manufacturing",
                   3: "time efficiency",
                   4: "mterial efficiency",
                   5: "copying",}

#SETTINGS

configFile = 'config.json'
with open(configFile, 'r') as config:
  configDict = json.load(config)

settings = SimpleNamespace()
settings.__dict__.update(configDict)


#TEMP, SHOULD TAKE THIS AWAY WITH REWORK OF DATA REQUEST CLASSES
settings.DataObjectStorage = []
#TEMP

#update of the login code
#----------------------------------------------------------------------
def updateCode(code):
  """listen for code broadcasts and set the variable when received."""
  settings.code = code

pub.subscribe(updateCode, "code")

#DATABASES
staticDb = sqlite3.connect(os.path.join(settings.dataFolder, settings.staticDBName))
currentDb = sqlite3.connect(os.path.join(settings.dataFolder, settings.charDBName))
logDb = sqlite3.connect(os.path.join(settings.dataFolder, settings.logDB))

# STATIC DATA AND UTILITY FUNCTIONS
#----------------------------------------------------------------------
def dbQuery(database, command, fetchAll = False):
  response = database.execute(command)
  if fetchAll:
    rows = response.fetchall()
    return rows
  else:
    row = response.fetchone()
    if not row:
      return None
    elif len(row) == 1:
      return row[0]
    else:
      return unpack(row, flatten = True)

#----------------------------------------------------------------------
def unpack(listOfTuples, flatten = False, element = 0):
  if flatten:
    return [item for tuples in listOfTuples for item in tuples]
  else:
    return [x[element] for x in listOfTuples]

#----------------------------------------------------------------------
def allInventables(onlyBPO = False):
  """return the list of all T2 and T3 typeIDs that can be invented from currently owned BPs"""
  if onlyBPO:
    command = ('SELECT "typeID" '
               'FROM "blueprints" '
               'WHERE "bpo" = 1 '
               'AND "inventable" = 1')
  else:
    command = ('SELECT "typeID" '
               'FROM "blueprints" '
               'where "inventable" = 1')

  #unpack and get unique values
  inventablesTupleList = dbQuery(currentDb, command, fetchAll=True)
  inventablesList = unpack(inventablesTupleList)
  uniqueInventables = list(set(inventablesList))

  #extract invented IDs from static db
  inventedList = []
  for inventable in uniqueInventables:
    command = (f'SELECT "productTypeID" '
               f'FROM "industryActivityProducts" '
               f'WHERE "typeID" = "{inventable}"'
               f'AND "activityID" = "8"')
    inventedTupleList = dbQuery(staticDb, command, fetchAll=True)
    inventedList.extend(unpack(inventedTupleList))

  return inventedList

#----------------------------------------------------------------------
def idName(idOrName):
  """return id if name is provided and vice versa"""
  try:
    idOrName = int(idOrName)
    command = f'SELECT "typeName" FROM "invTypes" WHERE "typeID" = {idOrName}'
  except ValueError:
    command = f'SELECT "typeID" FROM "invTypes" WHERE "typeName" = {idOrName}'

  return dbQuery(staticDb, command)

#----------------------------------------------------------------------
def idNames(idsOrNames: list):
  """given a list of names or typeIDs, return the result of idName for each"""
  return [idName(x) for x in idsOrNames]

#----------------------------------------------------------------------
def inventedFrom(typeID):
  """given a bp id, return the typeID of the blueprint from which it is invented, if at all"""
  command = (f'SELECT "typeID"'
             f'FROM "industryActivityProducts"'
             f'WHERE "activityID" = 8 '
             f'AND "productTypeID" = {typeID}')

  invented = dbQuery(staticDb, command)
  if invented:
    return invented
  else:
    return False

#----------------------------------------------------------------------
def inventedFroms(typeIDs : list):
  """given a list of typeIDs, return the result of inventedFrom for each"""
  return [inventedFrom(item) for item in typeIDs]

#----------------------------------------------------------------------
def stationName(stationID):
  """given a stationID, return the station's name"""
  command = (f'SELECT "stationName"'
             f'FROM "staStations"'
             f'WHERE "stationID" = {stationID}')

  stationName = dbQuery(staticDb, command)
  if stationName:
    return stationName
  else:
    return None

#----------------------------------------------------------------------
def inventable(typeID):
  """determine if a typeID can be invented or reverse engineered"""
  command = (f'SELECT "time"'
             f'FROM "industryActivity"'
             f'WHERE "activityID" = 8 '
             f'AND "typeID" = {typeID}')

  inventable = dbQuery(staticDb, command)
  if inventable:
    return True
  else:
    return False

#----------------------------------------------------------------------
def bpClass(typeID):
  """determine if the typeID is t1, t2 or t3"""
  t3Items = ['Legion', 'Tengu', 'Loki', 'Proteus',
             'Jackdaw', 'Hekate', 'Svipul', 'Confessor']

  if not inventedFrom(typeID):
    return 1
  else:
    if any(word in idName(typeID) for word in t3Items):
      return 3
    else:
      return 2

#----------------------------------------------------------------------
def productID(typeID):
  """return id if name is provided and vice versa"""
  typeID = int(typeID)
  command = (f'SELECT "productTypeID" '
             f'FROM "industryActivityProducts" '
             f'WHERE "typeID" = {typeID}')
  prodID = dbQuery(staticDb, command)
  if prodID:
    return prodID
  else:
    return None


def marketSize(typeID):
  """estimate quantity of things to put on the market on the basis of their market category"""
  prodID = productID(typeID)
  command = (f'SELECT "marketGroupID" '
             f'FROM "invTypes" '
             f'WHERE "TypeID" = "{prodID}" ')
  marketGroupID = dbQuery(staticDb, command)

  if marketGroupID:
    return _marketGroupExplorer(marketGroupID, prodID)
  else:
    raise("{} does not have copy time. maybe it's not a bpo".format(StaticData.idName(typeID)))

#----------------------------------------------------------------------
def marketSizes(typeIDs):
  """applies market size to a list of typeIDs"""
  return [marketSize(x) for x in typeIDs]

#----------------------------------------------------------------------
def _marketGroupExplorer(marketGroupID, typeID):
  """recursively walk the tree of market groups until it finds one in a known category"""
  frigsDessiesID = [1361, 1372]
  cruisersBCsID = [1367, 1374]
  modulesID = [9]
  componentsID = [800, 798, 796, 1097, 1191]
  ammoScriptsID = [2290, 100, 99, 1094, 114]
  miningCrystalsID = [593]
  deployableID = [404]
  rigsID = [1111]
  droneID = [157]

  if marketGroupID in frigsDessiesID:
    return [30, 10, 2]
  elif marketGroupID in ammoScriptsID:
    return [300, 50, 100]
  elif marketGroupID in miningCrystalsID:
    return [50, 50, 20]
  elif marketGroupID in cruisersBCsID:
    return [5, 3, 1]
  elif marketGroupID in modulesID:
    return [50, 50, 20]
  elif marketGroupID in componentsID:
    return [1, 1, 1]
  elif marketGroupID in deployableID:
    return [10, 10, 5]
  elif marketGroupID in rigsID:
    return [50, 20, 5]
  elif marketGroupID in droneID:
    return [300, 100, 20]
  elif marketGroupID is None:
    raise TypeError('I do not know the market group of this blueprint: {}'.format(idName(typeID)))
  else:
    command = (f'SELECT "parentGroupID" '
               f'FROM "invMarketGroups" '
               f'WHERE "marketGroupID" = {marketGroupID}' )
    marketGroupID = dbQuery(staticDb, command)

    return _marketGroupExplorer(marketGroupID,  typeID)

#----------------------------------------------------------------------
def onTheMarket(typeID):
  """return the total number of produced items being sold on the market"""
  command = (f'SELECT "remainingItems" '
             f'FROM "MarketOrders" '
             f'WHERE "typeID" = "{typeID}" '
             f'AND "sellOrder" = 1 ')

  remainingItems = dbQuery(currentDb, command, fetchAll=True)
  remainingItems = sum(unpack(remainingItems, flatten= True))

  return remainingItems

#----------------------------------------------------------------------
def onTheMarkets(typeIDs):
  """return result of onTheMarkets for a list of typeIDs"""
  return [onTheMarket(x) for x in typeIDs]

#----------------------------------------------------------------------
def totalRuns(typeID):
  """return the total number of runs for a given blueprint"""
  command = (f'SELECT "runs" '
             f'FROM "Blueprints" '
             f'WHERE "typeID" = "{typeID}" '
             f'AND "bpo" = "0"')
  runs = dbQuery(currentDb, command, fetchAll=True)
  totRuns = sum(unpack(runs, flatten=True))

  if totRuns:
    return totRuns
  else:
    return 0

#----------------------------------------------------------------------
def jobRuns(typeID, activity = 1):
  """return the number of runs of typeID that are being produced"""
  command = (f'SELECT "runs" '
             f'FROM "IndustryJobs" '
             f'WHERE "bptypeID" = "{typeID}" '
             f'AND "activityID" = "{activity}" ')
  runs = dbQuery(currentDb, command, fetchAll=True)
  totRuns = sum(unpack(runs, flatten=True))

  if totRuns:
    return totRuns
  else:
    return 0

#----------------------------------------------------------------------
def _marketGroupPath(marketGroupID, retList = []):
  """return a list of all parent market groups above the provided one"""

  tempList = []
  command =  (f'SELECT "parentGroupID" '
              f'FROM "invMarketGroups" '
              f'WHERE "marketGroupID" = {marketGroupID}')
  ParentmarketGroupID = dbQuery(staticDb, command)

  if ParentmarketGroupID:
    tempList.append(ParentmarketGroupID)
    tempList.extend(retList)
    return _marketGroupPath(ParentmarketGroupID,  tempList)
  else:
    return retList


#----------------------------------------------------------------------
def component(typeID):
  """determine if blueprint is a component blueprint or not"""
  componentBlueprintMarketGroup = 800

  command = (f'SELECT "marketGroupID" '
             f'FROM "invTypes" '
             f'WHERE "TypeID" = {typeID}')
  marketGroupID = dbQuery(staticDb, command)

  if marketGroupID:
    marketGroupList = _marketGroupPath(marketGroupID, [marketGroupID])
  else:
    raise TypeError(f'{StaticData.idName(typeID)} has no market group?')

  if componentBlueprintMarketGroup in marketGroupList:
    return True
  else:
    return False

#----------------------------------------------------------------------
def producerID(typeID):
  """return id if name is provided and vice versa"""
  typeID = int(typeID)
  command =  (f'SELECT "typeID" '
              f'FROM "industryActivityProducts" '
              f'WHERE "productTypeID" = {typeID}')
  producer = dbQuery(staticDb, command)
  if producer is not None:
    return str(producer)
  else:
    return None

#----------------------------------------------------------------------
def buildable(typeID):
  """determine if item is buildable from bpo or not"""
  producer = producerID(typeID)

  if producer:
    return True
  else:
    return False


########################################################################
class StaticData():
  """"""

  _database = sqlite3.connect(os.path.join(settings.dataFolder, settings.staticDBName))
  T1toT2, T2toT1 = {}, {}



  #----------------------------------------------------------------------
  @classmethod
  def _inventablesFetcher(cls):
    """create dictionaries of inventables"""
    T1toT2 = {}
    T2toT1 = {}

    T1T2 = cls._database.execute('SELECT "typeID","productTypeID" FROM "industryActivityProducts" where "activityID" = 8')
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
  def originatorBp(cls, typeID):
    """return the id of the bpo that is used to derive the blueprint (copy or invent)"""
    typeID = int(typeID)

    if typeID in cls.T2toT1:
      return cls.T2toT1[typeID][0]
    else:
      return None



  #----------------------------------------------------------------------
  @classmethod
  def baseManufacturingCost(cls, typeID):
    """calculate the manufacturing cost of an item"""
    typeID = int(typeID)
    returnDict = {}
    selected = cls._database.execute('SELECT "materialTypeID", "quantity" FROM "industryActivityMaterials" WHERE "TypeID" = ? and "activityID" = 1' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
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
    baseProb = cls._database.execute('SELECT "probability" FROM "industryActivityProbabilities" WHERE "TypeID" = ? and "activityID" = 8' , (bpID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    reqSkills = cls._database.execute('SELECT "skillID" FROM "industryActivitySkills" WHERE "TypeID" = ? and "activityID" = 8' , (bpID, )) #note that parameters of execute must be a tuple, even if only contains only one element

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
    itemGroup = cls._database.execute('SELECT "groupID" FROM "invTypes" WHERE "TypeID" = ?' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    itemGroup = itemGroup.fetchone()[0]
    itemCategory = cls._database.execute('SELECT "categoryID" FROM "invGroups" WHERE "groupID" = ?' , (itemGroup, )) #note that parameters of execute must be a tuple, even if only contains only one element
    itemCategory = int(itemCategory.fetchone()[0])
    return itemCategory

  #----------------------------------------------------------------------
  @classmethod
  def datacoreRequirements(cls, typeID):
    """return the number of datacores required to invent a particular bpc"""
    returnDict = {}
    datacoresQuantities = cls._database.execute('SELECT "materialTypeID","quantity" FROM "industryActivityMaterials" WHERE "TypeID" = ? and "activityID" = 8' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    datacoresQuantities = datacoresQuantities.fetchall()

    for tup in datacoresQuantities:
      returnDict[tup[0]] = tup[1]

    return returnDict

  #----------------------------------------------------------------------
  @classmethod
  def printDict(cls, dictionary):
    """print a readable version of the dictionaries containing the typeid:value structure"""

    for item in dictionary:
      print(f'{StaticData.idName(item)}\t{dictionary[item]}')


  #----------------------------------------------------------------------
  @classmethod
  def productAmount(cls, typeID):
    """return the amount of items produced by one run"""
    quantity = ""
    dbQuantity = cls._database.execute('SELECT "quantity" FROM "industryActivityProducts" WHERE "TypeID" = ? and "activityID" = 1' , (str(typeID), )) #note that parameters of execute must be a tuple, even if only contains only one element
    dbQuantity = dbQuantity.fetchone()

    quantity = int(dbQuantity[0])

    return quantity

  #----------------------------------------------------------------------
  @classmethod
  def t2BlueprintAmount(cls, typeID):
    """return the amount of runs that an invented blueprint is born with"""
    quantity = ""
    dbQuantity = cls._database.execute('SELECT "quantity" FROM "industryActivityProducts" WHERE "TypeID" = ? and "activityID" = 8' , (str(typeID), )) #note that parameters of execute must be a tuple, even if only contains only one element
    dbQuantity = dbQuantity.fetchone()

    quantity = int(dbQuantity[0])

    return quantity

  #----------------------------------------------------------------------
  @classmethod
  def materialSubtraction(cls, minuhend, subtrahend):
    """subtract elements of two dictionaries from one another"""
    minuhendCopy = dict(minuhend)
    subtrahendCopy = dict(subtrahend)
    result = {}
    remainder = {}

    for key in subtrahend:
      if key in minuhendCopy:
        sub = int(minuhendCopy[key]) - int(subtrahendCopy[key])
        if sub == 0:
          del minuhendCopy[key]
          del subtrahendCopy[key]
        elif sub > 0:
          minuhendCopy[key] = sub
          del subtrahendCopy[key]
        elif sub < 0:
          del minuhendCopy[key]
          subtrahendCopy[key] = sub * -1

    return (minuhendCopy, subtrahendCopy)

  #----------------------------------------------------------------------
  @classmethod
  def materialAddition(cls, addend1, addend2):
    """subtract elements of two dictionaries from one another"""
    result = {}
    addend2Keys = addend2.keys()

    for key in addend1:
      if key in addend2:
        addition = int(addend1[key]) + int(addend2[key])
        addend2Keys.remove(key)
        result[key] = addition
      if key not in addend2:
        result[key] = addend1[key]

    for key in addend2Keys:
      result[key] = addend2[key]


    return result




#necessary patch to updata static variables from internal methods
StaticData.T1toT2, StaticData.T2toT1 = StaticData._inventablesFetcher()








