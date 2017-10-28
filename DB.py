from staticClasses import StaticData, settings
import sqlite3
import datetime
import scipy
import time
import os
import re
from API import DataRequest
import swagger_client

########################################################################
class DBUpdate:
  """Push data returned from the API to the playerDB"""
  #db connection
  database = sqlite3.connect(os.path.join(settings.dataFolder, settings.charDBName))

  #----------------------------------------------------------------------
  @classmethod
  def updateAssets(cls):
    """
    take data in the form of:
      {
        "is_singleton": false,
        "item_id": 1000000016835,
        "location_flag": "Hangar",
        "location_id": 60002959,
        "location_type": "station",
        "type_id": 3516
      }

    from the assets api and push the appropriate components to the database
    """
    assets = DataRequest.getAssets()
    valuesList = []

    for item in assets:
      itemName = StaticData.idName(item.type_id)

      #check if bp ###normally this is done through singleton checks, but singletons don't work
      if 'blueprint' in itemName.lower():
        continue

      dbRow = (item.item_id,
               item.type_id,
               item.is_singleton,
               item.location_id,
               item.location_flag,
               item.location_type,
               item.quantity,
               itemName)
      valuesList.append(dbRow)

    cls._DBWipe(['Assets'])
    cls.database.executemany('INSERT INTO Assets VALUES (?,?,?,?,?,?,?,?)', valuesList)
    cls.database.commit()


  #----------------------------------------------------------------------
  @classmethod
  def updateBlueprints(cls):
    """get blueprint data in the form of
       {
       'item_id': 1001131739044,
       'location_flag': 'CorpSAG2',
       'location_id': 1025695702796,
       'material_efficiency': 10,
       'quantity': -1,
       'runs': -1,
       'time_efficiency': 20,
       'type_id': 1153
       }
       and push it to the blueprints table
    """
    blueprints = DataRequest.getBlueprints()
    valuesList = []

    for blueprint in blueprints:
      #recover plain name
      itemName = StaticData.idName(blueprint.type_id)

      #determina if bpo, t1 copy or t2 copy ### or t3 copy
      if blueprint.quantity == -1:
        bpo = 1
      else:
        bpo = 0
      bpClass = StaticData.bpClass(blueprint.type_id)


      #determine product id and name
      productID = StaticData.productID(blueprint.type_id)
      if productID:
        productName = StaticData.idName(productID)
      else:
        productID = 'NULL'
        productName = 'NULL'


      #determine if inventable or invented
      inventable = int(StaticData.inventable(blueprint.type_id))  #needs to be integer not bool
      inventedFromID = StaticData.invented(blueprint.type_id)
      if not inventedFromID:
        inventedFromID = 'NULL'
        inventedFromName = 'NULL'
      else:
        inventedFromName = StaticData.idName(inventedFromID)

      #determine if component
      if bpClass == 1:
        component = int(StaticData.component(blueprint.type_id))

      #set ignore flag
      dbRow = (blueprint.item_id,
               blueprint.type_id,
               itemName,
               blueprint.location_id,
               blueprint.location_flag,
               bpo,
               bpClass,
               blueprint.material_efficiency,
               blueprint.time_efficiency,
               blueprint.runs,
               productID,
               productName,
               component,
               inventable,
               inventedFromID,
               inventedFromName  )
      valuesList.append(dbRow)


      #itemID, typeID, typeName, class, ME, TE, runs, prodID, prodName, inventable, component,
      #inventedFrom, inventedFromName

    cls.database.executemany('INSERT INTO Blueprints VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', valuesList)
    cls.database.commit()

  #----------------------------------------------------------------------
  @classmethod
  def updateMaterials(cls):
    """"""
    assets = cls.database.execute( (f'SELECT "typeID", "quantity" '
                                    f'FROM "Assets" ') )
    assetRows = assets.fetchall()

    materialsDict = {}
    for row in assetRows:
      typeID = row[0]
      quantity = row[1]
      if typeID in materialsDict:
        materialsDict[typeID] += quantity
      else:
        materialsDict[typeID] = quantity

    valuesList = []
    for typeID in materialsDict:
      buildable = int(StaticData.buildable(typeID))
      typeName = StaticData.idName(typeID)
      dbRow = (typeID,
               typeName,
               materialsDict[typeID],
               buildable)
      valuesList.append(dbRow)

    cls.database.executemany( ('INSERT INTO AggregatedMaterials '
                               'VALUES (?,?,?,?)')
                              , valuesList)
    cls.database.commit()

  #----------------------------------------------------------------------
  @classmethod
  def updateIndustryJobs(cls):
    """"""
    indyJobs = DataRequest.getIndustryJobs()

    #jobid, itemid, bpid, bptypeName, runs, prodtypeID, prodTypeName endDate, status

    valuesList = []
    for job in indyJobs:
      jobID = job.job_id
      bpID = job.blueprint_id
      bpTypeID = job.blueprint_type_id
      bpTypeName = StaticData.idName(bpTypeID)
      runs = job.runs
      endDate = job.end_date
      status = job.status
      productTypeID = job.product_type_id
      productTypeName = StaticData.idName(productTypeID)
      installerID = job.installer_id
      installerName = DataRequest.getName(installerID)[0].character_name
      activityID = job.activity_id
      activityName = StaticData.activityID2Name[activityID]

      dbRow = (jobID,  #
               bpID,  #
               bpTypeID,  #
               bpTypeName,  #
               runs,  #
               productTypeID,  #
               productTypeName,  #
               endDate,  #
               status,  #
               installerID,  #
               installerName,  #
               activityID,  #
               activityName)  #
      valuesList.append(dbRow)

    cls.database.executemany( ('INSERT INTO IndustryJobs '
                               'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)')
                              , valuesList)
    cls.database.commit()

  #----------------------------------------------------------------------
  @classmethod
  def updateMarketOrders(cls):
    """"""
    marketOrders = DataRequest.getMarketOrders()

    valuesList = []
    for marketOrder in marketOrders:
      if marketOrder.state == 'completed':
        continue
      orderID = marketOrder.order_id
      stationID = marketOrder.location_id
      remainingItems = marketOrder.volume_remain
      typeID = marketOrder.type_id
      typeName = StaticData.idName(typeID)
      sellOrder = int(not marketOrder.is_buy_order)
      stationName = StaticData.stationName(stationID)

      dbRow = (orderID,
               typeID,
               typeName,
               remainingItems,
               sellOrder,
               stationID,
               stationName)
      valuesList.append(dbRow)
    cls.database.executemany( ('INSERT INTO MarketOrders '
                                   'VALUES (?,?,?,?,?,?,?)')
                                  , valuesList)
    cls.database.commit()

  #----------------------------------------------------------------------
  @classmethod
  def _DBWipe(cls,  tableNames = []):
    """wipe the database of all entries"""
    if not tableNames:
      tableRequest = cls.database.execute("SELECT name FROM sqlite_master WHERE type='table';")
      tableNames = [x[0] for x in tableRequest]

    for table in tableNames:
      cls.database.execute(f'DELETE FROM {table}')

    cls.database.commit()

  #----------------------------------------------------------------------
  @classmethod
  def _DBDump(cls):
    """dump the database in a txt file for future restoration if needed"""
    #dumping current db
    with open('dump{}.sql'.format(time.time()), 'w') as f:
      for line in cls.database.iterdump():
        f.write('{}\n'.format(line))

    #deleting too old dumps
    oldDumps = [x for x in os.listdir(settings.dbfolder) if x.startswith('dump')]
    if len(oldDumps > 3):
      oldDumps.sort()
      os.remove(os.path.join(settings.dbfolder, oldDumps[0]))

  #----------------------------------------------------------------------
  def _DBRestore(self):
    """read a dump file and restore old databases"""
    pass

  #----------------------------------------------------------------------
  @classmethod
  def updateAll(cls):
    """"""
    cls._DBWipe()
    cls.updateAssets()
    cls.updateBlueprints()
    cls.updateMaterials()
    cls.updateIndustryJobs()
    cls.updateMarketOrders()


