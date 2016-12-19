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
	"""parse static data files and arranges them in python data structures accessible by other classes"""

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
		#prodIDtobpID product ID to blueprint ID
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



		#bpNamesToID blueprint Names to blueprint ID
		for i in bpNamesbpID:
			i = i.rstrip()
			tempList = i.split("\t")
			self.bpNamesToID[tempList[0]] = tempList[1]

		#bpIDtoMaterials blueprint ID to dictionary of materials required
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
	"""encode all the necessary information to calculate material requirements in different conditions"""

	#----------------------------------------------------------------------
	def __init__(self, staticData, bpMe, componentsMe, bpFactoryModifier, componentsFactoryModifier):
		"""Constructor"""
		
		self.bpMaterialModifier = float(bpMe * bpFactoryModifier) #multiplies the MM of the blueprint to be produced with the MM of the assembly array to obtain the total MM
		self.componentMaterialModifier = float(componentsMe * componentsFactoryModifier) #same as above for blueprint and array of components 
		self.staticData =  staticData
	#----------------------------------------------------------------------
	def componentMaterials(self, productionTask, ownedMaterials = {}, undergoingProduction = {}, recursion=0):
		"""calculate the required component materials for a given set of production tasks"""
		#dict with the total component materials required
		componentMats = {}
		productionTaskIDs = {}
		undergoingProductionComponents = {}
		#converting productionTask names to blueprints
		for i in productionTask:
			if self.staticData.typeNamesToID[i] in self.staticData.prodIDToBpID:
				productionTaskIDs[self.staticData.prodIDToBpID[self.staticData.typeNamesToID[i]]] = productionTask[i]
				
		#temporary dictionary used to integrate stuff in totalMats
		componentMatsTemp = {} 
		
		#iterate over the list of stuff to produce
		for bpID in productionTaskIDs:
			#products will be produced in batches of x where x is this number
			runsPerBatch = int(productionTaskIDs[bpID][0])
			
			#id of the blueprint to be produced
			#bpID = self.staticData.bpNamesToID[i]
			
			#there will be a total of x batches produces where x is this number
			totalBatches = int(productionTaskIDs[bpID][1]) 

			#iterate over the materials required for each item
			for materialID in self.staticData.bpIDToMaterials[bpID]:
				#quantity of this particular material required
				baseQuantity = int(self.staticData.bpIDToMaterials[bpID][materialID]) 
				#if this material is already in the temp list adds the calculated material requirements to it, otherwise creates a new entry
				if materialID in componentMatsTemp:
					componentMatsTemp[materialID] = max(runsPerBatch, math.ceil( (baseQuantity * runsPerBatch * self.bpMaterialModifier)  )) + int(componentMatsTemp[materialID])
				else:
					componentMatsTemp[materialID] = max(runsPerBatch, math.ceil( (baseQuantity * runsPerBatch * self.bpMaterialModifier)  )) # + 0.01
			
			#multiplies the material requirements for 1 batch for the number of batches and integrates into totalMats
			for i in componentMatsTemp:
				if i in componentMats:
					componentMats[i] = componentMats[i] + (componentMatsTemp[i] * totalBatches)
				else:
					componentMats[i] = componentMatsTemp[i] * totalBatches
			
			#resets totalmatstemp
			componentMatsTemp = {}	

		#recursively calls itself on the list of already undergoing productions in order to get the component requirements to subtract from owned materials
		if recursion < 1:
			undergoingProductionComponents = self.componentMaterials(undergoingProduction,  recursion=1)
		
		# subtract already owned materials if any
		ownedMaterials = self.materialSubtraction(ownedMaterials, undergoingProductionComponents)
		
		#subtract already owned materials if any from the amount of materials needed
		componentMats = self.materialSubtraction(componentMats, ownedMaterials)

		#return values
		return componentMats


	#----------------------------------------------------------------------
	def baseMaterials(self, productionTask,  ownedMaterials = {},  undergoingProduction = {}):
		"""determine the base material components for a given production task"""
		#determine the lists of component materials by calling the componentMaterials method
		componentMats = self.componentMaterials(productionTask, ownedMaterials, undergoingProduction)
		#variable definition
		baseMats = {}
		
		#look in totalMats for buildable things
		for i in componentMats:
			if i in self.staticData.prodIDToBpID:
				runsPerBatch = int(componentMats[i])
				bpID = self.staticData.prodIDToBpID[i]
				totalBatches = 1 #always 1, there is no limit to component production

				for mat in self.staticData.bpIDToMaterials[bpID]:
					baseQuantity = int(self.staticData.bpIDToMaterials[bpID][mat])
					if mat in baseMats:	
						baseMats[mat] = max(runsPerBatch, math.ceil( (baseQuantity * runsPerBatch * self.componentMaterialModifier)  )) + int(baseMats[mat])
					else:
						baseMats[mat] = max(runsPerBatch, math.ceil( (baseQuantity * runsPerBatch * self.componentMaterialModifier)   ))
			else:
				if i in baseMats:
					baseMats[i] = componentMats[i] + baseMats[i]
				else:
					baseMats[i] = componentMats[i]

		
		# subtract already owned materials
		undergoingProductionComponents = self.componentMaterials(undergoingProduction)
		ownedMaterials = self.materialSubtraction(ownedMaterials, undergoingProductionComponents)

		#
		baseMats = self.materialSubtraction(baseMats, ownedMaterials)
		
		#return
		return baseMats
				
	#-----------------------------------------------------------------------
	def materialSubtraction(self, minuend, subtrahend):
			for i in subtrahend:
				if i in self.staticData.typeNamesToID:
					z = self.staticData.typeNamesToID[i]
				elif i in self.staticData.typeIDToNames:
					z = self.staticData.typeIDToNames[i]
				else:
					continue
				if z in minuend:
					minuend[z] =  int(minuend[z]) - int(subtrahend[i])
					if minuend[z] <= 0:
						minuend.pop(z)
			return minuend
	
	#----------------------------------------------------------------------
	def printMats(self, materials):
		"""print material components coming from componentMaterials or baseMaterials"""
		for i in materials:
			print "{0}\t{1}".format(self.staticData.typeIDToNames[i], int(materials[i]))		

