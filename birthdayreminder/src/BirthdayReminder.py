from __future__ import print_function
#
#  Birthday Reminder E2 Plugin
#
#  $Id: BirthdayReminder.py,v 1.0 2011-08-29 00:00:00 Shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#


# PYTHON IMPORTS
from copy import copy
from csv import writer as csv_writer, reader as csv_reader
from datetime import datetime, date
from operator import itemgetter
from os import path as os_path
from os.path import isfile
from pickle import dump as pickle_dump, load as pickle_load
from time import mktime, strptime
from functools import cmp_to_key

# ENIGMA IMPORTS
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.config import config, NoSave, getConfigListEntry, ConfigSubsection, ConfigText, ConfigInteger, ConfigSelection, ConfigDirectory, ConfigClock
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.GUIComponent import GUIComponent
from Components.Label import Label
from Components.MultiContent import MultiContentEntryText
from Components.Sources.List import List
from Components.Sources.Source import Source
from Components.Sources.StaticText import StaticText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Screen import Screen
from skin import parseColor
from Tools import Notifications

# for localized messages
from . import _

CSVFILE = "/tmp/birthdayreminder.csv"


class BirthdayStore:
	def __init__(self):
		self.load()

	def readRawFile(self):
		data = None
		fileName = config.plugins.birthdayreminder.file.value
		if isfile(fileName):
			try:
				f = open(fileName, "r")
				data = f.read()
				f.close()
			except IOError as xxx_todo_changeme:
				(error_no, error_str) = xxx_todo_changeme.args
				print("[Birthday Reminder] ERROR reading from file %s. Error: %s, %s" % (fileName, error_no, error_str))
				text = _("Error reading file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
				Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR)

		return data

	def writeRawFile(self, data):
		fileName = config.plugins.birthdayreminder.file.value
		try:
			f = open(fileName, "wb")
			f.write(data)
			f.close()
		except IOError as xxx_todo_changeme2:
			(error_no, error_str) = xxx_todo_changeme2.args
			print("[Birthday Reminder] ERROR writing to file %s. Error: %s, %s" % (fileName, error_no, error_str))
			text = _("Error writing file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
			Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR)

	# read the birthday information from file
	def load(self):
		fileName = config.plugins.birthdayreminder.file.value
		print("[Birthday Reminder] reading from file", fileName)

		tmpList = []
		if isfile(fileName):
			try:
				f = open(fileName, "rb")
				tmpList = pickle_load(f)
				f.close()
			except IOError as xxx_todo_changeme1:
				(error_no, error_str) = xxx_todo_changeme1.args
				print("[Birthday Reminder] ERROR reading from file %s. Error: %s, %s" % (fileName, error_no, error_str))
				text = _("Error reading file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
				Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR)

			print("[Birthday Reminder] read %s birthdays" % len(tmpList))
		else:
			print("[Birthday Reminder] File %s not found." % fileName)

		self.bDayList = tmpList

	# write the birthday information to file
	def save(self, data=None):
		fileName = config.plugins.birthdayreminder.file.value
		print("[Birthday Reminder] writing to file", fileName)

		try:
			f = open(fileName, "wb")
			if data:
				pickle_dump(data, f)
			else:
				pickle_dump(self.getBirthdayList(), f)
			f.close()
			print("[Birthday Reminder] wrote %s birthdays to %s" % (self.getSize(), fileName))
		except IOError as xxx_todo_changeme3:
			(error_no, error_str) = xxx_todo_changeme3.args
			print("[Birthday Reminder] ERROR writing to file %s. Error: %s, %s" % (fileName, error_no, error_str))
			text = _("Error writing file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
			Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR)

	# return the number of birthdays in list
	def getSize(self):
		return len(self.bDayList)

	# return the list of birthdays
	def getBirthdayList(self):
		return self.bDayList

	# add a new entry to the list
	def addEntry(self, entry):
		self.bDayList.append(entry)
		self.save()

	# remove an entry from the list
	def removeEntry(self, idx):
		self.bDayList.pop(idx)
		self.save()

	# update a list entry
	def updateEntry(self, oldEntry, newEntry):
		idx = self.bDayList.index(oldEntry)
		self.bDayList[idx] = newEntry
		self.save()

	# get a list entry
	def getEntry(self, idx):
		return self.bDayList[idx]


