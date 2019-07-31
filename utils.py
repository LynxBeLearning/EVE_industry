import os
import json
import math
import sqlite3
from pubsub import pub
from types import SimpleNamespace
from scipy.stats import binom as binomial

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
  #some fuckery is going on here.
  #is fetchone ever necessary?
  #if only one tuple is present, fetchall returns list of 1 tuple
  #fetchone returns just the tuple.
  #need testing
  response = database.execute(command)
  if fetchAll:
    rows = response.fetchall()
    if rows and len(rows[0]) == 1:
      return unpack(rows, flatten = True)
    else:
      return rows
  else:
    row = response.fetchone()
    if not row:
      return None
    elif len(row) == 1:
      return row[0]
    else:
      #return unpack(row, flatten = True)
      return row

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
  inventablesList = dbQuery(currentDb, command, fetchAll=True)
  uniqueInventables = list(set(inventablesList))

  #extract invented IDs from static db
  inventedList = []
  for inventable in uniqueInventables:
    command = (f'SELECT "productTypeID" '
               f'FROM "industryActivityProducts" '
               f'WHERE "typeID" = "{inventable}"'
               f'AND "activityID" = "8"')
    inventedTempList = dbQuery(staticDb, command, fetchAll=True)
    inventedList.extend(inventedTempList)

  return list(set(inventedList))

#----------------------------------------------------------------------
def idName(idOrName):
  """return id if name is provided and vice versa"""
  try:
    idOrName = int(idOrName)
    command = f'SELECT "typeName" FROM "invTypes" WHERE "typeID" = {idOrName}'
  except ValueError:
    command = f'SELECT "typeID" FROM "invTypes" WHERE "typeName" = "{idOrName}"'

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
def solarSystemName(solarSystemID):
  """"""
  command = (f'SELECT "solarSystemName" '
             f'FROM "mapSolarSystems" '
             f'WHERE "solarSystemID" = {solarSystemID}')

  systemName = dbQuery(staticDb, command)

  if systemName:
    return systemName
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
  """return the id of the product of typeID"""
  typeID = int(typeID)
  command = (f'SELECT "productTypeID" '
             f'FROM "industryActivityProducts" '
             f'WHERE "typeID" = {typeID}')
  prodID = dbQuery(staticDb, command)
  if prodID:
    return prodID
  else:
    return None

#----------------------------------------------------------------------
def size(typeID):
  """return list of 3 elements: copySize, manufSize and minMarketSize"""
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
def sizes(typeIDs):
  """applies market size to a list of typeIDs"""
  return [size(x) for x in typeIDs]

#----------------------------------------------------------------------
def _marketGroupExplorer(marketGroupID, typeID):
  """recursively walk the tree of market groups until it finds one in a known category"""
  frigsDessiesID = [1361, 1372]
  cruisersBCsID = [1367, 1374, 629]  #629 is transport ships
  modulesID = [9]
  componentsID = [800, 798, 796, 1097, 1191]
  ammoScriptsID = [2290, 100, 99, 1094, 114]
  battleshipsID = [1377, 1376]
  miningCrystalsID = [593]
  deployableID = [404]
  rigsID = [1111]
  droneID = [157]
  subsystems = [1112]


  if marketGroupID in frigsDessiesID:
    return [30, 10, 2]
  elif marketGroupID in battleshipsID:
    return [3, 1, 1]
  elif marketGroupID in ammoScriptsID:
    return [300, 50, 100]
  elif marketGroupID in miningCrystalsID:
    return [50, 50, 20]
  elif marketGroupID in cruisersBCsID:
    return [5, 3, 1]
  elif marketGroupID in subsystems:
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
  prodID = productID(typeID)
  command = (f'SELECT "remainingItems" '
             f'FROM "MarketOrders" '
             f'WHERE "typeID" = "{prodID}" '
             f'AND "sellOrder" = 1 ')

  remainingItems = dbQuery(currentDb, command, fetchAll=True)
  remainingItems = sum(remainingItems)

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
  totRuns = sum(runs)

  if totRuns:
    return totRuns
  else:
    return 0

