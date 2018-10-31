import os
import API
import time
import datetime
import corpDB
import sqlite3
import swagger_client
import utils



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
        productName = utils.idName(productTypeID)
        activityName = utils.activityID2Name[activityID]
        bpTypeID = job.blueprint_type_id
        bpName = utils.idName(bpTypeID)
        runs = job.runs
        cost = job.cost
        startDate = job.start_date
        endDate = job.end_date
        installerID = job.installer_id
        installerName = API.getName(installerID).name

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
        with utils.logDb:
            utils.logDb.executemany( ('INSERT INTO indyJobsLog '
                                   'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
                                  , valuesList)

#----------------------------------------------------------------------
def _getPresentJobIDs():
    """"""
    dbResponse = utils.logDb.execute( (f'SELECT "jobID" '
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
        typeName = utils.idName(typeID)
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
        with utils.logDb:
            utils.logDb.executemany( ('INSERT INTO transactionLog '
                                   'VALUES (?,?,?,?,?,?,?,?,?,?,?)')
                                  , valuesList)


#----------------------------------------------------------------------
def _getPresentTransIDs():
    """"""
    dbResponse = utils.logDb.execute( (f'SELECT "transID" '
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
        refID = entry.id
        refType = entry.ref_type
        delta = entry.amount
        balance = entry.balance
        date = entry.date
        if entry.context_id_type:
            if entry.context_id_type == "market_transaction_id":
                transactionID = entry.context_id
                jobID = 'NULL'
            elif entry.context_id_type == "industry_job_id":
                transactionID = 'NULL'
                jobID = entry.context_id
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
        with utils.logDb:
            utils.logDb.executemany( ('INSERT INTO journalLog '
                                   'VALUES (?,?,?,?,?,?,?)')
                                  , valuesList)

#----------------------------------------------------------------------
def _getJournalRefIDs():
    """"""
    dbResponse = utils.logDb.execute( (f'SELECT "refID" '
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
    materials = utils.currentDb.execute( (f'SELECT "typeID", "quantity" '
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
                typeName = utils.idName(typeID)

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
            typeName = utils.idName(typeID)

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
            typeName = utils.idName(typeID)

            dbRow = (timestamp,
             typeID,
             delta,
             balance,
             typeName)
            valuesList.append(dbRow)

    #updating database
    with utils.logDb:
        utils.logDb.executemany(('INSERT INTO materialsLog '
                              '(timestamp,typeID,delta,balance,typeName)'
                              'VALUES (?,?,?,?,?)')
                             , valuesList)


#----------------------------------------------------------------------
def _getLastEntries():
    """"""
    bdResponse = utils.logDb.execute( (f'SELECT DISTINCT "typeID" '
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
    logEntries = utils.logDb.execute( (f'SELECT "timestamp", "balance" '
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