class BirthdayReminder(Screen, HelpableScreen):
	skin = """
		<screen position="center,center" size="560,320" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="name" position="5,45" size="170,25" zPosition="5" valign="center" halign="left" font="Regular;21" transparent="1" foregroundColor="white" />
			<widget name="birthday" position="305,45" size="165,25" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" />
			<widget name="age" position="475,45" size="50,25" zPosition="5" valign="center" halign="right" font="Regular;21" transparent="1" foregroundColor="white" />
			<widget source="list" render="Listbox" position="5,75" size="550,225" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (0, 0), size = (295, 25), font=0, flags = RT_HALIGN_LEFT, text = 0),
							MultiContentEntryText(pos = (300, 0), size = (165, 25), font=0, flags = RT_HALIGN_CENTER, text = 1),
							MultiContentEntryText(pos = (470, 0), size = (50, 25), font=0, flags = RT_HALIGN_RIGHT, text = 2),
						],
					"fonts": [gFont("Regular", 22)],
					"itemHeight": 25
					}
				</convert>
			</widget>
		</screen>""" % _("Birthday Reminder")

	def __init__(self, session, birthdaytimer):
		self.session = session
		self.birthdaytimer = birthdaytimer

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel": (self.exit, _("Exit the plugin")),
		}, -1)

		self["BaseActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.addBirthday, _("Add a birthday")),
			"blue": (self.openExtras, _("Open the extras menu")),
		}, -1)

		# this ActionMap can be enabled/disabled depending on the number of list entries
		self["EditActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green": (self.editBirthday, _("Edit the selected entry")),
			"yellow": (self.removeBirthday, _("Remove the selected entry")),
		}, -1)

		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
		{
			"prevBouquet": (self.changeSortingUp, _("Sorting next")),
			"nextBouquet": (self.changeSortingDown, _("Sorting previous")),
		}, -1)

		self["key_red"] = StaticText(_("Add"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Extras"))

		self["name"] = Label(_("Name"))
		self["birthday"] = Label(_("Birthday"))
		self["age"] = Label(_("Age"))

		self["list"] = BirthdayList(self.birthdaytimer.getBirthdayList())
		self.setButtonState()

		self.onLayoutFinish.append(self.cbOnLayoutFinished)

	def cbOnLayoutFinished(self):
		self.setListSorted()

	# exit the plugin
	def exit(self):
		self.close()

	# add a birthday
	def addBirthday(self):
		self.session.openWithCallback(self.cbAddBirthday, EditBirthdayScreen)

	# edit a birthday
	def editBirthday(self):
		selected = self["list"].getCurrent()

		if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy":
			t = strptime(selected[1], "%m/%d/%Y")
		else:
			t = strptime(selected[1], "%d.%m.%Y")

		newDate = date(*t[:3])
		self.bDayBeforeChange = (selected[0], newDate)
		self.session.openWithCallback(self.cbEditBirthday, EditBirthdayScreen, self.bDayBeforeChange)

	# remove a birthday?
	def removeBirthday(self):
		selected = self["list"].getCurrent()
		self.session.openWithCallback(self.cbDeleteBirthday, MessageBox, _("Do you really want to delete the entry for %s?") % selected[0], MessageBox.TYPE_YESNO)

	# set the state of the buttons depending on the list size
	def setButtonState(self):
		if not self.birthdaytimer.getSize():  # no entries in list
			self["EditActions"].setEnabled(False)
			self["key_green"].setText("")
			self["key_yellow"].setText("")
		else:
			self["EditActions"].setEnabled(True)
			self["key_green"].setText(_("Edit"))
			self["key_yellow"].setText(_("Remove"))

	# open extras menu
	def openExtras(self):
		choiceList = [(_("Export CSV file"), "csvexport"), (_("Import CSV file"), "csvimport"), (_("Distribute birthdays to other Dreamboxes"), "sendListOffer")]
		self.session.openWithCallback(self.cbOpenExtras, ChoiceBox, title=_("What do you want to do?"), list=choiceList)

	def cbOpenExtras(self, result):
		if result == None:
			return
		elif result[1] == "csvexport":
			self.saveCSV()
		elif result[1] == "csvimport":
			self.loadCSV()
		elif result[1] == "sendListOffer":
			self.sendListOffer()

	# this callback is called when a birthday was added
	def cbAddBirthday(self, name, birthday):
		if name == None and birthday == None:
			return

		entry = (name, birthday)
		self.birthdaytimer.addEntry(entry)
		self["list"].setList(self.birthdaytimer.getBirthdayList())
		self.setButtonState()
		self.birthdaytimer.addTimer(entry)
		if config.plugins.birthdayreminder.preremind.value != "-1":
			self.birthdaytimer.addTimer(entry, preremind=True)

		self.setListSorted(newEntry=entry)

	# this callback is called when a birthday was edited
	def cbEditBirthday(self, name, birthday):
		(oldName, oldBirthday) = self.bDayBeforeChange
		if (name == oldName and birthday == oldBirthday) or (name == None and birthday == None):
			return

		newEntry = (name, birthday)
		self.birthdaytimer.updateEntry(self.bDayBeforeChange, newEntry)
		self.birthdaytimer.updateTimer(self.bDayBeforeChange, newEntry)
		self["list"].updateList(self.birthdaytimer.getBirthdayList())

		self.setListSorted(newEntry=newEntry)

	# really delete the selected birthday entry?
	def cbDeleteBirthday(self, result):
		if not result:
			return

		selected = self["list"].getCurrent()

		if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy":
			t = strptime(selected[1], "%m/%d/%Y")
		else:
			t = strptime(selected[1], "%d.%m.%Y")

		newDate = date(*t[:3])
		entry = (selected[0], newDate)
		self.birthdaytimer.removeTimersForEntry(entry)
		idx = self["list"].getIndex()
		self.birthdaytimer.removeEntry(idx)
		self["list"].setList(self.birthdaytimer.getBirthdayList())

		# set selection
		size = self.birthdaytimer.getSize()
		if size > 1 and idx < size:
			self["list"].setIndex(idx)
		elif size > 1 and idx >= size:
			self["list"].setIndex(size - 1)

		self.setButtonState()

	# change direction of sorting upwards
	def changeSortingUp(self):
		if config.plugins.birthdayreminder.sortby.value == "1":
			config.plugins.birthdayreminder.sortby.value = "3"
		else:
			val = int(config.plugins.birthdayreminder.sortby.value) - 1
			config.plugins.birthdayreminder.sortby.value = str(val)

		config.plugins.birthdayreminder.sortby.save()
		self.setListSorted()

	# change direction of sorting downwards
	def changeSortingDown(self):
		if config.plugins.birthdayreminder.sortby.value == "3":
			config.plugins.birthdayreminder.sortby.value = "1"
		else:
			val = int(config.plugins.birthdayreminder.sortby.value) + 1
			config.plugins.birthdayreminder.sortby.value = str(val)

		config.plugins.birthdayreminder.sortby.save()
		self.setListSorted()

	# birthday list sorting
	def setListSorted(self, newEntry=None):
		if not self.birthdaytimer.getSize():
			return

		if config.plugins.birthdayreminder.sortby.value == "1":  # sort by name
			self["name"].instance.setForegroundColor(parseColor("yellow"))
			self["birthday"].instance.setForegroundColor(parseColor("white"))
			self["age"].instance.setForegroundColor(parseColor("white"))
			self.birthdaytimer.bDayList.sort(key=lambda t: tuple(t[0].lower()))
		elif config.plugins.birthdayreminder.sortby.value == "2":  # sort by upcoming birthday
			self["name"].instance.setForegroundColor(parseColor("white"))
			self["birthday"].instance.setForegroundColor(parseColor("yellow"))
			self["age"].instance.setForegroundColor(parseColor("white"))
			#self.birthdaytimer.bDayList.sort(key=itemgetter(1), cmp=self.compareDates)
			self.birthdaytimer.bDayList.sort(key=cmp_to_key(self.compareDates))
		else:  # sort by age
			self["name"].instance.setForegroundColor(parseColor("white"))
			self["birthday"].instance.setForegroundColor(parseColor("white"))
			self["age"].instance.setForegroundColor(parseColor("yellow"))
			#self.birthdaytimer.bDayList.sort(key=itemgetter(1), cmp=self.compareAges)
			self.birthdaytimer.bDayList.sort(key=cmp_to_key(self.compareAges))

		self["list"].setList(self.birthdaytimer.getBirthdayList())

		if newEntry:
			newIdx = self["list"].getIndexForEntry(newEntry)
			self["list"].setIndex(newIdx)

	def compareDates(self, x, y):
		x = x[1]
		y = y[1]
		today = date.today()

		try:
			bDay1 = x.replace(year=today.year)
		except ValueError:  # raised on feb 29th
			bDay1 = x.replace(year=today.year, day=x.day - 1)

		if bDay1 < today:  # next birthday in next year
			try:
				bDay1 = x.replace(year=today.year + 1)
			except ValueError:  # raised on feb 29th
				bDay1 = x.replace(year=today.year + 1, day=x.day - 1)
		ts1 = int(mktime(bDay1.timetuple()))

		try:
			bDay2 = y.replace(year=today.year)
		except ValueError:  # raised on feb 29th
			bDay2 = y.replace(year=today.year, day=y.day - 1)

		if bDay2 < today:  # next birthday in next year
			try:
				bDay2 = y.replace(year=today.year + 1)
			except ValueError:  # raised on feb 29th
				bDay2 = y.replace(year=today.year + 1, day=y.day - 1)
		ts2 = int(mktime(bDay2.timetuple()))

		return ts1 - ts2

	def compareAges(self, x, y):
		x = x[1]
		y = y[1]
		ageX = getAge(x)
		ageY = getAge(y)

		if ageX == ageY:  # ages are the same, sort by birthday
			tX = int(mktime(x.timetuple()))
			tY = int(mktime(y.timetuple()))
			return tX - tY
		else:
			return ageX - ageY

	def saveCSV(self):
		print("[Birthday Reminder] exporting CSV file", CSVFILE)
		try:
			csvFile = open(CSVFILE, "wb")
			writer = csv_writer(csvFile)
			writer.writerows(self.birthdaytimer.getBirthdayList())
			csvFile.close()
			self.session.open(MessageBox, _("Wrote CSV file %s.") % CSVFILE, MessageBox.TYPE_INFO)
		except:
			self.session.open(MessageBox, _("Can't write CSV file %s.") % CSVFILE, MessageBox.TYPE_ERROR)

	def loadCSV(self):
		print("[Birthday Reminder] importing CSV file", CSVFILE)

		if not isfile(CSVFILE):
			text = _("Can't find CSV file %s!") % CSVFILE
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
			return

		try:
			csvFile = open(CSVFILE, "r")
		except IOError as xxx_todo_changeme4:
			(error_no, error_str) = xxx_todo_changeme4.args
			text = _("Error reading file %s.\n\nError: %s, %s") % (CSVFILE, error_no, error_str)
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
			return

		csvList = []
		try:
			reader = csv_reader(csvFile)

			for row in reader:
				name = row[0]
				bDay = row[1]
				t = strptime(bDay, "%Y-%m-%d")
				mt = int(mktime(t))
				newDate = date.fromtimestamp(mt)
				entry = (name, newDate)
				csvList.append(entry)

			csvFile.close()
		except:
			text = _("Can't import CSV data from file %s.") % CSVFILE
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
			return

		# the critical part is done, now update the lists and timers

		self.birthdaytimer.bDayList = copy(csvList)
		self.birthdaytimer.save()
		self["list"].setList(self.birthdaytimer.getBirthdayList())
		self.setListSorted()
		self.setButtonState()

		self.birthdaytimer.timer_list = []
		self.birthdaytimer.start()

		self.session.open(MessageBox, _("CSV import successful!"), MessageBox.TYPE_INFO)

	def sendListOffer(self):
		print("[Birthday Reminder] broadcasting list offer")
		self.birthdaytimer.broadcastProtocol.sendBroadcast("offeringList")


class BirthdayList(List):
	def __init__(self, list=[]):
		List.__init__(self, list=[])
		self.__list = list

	def setList(self, list):
		self.__list = list
		self.changed((self.CHANGED_ALL,))

	# some kind of buildFunc replacement :)
	def getList(self):
		if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy":
			format = "%m/%d/%Y"
		else:
			format = "%d.%m.%Y"

		l = []
		for entry in self.__list:
			name = entry[0]
			birthday = entry[1].strftime(format)
			age = str(getAge(entry[1]))
			l.append((name, birthday, age))
		return l

	list = property(getList, setList)

	def getIndexForEntry(self, entry):
		if self.master is not None:
			return self.__list.index(entry)
		else:
			return None


class EditBirthdayScreen(Screen, ConfigListScreen, HelpableScreen):
	skin = """
		<screen position="center,center" size="560,320" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,45" size="550,235" scrollbarMode="showOnDemand" />
			<widget name="error" position="5,285" size="550,30" zPosition="5" font="Regular;21" transparent="1" halign="center" valign="center" foregroundColor="red" />
		</screen>"""

	def __init__(self, session, entry=None):
		self.session = session
		Screen.__init__(self, session)

		if entry == None:
			self.setTitle(_("Add birthday"))
			config.plugins.birthdayreminder.name = NoSave(ConfigText(default="", fixed_size=False, visible_width=40))
			config.plugins.birthdayreminder.day = NoSave(ConfigInteger(default=1, limits=(1, 31)))
			config.plugins.birthdayreminder.month = NoSave(ConfigInteger(default=1, limits=(1, 12)))
			config.plugins.birthdayreminder.year = NoSave(ConfigInteger(default=1900, limits=(1900, 2050)))
		else:
			self.setTitle(_("Edit birthday"))
			(name, birthday) = entry
			config.plugins.birthdayreminder.name = NoSave(ConfigText(default=name, fixed_size=False, visible_width=40))
			config.plugins.birthdayreminder.day = NoSave(ConfigInteger(default=birthday.day, limits=(1, 31)))
			config.plugins.birthdayreminder.month = NoSave(ConfigInteger(default=birthday.month, limits=(1, 12)))
			config.plugins.birthdayreminder.year = NoSave(ConfigInteger(default=birthday.year, limits=(1900, 2050)))

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["error"] = Label(_("Invalid date!"))
		self["error"].hide()

		list = []
		list.append(getConfigListEntry(_("Name:"), config.plugins.birthdayreminder.name))
		if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy":
			list.append(getConfigListEntry(_("Month:"), config.plugins.birthdayreminder.month))
			list.append(getConfigListEntry(_("Day:"), config.plugins.birthdayreminder.day))
		else:
			list.append(getConfigListEntry(_("Day:"), config.plugins.birthdayreminder.day))
			list.append(getConfigListEntry(_("Month:"), config.plugins.birthdayreminder.month))
		list.append(getConfigListEntry(_("Year:"), config.plugins.birthdayreminder.year))

		ConfigListScreen.__init__(self, list)
		HelpableScreen.__init__(self)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel": (self.cancel, _("Cancel")),
			'ok': (self.ok, _("VirtualKeyBoard")),
		}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.cancel, _("Cancel")),
			"green": (self.accept, _("Accept changes")),
		}, -1)

	# close this screen
	def cancel(self):
		self.close(None, None)

	# open VirtualKeyBoard
	def ok(self):
		text = self["config"].getCurrent()[1].value
		if text == config.plugins.birthdayreminder.name.value:
			title = _("Enter the name of the person:")
			self.session.openWithCallback(self.VirtualKeyBoardCallBack, VirtualKeyBoard, title=title, text=text)
		else:
			pass

	# VirtualKeyBoard callback
	def VirtualKeyBoardCallBack(self, callback):
		try:
			if callback:
				self["config"].getCurrent()[1].value = callback
			else:
				pass
		except:
			pass

	# close the screen if we've got a valid date, otherwise show a warning
	def accept(self):
		try:
			birthdayDt = datetime(config.plugins.birthdayreminder.year.value, config.plugins.birthdayreminder.month.value, config.plugins.birthdayreminder.day.value)
			birthday = datetime.date(birthdayDt)
			self.close(config.plugins.birthdayreminder.name.value, birthday)
		except ValueError:
			self["error"].show()


