from reverence import blue


##TODO: read xls files and generate a dictionary with key blueprintID and values another dictionary with materials costs for production.
## another dictionary with name -> blueprintID and a third with typeID -> blueprintID, maybe also a 4th with typeID for materials -> name

########################################################################
class EveData:
	"""data read from the EVE online static dump through reverence."""

	#----------------------------------------------------------------------
	def __init__(self, path):
		"""Constructor"""

		#eve cache reader initialization
		eve = blue.EVE(path)
		self.cache = eve.getconfigmgr()

		#variable initialization
		manufacturableID = []
		manufacturableNames =  []
		self.manufacturableIdNames = {}

		self.blueprintData = self.cache.invbptypes
		self.everythingData = self.cache.invtypes
		self.mineralData = self.cache.invtypematerials

		#generating names to
		for u in self.blueprintData.Select("productTypeID"):
			manufacturableID.append(u)

		for i in manufacturableID:
			manufacturableNames.append(self.everythingData.get(i).typeName)

		for u, z in zip(manufacturableID, manufacturableNames):
			self.manufacturableIdNames[z] = u    

	#----------------------------------------------------------------------
	def resources(self, manufacturingList):
		"""determine the mineral cost of stuff"""
		totalMinerals = {}

		for key in manufacturingList:
			for row in self.mineralData.get(self.manufacturableIdNames[key]):
				totalMinerals[self.everythingData.get(row.materialTypeID).typeName] =  row.quantity * manufacturingList[key]
		
		return totalMinerals




pls = EveData("F:\giochi\Eve Online")
la = {}
la["Nemesis"] =  1
pls.resources(la)
print "lol"


cfg.invtypematerials.get(638)[1].materialTypeID
35
cfg.invtypematerials.get(638)[1].quantity

for u, d in self.blueprintData.Select("blueprintTypeID",  "productTypeID"):
	print "{0}\t{1}".format(d, u)
	
for i in pls.cache.invbptypes.Select():
	print "{0}\t{1}".format(i, pls.manufacturableIdNames[i])
	

gooby = []
for u in self.blueprintData.Select("blueprintTypeID"):
	gooby.append(u)
	
for i in gooby:
	print "{0}\t{1}".format(pls.cache.invtypes.get(i).typeName, i)