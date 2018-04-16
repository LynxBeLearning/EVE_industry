import os
import API
import time
import sqlite3
import tempfile
import datetime
import swagger_client
import utils


#----------------------------------------------------------------------
def updateAssets():
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
  assets = API.getAssets()
  valuesList = []

  for item in assets:
    itemName = utils.idName(item.type_id)

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

  with utils.currentDb:
    utils.currentDb.executemany('INSERT INTO Assets VALUES (?,?,?,?,?,?,?,?)', valuesList)


#----------------------------------------------------------------------
def updateBlueprints():
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
  blueprints = API.getBlueprints()
  valuesList = []

  for blueprint in blueprints:
    #recover plain name
    itemName = utils.idName(blueprint.type_id)

    #determina if bpo, t1 copy or t2 copy ### or t3 copy
    if blueprint.quantity == -1:
      bpo = 1
    else:
      bpo = 0
    bpClass = utils.bpClass(blueprint.type_id)


    #determine product id and name
    productID = utils.productID(blueprint.type_id)
    if productID:
      productName = utils.idName(productID)
    else:
      productID = 'NULL'
      productName = 'NULL'


    #determine if inventable or invented
    inventable = int(utils.inventable(blueprint.type_id))  #needs to be integer not bool
    inventedFromID = utils.inventedFrom(blueprint.type_id)
    if not inventedFromID:
      inventedFromID = 'NULL'
      inventedFromName = 'NULL'
    else:
      inventedFromName = utils.idName(inventedFromID)

    #determine if component
    if bpClass == 1:
      component = int(utils.component(blueprint.type_id))

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

  with utils.currentDb:
    utils.currentDb.executemany('INSERT INTO Blueprints VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                         valuesList)

#----------------------------------------------------------------------
def updateMaterials():
  """"""
  assets = utils.currentDb.execute( (f'SELECT "typeID", "quantity" '
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
    buildable = int(utils.buildable(typeID))
    typeName = utils.idName(typeID)
    dbRow = (typeID,
             typeName,
             materialsDict[typeID],
             buildable)
    valuesList.append(dbRow)


  with utils.currentDb:
    utils.currentDb.executemany( ('INSERT INTO AggregatedMaterials '
                           'VALUES (?,?,?,?)')
                          , valuesList)


#----------------------------------------------------------------------
def updateIndustryJobs():
  """"""
  indyJobs = API.getIndustryJobs()

  #jobid, itemid, bpid, bptypeName, runs, prodtypeID, prodTypeName endDate, status

  valuesList = []
  for job in indyJobs:
    jobID = job.job_id
    bpID = job.blueprint_id
    bpTypeID = job.blueprint_type_id
    bpTypeName = utils.idName(bpTypeID)
    runs = job.runs
    endDate = job.end_date
    status = job.status
    productTypeID = job.product_type_id
    productTypeName = utils.idName(productTypeID)
    installerID = job.installer_id
    installerName = API.getName(installerID)[0].character_name
    activityID = job.activity_id
    activityName = utils.activityID2Name[activityID]

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

  with utils.currentDb:
    utils.currentDb.executemany( ('INSERT INTO IndustryJobs '
                           'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)')
                          , valuesList)

#----------------------------------------------------------------------
def updateMarketOrders():
  """"""
  marketOrders = API.getMarketOrders()

  valuesList = []
  for marketOrder in marketOrders:
    orderID = marketOrder.order_id
    stationID = marketOrder.location_id
    remainingItems = marketOrder.volume_remain
    typeID = marketOrder.type_id
    typeName = utils.idName(typeID)
    sellOrder = 1 if marketOrder.is_buy_order else 0
    stationName = utils.stationName(stationID)

    dbRow = (orderID,
             typeID,
             typeName,
             remainingItems,
             sellOrder,
             stationID,
             stationName)
    valuesList.append(dbRow)

  with utils.currentDb:
    utils.currentDb.executemany( ('INSERT INTO MarketOrders '
                           'VALUES (?,?,?,?,?,?,?)')
                          , valuesList)

#----------------------------------------------------------------------
def updateBlueprintPriority():
  """calculate priority for every t2/3 blueprint and push it to db"""
  allInventables = utils.allInventables()
  allInventablesNames = utils.idNames(allInventables)
  parentIDs = utils.inventedFroms(allInventables)
  parentNames = utils.idNames(parentIDs)

  sizes = utils.marketSizes(allInventables)

  #calculate if sufficient number of items on market
  minMarketSizes = [x[2] for x in sizes]
  remainingItems = utils.onTheMarkets(allInventables)
  marketOk = [1 if x >= y else 0 for x, y in zip(remainingItems, minMarketSizes)]

  #check if item is being produced
  prodRuns = [utils.jobRuns(x) for x in allInventables]

  #calculate if sufficient amount of t2/3 bpc
  manufSizes = [x[1] for x in sizes]
  totalRuns = [utils.totalRuns(x) for x in allInventables]
  bpcRunsOk = [1 if x >= y else 0 for x, y in zip(totalRuns, manufSizes)]

  #check if item is being invented
  invRuns = [utils.jobRuns(x, activity= 8, parent= True) for x in allInventables]

  #calculate if sufficient amount of parent bpc exist
  copySizes = [x[0] for x in sizes]
  totalParentRuns = [utils.totalRuns(x) for x in parentIDs]
  parentBpcRunsOk = [1 if x >= y else 0 for x, y in zip(totalParentRuns, copySizes)]

  #check if parent is being copied
  copyRuns = [utils.jobRuns(x, activity= 5, parent = True) for x in allInventables]

  #calculate priority and push to database
  rowList = []
  for index in range(len(allInventables)):
    typeID = allInventables[index]
    name = allInventablesNames[index]
    parentTypeID = parentIDs[index]
    parentName = parentNames[index]
    marketOK = marketOk[index]
    inProduction = prodRuns[index]
    t2bpcOK = bpcRunsOk[index]
    beingInvented = invRuns[index]
    parentBpcOK = parentBpcRunsOk[index]
    parentBeingCopied = copyRuns[index]
    lowPriority = 0

    if t2bpcOK and not inProduction and not marketOK:
      priority = 'manufacturing'
    elif not t2bpcOK and not beingInvented and parentBpcOK:
      priority = 'invention'
    elif not parentBpcOK and not parentBeingCopied:
      priority = 'copying'
    else:
      if t2bpcOK and not inProduction and marketOK:
        priority = 'manufacturing'
        lowPriority = 1
      elif not t2bpcOK and not beingInvented and parentBpcOK:
        priority = 'invention'
        lowPriority = 1
      elif not parentBpcOK and not parentBeingCopied:
        priority = 'copying'
        lowPriority = 1
      else:
        priority = "no priority"

    rowList.append([typeID, name, parentTypeID, parentName, marketOK, inProduction, t2bpcOK,
                   beingInvented, parentBpcOK, parentBeingCopied, priority, lowPriority])

  with utils.currentDb:
    utils.currentDb.executemany('INSERT INTO BlueprintPriority VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                         rowList)


#----------------------------------------------------------------------
def _DBWipe(tableNames = []):
  """wipe the database of all entries"""
  if not tableNames:
    tableRequest = utils.currentDb.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tableNames = [x[0] for x in tableRequest]

  for table in tableNames:
    utils.currentDb.execute(f'DELETE FROM {table}')

  utils.currentDb.commit()

#----------------------------------------------------------------------
def _DBDump(dumpPath):
  """dump the database in a txt file."""
  #dumping current db
  with open(dumpPath, 'w') as f:
    for line in utils.currentDb.iterdump():
      isGoodLine = (line.startswith("INSERT INTO") or
                   line.startswith("BEGIN TRANSACTION") or
                   line.startswith("COMMIT"))
      if isGoodLine:
        f.write(f'{line}\n')

#----------------------------------------------------------------------
def _DBRestore(dumpPath):
  """read a dump file and restore old databases"""
  _DBWipe()
  with open(dumpPath, 'r') as f:
    dump = f.read()
    with utils.currentDb:
      utils.currentDb.executescript(dump)

#----------------------------------------------------------------------
def updateAll():
  """"""
  #check network connectivity
  if not API.networkConnectivity():
    raise ConnectionError("No internet connectivity.\n")

  #database temporary backup
  dump = tempfile.NamedTemporaryFile(mode = 'w', dir = utils.settings.dataFolder)
  _DBDump(dump.name)

  #attempt update
  try:
    _DBWipe()
    updateAssets()
    updateBlueprints()
    updateMaterials()
    updateIndustryJobs()
    updateMarketOrders()
    updateBlueprintPriority()
  except Exception:
    _DBRestore(dump.name)
    dump.close()
    raise



















