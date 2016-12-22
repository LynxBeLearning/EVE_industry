from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import threading
import urlparse
import base64
import os
import webbrowser
import json
import csv
import requests
import grequests
import time
import pubsub
import locale
import eveapi
import tempfile
import cPickle
import zlib
import re
import datetime
from os.path import join, exists
from Auth import Settings,  AuthOperations

########################################################################
class rawBlueprint:
  """"""

  #----------------------------------------------------------------------
  def __init__(self, apiRow):
    """Constructor"""
    self.itemID = apiRow[0] #unique id of the item, changes if item changes location
    self.locationID = apiRow[1] #id of the place where the item is, containers count as different locations and have ids that depend on the station or citadel
    self.typeID = apiRow[2] #id of the item type
    self.name = apiRow[3] #actual name of the item
    self.flag = apiRow[4] #
    if apiRow[5] == -1: #not really a quantity, -1 for bpo, -2 for bpc
      self.bpo = 1
      self.bpc = 0
    elif apiRow[5] == -2:
      self.bpo = 0
      self.bpc = 1
    self.TE = apiRow[6]
    self.ME = apiRow[7]
    self.runs = apiRow[8]
    
    
  


########################################################################
class apiBlueprintParser:
  """parse raw api blueprint output into data structures."""

  #----------------------------------------------------------------------
  def __init__(self, blueprintApiObj):
    """Constructor"""
    #list of all itemid with same itemtype
    for row in blueprintApiObj.blueprints._rows:
      bpx = row[5] #-1 = origina, -2 = copy
      TE = row[6]
      ME = row[7]
      name = row[3]
      location = row[1]
      runs = row[8]    
    
  
  



cachedApi = eveapi.EVEAPIConnection(cacheHandler=MyCacheHandler(debug=True))
joltanXml = cachedApi.auth(keyID=settings.keyID, vCode=settings.vCode).character(1004487144)
blueprints = joltanXml.Blueprints()