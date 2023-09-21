# PYTHON IMPORTS
from copy import copy
from csv import writer as csv_writer, reader as csv_reader
from datetime import datetime, date
from os.path import isfile, join, split
from pickle import dump, load
from time import mktime, strptime
from functools import cmp_to_key

# ENIGMA IMPORTS
from Components.ActionMap import HelpableActionMap
from Components.config import config, NoSave, ConfigText, ConfigInteger, ConfigDirectory
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from skin import parseColor
from Tools import Notifications
from Screens.LocationBox import defaultInhibitDirs, LocationBox
from Screens.Setup import Setup

# for localized messages
from . import _

CSVFILE = "/tmp/birthdayreminder.csv"
MODULE_NAME = __name__.split(".")[-1]


class BirthdayStore:
	def __init__(self):
		self.loadStore()

	def readRawFile(self):
		data = None
		fileName = config.plugins.birthdayreminder.file.value
		if isfile(fileName):
			try:
				with open(fileName, "r") as f:
					data = f.read()
			except IOError as err:
				(error_no, error_str) = err.args
				print("[%s] ERROR reading from file %s. Error: %s, %s" % (MODULE_NAME, fileName, error_no, error_str))
				text = _("Error reading file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
				Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=3)
		return data

	def writeRawFile(self, data):
		fileName = config.plugins.birthdayreminder.file.value
		try:
			with open(fileName, "w") as f:
				f.write(data)
		except IOError as err:
			(error_no, error_str) = err.args
			print("[%s] ERROR writing to file %s. Error: %s, %s" % (MODULE_NAME, fileName, error_no, error_str))
			text = _("Error writing file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
			Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=3)

	def loadStore(self):  # read the birthday information from file
		fileName = config.plugins.birthdayreminder.file.value
		print("[%s] reading from file %s" % (MODULE_NAME, fileName))
		tmpList = []
		if isfile(fileName):
			try:
				with open(fileName, "rb") as f:
					tmpList = load(f)
			except IOError as err:
				(error_no, error_str) = err.args
				print("[%s] ERROR reading from file %s. Error: %s, %s" % (MODULE_NAME, fileName, error_no, error_str))
				text = _("Error reading file %s.\n\nError: %s, %s") % (fileName, error_no, error_str)
				Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=3)
			print("[%s] read %s birthdays" % (MODULE_NAME, len(tmpList)))
		else:
			print("[%s] File %s not found." % (MODULE_NAME, fileName))
		self.bDayList = tmpList

	def saveStore(self, data=None):  # write the birthday information to file
		fileName = config.plugins.birthdayreminder.file.value
		print("[%s] writing to file %s" % (MODULE_NAME, fileName))
		try:
			with open(fileName, "wb") as f:
				dump(data if data else self.getBirthdayList(), f)
			print("[%s] wrote %s birthdays to %s" % (MODULE_NAME, self.getSize(), fileName))
		except IOError as err:
			(error_no, error_str) = err.args
			print("[%s] ERROR writing to file %s. Error: %s, %s" % (MODULE_NAME, fileName, error_no, error_str))
			text = _("Error writing file %s.\n\nError: %s, %s") % (MODULE_NAME, fileName, error_no, error_str)
			Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=3)

	def getSize(self):  # return the number of birthdays in list
		return len(self.bDayList)

	def getBirthdayList(self):  # return the list of birthdays
		return self.bDayList

	def addEntry(self, entry):  # add a new entry to the list
		self.bDayList.append(entry)
		self.saveStore()

	def removeEntry(self, idx):  # remove an entry from the list
		self.bDayList.pop(idx)
		self.saveStore()

	def updateEntry(self, oldEntry, newEntry):  # update a list entry
		idx = self.bDayList.index(oldEntry)
		self.bDayList[idx] = newEntry
		self.saveStore()

	def getEntry(self, idx):  # get a list entry
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
		self["key_red"] = StaticText(_("Add"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Extras"))
		self["name"] = Label(_("Name"))
		self["birthday"] = Label(_("Birthday"))
		self["age"] = Label(_("Age"))
		self["list"] = BirthdayList(self.birthdaytimer.getBirthdayList())
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
		self.setButtonState()
		self.onLayoutFinish.append(self.cbOnLayoutFinished)

	def cbOnLayoutFinished(self):
		self.setListSorted()

	def exit(self):  # exit the plugin
		self.close()

	def addBirthday(self):  # add a birthday
		self.session.openWithCallback(self.cbAddBirthday, EditBirthdaySetting)

	def editBirthday(self):  # edit a birthday
		selected = self["list"].getCurrent()
		t = strptime(selected[1], "%m/%d/%Y") if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy" else strptime(selected[1], "%d.%m.%Y")
		newDate = date(*t[:3])
		self.bDayBeforeChange = (selected[0], newDate)
		self.session.openWithCallback(self.cbEditBirthday, EditBirthdaySetting, self.bDayBeforeChange)

	def removeBirthday(self):  # remove a birthday?
		selected = self["list"].getCurrent()
		self.session.openWithCallback(self.cbDeleteBirthday, MessageBox, _("Do you really want to delete the entry for %s?") % selected[0], MessageBox.TYPE_YESNO)

	def setButtonState(self):  # set the state of the buttons depending on the list size
		if not self.birthdaytimer.getSize():  # no entries in list
			self["EditActions"].setEnabled(False)
			self["key_green"].setText("")
			self["key_yellow"].setText("")
		else:
			self["EditActions"].setEnabled(True)
			self["key_green"].setText(_("Edit"))
			self["key_yellow"].setText(_("Remove"))

	def openExtras(self):  # open extras menu
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

	def cbAddBirthday(self, name, birthday):  # this callback is called when a birthday was added
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

	def cbEditBirthday(self, name, birthday):  # this callback is called when a birthday was edited
		(oldName, oldBirthday) = self.bDayBeforeChange
		if (name == oldName and birthday == oldBirthday) or (name == None and birthday == None):
			return
		newEntry = (name, birthday)
		self.birthdaytimer.updateEntry(self.bDayBeforeChange, newEntry)
		self.birthdaytimer.updateTimer(self.bDayBeforeChange, newEntry)
		self["list"].updateList(self.birthdaytimer.getBirthdayList())
		self.setListSorted(newEntry=newEntry)

	def cbDeleteBirthday(self, result):  # really delete the selected birthday entry?
		if not result:
			return
		selected = self["list"].getCurrent()
		t = strptime(selected[1], "%m/%d/%Y") if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy" else strptime(selected[1], "%d.%m.%Y")
		newDate = date(*t[:3])
		entry = (selected[0], newDate)
		self.birthdaytimer.removeTimersForEntry(entry)
		idx = self["list"].getIndex()
		self.birthdaytimer.removeEntry(idx)
		self["list"].setList(self.birthdaytimer.getBirthdayList())
		size = self.birthdaytimer.getSize()  # set selection
		if size > 1 and idx < size:
			self["list"].setIndex(idx)
		elif size > 1 and idx >= size:
			self["list"].setIndex(size - 1)
		self.setButtonState()

	def changeSortingUp(self):  # change direction of sorting upwards
		if config.plugins.birthdayreminder.sortby.value == "1":
			config.plugins.birthdayreminder.sortby.value = "3"
		else:
			val = int(config.plugins.birthdayreminder.sortby.value) - 1
			config.plugins.birthdayreminder.sortby.value = str(val)
		config.plugins.birthdayreminder.sortby.save()
		self.setListSorted()

	def changeSortingDown(self):  # change direction of sorting downwards
		if config.plugins.birthdayreminder.sortby.value == "3":
			config.plugins.birthdayreminder.sortby.value = "1"
		else:
			val = int(config.plugins.birthdayreminder.sortby.value) + 1
			config.plugins.birthdayreminder.sortby.value = str(val)
		config.plugins.birthdayreminder.sortby.save()
		self.setListSorted()

	def setListSorted(self, newEntry=None):  # birthday list sorting
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
			self.birthdaytimer.bDayList.sort(key=cmp_to_key(self.compareDates))
		else:  # sort by age
			self["name"].instance.setForegroundColor(parseColor("white"))
			self["birthday"].instance.setForegroundColor(parseColor("white"))
			self["age"].instance.setForegroundColor(parseColor("yellow"))
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
		print("[%s] exporting CSV file %s" % (MODULE_NAME, CSVFILE))
		try:
			with open(CSVFILE, "w") as csvFile:
				writer = csv_writer(csvFile)
				writer.writerows(self.birthdaytimer.getBirthdayList())
			self.session.open(MessageBox, _("Wrote CSV file %s.") % CSVFILE, MessageBox.TYPE_INFO, timeout=3)
		except Exception as err:
			self.session.open(MessageBox, _("Can't write CSV file '%s'. Error: %s") % (CSVFILE, str(err)), MessageBox.TYPE_ERROR, timeout=3)

	def loadCSV(self):
		print("[%s] importing CSV file %s" % (MODULE_NAME, CSVFILE))
		if not isfile(CSVFILE):
			text = _("Can't find CSV file %s!") % CSVFILE
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=3)
			return
		csvList = []
		try:
			with open(CSVFILE, "r") as csvFile:
				reader = csv_reader(csvFile)
				for row in reader:
					name = row[0]
					bDay = row[1]
					if bDay[:4].isdigit() and int(bDay[:4]) < 1910:  # avoid crashes due to E2-problem with mktime() and dates < 1901-12-15'
						bDay = "1910%s" % bDay[4:]
					newDate = date.fromtimestamp(mktime(strptime(bDay, "%Y-%m-%d")))
					entry = (name, newDate)
					csvList.append(entry)
		except IOError as err:
			(error_no, error_str) = err.args
			text = _("Error reading file %s.\n\nError: %s, %s") % (CSVFILE, error_no, error_str)
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=3)
			return
		self.birthdaytimer.bDayList = copy(csvList)  # the critical part is done, now update the lists and timers
		self.birthdaytimer.saveStore()
		self["list"].setList(self.birthdaytimer.getBirthdayList())
		self.setListSorted()
		self.setButtonState()
		self.birthdaytimer.timer_list = []
		self.birthdaytimer.start()
		self.session.open(MessageBox, _("CSV import successful!"), MessageBox.TYPE_INFO, timeout=3)

	def sendListOffer(self):
		print("[%s] broadcasting list offer" % MODULE_NAME)
		self.birthdaytimer.broadcastProtocol.sendBroadcast("offeringList")