########################################################################
class LogDBUpdate:
  """"""
  #db connection
  logDatabase = sqlite3.connect(os.path.join(settings.dataFolder, settings.logDB))
  currentDatabase = sqlite3.connect(os.path.join(settings.dataFolder, settings.charDBName))
  #----------------------------------------------------------------------
  @classmethod
  def updateMaterialLog(cls):
    """"""
    #getting newly updated info
    materials = cls.currentDatabase.execute( (f'SELECT "typeID", "quantity" '
                                              f'FROM "AggregatedMaterials" ') )
    materialsRows = materials.fetchall()

    #getting current mats
    currentMatsDict = {}
    for material in materialsRows:
      typeID = material[0]
      currentQuantity = material[1]
      currentMatsDict[typeID] = currentQuantity

    #checking for new materials
    valuesList = []
    for typeID,currentQuantity in currentMatsDict.items():
      #checking previous log entry for this material
      lastLogEntry = cls._getLastLogEntry(typeID)

      if lastLogEntry:
        oldBalance = lastLogEntry[1]
        if oldBalance == currentMatsDict[typeID]:
          continue
        else:
          matEntryID = 'NULL'
          delta = currentQuantity - oldBalance
          timestamp = time.time()
          balance = currentQuantity
          typeName = StaticData.idName(typeID)

          dbRow = (timestamp,
                   typeID,
                   delta,
                   balance,
                   typeName)
          valuesList.append(dbRow)

      else:
        matEntryID = 'NULL'
        delta = 0
        timestamp = time.time()
        balance = currentQuantity
        typeName = StaticData.idName(typeID)

        dbRow = (timestamp,
                 typeID,
                 delta,
                 balance,
                 typeName)
        valuesList.append(dbRow)


    #checking for depleted materials
    lastEntries = cls._getLastEntries()

    for entry in lastEntries:
      typeID = entry[0][0]
      timestamp = entry[1]
      balance = entry[2]

      if typeID not in currentMatsDict and balance > 0:
        matEntryID = 'NULL'
        delta = -balance
        timestamp = time.time()
        balance = 0
        typeName = StaticData.idName(typeID)

        dbRow = (timestamp,
                 typeID,
                 delta,
                 balance,
                 typeName)
        valuesList.append(dbRow)

    #updating database
    cls.logDatabase.executemany( ('INSERT INTO materialsLog '
                                  '(timestamp,typeID,delta,balance,typeName)'
                                  'VALUES (?,?,?,?,?)')
                                 , valuesList)
    cls.logDatabase.commit()

  #----------------------------------------------------------------------
  @classmethod
  def _getLastEntries(cls):
    """"""
    bdResponse = cls.logDatabase.execute( (f'SELECT DISTINCT "typeID" '
                                                f'FROM "materialsLog" ') )
    uniqueTypeIDs = bdResponse.fetchall()

    lastEntries = []
    for typeID in uniqueTypeIDs:
      lastLogEntry = cls._getLastLogEntry(typeID[0])
      timestamp = lastLogEntry[0]
      balance = lastLogEntry[1]
      lastEntries.append([typeID, timestamp, balance])

    return lastEntries

  #----------------------------------------------------------------------
  @classmethod
  def _getLastLogEntry(cls, typeID):
    """"""
    logEntries = cls.logDatabase.execute( (f'SELECT "timestamp", "balance" '
                                           f'FROM materialsLog '
                                           f'WHERE typeID = {typeID} '
                                           f'ORDER BY "timestamp" DESC') )
    lastLogEntry = logEntries.fetchone()

    if lastLogEntry:
      return lastLogEntry
    else:
      return None




if __name__ == '__main__':

  LogDBUpdate.updateMaterialLog()
  print('asdasd')
  pass