#----------------------------------------------------------------------
def readOwnedMats(path):
	"""read file output by copying eve stuff"""
	matFile = open(path)
	mats = {}
	for i in matFile:
		i = i.rstrip()
		tempList = i.split("\t")
		tempList[1] = tempList[1].replace(',', '')
		if tempList[0] not in mats:
			mats[tempList[0]] = int(tempList[1])
		else:
			mats[tempList[0]] = int(tempList[1]) + int(mats[tempList[0]])
	matFile.close()
	return mats










#----------------------------------------------------------------------
def readProductionTask(path):
	"""read production stuff"""
	productionTask = open(path)
	productionDict = {}
	for i in productionTask:
		i = i.strip()
		i = i.replace(" Blueprint", "")
		if i in productionDict:
			productionDict[i] = productionDict[i] + 1
		else:
			productionDict[i] = 1
	for i in productionDict:
		if re.search("II", i) is not None:
			productionDict[i] = [10, productionDict[i]]
		elif re.search("Tengu | Loki | Legion | Proteus", i) is not None:
			productionDict[i] = [3, productionDict[i]]
		else:
			productionDict[i] = [1, productionDict[i]]
	productionTask.close()
	return productionDict
				



pls = StaticData()


#pDict = {"Legion":  [10, 2]} #{"100MN Microwarpdrive II": [10, 2 ], "Ares": [1, 4], "Ballistic Control System II": [10, 5], "Energized Adaptive Nano Membrane II": [10, 5], "Gyrostabilizer II": [10, 6], "Heat Sink II": [10, 2], "Helios": [1, 3], "Modulated Strip Miner II": [10, 3], "Nemesis": [1, 12], "Prospect": [1, 3], "Salvager II": [10, 1], "Small Tractor Beam II": [10, 4], "Taranis": [1, 6]}
#undergoing = {"Nemesis": [1, 21], "Taranis": [1, 4], "100MN Microwarpdrive II": [10, 8], "Modulated Strip Miner II": [10, 4], "Ballistic Control System II": [10, 1]}

ownDict =  readOwnedMats("ownfile.txt")
pDict = readProductionTask("production.txt")



origBpMe =  0.98 # 0.98
origBpFactory = 0.98 #  0.98

compBpMe = 0.90
compBpFactory = 0.98


solo = MineralRequirements(pls, origBpMe, compBpMe, origBpFactory, compBpFactory)

solo.printMats(solo.componentMaterials(pDict,  ownDict)) #  ownDict,   
#solo.printMats(solo.baseMaterials(pDict,  ownDict)) #  ownDict,  




#for i in pDict:
#	total = pDict[i][0] * pDict[i][1]
#	print("{0}\t{1}".format(i, total))