class BirthdayList(List):
	def __init__(self, list=None):
		List.__init__(self, list=[])
		self.__list = list

	def setList(self, list):
		self.__list = list
		self.changed((self.CHANGED_ALL,))

	def getList(self):  # some kind of buildFunc replacement :)
		dformat = "%m/%d/%Y" if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy" else "%d.%m.%Y"
		l = []
		if self.__list:
			for entry in self.__list:
				name = entry[0]
				birthday = entry[1].strftime(dformat)
				age = str(getAge(entry[1]))
				l.append((name, birthday, age))
			return l
	list = property(getList, setList)

	def getIndexForEntry(self, entry):
		if self.__list:
			return self.__list.index(entry) if self.master is not None else None


class EditBirthdaySetting(Setup):
	def __init__(self, session, entry=None):
		(name, birthday) = entry if entry is not None else ("", date(*strptime("1.1.1900", "%d.%m.%Y")[:3]))
		config.plugins.birthdayreminder.name = NoSave(ConfigText(default=name, fixed_size=False, visible_width=40))
		config.plugins.birthdayreminder.day = NoSave(ConfigInteger(default=birthday.day, limits=(1, 31)))
		config.plugins.birthdayreminder.month = NoSave(ConfigInteger(default=birthday.month, limits=(1, 12)))
		config.plugins.birthdayreminder.year = NoSave(ConfigInteger(default=birthday.year, limits=(1900, 2050)))
		Setup.__init__(self, session, "EditBirthdaySetting", plugin="Extensions/BirthdayReminder", PluginLanguageDomain="BirthdayReminder")
		self.setTitle(_("Add birthday") if entry is None else _("Edit birthday"))

	def keyCancel(self):
		self.close(None, None)

	def keySave(self):
		try:
			birthdayDt = datetime(config.plugins.birthdayreminder.year.value, config.plugins.birthdayreminder.month.value, config.plugins.birthdayreminder.day.value)
			birthday = datetime.date(birthdayDt)
			self.close(config.plugins.birthdayreminder.name.value, birthday)
		except ValueError:
			self["footnote"].setText(_("Invalid date!"))