class BirthdayReminderSettings(Screen, ConfigListScreen, HelpableScreen):
	skin = """
		<screen position="center,center" size="560,320" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,45" size="550,270" scrollbarMode="showOnDemand" />
		</screen>""" % _("Birthday Reminder Settings")

	def __init__(self, session, birthdaytimer):
		self.session = session
		self.birthdaytimer = birthdaytimer
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_blue"] = StaticText(_("Birthdays"))

		path, filename = os_path.split(config.plugins.birthdayreminder.file.value)
		self.path = NoSave(ConfigDirectory(default=path))
		self.filename = NoSave(ConfigText(default=filename, visible_width=50, fixed_size=False))

		list = []
		list.append(getConfigListEntry(_("Path to birthday file:"), self.path))
		list.append(getConfigListEntry(_("Birthday filename:"), self.filename))
		list.append(getConfigListEntry(_("Date format:"), config.plugins.birthdayreminder.dateFormat))
		list.append(getConfigListEntry(_("Remind before birthday:"), config.plugins.birthdayreminder.preremind))
		list.append(getConfigListEntry(_("Notification time:"), config.plugins.birthdayreminder.notificationTime))
		list.append(getConfigListEntry(_("Sort birthdays by:"), config.plugins.birthdayreminder.sortby))
		list.append(getConfigListEntry(_("Show plugin in extensions menu:"), config.plugins.birthdayreminder.showInExtensions))
		list.append(getConfigListEntry(_("Networking port (default: 7374):"), config.plugins.birthdayreminder.broadcastPort))

		ConfigListScreen.__init__(self, list)
		HelpableScreen.__init__(self)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel": (self.cancel, _("Cancel")),
			"ok": (self.keySelect, _("Change path")),
		}, -1)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.cancel, _("Cancel")),
			"green": (self.save, _("Save")),
			"blue": (self.editBirthdays, _("Edit birthdays")),
		}, -1)

		# save the setting value on start for comparison if the user changed it
		self.preremind = config.plugins.birthdayreminder.preremind.value
		self.notificationTime = copy(config.plugins.birthdayreminder.notificationTime.value)

	def keySelect(self):
		text = self["config"].getCurrent()[1].value
		if text == self.path.value:
			self.session.openWithCallback(self.pathSelected, PathSelectionScreen, self.path.value)
		elif text == self.filename.value:
			title = _("Choose the filename:")
			self.session.openWithCallback(self.VirtualKeyBoardCallBack, VirtualKeyBoard, title=title, text=text)
		else:
			pass

	def pathSelected(self, res):
		if res is not None:
			self.path.value = res

	# VirtualKeyBoard callback
	def VirtualKeyBoardCallBack(self, callback):
		try:
			if callback:
				self["config"].getCurrent()[1].value = callback
			else:
				pass
		except:
			pass

	# save the config changes
	def save(self):
		for x in self["config"].list:
			x[1].save()

		config.plugins.birthdayreminder.file.value = os_path.join(self.path.value, self.filename.value)
		config.plugins.birthdayreminder.file.save()
		config.plugins.birthdayreminder.file.changed()

		if config.plugins.birthdayreminder.preremind.value != self.preremind:
			if self.preremind == "-1":
				config.plugins.birthdayreminder.preremindChanged.setValue(True)  # there are no preremind timers, add new timers
			else:
				config.plugins.birthdayreminder.preremindChanged.setValue(False)  # change existing preremind timers

		if config.plugins.birthdayreminder.notificationTime.value != self.notificationTime:
			config.plugins.birthdayreminder.notificationTimeChanged.setValue(True)

		self.close()

	# don't save any config changes
	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def editBirthdays(self):
		self.session.open(BirthdayReminder, self.birthdaytimer)


