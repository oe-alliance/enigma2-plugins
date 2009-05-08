Version = '$Header$';

from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from Components.config import config
from enigma import eServiceReference

from re import sub
from time import strftime, localtime, time

class WAPfunctions(Source):
	LISTTIME = 0
	REPEATED = 1
	SERVICELIST = 2
	OPTIONLIST = 3
	FILLVALUE = 4
	LOCATIONLIST = 5
	TAGLIST = 6
	DELETEOLD = 7
	
	lut = {	"Name":0,
			"Value":1,
			"Selected":2
	}
	
	def __init__(self, session, func=LISTTIME):
		self.func = func
		Source.__init__(self)		
		self.session = session
		self.result = ["unknown command (%s)" % self.func]

	def handleCommand(self, cmd):
		print "WAPfunctions: handleCommand", cmd
		if self.func is self.LISTTIME:
			self.result = self.fillListTime(cmd)
		elif self.func is self.REPEATED:
			self.result = self.fillRepeated(cmd)
		elif self.func is self.SERVICELIST:
			self.result = self.serviceList(cmd)
		elif self.func is self.OPTIONLIST:
			self.result = self.fillOptionList(cmd)
		elif self.func is self.FILLVALUE:
			self.result = self.fillValue(cmd)
		elif self.func is self.LOCATIONLIST:
			self.result = self.locationList(cmd)
		elif self.func is self.TAGLIST:
			self.result = self.tagList(cmd)
		elif self.func is self.DELETEOLD:
			self.result = self.deleteOldSaved(cmd)
		else:
			self.result = ["unknown command cmd(%s) self.func(%s)" % (cmd, self.func)]

	def fillListTime(self, param):
		print "fillListTime", param
		
		input = 0
		start = 1
		end = 1
		
		timeNow = time()
		timePlusTwo = timeNow + 7200

		if param.has_key('begin'):
			begin = param['begin'] or 0
			begin = int(begin)
			del param['begin']
			if begin > 0:
				timeNow = begin
		if param.has_key('end'):
			end = param['end'] or 0
			end = int(end)
			del param['end']
			if end > 0:
				timePlusTwo = end
		
		t = {}
		t["sday"] = t["day"] = strftime("%d", localtime(timeNow))
		t["smonth"] = t["month"] = strftime("%m", localtime(timeNow))
		t["syear"] = t["year"] = strftime("%Y", localtime(timeNow))
		t["smin"] = strftime("%M", localtime(timeNow))
		t["shour"] = strftime("%H", localtime(timeNow))
		t["emin"] = strftime("%M", localtime(timePlusTwo))
		t["ehour"] = strftime("%H", localtime(timePlusTwo))
		
		key = ""
		for i in param:
			p = str(i)
			if p != "sRef" and param[p] != None:
				key = p

		if key == "smin" or key == "emin" :
			start = 0
			end = 59
		elif key == "shour" or key == "ehour":
			start = 1
			end = 24
		elif key == "day" or key == "sday":
			start = 1
			end = 31
		elif key == "month" or key == "smonth":
			start = 1
			end = 12
		else:
			start = int(t[key])
			end = int(t[key]) + 2
		
		if param[key] == "now" or param[key] == "end" or param[key] == "begin":
			input = int(t[key])
		else:
			input = param[key] or 0
			input = int(input)
		
		self.result = self.fillOptionListAny(input, start, end)
		return self.result
	
	def fillOptionListAny(self, input, start, end):
		returnList = []
		for i in range(start, end + 1, 1):
			returnList1 = []
			j = str(i)
			if len(j) == 1:
				j = "0%s" % j
			returnList1.append(j)
			returnList1.append(i)
			if i == input:
				returnList1.append("selected")
			else:
				returnList1.append("")
			returnList.append(returnList1)
		return returnList
		
	def fillRepeated(self, param):
		print "fillRepeated", param
		repeated = param or 0
		repeated = int(repeated)
		
		self.lut = {"Name":0
			, "Value":1
			, "Description":2
			, "Selected":3
		}
		
		mo = ["mo", 	1, "Mo "]#"Monday"]
		tu = ["tu", 	2, "Tu "]#"Tuesday"]
		we = ["we", 	4, "We "]#"Wednesday"]
		th = ["th", 	8, "Th "]#"Thursday"]
		fr = ["fr", 16, "Fr "]#"Friday"]
		sa = ["sa", 32, "Sa "]#"Saturday"]
		su = ["su", 64, "Su "]#"Sunday"]
		mf = ["mf", 31, "Mo-Fr"]
		ms = ["ms", 127, "Mo-Su"]
		
		if repeated == 127:
			repeated = repeated - 127
			ms.append("checked")
		else:
			ms.append("")
		
		if repeated >= 64:
			repeated = repeated - 64
			su.append("checked")
		else:
			su.append("")
		
		if repeated >= 32:
			repeated = repeated - 32
			sa.append("checked")
		else:
			sa.append("")
		
		if repeated == 31:
			repeated = repeated - 31
			mf.append("checked")
		else:
			mf.append("")

		if repeated >= 16:
			repeated = repeated - 16
			fr.append("checked")
		else:
			fr.append("")

		if repeated >= 8:
			repeated = repeated - 8
			th.append("checked")
		else:
			th.append("")
		
		if repeated >= 4:
			repeated = repeated - 4
			we.append("checked")
		else:
			we.append("")
		
		if repeated >= 2:
			repeated = repeated - 2
			tu.append("checked")
		else:
			tu.append("")
		
		if repeated == 1:
			repeated = repeated - 1
			mo.append("checked")
		else:
			mo.append("")
			
		returnList = []
		returnList.append(mo)
		returnList.append(tu)
		returnList.append(we)
		returnList.append(th)
		returnList.append(fr)
		returnList.append(sa)
		returnList.append(su)
		returnList.append(mf)
		returnList.append(ms)

		return returnList
	
	def serviceListOne(self, bouquet, selref):
		ref = eServiceReference(bouquet)
		self.servicelist = ServiceList(ref, command_func=self.getServiceList, validate_commands=False)
		self.servicelist.setRoot(ref)
		returnList = []
		for (ref2, name) in self.servicelist.getServicesAsList():
			print "ref2: (", ref2, ") name: (", name, ")"
			returnListPart = []
			returnListPart.append(name)
			returnListPart.append(ref2)
			if ref2 == str(selref):
				returnListPart.append("selected")
				self.sRefFound = 1
			else:
				returnListPart.append("")
			returnList.append(returnListPart)
		return returnList

	def serviceList(self, param):
		print "serviceList: ", param
		sRef = str(param["sRef"])
		bouquet = str(param["bouquet"])
		self.sRefFound = 0
		
		if bouquet == '':
			returnList = []
			bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
			ref = eServiceReference(bouquet)
			self.servicelist = ServiceList(ref, command_func=self.getServiceList, validate_commands=False)
			self.servicelist.setRoot(ref)
			for (ref2, name) in self.servicelist.getServicesAsList():
				part = self.serviceListOne(ref2, sRef)
				if part:
					returnList = returnList + [["-- " + name + " --", "<" + name + ">", ""]] + part
			bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.radio" ORDER BY bouquet'
			ref = eServiceReference(bouquet)
			self.servicelist = ServiceList(ref, command_func=self.getServiceList, validate_commands=False)
			self.servicelist.setRoot(ref)
			for (ref2, name) in self.servicelist.getServicesAsList():
				part = self.serviceListOne(ref2, sRef)
				if part:
					returnList = returnList + [["-- " + name + " --", "<" + name + ">", ""]] + part
		else:
			returnList = self.serviceListOne(bouquet, sRef)

		if self.sRefFound == 0 and sRef != '':
			returnListPart = ["Inserted", sRef, "selected"]
			returnList = [returnListPart] + returnList
		#print returnList
		return returnList

	def getServiceList(self, ref):
		self.servicelist.root = ref

	def locationList(self, param):
		print "locationList", param
		dirname = param
		lst = config.movielist.videodirs.value
		if not dirname:
			dirname = "/hdd/movie/"
		if not dirname in lst:
			lst = [dirname] + lst
		returnList = [[lst[i], i, dirname == lst[i] and "selected" or ""] for i in range(len(lst))]
		return returnList

	def tagList(self, param):
		print "tagList", param
		tag = param
		try:
			file = open("/etc/enigma2/movietags")
			taglist = [x.rstrip() for x in file.readlines()]
			while "" in taglist:
				taglist.remove("")
			file.close()
		except IOError, ioe:
			taglist = []
		if not tag in taglist:
			taglist = [tag] + taglist
		if not "" in taglist:
			taglist.append("")
		returnList = [[taglist[i], i, tag == taglist[i] and "selected" or ""] for i in range(len(taglist))]
		return returnList

	def fillOptionList(self, param):
		print "fillOptionList", param
		returnList = []
		if param.has_key("justplay"):
			number = param["justplay"] or 0
			number = int(number)
			returnList.append(["Record", 0, number == 0 and "selected" or ""])
			returnList.append(["Zap", 1, number == 1 and "selected" or ""])
		elif param.has_key("afterevent"):
			number = param["afterevent"] or 0
			number = int(number)
			returnList.append(["Nothing", 0, number == 0 and "selected" or ""])
			returnList.append(["Standby", 1, number == 1 and "selected" or ""])
			returnList.append(["Deepstandby/Shutdown", 2, number == 2 and "selected" or ""])
			returnList.append(["Auto", 3, number == 3 and "selected" or ""])
		return returnList
	
	def deleteOldSaved(self, param):
		print "deleteOldSaved", param
		returnList = []
		returnList.append(["deleteOldOnSave", param["deleteOldOnSave"], ""])
		returnList.append(["command", param["command"], ""])
		if int(param["deleteOldOnSave"]) == 1:
			returnList.append(["channelOld", param["sRef"], ""])
			returnList.append(["beginOld", param["begin"], ""])
			returnList.append(["endOld", param["end"], ""])
		return returnList
			
	
	def fillValue(self, param):
		print "fillValue: ", param
		return [["", param, ""]]

	def getText(self):
		(result, text) = self.result
		return text
	
	def filterXML(self, item):
		item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;")
		return item

	def getList(self):
		return self.result

	text = property(getText)
	list = property(getList)
