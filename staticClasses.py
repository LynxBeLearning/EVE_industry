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
    
              
#necessary patch to updata static variables from internal methods
StaticData.T1toT2, StaticData.T2toT1 = StaticData._inventablesFetcher()
        
      
    
print "vorij"