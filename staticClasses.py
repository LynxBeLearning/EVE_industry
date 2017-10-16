import sqlite3
import os
import json
from types import SimpleNamespace
from pubsub import pub

configFile = 'config.json'
with open(configFile, 'r') as config:
  configDict = json.load(config)

settings = SimpleNamespace()
settings.__dict__.update(configDict)

#TEMP, SHOULD TAKE THIS AWAY WITH REWORK OF DATA REQUEST CLASSES
settings.DataObjectStorage = []
#TEMP

#update of the login code
def updateCode(code):
  """listen for code broadcasts and set the variable when received."""
  settings.code = code

pub.subscribe(updateCode, "code")


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
  def idName(cls, idOrName):
    """return id if name is provided and vice versa"""
    try:
      idOrName = int(idOrName)
      selected = cls._database.execute('SELECT "typeName" FROM "invTypes" WHERE "typeID" = ?', (idOrName, )) #note that parameters of execute must be a tuple, even if only contains only one element
      nameTuple = selected.fetchone()
      return str(nameTuple[0]) #[0] is required because fetchone returns a tuple
    except ValueError:
      selected = cls._database.execute('SELECT "typeID" FROM "invTypes" WHERE "typeName" = ?', (idOrName, ))
      nameTuple = selected.fetchone()
      return str(nameTuple[0])



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
  def productID(cls, ID):
    """return id if name is provided and vice versa"""
    ID = int(ID)
    selected = cls._database.execute('SELECT "productTypeID" FROM "industryActivityProducts" WHERE "typeID" = ?', (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    productTuple = selected.fetchone()
    if productTuple is not None:
      return int(productTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      return None

  #----------------------------------------------------------------------
  @classmethod
  def producerID(cls, ID):
    """return id if name is provided and vice versa"""
    ID = int(ID)
    selected = cls._database.execute('SELECT "typeID" FROM "industryActivityProducts" WHERE "productTypeID" = ?', (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    producerTuple = selected.fetchone()
    if producerTuple is not None:
      return str(producerTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      return None
  #----------------------------------------------------------------------
  @classmethod
  def marketSize(cls, typeID):
    """estimate quantity of things to put on the market on the basis of their market category"""
    typeID = cls.productID(int(typeID)) #need product typeID
    selected = cls._database.execute('SELECT "marketGroupID" FROM "invTypes" WHERE "TypeID" = ? ' , (typeID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    marketGroupID = selected.fetchone()

    if marketGroupID[0]:
      return cls.__marketGroupExplorer(marketGroupID[0], typeID)
    else:
      raise("{} does not have copy time. maybe it's not a bpo".format(StaticData.idName(typeID)))

  #----------------------------------------------------------------------
  @classmethod
  def __marketGroupExplorer(cls, marketGroupID, typeID):
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
      raise TypeError('I do not know the market group of this blueprint: {}'.format(cls.idName(typeID)))
    else:
      selected = cls._database.execute('SELECT "parentGroupID" FROM "invMarketGroups" WHERE "marketGroupID" = ?' , (marketGroupID, )) #note that parameters of execute must be a tuple, even if only contains only one element
      parentGroupTuple = selected.fetchone()
      marketGroupID = parentGroupTuple[0]

      return cls.__marketGroupExplorer(marketGroupID,  typeID)

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








