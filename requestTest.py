#from bravado.requests_client import RequestsClient
#from bravado.client import SwaggerClient
import requests
import json
import csv
import eveapi
import tempfile
import time
import cPickle
import zlib
import os
import datetime
from os.path import join, exists
from Auth import Settings,  AuthOperations

locations = {
             1022771210683 : "zansha mining, bpc container", #zansha mining, bpc container
             1022832888095 : "zansha neuro, researched bpo container", #zansha neuro, researched bpo container
             1022771182111 : "zansha mining, component bpos",  #zansha mining, components bpos container
             1022756068998 : "zansha neuro, hangar",  #zansha neuro, hangar
            }


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
class requestUrls:
  """return correct urls to submit requests"""

  #----------------------------------------------------------------------
  def __init__(self, characterID):
    """Constructor"""
    
    self.assetsUrl = 'https://esi.tech.ccp.is/latest/characters/{}/assets/'.format(characterID)
    

########################################################################
class getAssets:
  """get asset data from ESI"""

  #----------------------------------------------------------------------
  def __init__(self,  assetUrl, authHeader):
    """Constructor"""
    
    r = requests.get(assetUrl, headers=authHeader)
    self.assets = r.json()
    
    
  







def needResearch(blueprintApiObj):
  """Constructor"""
  for row in blueprintApiObj.blueprints._rows:
    bpx = row[5] #-1 = origina, -2 = copy
    TE = row[6]
    ME = row[7]
    name = row[3]
    location = row[1]

    #print row

    if bpx == -1 and (location in locations):
      if 20 - TE > 0:
        print "{} {} TE ".format(name, (20 - TE) / 2, locations[location])
      if 10 - ME > 0:
        print "{} {} ME ".format(name, 10 - ME,  locations[location]) 

def needCopying(blueprintApiObj):
  """Constructor"""
  runCounter = {}
  bpoList = []  
  
  for row in blueprintApiObj.blueprints._rows:
    bpx = row[5] #-1 = origina, -2 = copy
    TE = row[6]
    ME = row[7]
    name = row[3]
    location = row[1]
    runs = row[8]
    


    if bpx == -1 and (location in locations) and ME == 10 and TE == 20:
      if name in bpoList:
        pass
      else:        
        bpoList.append(name)

    if bpx == -2 and (location in locations) and (ME == 10 and TE == 20):
      if name in runCounter:
        runCounter[name] = [runs + runCounter[name][0], 1 + runCounter[name][1]]
      else:
        runCounter[name] = [runs, 1]  
        
  for i in bpoList:
    if i not in runCounter:
      print "{} has no copies available".format(i)
    elif runCounter[i][0] < 20:
      print "{} has {} total runs over {} bpc".format(i, runCounter[i][0], runCounter[i][1])
      
      
    


    
  




settings = Settings()
joltan = AuthOperations(settings)
joltanUrls = requestUrls(joltan.chrID)
joltanAssets = getAssets(joltanUrls.assetsUrl, joltan.authHeader)


cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=settings.keyID, vCode=settings.vCode).character(1004487144)
transactions = joltanXml.Blueprints()
needResearch(transactions)
needCopying(transactions)

print "kaorlghj"