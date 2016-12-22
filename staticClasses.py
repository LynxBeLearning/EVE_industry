import sqlite3

db = 'static_ascension.sqlite'

########################################################################
class StaticData:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, databasePath):
    """Constructor"""
    
    self.database = sqlite3.connect(databasePath)
    self.T1toT2, self.T2toT1 = self.__inventablesFetcher()
    
  #----------------------------------------------------------------------
  def idName(self, idOrName):
    """return id if name is provided and vice versa"""
    try:
      idOrName = int(idOrName)
      selected = self.database.execute('SELECT "typeName" FROM "invTypes" WHERE "typeID" = ?', (idOrName, )) #note that parameters of execute must be a tuple, even if only contains only one element
      nameTuple = selected.fetchone()
      return str(nameTuple[0]) #[0] is required because fetchone returns a tuple      
    except ValueError:
      selected = self.database.execute('SELECT "typeID" FROM "invTypes" WHERE "typeName" = ?', (idOrName, ))
      nameTuple = selected.fetchone()
      return str(nameTuple[0]) 
   
  #----------------------------------------------------------------------
  def __inventablesFetcher(self):
    """create dictionaries of inventable  """
    T1toT2 = {} 
    T2toT1 = {}
    
    T1T2 = self.database.execute('SELECT "typeID","productTypeID" FROM "industryActivityProducts" where "activityID" = 8')
    for row in T1T2:
      if row[0] in T1toT2:
        T1toT2[row[0]].append(row[1])
      else:
        T1toT2[row[0]] = [row[1]]
        
      if row[1] in T2toT1:
        T2toT1[row[1]].append(row[0])
      else:
        T2toT1[row[1]] = [row[0]]      

    return (T1toT2, T2toT1)
    

    
              
    
    