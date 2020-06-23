# -*- coding: utf-8 -*-
# code by GeminiTeam

from __future__ import print_function
from enigma import eTimer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.Pixmap import MultiPixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Console import Console
from Tools.Directories import pathExists, createDir
from Tools.BoundFunction import boundFunction
from Tools.LoadPixmap import LoadPixmap

from Tools.Directories import resolveFilename, SCOPE_SKIN
SkinDefaultPath = resolveFilename(SCOPE_SKIN, "skin_default/")

from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection, NoSave
config.plugins.eparted = ConfigSubsection()

from locale import _
from os import system as os_system, path as os_path, listdir
import six
#from Plugins.Bp.geminimain.gTools import cleanexit

LIST_TYPE_DEV = 0
LIST_TYPE_PAR = 1
LIST_TYPE = 0

DEV_PATH = 1
DEV_SIZE = 2
DEV_TYPE = 3
DEV_NAME = 7

PA_NR = 1
PA_START = 2
PA_END = 3
PA_SIZE = 4
PA_FS = 5
PA_TYPE = 6
PA_NAME = 7

#-----------------------------------------------------------------------------

def getInt_epart(val):
	try:
		return int(float(val[0:-2]))#Einheit abschneiden
	except:
		return 0

def parseCmd(result):
	devlist = []
	try:
		entry = []
		addok = False
		for x in result.split('\n'):
			#if x=="BYT;":#start
			if x.find("BYT;") >= 0:
				addok = True
			elif x == "":#end
				if addok and len(entry):
					devlist.append(entry)
				addok = False
				entry = []
			else:
				if addok and len(x) > 1 and x[len(x) - 1] == ';':
					l = x.split(':')
					if len(l) == 7:#Part
						l.insert(0, LIST_TYPE_PAR)
						l[PA_START] = getInt_epart(l[PA_START])
						l[PA_END] = getInt_epart(l[PA_END])
						l[PA_SIZE] = getInt_epart(l[PA_SIZE])
						l[PA_NAME] = ""
						if l[PA_FS].find("linux-swap") == 0:
							l[PA_FS] = "linux-swap"
						entry.append(l)
					elif len(l) == 8:#Device
						if l[0].find("/dev/mtd") < 0:
							l.insert(0, LIST_TYPE_DEV)
							entry.append(l)
	except:
		print("[eParted] <parse error>")
		return []
	return devlist

def myExecute(cmd, session, test=False):
	if test:
		from time import sleep
		sleep(5)
		result = 0
	else:
		res = os_system(cmd)
		result = (res >> 8)
	print("[eParted]", result, cmd)
	if result != 0 and session is not None:
		session.open(MessageBox, _("Error command '%s'") % cmd, MessageBox.TYPE_ERROR, timeout=8)
	return result
	
def getMountP():
	try:
		mounts = open("/proc/mounts")
	except IOError:
		return []

	lines = mounts.readlines()
	mounts.close()
	return lines

def ismounted(dev):
	for x in getMountP():
		parts = x.strip().split(" ")
		if len(parts) > 1:
			realpath = os_path.realpath(parts[0])
			if realpath == dev:
				return parts[1]
	return None

rereaddevices = False
#-------------------------------------------------------------------------------------

