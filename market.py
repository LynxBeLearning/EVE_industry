import API
import math
import utils
import statistics

#in memory caching
avgPrices = {}



#----------------------------------------------------------------------
def millify(n):
    millnames = ['',' Thousand',' M',' B',' T']
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.2f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

#----------------------------------------------------------------------
def avgSellPrice(typeID, avgOrders = 5):
    """calculate the price at which a typeID will sell in a given station"""
    amarrStation = 60008494

    if typeID in avgPrices:
        return avgPrices[typeID]
    else:
        orders = API.getRegionOrders(typeID)

        prices = []
        for order in orders:
            if order.location_id != amarrStation:
                continue
            prices.append(order.price)

        if len(prices) <= avgOrders:
            mean = statistics.mean(prices)
        else:
            mean = statistics.mean(sorted(prices)[1:avgOrders])

        avgPrices[typeID] = mean

        return mean

if __name__ == "__main__":
    a = avgSellPrice(34)
    print(a)