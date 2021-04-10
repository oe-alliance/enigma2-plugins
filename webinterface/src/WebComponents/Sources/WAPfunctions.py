Version = '$Header$'

from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_CONFIG, SCOPE_HDD
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
		self.result = ("unknown command (%s)" % (self.func), )

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
			self.result = ("unknown command cmd(%s) self.func(%s)" % (cmd, self.func), )

	def fillListTime(self, param):
		print "fillListTime", param

		input = 0
		start = 1
		end = 1

		timeNow = time()
		timePlusTwo = timeNow + 7200

		if 'begin' in param:
			begin = param['begin'] or 0
			begin = int(begin)
			del param['begin']
			if begin > 0:
				timeNow = begin
		if 'end' in param:
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

		if key == "smin" or key == "emin":
			start = 0
			end = 59
		elif key == "shour" or key == "ehour":
			start = 0
			end = 23
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
			returnList1.extend((j, i))
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

		self.lut = {"Name":0			, "Value":1			, "Description":2			, "Selected":3
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

		return [
			mo,
			tu,
			we,
			th,
			fr,
			sa,
			su,
			mf,
			ms,
		]

	def serviceListOne(self, bouquet, selref):
		ref = eServiceReference(bouquet)
		self.servicelist = ServiceList(ref, command_func=self.getServiceList, validate_commands=False)
		self.servicelist.setRoot(ref)
		returnList = []
		for (ref2, name) in self.servicelist.getServicesAsList():
			print "ref2: (", ref2, ") name: (", name, ")"
			returnListPart = [
				name,
				ref2
			]
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
			dirname = resolveFilename(SCOPE_HDD)
		if not dirname in lst:
			lst = [dirname] + lst
		returnList = [[lst[i], i, dirname == lst[i] and "selected" or ""] for i in range(len(lst))]
		return returnList

	def tagList(self, param):
		print "tagList", param
		tag = param
		try:
			file = open(resolveFilename(SCOPE_CONFIG, "movietags"))
			taglist = [x.rstrip() for x in file]
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
		if "justplay" in param:
			number = param["justplay"] or 0
			number = int(number)
			return (
				("Record", 0, number == 0 and "selected" or ""),
				("Zap", 1, number == 1 and "selected" or "")
			)
		elif "afterevent" in param:
			number = param["afterevent"] or 0
			number = int(number)
			return (
				("Nothing", 0, number == 0 and "selected" or ""),
				("Standby", 1, number == 1 and "selected" or ""),
				("Deepstandby/Shutdown", 2, number == 2 and "selected" or ""),
				("Auto", 3, number == 3 and "selected" or "")
			)
		else:
			return ()

	def deleteOldSaved(self, param):
		print "deleteOldSaved", param
		returnList = [
			("deleteOldOnSave", param["deleteOldOnSave"], ""),
			("command", param["command"], "")
		]
		if int(param["deleteOldOnSave"]) == 1:
			returnList.extend((
				("channelOld", param["sRef"], ""),
				("beginOld", param["begin"], ""),
				("endOld", param["end"], "")
			))
		return returnList

	def fillValue(self, param):
		print "fillValue: ", param
		return (("", param, ""),)

	def getText(self):
		(result, text) = self.result
		return text

	def filterXML(self, item):
		item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;")
		return item

	text = property(getText)
	list = property(lambda self: self.result)
