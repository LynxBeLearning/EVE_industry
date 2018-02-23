import os
import API
import time
import datetime
import corpDB
import sqlite3
import swagger_client
from staticClasses import StaticData, settings

#db connection
database = sqlite3.connect(os.path.join(settings.dataFolder, settings.logDB))

#----------------------------------------------------------------------
def updateIndyJobsLog():
    """"""
    indyJobs = API.getIndustryJobs()

    valuesList = []
    for job in indyJobs:
        jobID = job.job_id
        bpID = job.blueprint_id
        activityID = job.activity_id
        productTypeID = job.product_type_id
        productName = StaticData.idName(productTypeID)
        activityName = StaticData.activityID2Name[activityID]
        bpTypeID = job.blueprint_type_id
        bpName = StaticData.idName(bpTypeID)
        runs = job.runs
        cost = job.cost
        startDate = job.start_date
        endDate = job.end_date
        installerID = job.installer_id
        installerName = API.getName(installerID)[0].character_name

        dbRow = (jobID,
           bpID,
           bpTypeID,
           activityID,
           productTypeID,
           activityName,
           bpName,
           productName,
           runs,
           cost,
           startDate,
           endDate,
           installerID,
           installerName)
        valuesList.append(dbRow)

    presentJobIDs = _getPresentJobIDs()
    valuesList = [x for x in valuesList if x[0] not in presentJobIDs]

    if valuesList:
        with database:
            database.executemany( ('INSERT INTO indyJobsLog '
                                   'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
                                  , valuesList)

#----------------------------------------------------------------------
def _getPresentJobIDs():
    """"""
    dbResponse = database.execute( (f'SELECT "jobID" '
                                       f'FROM indyJobsLog ') )
    jobIDs = dbResponse.fetchall()

    if not jobIDs:
        return []
    else:
        return [x[0] for x in jobIDs]


def upgradeTransactionLog():
    """"""
    transactions = API.getMarketTransactions()

    valuesList = []
    for transaction in transactions:
        transID = transaction.transaction_id
        journalRefID = transaction.journal_ref_id
        date = transaction.date
        typeID = transaction.type_id
        typeName = StaticData.idName(typeID)
        quantity = transaction.quantity
        unitPrice = transaction.unit_price
        totalPrice = unitPrice * quantity
        locID = transaction.location_id
        isSell = int(not transaction.is_buy)
        clientID = transaction.client_id
        #transID, journalRefID, date, typeID, quantity, unitPrice, locationID, isSell, clientID
        dbRow = (transID,
           journalRefID,
           date,
           typeID,
           typeName,
           quantity,
           unitPrice,
           totalPrice,
           locID,
           isSell,
           clientID)
        valuesList.append(dbRow)

    presentTransIDs = _getPresentTransIDs()
    valuesList = [x for x in valuesList if x[0] not in presentTransIDs]

    if valuesList:
        with database:
            database.executemany( ('INSERT INTO transactionLog '
                                   'VALUES (?,?,?,?,?,?,?,?,?,?,?)')
                                  , valuesList)


#----------------------------------------------------------------------
def _getPresentTransIDs():
    """"""
    dbResponse = database.execute( (f'SELECT "transID" '
                                       f'FROM transactionLog ') )
    transIDs = dbResponse.fetchall()

    if not transIDs:
        return []
    else:
        return [x[0] for x in transIDs]

#----------------------------------------------------------------------
def updateJournalLog():
    """"""
    journal = API.getJournal()

    valuesList = []
    for entry in journal:
        refID = entry.ref_id
        refType = entry.ref_type
        delta = entry.amount
        balance = entry.balance
        date = entry.date
        if entry.extra_info:
            if entry.extra_info.transaction_id:
                transactionID = entry.extra_info.transaction_id
            else:
                transactionID = 'NULL'
            if entry.extra_info.job_id:
                jobID = entry.extra_info.job_id
            else:
                jobID = 'NULL'
        else:
            transactionID = 'NULL'
            jobID = 'NULL'


        dbRow = (refID,
           refType,
           delta,
           balance,
           date,
           transactionID,
           jobID)
        valuesList.append(dbRow)


    currentRefIDs = _getJournalRefIDs()
    valuesList = [x for x in valuesList if x[0] not in currentRefIDs]

    if valuesList:
        with database:
            database.executemany( ('INSERT INTO journalLog '
                                   'VALUES (?,?,?,?,?,?,?)')
                                  , valuesList)

#----------------------------------------------------------------------
def _getJournalRefIDs():
    """"""
    dbResponse = database.execute( (f'SELECT "refID" '
                                       f'FROM journalLog ') )
    journalRefIDs = dbResponse.fetchall()

    if not journalRefIDs:
        return []
    else:
        return [x[0] for x in journalRefIDs]
        #refID, refType, delta, balance, date, transactionID, jobID


#----------------------------------------------------------------------
def updateMaterialLog():
    """"""
    #getting newly updated info
    materials = corpDB.database.execute( (f'SELECT "typeID", "quantity" '
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
        lastLogEntry = _getLastLogEntry(typeID)

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
            delta = currentQuantity
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
    lastEntries = _getLastEntries()

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
    with database:
        database.executemany(('INSERT INTO materialsLog '
                              '(timestamp,typeID,delta,balance,typeName)'
                              'VALUES (?,?,?,?,?)')
                             , valuesList)


#----------------------------------------------------------------------
def _getLastEntries():
    """"""
    bdResponse = database.execute( (f'SELECT DISTINCT "typeID" '
                                       f'FROM "materialsLog" ') )
    uniqueTypeIDs = bdResponse.fetchall()

    lastEntries = []
    for typeID in uniqueTypeIDs:
        lastLogEntry = _getLastLogEntry(typeID[0])
        timestamp = lastLogEntry[0]
        balance = lastLogEntry[1]
        lastEntries.append([typeID, timestamp, balance])

    return lastEntries

#----------------------------------------------------------------------
def _getLastLogEntry(typeID):
    """"""
    logEntries = database.execute( (f'SELECT "timestamp", "balance" '
                                       f'FROM materialsLog '
                                       f'WHERE typeID = {typeID} '
                                       f'ORDER BY "timestamp" DESC') )
    lastLogEntry = logEntries.fetchone()

    if lastLogEntry:
        return lastLogEntry
    else:
        return None



#----------------------------------------------------------------------
def updateAll():
    """"""
    if not API.networkConnectivity():
        raise ConnectionError("No internet connectivity.\n")

    updateJournalLog()
    updateMaterialLog()
    upgradeTransactionLog()
    updateIndyJobsLog()