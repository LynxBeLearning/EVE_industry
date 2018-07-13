import API
import math
import time
import utils
import operator
import statistics
import manufacturing

#in memory caching
avgPrices = {}

#----------------------------------------------------------------------
def _updateCachedAvgPrice(typeID, price):
    """updates the average price on the current database"""
    name = utils.idName(typeID)
    date = time.time()
    command = (f'REPLACE into avgPrices (typeID, typeName, avgPrice, date) '
               f'VALUES({typeID}, "{name}", {price}, {date})')

    with utils.currentDb as database:
        database.execute(command)

#----------------------------------------------------------------------
def _getCachedAvgPrice(typeID):
    """query the current database for avg prices"""
    command = (f'SELECT "avgPrice", "date" '
               f'FROM "avgPrices" '
               f'WHERE "typeID" = {typeID}')

    cachedPrice = utils.dbQuery(utils.currentDb, command)

    if cachedPrice:
        return cachedPrice
    else:
        return [None, None]

#----------------------------------------------------------------------
def processOrders(orders):
    """filter outliers and unwanted orders"""
    amarrStation = 60008494
    processedPrices = []
    amarrPrices = []

    for order in orders:
        price = order.price
        location = order.location_id

        if location == amarrStation:
            amarrPrices.append(price)

    amarrPrices = sorted(amarrPrices)

    for price in amarrPrices:
        if len(processedPrices) < 2:
            meanPrices = price
        else:
            meanPrices = statistics.mean(processedPrices)
        threshold = meanPrices + (0.1 * meanPrices)

        if price < threshold:
            processedPrices.append(price)

    return processedPrices



#item + 5%
#
#

#----------------------------------------------------------------------
def avgSellPrice(typeID, avgOrders = 5, maxCacheAge = 3600):
    """calculate the price at which a typeID will sell in a given station"""

    avgPrice, cacheTime = _getCachedAvgPrice(typeID)

    if cacheTime:
        cacheAge = time.time() - cacheTime

    if avgPrice and cacheAge < maxCacheAge:
        return avgPrice
    else:
        prices = processOrders(API.getRegionOrders(typeID))

        if len(prices) == 0:
            print(f"No orders found for {utils.idName(typeID)}, results might be off..")
            return(0)
        if len(prices) <= avgOrders:
            mean = statistics.mean(prices)
        else:
            mean = statistics.mean(sorted(prices)[1:avgOrders])

        _updateCachedAvgPrice(typeID, mean)

        return mean

#----------------------------------------------------------------------
def profits(typeIDs, report = True):  #requires dict with typeID:manufSize
    """orders items on the basis of expected profit"""
    profits = {}
    priceCosts = {}
    counter = 1

    for typeID in typeIDs:
        print(f'{counter}/{len(typeIDs)}')
        counter += 1

        manufSize = typeIDs[typeID]
        productID = utils.productID(typeID)
        batchSellPrice = avgSellPrice(productID) * manufSize

        matsToBuild = manufacturing.manufactureItems(disregardOwnedMats=True,
                                                     report=False,
                                                     typeIDs={typeID: manufSize,})

        totalMatCost = 0
        for mat in matsToBuild:
            numMats = matsToBuild[mat]
            matCost = avgSellPrice(mat) * numMats
            totalMatCost += matCost


        profits[typeID] = batchSellPrice - totalMatCost
        priceCosts[typeID] = (batchSellPrice, totalMatCost)


    if report:
        #order by profit
        orderedTypeIDs = [prof[0] for prof in sorted(profits.items(), key= operator.itemgetter(1))]

        for typeID in orderedTypeIDs:
            batchSellPrice,  totalMatCost = priceCosts[typeID]
            markup = round(( (batchSellPrice - totalMatCost) / totalMatCost ) * 100, 1)


            print(f'{utils.idName(typeID)}: '
                  f'{utils.millify(profits[typeID])} projected profits, '
                  f'{markup}% markup')
    return profits


if __name__ == "__main__":
    a = avgSellPrice(34)
    print(a)