class BirthdayReminderSettings(Setup):
	def __init__(self, session, birthdaytimer):
		self.birthdaytimer = birthdaytimer
		path, filename = split(config.plugins.birthdayreminder.file.value)
		self.path = NoSave(ConfigDirectory(default=path))
		self.filename = NoSave(ConfigText(default=filename, visible_width=50, fixed_size=False))
		self.preremind = config.plugins.birthdayreminder.preremind.value
		self.notificationTime = copy(config.plugins.birthdayreminder.notificationTime.value)
		Setup.__init__(self, session, "BirthdayReminderSettings", plugin="Extensions/BirthdayReminder", PluginLanguageDomain="BirthdayReminder")
		self.setTitle(_("Birthday Reminder Settings"))
		self["key_blue"] = StaticText(_("Birthdays"))
		self["blueActions"] = HelpableActionMap(self, ["ColorActions"], {
			"blue": (self.editBirthdays, _("Edit birthdays"))
		}, prio=0)

	def keySelect(self):
		if self.getCurrentItem() == self.path:
			self.session.openWithCallback(self.keySelectCallback, BirthdayReminderLocationBox, initDir=self.path.value)
			return
		Setup.keySelect(self)

	def keySelectCallback(self, path):
		if path is not None:
			path = join(path, "")
			self.path.value = path
		self["config"].invalidateCurrent()
		self.changedEntry()

	def keySave(self):
		config.plugins.birthdayreminder.file.value = join(self.path.value, self.filename.value)
		config.plugins.birthdayreminder.file.save()
		config.plugins.birthdayreminder.file.changed()
		if config.plugins.birthdayreminder.preremind.value != self.preremind:
			if self.preremind == "-1":
				config.plugins.birthdayreminder.preremindChanged.setValue(True)  # there are no preremind timers, add new timers
			else:
				config.plugins.birthdayreminder.preremindChanged.setValue(False)  # change existing preremind timers
		if config.plugins.birthdayreminder.notificationTime.value != self.notificationTime:
			config.plugins.birthdayreminder.notificationTimeChanged.setValue(True)
		Setup.keySave(self)

	def editBirthdays(self):
		self.session.open(BirthdayReminder, self.birthdaytimer)


class BirthdayReminderLocationBox(LocationBox):
	def __init__(self, session, initDir):
		inhibit = defaultInhibitDirs
		inhibit.remove("/etc")
		LocationBox.__init__(self, session, text=_("Select a path for the birthday file"), currDir=join(initDir, ""), inhibitDirs=inhibit,)
		self.skinName = ["WeatherSettingsLocationBox", "LocationBox"]


def getAge(birthday):
	today = date.today()
	try:
		bDay = birthday.replace(year=today.year)  # take care of feb 29th, use feb 28th if necessary
	except ValueError:  # raised on feb 29th
		bDay = birthday.replace(year=today.year, day=birthday.day - 1)
	age = today.year - birthday.year
	return age - 1 if bDay > today else age
