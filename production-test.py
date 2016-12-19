import re
import math
import wx

# bpName -> ID -> materials -> if materials are buildable: materialsID -> bpID -> materials
#
# typeNames -> IDs
# bpNames -> bpIDs
# bpIDs -> dictionary(matID -> quantity)
# prodID -> bpID
# if matID is in (prodID -> bpID):
#     bpIDs -> dictionary(matID -> quantity)

########################################################################
class StaticData:
	""""""

	#----------------------------------------------------------------------
	def __init__(self):
		"""Constructor"""
		#filehandles
		bpProdFile = open("bpID_ProdID.txt")
		materialsFile =  open("material_activities.txt")
		typeFiles = open("invTypes.txt")
		bpNamesbpID = open("bpNamesToIDs.txt")

		#variable definition
		self.prodIDToBpID = {}
		self.typeNamesToID = {}
		self.bpNamesToID = {}
		self.bpIDToMaterials = {}
		self.typeIDToNames = {}

		#parsing and filling of the tables
		#prodIDtobpID
		for i in bpProdFile:
			i = i.rstrip()
			tempList = i.split("\t")
			self.prodIDToBpID[tempList[0]] = tempList[1]

		#typeNames to ID and ID to names
		for i in typeFiles:
			i = i.rstrip()
			if not i:
				continue
			tempList = i.split("\t")
			if tempList[9] is not "1":
				continue			
			self.typeNamesToID[tempList[2]] = tempList[0]
			self.typeIDToNames[tempList[0]] = tempList[2]
			


		#bpNamesToID
		for i in bpNamesbpID:
			i = i.rstrip()
			tempList = i.split("\t")
			self.bpNamesToID[tempList[0]] = tempList[1]

		#bpIDtoMaterials
		for i in materialsFile:
			i = i.rstrip()
			tempList = i.split("\t")
			if tempList[1] != "1":
				continue
			if tempList[0] not in self.bpIDToMaterials:
				self.bpIDToMaterials[tempList[0]] = {}
				self.bpIDToMaterials[tempList[0]][tempList[2]] = tempList[3]
			else:
				self.bpIDToMaterials[tempList[0]][tempList[2]] = tempList[3]

########################################################################
class MineralRequirements:
	""""""

	#----------------------------------------------------------------------
	def __init__(self, productionDict, staticData, ownedMaterialsList, bpMe, componentsMe, bpFactoryModifier, componentsFactoryModifier):
		"""Constructor"""
		self.bpMe = bpMe
		self.componentsMe = componentsMe
		self.bpFactoryModifier = bpFactoryModifier
		self.componentsFactoryModifier = componentsFactoryModifier
		self.productionDict = productionDict
		self.staticData =  staticData
		self.ownedMaterialsList = ownedMaterialsList
	#----------------------------------------------------------------------
	def calculation(self, components = 1):
		"""calculate the required component materials for a given set of production tasks"""
		totalMats = {}
		totalMatsTemp = {}
		totalMatsFinal = {}
		for i in self.productionDict:
			
			runs = int(self.productionDict[i][0])
			bpID = self.staticData.bpNamesToID[i]
			totalRuns = int(self.productionDict[i][1])
			
			materialModifier = float(self.bpMe * self.bpFactoryModifier)
			for mat in self.staticData.bpIDToMaterials[bpID]:
				baseMats = int(self.staticData.bpIDToMaterials[bpID][mat])
				if mat in totalMatsTemp:
					totalMatsTemp[mat] = max(runs, math.ceil( (baseMats * runs * materialModifier) + 0.01 )) + int(totalMatsTemp[mat])
				else:
					totalMatsTemp[mat] = max(runs, math.ceil( (baseMats * runs * materialModifier) + 0.01 ))
			
			for i in totalMatsTemp:
				if i in totalMats:
					totalMats[i] = totalMats[i] + (totalMatsTemp[i] * totalRuns)
				else:
					totalMats[i] = totalMatsTemp[i] * totalRuns
			totalMatsTemp = {}	
		
		
				
		# subtract already owned materials
		for i in self.ownedMaterialsList:
			if i in self.staticData.typeNamesToID:
				z = self.staticData.typeNamesToID[i]
			else:
				continue
			if z in totalMats:
				totalMats[z] =  totalMats[z] - int(self.ownedMaterialsList[i])
				if totalMats[z] <= 0:
					totalMats.pop(z)
				
		
		
		#print stuff
		if components:
			for i in totalMats:
				print "{0}\t{1}".format(self.staticData.typeIDToNames[i], int(totalMats[i]))
		
		#look in totalMats for buildable things
		
		for i in totalMats:
			if i in self.staticData.prodIDToBpID:
				runs = int(totalMats[i])
				bpID = self.staticData.prodIDToBpID[i]
				totalRuns = 1
				
				materialModifier = float(self.componentsMe * self.componentsFactoryModifier)
				for mat in self.staticData.bpIDToMaterials[bpID]:
					baseMats = int(self.staticData.bpIDToMaterials[bpID][mat])
					if mat in totalMatsFinal:	
						totalMatsFinal[mat] = max(runs, math.ceil( (baseMats * runs * materialModifier) + 0.01 )) + int(totalMatsFinal[mat])
					else:
						totalMatsFinal[mat] = max(runs, math.ceil( (baseMats * runs * materialModifier) + 0.01 ))
			else:
				if i in totalMatsFinal:
					totalMatsFinal[i] = totalMats[i] + totalMatsFinal[i]
				else:
					totalMatsFinal[i] = totalMats[i]
					
					
		# subtract already owned materials
		for i in self.ownedMaterialsList:
			if i in self.staticData.typeNamesToID:
				z = self.staticData.typeNamesToID[i]
			else:
				continue
			if z in totalMatsFinal:
				totalMatsFinal[z] =  totalMatsFinal[z] - int(self.ownedMaterialsList[i])
				if totalMatsFinal[z] <= 0:
					totalMatsFinal.pop(z)		
		
		if not components:
			for i in totalMatsFinal:
				print "{0}\t{1}".format(self.staticData.typeIDToNames[i], int(totalMatsFinal[i])* totalRuns) 		

#----------------------------------------------------------------------
def readOwned():
	"""read file output by copying eve stuff"""
	ownFile = open("ownfile.txt")
	own = {}
	for i in ownFile:
		i = i.rstrip()
		tempList = i.split("\t")
		tempList[1] = tempList[1].replace(',', '')
		if tempList[0] not in own:
			own[tempList[0]] = tempList[1]
		else:
			own[tempList[0]] = tempList[1] + own[tempList[0]]
		
	return own
		
	
	
					
				





pls = StaticData()


pDict = {"Tristan Blueprint": [1, 21], "Atron Blueprint": [1, 4]} #{"Nemesis Blueprint" : [1, 21], "Taranis Blueprint" : [1, 4], "100MN Microwarpdrive II Blueprint" : [10, 8], "Ballistic Control System II Blueprint" : [10, 1], "Modulated Strip Miner II Blueprint" : [10, 4]}  #runs, totalruns

ownDict = readOwned()
nullDict = {}

origBpMe = 0.92
origBpFactory = 1 # 0.98

compBpMe = 0.90
compBpFactory = 0.98

solo = MineralRequirements(pDict, pls, nullDict, origBpMe, compBpMe, origBpFactory, compBpFactory)

solo.calculation(1)







