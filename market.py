import eveapi
import reverence

import time
import tempfile
import cPickle
import zlib
import os
import datetime
from os.path import join, exists
from httplib import HTTPException
from operator import itemgetter
import re

########################################################################
KEYID = 2371617
VCODE = "310BIeJVttkx0H3Q2EHCsHm4ppHNe53YEs2J2CakcyAVrptOS6WKS3eLAFuNeauX"
VOLCONSTANT = 3

########################################################################
class MyCacheHandler(object):
    # Note: this is an example handler to demonstrate how to use them.
    # a -real- handler should probably be thread-safe and handle errors
    # properly (and perhaps use a better hashing scheme).

    def __init__(self, debug=False):
        self.debug = debug
        self.count = 0
        self.cache = {}
        self.tempdir = join(tempfile.gettempdir(), "eveapi")
        if not exists(self.tempdir):
            os.makedirs(self.tempdir)

    def log(self, what):
        if self.debug:
            print "[%d] %s" % (self.count, what)

    def retrieve(self, host, path, params):
        # eveapi asks if we have this request cached
        key = hash((host, path, frozenset(params.items())))

        self.count += 1  # for logging

        # see if we have the requested page cached...
        cached = self.cache.get(key, None)
        if cached:
            cacheFile = None
            #print "'%s': retrieving from memory" % path
        else:
            # it wasn't cached in memory, but it might be on disk.
            cacheFile = join(self.tempdir, str(key) + ".cache")
            if exists(cacheFile):
                self.log("%s: retrieving from disk" % path)
                f = open(cacheFile, "rb")
                cached = self.cache[key] = cPickle.loads(zlib.decompress(f.read()))
                f.close()

        if cached:
            # check if the cached doc is fresh enough
            if time.time() < cached[0]:
                self.log("%s: returning cached document" % path)
                return cached[1]  # return the cached XML doc

            # it's stale. purge it.
            self.log("%s: cache expired, purging!" % path)
            del self.cache[key]
            if cacheFile:
                os.remove(cacheFile)

        self.log("%s: not cached, fetching from server..." % path)
        # we didn't get a cache hit so return None to indicate that the data
        # should be requested from the server.
        return None

    def store(self, host, path, params, doc, obj):
        # eveapi is asking us to cache an item
        key = hash((host, path, frozenset(params.items())))

        cachedFor = obj.cachedUntil - obj.currentTime
        if cachedFor:
            self.log("%s: cached (%d seconds)" % (path, cachedFor))

            cachedUntil = time.time() + cachedFor

            # store in memory
            cached = self.cache[key] = (cachedUntil, doc)

            # store in cache folder
            cacheFile = join(self.tempdir, str(key) + ".cache")
            f = open(cacheFile, "wb")
            f.write(zlib.compress(cPickle.dumps(cached, -1)))
            f.close()



########################################################################
class Orders:
    """stores exported orders"""

    #----------------------------------------------------------------------
    def __init__(self, ordersFile, IDfile, referenceFile=None  ):
        """Constructor"""

        ####initialization

        ##raw files
        orders =  open(ordersFile)
        references =  open(referenceFile)
        ids = open(IDfile)

        ##dictionaries and variables
        self.sellDict = {}
        self.buyDict = {}
        self.refTable = []
        self.idDict = {}
        self.reference =  []

        ## ID Dictionary initialization
        for i in ids:
            i = i.strip().split("\t")
            if len(i) != 2:
                continue
            self.idDict[i[0]] = i[1]


        ####orders parsing
        for order in orders:
            tempTable = order.strip().strip(",").split(",")
            if tempTable[21] ==  'escrow':
                continue
            if tempTable[9] == 'True':
                #in order: itemID, totalVolume, remainingVolume, escrow
                self.buyDict[tempTable[1]] = [tempTable[11], tempTable[12]]
            else:
                self.sellDict[tempTable[1]] = [tempTable[11], tempTable[12]]

        for key in self.buyDict.keys():
            self.buyDict[self.idDict[key]] =  self.buyDict[key]
            del self.buyDict[key]
        for key in self.sellDict.keys():
            self.sellDict[self.idDict[key]] =  self.sellDict[key]
            del self.sellDict[key]            

        ####reference parsing

        for ref in references:
            self.reference.append(ref.strip())

    #----------------------------------------------------------------------
    def buyOrders(self):
        """displaye stuff that is in reference but not in buy order"""
        for i in self.reference:
            if i not in self.buyDict.keys():
                print i



    #----------------------------------------------------------------------
    def sellOrders(self):
        """display the orders for which stock is present buy sell order is not"""
        
        
        for i in self.reference:
            if i not in self.sellDict.keys():
                print i
        
        #####old stuff, could be usefull