class Ceparted(Screen):
	skin = """<screen position="center,center" size="600,200" title="eParted v0.13">
			<widget name="list" position="5,5" size="590,190" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.Exit,
			"ok": self.Ok
		}, -1)

		self["list"] = MenuList(list=[])
		self.Console = Console()
		global rereaddevices
		rereaddevices = True
		self.__readDev()

	def Ok(self):
		sel = self["list"].getCurrent()
		if sel and sel[1]:
			global rereaddevices
			rereaddevices = False
			self.session.openWithCallback(self.__readDev, Cpart, sel[1])
	
	def __readDev(self):
		global rereaddevices
		if rereaddevices:
			self.Console.ePopen("parted -m -l", self.__FinishedConsole)
		
	def Exit(self):
		self.Console.killAll()
		self.close()
		#cleanexit(__name__)

	def __FinishedConsole(self, result, retval, extra_args=None):
		result = six.ensure_str(result)
		if retval == 0 and '\n' in result:
			list = []
			for x in parseCmd(result):
				if x[0][LIST_TYPE] == LIST_TYPE_DEV:
					name = x[0][DEV_NAME]
					if len(name) == 0:
						name = x[0][DEV_PATH]
					tstr = name
					tstr += "  (%s - %d %s %s)" % (x[0][DEV_SIZE], len(x) - 1, _("partition(s)"), x[0][DEV_PATH])
					list.append((tstr, (name, x[0][DEV_PATH], x[0][DEV_SIZE])))
			self["list"].setList(list)

#-------------------------------------------------------------------------------------

class AddPart(Screen, ConfigListScreen):
	skin = """<screen name="AddPart" position="center,center" size="600,190" title="add Partition" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="5,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" />
			<widget render="Label" source="key_green" position="155,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" />
			<widget name="config" position="5,60" size="590,120" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, maxsize, unit, countpart):
		Screen.__init__(self, session)
		self.session = session
		self.setup_title = _("add partition")

		menu = []
		default = "ext3"
		if pathExists("/sbin/mkfs.ext2"):
			menu.append("ext2")
		if pathExists("/sbin/mkfs.ext3"):
			menu.append("ext3")
		if pathExists("/sbin/mkfs.ext4"):
			menu.append("ext4")
			default = "ext4"
		if pathExists("/sbin/mkfs.xfs"):
			menu.append("xfs")
		if pathExists("/sbin/mkswap"):
			menu.append("linux-swap")
		if pathExists("/sbin/mkfs.vfat"):
			menu.append("fat32")
		if pathExists("/usr/sbin/mkfs.msdos"):
			menu.append("fat16")
		config.plugins.eparted.fs = NoSave(ConfigSelection(default=default, choices=menu))
		config.plugins.eparted.size = NoSave(ConfigInteger(default=maxsize, limits=[1, maxsize]))

		list = []
		if countpart < 4:#nur 4 parts möglich bei primary
			list.append(getConfigListEntry(_("size in %s (max %d %s):") % (unit, maxsize, unit), config.plugins.eparted.size))
		list.append(getConfigListEntry(_("filesystem:"), config.plugins.eparted.fs))
		ConfigListScreen.__init__(self, list, session=session)
		
		self["key_red"] = StaticText(_("cancel"))
		self["key_green"] = StaticText(_("ok"))
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"green": self.keySave,
			"save": self.keySave,
			"ok": self.keySave,
		}, -2)

	def keyCancel(self):
		self.close()
		
	def keySave(self):
		if config.plugins.eparted.size.value > 0:
			self.close((config.plugins.eparted.size.value, config.plugins.eparted.fs.value))

#-------------------------------------------------------------------------------------