#----------------------------------------------------------------------
def jobRuns(typeID, activity = 1, parent = False):
  """return the number of runs of typeID that are being produced"""


  if parent:
    parentTypeID = inventedFrom(typeID)
    command = (f'SELECT "runs" '
               f'FROM "IndustryJobs" '
               f'WHERE "bpTypeID" = {parentTypeID} '
               f'AND "activityID" = {activity} ')
  else:
    command = (f'SELECT "runs" '
                 f'FROM "IndustryJobs" '
                 f'WHERE "bpTypeID" = {typeID} '
                 f'AND "activityID" = {activity} ')
  runs = dbQuery(currentDb, command, fetchAll=True)
  totRuns = sum(runs)

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
def getMarketGroup(typeID):
  """get the marketgroup of the typeID"""
  command = (f'SELECT "marketGroupID" '
             f'FROM "invTypes" '
             f'WHERE "TypeID" = {typeID}')
  marketGroupID = dbQuery(staticDb, command)

  return marketGroupID

#----------------------------------------------------------------------
def rigBonus(typeID):
  """return true if the typeID is eligible for the material reduction due to citadel rigs"""
  componentsMarketGroup = 1035
  shipsMarketGroup = 4
  structureMarketGroup = 477

  riggedMarketGroups = [componentsMarketGroup,
                        shipsMarketGroup,
                        structureMarketGroup]

  prodID = productID(typeID)

  marketGroupID = getMarketGroup(prodID)
  parentGroups = _marketGroupPath(marketGroupID, [marketGroupID])

  if any([True for ID in parentGroups if ID in riggedMarketGroups]):
    return True
  else:
    return False

#----------------------------------------------------------------------
def component(typeID):
  """determine if blueprint is a component blueprint or not"""
  componentBlueprintMarketGroup = 800

  marketGroupID = getMarketGroup(typeID)

  if marketGroupID:
    marketGroupList = _marketGroupPath(marketGroupID, [marketGroupID])
  else:
    raise TypeError(f'{idName(typeID)} has no market group?')

  if componentBlueprintMarketGroup in marketGroupList:
    return True
  else:
    return False

#----------------------------------------------------------------------
def producerID(typeID):
  """return the id of the bp from which typeID is produced"""
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

#----------------------------------------------------------------------
def inventionProb(typeID, isParent = True):
  """calculate invention probability based on skill levels"""
  encryptionSkillsID = [21791,23087,21790,23121]
  if not isParent:
    typeID = producerID(typeID)

  baseProbCommand = (f'SELECT "probability" '
                     f'FROM "industryActivityProbabilities" '
                     f'WHERE "TypeID" = {typeID} '
                     f'AND "activityID" = 8')

  reqSkillsCommand = (f'SELECT "skillID" '
                      f'FROM "industryActivitySkills" '
                      f'WHERE "TypeID" = {typeID} '
                      f'AND "activityID" = 8')

  baseProb = dbQuery(staticDb, baseProbCommand)
  reqSkills = dbQuery(staticDb, reqSkillsCommand, fetchAll=True)

  encryptionSkill = ''
  scienceSkills = []

  #assuming flat 4 skill level now, might update in future.
  #infrastructure to query api for skill levels is already in place
  #database schema must be updated to accomodate skills storage
  #and a function must be made to query the db and recover the corresponding level
  for skill in reqSkills:
    if skill in encryptionSkillsID:
      encryptionSkill = float(4)
    else:
      scienceSkills.append(float(4))

  scienceSkill1 = scienceSkills[0]
  scienceSkill2 = scienceSkills[1]

  modifiedProb = round(baseProb * (1.0 + ( (scienceSkill1 + scienceSkill2 ) / 30 + (encryptionSkill / 40) ) ), 3)
  return modifiedProb