#        buyList = [pls.buyDict[i][0] for i in range(len(pls.buyDict))]
#        fullStock = []#

#        for i in self.reference:
#            if i not in buyList:
#                fullStock.append(i)

 #       sellList = [pls.sellTable[i][0] for i in range(len(pls.sellTable))]#

#        for i in fullStock:
#            if i not in sellList:
#                print i

                ####slice = [pls.buyTable[i][0] for i in range(len(pls.buyTable))] to slice table

########################################################################
class WalletTransactions:
    """query the EVE api and retrieve transactions"""

    #----------------------------------------------------------------------
    def __init__(self, keyId, vcode,  reference):
        """Constructor"""

        ##initialization
        self.transactionTable = [] #date, type, price, quantity, buy(boolean)
        self.soldItems = []
        self.boughtItems = []
        
        cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
        joltan = cachedApi.auth(keyID=keyId, vCode=vcode).character(1004487144)
        transactions = joltan.WalletTransactions()
        self.sold = transactions.transactions.GroupedBy("transactionType")["sell"]
        self.bought = transactions.transactions.GroupedBy("transactionType")["buy"]
        
        self.soldItems = [self.sold._rows[i][3] for i in range(len(self.sold._rows))]
        self.boughtItems = [self.bought._rows[i][3] for i in range(len(self.bought._rows))]
        for item in reference:
            if item in self.soldItems:
                for row in self.sold.GroupedBy("typeName")[item]:
                    self.transactionTable.append([row.transactionDateTime, item, row.price, row.quantity, 0])
            if item in self.boughtItems:
                for row in self.bought.GroupedBy("typeName")[item]:
                    self.transactionTable.append([row.transactionDateTime, item, row.price, row.quantity, 1])
        self.transactionTable.sort(key=itemgetter(0))

    #----------------------------------------------------------------------
    def updateStockpile(self):
        """create or update a list with the current items, and the price paid for each"""
        self.databaseDict = {}
        self.volumeDict = {}
        
        ## read preexisting volumefile if it exists
        if not os.path.isfile("volume.txt"):
            ref = open("reference.txt")
            for i in ref:
                i = i.strip()
                self.volumeDict[i] = 0
        else:
            vol =  open("volume.txt")
            for i in vol:
                i = i.strip().split("\t")
                self.volumeDict[i[0]] = int(i[1]) 
        
        ## read preexisting database if it exists
        if not os.path.isfile("database.txt"):
            pass
        else:
            database = open("database.txt",  "r")
            for item in database:
                attributes = item.strip().split("\t") # name, date, quantity, price, 
                if attributes[0] not in self.databaseDict.keys():
                    self.databaseDict[attributes[0]] = [[attributes[1], attributes[2],  attributes[3]]]
                else:
                    self.databaseDict[attributes[0]].append([attributes[1], attributes[2], attributes[3]])
            database.close()
            
            
        ## determines the date of the last previously analized transaction to avoid analyzing it again
        if "lastDateAnalyzed" not in self.databaseDict.keys():
            lastDateAnalyzed = 0
        else:
            lastDateAnalyzed = int(self.databaseDict["lastDateAnalyzed"][0][0])

        ## updates the database with new information coming from self.transactionTable
        for item in self.transactionTable:
            if int(item[0]) < lastDateAnalyzed:
                continue
            if item[4] > 0:
                if item[1] not in self.databaseDict.keys():
                    self.databaseDict[item[1]] = [[item[0], item[3], item[2]]]
                else:
                    self.databaseDict[item[1]].append([item[0], item[3], item[2]])
            elif item[4] == 0:
                if item[1] not in self.databaseDict.keys():
                    continue
                else:
                    self.databaseDict[item[1]].sort(key=itemgetter(1))
                    spent = item[3]
                    #self.volumeDict[item[1]] += item[3] ####
                    
                    #error catching for when you sell more than you have, a common occurrence when
                    #database is incomplete
                    while spent > 0:
                        if  not self.databaseDict[item[1]]:
                            spent = 0
                            continue
                        
                        remaining = int(self.databaseDict[item[1]][-1][1]) - spent
                        if remaining > 0:
                            self.databaseDict[item[1]][-1][1] = remaining
                            spent = 0
                        elif remaining <= 0:
                            spent = spent - int(self.databaseDict[item[1]][-1][1])
                            del self.databaseDict[item[1]][-1]
                            
                            
        ## calculate new lastDateAnalyzed
        lastDateAnalyzed = self.transactionTable[-1][0]
        self.databaseDict["lastDateAnalyzed"] = [[lastDateAnalyzed, 0, 0]] 
        ## write new database
        
        open("database.txt", "w").close()
        databaseWrite = open("database.txt", "w")
        for key in self.databaseDict.keys():
            for items in self.databaseDict[key]:
                databaseWrite.write("{0}\t{1}\t{2}\t{3}\n".format(key, items[0], items[1], items[2]))
        databaseWrite.close()
        
        ## write new volume file
       
        volumeWrite =  open("volume.txt",  "w")
        for key in self.volumeDict.keys():
            volumeWrite.write("{0}\t{1}\n".format(key, self.volumeDict[key]))
        volumeWrite.close()
        





    #----------------------------------------------------------------------
    def currentStockpile(self): ###TODO ADD WAY TO DETERMINE TIME OF LAST TRANSACTION, DIFFERENTIATE BETWEEN ITEM IN STOCKPILE AND ITEM IN SELLING ORDER
        """prints current stockpile"""
        for item in self.databaseDict.keys():
            quantitySum = 0
            for i in self.databaseDict[item]:
                quantitySum = quantitySum + int(i[1])
            if quantitySum > 0:
                print "{0}\t{1}".format(item, quantitySum)
            
            