class Cpart(Screen):
	PA_TYPE_USE = 1
	PA_TYPE_LAST = 2
	PA_TYPE_FREE = 4

	skin = """<screen position="center,center" size="670,200" title="eParted">
			<widget source="list" render="Listbox" position="0,0" size="670,160" scrollbarMode="showOnDemand" enableWrapAround="on">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos = (0,5), size = (50, 30), font=0, flags = RT_HALIGN_LEFT, text=0),
				MultiContentEntryText(pos = (60,5), size = (150, 30), font=0, flags = RT_HALIGN_LEFT, text=1),
				MultiContentEntryText(pos = (210,5), size = (150, 30), font=0, flags = RT_HALIGN_LEFT, text=2),
				MultiContentEntryText(pos = (360,5), size = (150, 30), font=0, flags = RT_HALIGN_LEFT, text=3),
				MultiContentEntryText(pos = (510,5), size = (160, 30), font=0, flags = RT_HALIGN_LEFT, text=4)
				],
				"fonts": [gFont("Regular", 20)],
				"itemHeight": 35
				}
			</convert>
			</widget>
			<widget name="PixmapRed" position="25,170" size="15,16" pixmaps="skin_default/buttons/button_red_off.png,skin_default/buttons/button_red.png" transparent="1" alphatest="on" />
			<widget name="LabelRed" position="50,160" size="150,40" font="Regular;19" valign="center" />
			<widget name="PixmapGreen" position="225,170" size="15,16" pixmaps="skin_default/buttons/button_green_off.png,skin_default/buttons/button_green.png" transparent="1" alphatest="on" />
			<widget name="LabelGreen" position="250,160" size="150,40" font="Regular;19" valign="center" />
			<widget name="PixmapBlue" position="425,170" size="15,16" pixmaps="skin_default/buttons/button_blue_off.png,skin_default/buttons/button_blue.png" transparent="1" alphatest="on" />
			<widget name="LabelBlue" position="450,160" size="150,40" font="Regular;19" valign="center" />
		</screen>"""

	def __init__(self, session, entry):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.Exit,
			"green": self.KeyGreen,
			"blue": self.KeyBlue,
			"red": self.KeyRed
		}, -1)

		self["list"] = List(list=[])
		self["list"].onSelectionChanged.append(self.__SetLabels)
		self["PixmapRed"] = MultiPixmap()
		self["PixmapGreen"] = MultiPixmap()
		self["PixmapBlue"] = MultiPixmap()
		self["LabelRed"] = Label()
		self["LabelGreen"] = Label()
		self["LabelBlue"] = Label()

		self.__devpath = entry[DEV_PATH]
		self.__fullsize = 0
		self.__old_part_list = []
		self.__new_part_list = []
		self.__comlist = []
		self.__unit = entry[2][len(entry[2]) - 2:]

		self.Console = Console()
		self.__getPartInfo()
		
	def Exit(self):
		self.Console.killAll()
		self.close()
		
	def __getPartInfo(self, val=None):
		self.Console.ePopen("parted -m %s unit %s print" % (self.__devpath, self.__unit), self.__FinishedConsole)
		
	def __Filllist(self):
		list = []
		index = self["list"].getIndex()
		for x in self.__new_part_list:
			if x[LIST_TYPE] == LIST_TYPE_PAR:
				#print(x)
				p0 = "%s: %s" % (_("Nr"), x[PA_NR])
				p1 = "%s: %d%s" % (_("Start"), x[PA_START], self.__unit)
				p2 = "%s: %d%s" % (_("End"), x[PA_END], self.__unit)
				p3 = "%s: %d%s" % (_("Size"), x[PA_SIZE], self.__unit)
				p4 = "%s: %s" % (_("Type"), x[PA_FS])
				list.append((p0, p1, p2, p3, p4, x))
			self["list"].setList(list)
		self["list"].setIndex(index)
		self.__createCommandList()
		
	def __SetLabels(self):
		sel = self["list"].getCurrent()
		self["LabelGreen"].setText("")
		self["LabelRed"].setText("")
		if sel and sel[5]:
			if sel[5][PA_TYPE] & self.PA_TYPE_FREE and len(self.__new_part_list) < 6:
				self["PixmapGreen"].setPixmapNum(1)
				self["LabelGreen"].setText(_("add"))
			else:
				self["PixmapGreen"].setPixmapNum(0)
			if sel[5][PA_TYPE] & self.PA_TYPE_LAST and bool(sel[5][PA_TYPE] & self.PA_TYPE_FREE) == False:
				self["PixmapRed"].setPixmapNum(1)
				self["LabelRed"].setText(_("delete"))
			else:
				self["PixmapRed"].setPixmapNum(0)
				
	def __addFreePart(self, plist, lastPartEnd):
		x = [LIST_TYPE_PAR, str(len(plist)), lastPartEnd, self.__fullsize, 0, _("free"), (self.PA_TYPE_FREE | self.PA_TYPE_LAST), ";"]
		plist.append(x)
		
	def __FinishedConsole(self, result, retval, extra_args=None):
		result = six.ensure_str(result)
		if retval == 0 and '\n' in result:
			tlist = parseCmd(result)
			if len(tlist):
				self.__old_part_list = tlist[0][:]
				self.__new_part_list = tlist[0][:]

			lastPartEnd = 0
			count = 2
			for x in self.__old_part_list:
				if x[LIST_TYPE] == LIST_TYPE_DEV:
					self.__fullsize = getInt_epart(x[DEV_SIZE])
					name = x[DEV_NAME]
					if len(name) == 0:
						name = x[DEV_PATH]
					name += " (%s)" % x[DEV_SIZE]
					self.setTitle(name)
				else:
					lastPartEnd = x[PA_END]
					x[PA_TYPE] = self.PA_TYPE_USE
					if count == len(self.__old_part_list):#is letzte part
						x[PA_TYPE] |= self.PA_TYPE_LAST
					count += 1

			if lastPartEnd < self.__fullsize:#Wenn noch Frei, Part erstellen
				self.__addFreePart(self.__old_part_list, lastPartEnd)
				self.__addFreePart(self.__new_part_list, lastPartEnd)
			
			self.__Filllist()

	def KeyBlue(self):
		if len(self.__comlist):
			self.session.openWithCallback(self.__getPartInfo, Cpartexe, self.__comlist)

	def KeyRed(self):
		sel = self["list"].getCurrent()
		if sel and sel[1] and sel[5][PA_TYPE] & self.PA_TYPE_LAST and bool(sel[5][PA_TYPE] & self.PA_TYPE_FREE) == False:
			try:
				self.__new_part_list.remove(sel[5])#aktuelle part löschen
				for x in self.__new_part_list:
					if x[LIST_TYPE] == LIST_TYPE_PAR:
						if x[PA_TYPE] & self.PA_TYPE_FREE:#letzte Freie suchen und auch löschen
							self.__new_part_list.remove(x)
							break
						else:
							x[PA_TYPE] = self.PA_TYPE_USE
				
				lastPartEnd = 0
				if len(self.__new_part_list) > 1:#von letzter Part, TYp setzen und Ende ermitteln
					self.__new_part_list[len(self.__new_part_list) - 1][PA_TYPE] = self.PA_TYPE_USE | self.PA_TYPE_LAST
					lastPartEnd = self.__new_part_list[len(self.__new_part_list) - 1][PA_END]
				
				if lastPartEnd < self.__fullsize:#Wenn noch Frei, Part erstellen
					self.__addFreePart(self.__new_part_list, lastPartEnd)
				#for x in self.__new_part_list:
				#	if x[LIST_TYPE]==LIST_TYPE_PAR:
				#		print(x)
			except:
				print("[eParted] <remove part>")
			self.__Filllist()
			
	def KeyGreen(self):
		sel = self["list"].getCurrent()
		if sel and sel[5] and sel[5][PA_TYPE] & self.PA_TYPE_FREE and sel[5][PA_START] < sel[5][PA_END] and len(self.__new_part_list) < 6:
			self.session.openWithCallback(self.__CallbackAddPart, AddPart, sel[5][PA_END] - sel[5][PA_START], self.__unit, len(self.__new_part_list) - 1)
			
	def __CallbackAddPart(self, val=None):
		if val:
			for x in self.__new_part_list:
				if x[LIST_TYPE] == LIST_TYPE_PAR:
					if x[PA_TYPE] & self.PA_TYPE_FREE:
						x[PA_SIZE] = val[0]
						x[PA_FS] = val[1]
						x[PA_END] = x[PA_START] + x[PA_SIZE]
						x[PA_TYPE] = self.PA_TYPE_USE | self.PA_TYPE_LAST
						if x[PA_END] < self.__fullsize:#Wenn noch Frei, Part erstellen
							self.__addFreePart(self.__new_part_list, x[PA_END])
						break
					else:
						x[PA_TYPE] = self.PA_TYPE_USE
			self.__Filllist()
			
	def __addPart2Comlist(self, list, val, mkpart=True):
		#print(val)
		partnr = val[PA_NR]
		if mkpart:
			fs = val[PA_FS]
			com = "parted -s -a optimal %s mkpart primary %s %s%s %s%s" % (self.__devpath, fs, val[PA_START], self.__unit, val[PA_END], self.__unit)
			list.append((com, _("create partition %s") % partnr, None))
		
		mountdev = None
		if val[PA_FS] == "linux-swap":
			mkfs = "/sbin/mkswap"
		elif val[PA_FS] == "fat16":
			mkfs = "/usr/sbin/mkfs.msdos -F 16"
		elif val[PA_FS] == "fat32":
			mkfs = "/sbin/mkfs.vfat"
		else:
			mkfs = "/sbin/mkfs." + val[PA_FS]
			mountdev = self.__devpath + partnr
			if val[PA_FS] == "xfs":
				mkfs += " -f"

		com = "%s %s%s" % (mkfs, self.__devpath, partnr)
		list.append((com, _("make filesystem '%s' on partition %s (%d %s)") % (val[PA_FS], partnr, val[PA_SIZE], self.__unit), mountdev))
		
	def __delPart2Comlist(self, list, val):
		partnr = val[PA_NR]
		dev = "%s%s" % (self.__devpath, partnr)
		mp = ismounted(dev)
		if mp is not None:
			if myExecute("umount %s" % mp, self.session):
				return
		list.insert(0, ("parted -s -a none %s rm %s" % (self.__devpath, partnr), _("delete partition %s") % partnr, None))

	def __createCommandList(self):
		self.__comlist = []
		#welche parts sollen gelöscht werden
		for x in list(range(len(self.__old_part_list))):
			if self.__old_part_list[x][LIST_TYPE] == LIST_TYPE_PAR:
				if bool(self.__old_part_list[x][PA_TYPE] & self.PA_TYPE_FREE) == False:
					if len(self.__new_part_list) > x:
						if self.__old_part_list[x][PA_SIZE] != self.__new_part_list[x][PA_SIZE]:
							#print self.__old_part_list[x], self.__new_part_list[x]
							self.__delPart2Comlist(self.__comlist, self.__old_part_list[x])
					else:
						self.__delPart2Comlist(self.__comlist, self.__old_part_list[x])

		#welche parts sollen erstellt werden
		for x in list(range(len(self.__new_part_list))):
			if self.__new_part_list[x][LIST_TYPE] == LIST_TYPE_PAR:
				if bool(self.__new_part_list[x][PA_TYPE] & self.PA_TYPE_FREE) == False:
					if len(self.__old_part_list) > x and bool(self.__old_part_list[x][PA_TYPE] & self.PA_TYPE_FREE) == False:
						if self.__new_part_list[x][PA_SIZE] != self.__old_part_list[x][PA_SIZE]:
							#print self.__new_part_list[x], self.__old_part_list[x]
							self.__addPart2Comlist(self.__comlist, self.__new_part_list[x])
						else:
							if self.__new_part_list[x][PA_FS] != self.__old_part_list[x][PA_FS]:
								self.__addPart2Comlist(self.__comlist, self.__new_part_list[x], False)
					else:
						self.__addPart2Comlist(self.__comlist, self.__new_part_list[x])
		

		#for x in self.__comlist: print "[eParted] com =",x
		if len(self.__comlist):
			self["PixmapBlue"].setPixmapNum(1)
			self["LabelBlue"].setText(_("execute"))
		else:
			self["PixmapBlue"].setPixmapNum(0)
			self["LabelBlue"].setText("")