#----------------------------------------------------------------------
def nativeT2Runs(typeID):
  """return the amount of runs that an invented blueprint is born with"""
  command = (f'SELECT "quantity" '
             f'FROM "industryActivityProducts" '
             f'WHERE "productTypeID" = {typeID} '
             f'AND "activityID" = 8')
  runs = dbQuery(staticDb, command, fetchAll=False)
  return int(runs)


#----------------------------------------------------------------------
def reqInventionSuccesses(typeID):
  """return the amount of runs that an invented blueprint is born with"""
  manufSize = size(typeID)[1]
  totRuns = totalRuns(typeID)
  nativeBpRuns = nativeT2Runs(typeID)

  reqT2Blueprints = manufSize / nativeBpRuns
  ownedT2Blueprints = math.floor(totRuns / nativeBpRuns)

  reqInventionSuccesses = reqT2Blueprints - ownedT2Blueprints

  return(reqInventionSuccesses)

#----------------------------------------------------------------------
def inventionCalculator(typeID, alpha = 0.95):
  """calculate the number of invention runs necessary to have alpha probability of successNumber successes"""
  successNumber = reqInventionSuccesses(typeID)
  successProbability = inventionProb(typeID, isParent= False)

  for runs in range(200):
    prob = 1-binomial.cdf(successNumber, runs, successProbability)
    if prob > alpha:
      return runs


#----------------------------------------------------------------------
def getBlueprintsItems(typeID):
  """return all the blueprints items of the specified typeID"""
  command = (f'SELECT "ME", "runs" '
             f'FROM "Blueprints" '
             f'WHERE "typeID" = {typeID}')

  bpItems = dbQuery(currentDb, command, fetchAll=True)

  return bpItems

#----------------------------------------------------------------------
def printDict(dictionary):
  """print a readable version of the dictionaries containing the typeid:value structure"""

  for item in dictionary:
    print(f'{idName(item)}\t{dictionary[item]}')

#----------------------------------------------------------------------
def integrate(dictionary, key, value):
  """create a new entry if key is not in dictionary, otherwise adds value to the
  already existing entry dictionary[key]"""
  if key not in dictionary:
    dictionary[key] = value
  else:
    dictionary[key] += value

  return dictionary

#----------------------------------------------------------------------
def millify(n, sigDigits = 2):
  millnames = ['',' Thousand',' M',' B',' T']
  n = float(n)
  millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

  something = n / 10**(3 * millidx)
  somethat = millnames[millidx]
  return f'{something:.{sigDigits}f}{somethat}'

#----------------------------------------------------------------------
def dictSubtraction(minuhend, subtrahend):
  """subtract elements of two dictionaries from one another"""
  minuhendCopy = dict(minuhend)
  subtrahendCopy = dict(subtrahend)


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
def getOwnedMaterials():
  """return a dictionary containing owned materials"""
  command = (f'SELECT "typeID", "quantity" '
             f'FROM "aggregatedMaterials"')

  mats = dbQuery(currentDb, command, fetchAll=True)
  mats = dict(mats)
  return mats

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
  def productAmount(cls, typeID):
    """return the amount of items produced by one run"""
    quantity = ""
    dbQuantity = cls._database.execute('SELECT "quantity" FROM "industryActivityProducts" WHERE "TypeID" = ? and "activityID" = 1' , (str(typeID), )) #note that parameters of execute must be a tuple, even if only contains only one element
    dbQuantity = dbQuantity.fetchone()

    quantity = int(dbQuantity[0])

    return quantity


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
      elif key not in addend2:
        result[key] = addend1[key]

    for key in addend2Keys:
      result[key] = addend2[key]


    return result


#necessary patch to updata static variables from internal methods
StaticData.T1toT2, StaticData.T2toT1 = StaticData._inventablesFetcher()