########################################################################
class MarketLogs:
    """parse marketlogs and calculate a number of statistics"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        #variables
        itemName_pattern = re.compile("-(.+)-")
        self.logs = {}
        amarr = "60008494"

        
        
        for fileName in os.listdir("C:\Users\Tito\Documents\EVE\logs\Marketlogs"):
            buyOrders = []
            sellOrders = []
            
            match = itemName_pattern.findall(fileName)
            itemName = match[0]
            self.logs[itemName] = []
            filePath = os.path.join("C:/Users/Tito/Documents/EVE/logs/Marketlogs/", fileName)
            log = open(filePath, "r")
            for line in log:
                line = line.strip().split(",")
                
                if line[10] !=  amarr:
                    continue                
                
                line = [float(line[0]), line[7], line[10]] # price, buy, station

                
                if line[1] == "False":
                    sellOrders.append(line)
                else:
                    buyOrders.append(line)
                    
            buyOrders.sort(key=itemgetter(0))
            sellOrders.sort(key=itemgetter(0))
            
            self.logs[itemName].append(sellOrders[0])
            self.logs[itemName].append(buyOrders[-1])
            

    #----------------------------------------------------------------------
    def stockpileAppraiser(self, databaseDict,  volumeDict):
        """determine which items are worth selling"""
        marginTable = []
        
        for item in databaseDict.keys():
            if item == 'lastDateAnalyzed':
                continue
            priceSum = 0
            nSum =  0
            
            for i in databaseDict[item]:
                nSum = nSum + int(i[1])
                priceSum = priceSum +  int(i[1]) * float(i[2])
            try:
                mean = priceSum / nSum
            except:
                mean = 0
            
            revenue = self.logs[item][0][0]
            
            margin = (revenue -  mean) / revenue * 100
            
            profit = revenue - mean
            
            normProfit = profit *  (int(volumeDict[item]) / VOLCONSTANT)
            
            marginTable.append([item, str(margin)+"%", str(profit),  str(normProfit)])
            
            
        
        marginTable.sort(key=itemgetter(1))
        for i in marginTable:
            print "{0}\t{1}\t{2}\t{3}".format(i[0], i[1], i[2], i[3])


pls = Orders("orders.txt", "IDs.txt",  "reference.txt")
la = WalletTransactions(KEYID, VCODE, pls.reference)
la.updateStockpile()
pls.buyOrders()
#le = MarketLogs()
print("pls")