class Cpartexe(Screen):
	skin = """<screen position="center,center" size="670,400" title=" ">
			<widget source="list" render="Listbox" position="0,0" size="670,360" scrollbarMode="showOnDemand" enableWrapAround="on">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos = (40,5), size = (630, 30), font=0, flags = RT_HALIGN_LEFT, text=0),
				MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (35,35), png=1),
				],
				"fonts": [gFont("Regular", 22)],
				"itemHeight": 40
				}
			</convert>
			</widget>
			<widget name="PixmapButton" position="25,370" size="15,16" pixmaps="skin_default/buttons/button_green.png,skin_default/buttons/button_green_off.png" transparent="1" alphatest="on" />
			<widget name="LabelButton" position="50,360" size="620,40" font="Regular;19" valign="center" />
		</screen>"""

	def __init__(self, session, comlist):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.Exit,
			"green": self.KeyGreen,
			#"red": self.KeyRed
		}, -1)

		self.setTitle(_("execute"))
		self["PixmapButton"] = MultiPixmap()
		self["LabelButton"] = Label(_("Start") + " ?")

		self.mountlist = []
		list = []
		for x in comlist:
			print(x)
			list.append((x[1], None, x[0]))
			if x[2] is not None:
				self.mountlist.append(x[2])
		self["list"] = List(list)
		
		self.__Stimer = eTimer()
		self.__Stimer.callback.append(self.__exeList)
		self.__state = -1
		
	def __getPartitionUUID(self, device):
		try:
			if os_path.exists("/dev/disk/by-uuid"):
				for uuid in listdir("/dev/disk/by-uuid/"):
					if not os_path.exists("/dev/disk/by-uuid/" + uuid):
						return None
					if os_path.realpath("/dev/disk/by-uuid/" + uuid) == device:
						return ("/dev/disk/by-uuid/" + uuid, uuid)
			else:
				return (device, device[5:])
		except:
			print("[eParted] <error get UUID>")
		return None
		
	def __mountDevice(self):
		for x in self.mountlist:
			dev = self.__getPartitionUUID(x)
			if dev is not None:
				if os_path.exists("/media/" + dev[1]) == False:
					createDir("/media/" + dev[1], True)
				cmd = "mount %s /media/%s" % (dev[0], dev[1])
				myExecute(cmd, None)

	def Exit(self):
		if self.__state < 0:
			del self.__Stimer
			self.__mountDevice()
			self.close()
		
	def __exeList(self):
		if len(self["list"].list) > self.__state and self.__state > -1:
			res = myExecute(self["list"].list[self.__state][2], self.session)
			pic = "test_false.png"
			if res == 0:
				pic = "test_true.png"

			self["list"].list[self.__state] = (self["list"].list[self.__state][0], LoadPixmap(path=SkinDefaultPath + pic), self["list"].list[self.__state][2], self["list"].list[self.__state][2])
			self["list"].updateList(self["list"].list)
			self["list"].setIndex(self.__state)
			
			if res == 0:
				self.__state += 1
			else:
				self.__state = len(self["list"].list)#bei fehler ans Ende der liste
				self["PixmapButton"].setPixmapNum(0)
				self["LabelButton"].setText(_("quit"))
				
			self.__Stimer.start(500, True)
		else:
			self.__state = -2
			self["PixmapButton"].setPixmapNum(0)
			self["LabelButton"].setText(_("quit"))
		
	def KeyGreen(self):
		if self.__state == -1:
			global rereaddevices
			rereaddevices = True
			self.__state += 1
			self["PixmapButton"].setPixmapNum(1)
			self["LabelButton"].setText(_("Please Wait"))
			self["list"].setIndex(0)
			self.__Stimer.start(500, True)
		elif self.__state == -2:
			self.Exit()
	
	#def KeyRed(self):
	#	self.Exit()
