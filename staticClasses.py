import sqlite3


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
    if productTuple[0]:
      return int(productTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      raise("{} does is not a blueprint".format(StaticData.idName(ID)))
  
  @classmethod
  def producerID(cls, ID):
    """return id if name is provided and vice versa"""
    ID = int(ID)
    selected = cls.__database.execute('SELECT "typeID" FROM "industryActivityProducts" WHERE "productTypeID" = ?', (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
    producerTuple = selected.fetchone()
    if producerTuple[0]:
      return str(producerTuple[0]) #[0] is required because fetchone returns a tuple
    else:
      raise("{} is not produced by anything".format(StaticData.idName(ID)))  

  @classmethod
  def marketSize(cls, ID):
    """estimate quantity of things to put on the market on the basis of how long the bpo is to copy. trust me, it works. maybe."""
    ID = int(ID)
    selected = cls.__database.execute('SELECT "time" FROM "industryActivity" WHERE "TypeID" = ? and "activityID" = 5' , (ID, )) #note that parameters of execute must be a tuple, even if only contains only one element
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
      raise("{} does not have copy time. maybe it's not a bpo".format(StaticData.idName(ID)))  

#necessary patch to updata static variables from internal methods
StaticData.T1toT2, StaticData.T2toT1 = StaticData._inventablesFetcher()
        
      
    
print "vorij"