class PathSelectionScreen(Screen):
	skin = """
		<screen position="center,center" size="560,320" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="target" position="5,45" size="550,30" valign="center" font="Regular;21" />
			<widget name="filelist" position="5,80" size="550,235" scrollbarMode="showOnDemand" zPosition="5" />
		</screen>""" % ("Select a path for the birthday file")

	def __init__(self, session, initDir):
		Screen.__init__(self, session)
		inhibitDirs = ["/bin", "/boot", "/dev", "/tmp", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []

		self["filelist"] = FileList(initDir, showDirectories=True, showFiles=False, inhibitMounts=inhibitMounts, inhibitDirs=inhibitDirs)
		self["target"] = Label(initDir + "/")

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"ok": self.ok,
			"green": self.green,
			"red": self.cancel
		}, -1)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

	def cancel(self):
		self.close(None)

	def green(self):
		self.close(self["filelist"].getSelection()[0])

	def up(self):
		self["filelist"].up()
		self.updateTarget()

	def down(self):
		self["filelist"].down()
		self.updateTarget()

	def left(self):
		self["filelist"].pageUp()
		self.updateTarget()

	def right(self):
		self["filelist"].pageDown()
		self.updateTarget()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateTarget()

	def updateTarget(self):
		currFolder = self["filelist"].getSelection()[0]
		if currFolder is not None:
			self["target"].setText(currFolder)
		else:
			self["target"].setText(_("Invalid Location"))


def getAge(birthday):
	today = date.today()

	# take care of feb 29th, use feb 28th if necessary
	try:
		bDay = birthday.replace(year=today.year)
	except ValueError:  # raised on feb 29th
		bDay = birthday.replace(year=today.year, day=birthday.day - 1)

	age = today.year - birthday.year
	if bDay > today:
		return age - 1
	else:
		return age
