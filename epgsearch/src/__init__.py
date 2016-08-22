# -*- coding: utf-8 -*-
from Components.Language import language
from Components.NimManager import nimmanager
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from boxbranding import getImageDistro
from enigma import eServiceReference, eServiceCenter
import os, gettext

# Config
from Components.config import config, configfile, ConfigSet, ConfigSubsection, ConfigSelection, ConfigNumber, ConfigYesNo, ConfigSatlist

PluginLanguageDomain = "EPGSearch"
PluginLanguagePath = "Extensions/EPGSearch/locale"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.showinplugins = ConfigYesNo(default = False)
__searchDefaultScope = "currentbouquet" if getImageDistro() in ("easy-gui-aus", "beyonwiz") else "all"
config.plugins.epgsearch.scope = ConfigSelection(choices=[("all", _("all services")), ("allbouquets", _("all bouquets")), ("currentbouquet", _("current bouquet")), ("currentservice", _("current service")), ("ask", _("ask user"))], default=__searchDefaultScope)
config.plugins.epgsearch.defaultscope = ConfigSelection(choices=[("all", _("all services")), ("allbouquets", _("all bouquets")), ("currentbouquet", _("current bouquet")), ("currentservice", _("current service"))], default=__searchDefaultScope)
config.plugins.epgsearch.search_type = ConfigSelection(default = "partial", choices = [("partial", _("partial match")), ("exact", _("exact match")), ("start", _("title starts with"))])
config.plugins.epgsearch.search_case = ConfigSelection(default = "insensitive", choices = [("insensitive", _("case-insensitive search")), ("sensitive", _("case-sensitive search"))])
allowShowOrbital = getImageDistro() not in ("easy-gui-aus", "beyonwiz")
config.plugins.epgsearch.showorbital = ConfigYesNo(default = allowShowOrbital)
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.encoding = ConfigSelection(choices = ['UTF-8', 'ISO8859-15'], default = 'UTF-8')
config.plugins.epgsearch.history_length = ConfigNumber(default = 10)
config.plugins.epgsearch.add_search_to_epg = ConfigYesNo(default = True)

orbposDisabled = 3600

def getNamespaces(namespaces):
	lamedbServices = eServiceReference("1:7:1:0:0:0:0:0:0:0:" + " || ".join(map(lambda x: '(satellitePosition == %d)' % (x >> 16), namespaces)))
	hasNamespaces = set()
	if not namespaces:
		return hasNamespaces
	serviceHandler = eServiceCenter.getInstance()
	servicelist = serviceHandler.list(lamedbServices)
	if servicelist is not None:
		serviceIterator = servicelist.getNext()
		while serviceIterator.valid():
			ns = serviceIterator.getUnsignedData(4)
			if ns not in hasNamespaces and ns in namespaces:
				hasNamespaces.add(ns)
				if len(hasNamespaces) == len(namespaces):
					return hasNamespaces
			serviceIterator = servicelist.getNext()
	return hasNamespaces

def orbposChoicelist():
	choiceList = [(orbposDisabled, _('disabled'), 0)]
	nsDVBT = 0xeeee << 16
	nsDVBC = 0xffff << 16
	namespaces = set()
	if nimmanager.hasNimType("DVB-T") and nimmanager.terrestrialsList:
		namespaces.add(nsDVBT)
	if nimmanager.hasNimType("DVB-C") and nimmanager.cablesList:
		namespaces.add(nsDVBC)
	hasNamespaces = getNamespaces(namespaces)
	if nsDVBT in hasNamespaces:
		choiceList.append((nsDVBT >> 16, _('DVB-T Terrestrial services'), 0))
	if nsDVBC in hasNamespaces:
		choiceList.append((nsDVBC >> 16, _('DVB-C Cable services'), 0))
	choiceList += [
		(orbpos, nimmanager.getSatDescription(orbpos), 0)
		for orbpos in sorted(
			nimmanager.getConfiguredSats(),
			key=lambda x: x if x <= 1800 else x - 3600
		)
	]
	return choiceList

def isOrbposName(name):
	return name.startswith("orbpos") and name[6:].isdigit()

def doSave():
	saveFile = False
	for name, confItem in config.plugins.epgsearch.dict().iteritems():
		if (name == "numorbpos" or isOrbposName(name)) and confItem.isChanged():
			saveFile = True
			confItem.save()
	if saveFile:
		configfile.save()

def unusedOrbPosConfList():
	numorbpos = int(config.plugins.epgsearch.numorbpos.value)
	return [
		item for item in config.plugins.epgsearch.dict().iteritems()
		if isOrbposName(item[0]) and int(item[0][6:]) >= numorbpos
	]

def initOrbposConfigs():
	choiceList = orbposChoicelist()
	maxEntries = len(choiceList)
	oldVal = config.plugins.epgsearch.getSavedValue().get('numorbpos')
	listShrank = oldVal is not None and int(oldVal) > maxEntries
	choices = [str(i) for i in range(maxEntries + 1)]
	config.plugins.epgsearch.numorbpos = ConfigSelection(choices, default="1")
	if listShrank:
		config.plugins.epgsearch.numorbpos.value = str(maxEntries)

	# If the list got smaller, try to preserve the values of as
	# many entries as possible in the new list.
	orbPosList = []
	for name in (name for name in config.plugins.epgsearch.getSavedValue().keys() if isOrbposName(name)):
		setattr(config.plugins.epgsearch, name, ConfigSatlist(choiceList, default=orbposDisabled))
		if listShrank:
			orbPosList.append((getattr(config.plugins.epgsearch, name), int(name[6:])))
	if orbPosList:
		orbPosList.sort(key=lambda x: x[1])
		orbPosList.sort(key=lambda x: int(x[0].value) == orbposDisabled)
		for i in range(min(maxEntries, len(orbPosList))):
			getattr(config.plugins.epgsearch, "orbpos" + str(i)).value = orbPosList[i][0].value

def updateOrbposConfig(save=False):
	choiceList = orbposChoicelist()
	updateNumOrbpos(choiceList, save)
	setChoiceList = None
	# Add any new items & update any existing ones
	for filt in range(int(config.plugins.epgsearch.numorbpos.value)):
		name = "orbpos" + str(filt)
		if hasattr(config.plugins.epgsearch, name):
			if setChoiceList is None:
				setChoiceList = [(str(orbpos), desc) for (orbpos, desc, flags) in choiceList]
			confItem = getattr(config.plugins.epgsearch, name)
			confItem.setChoices(setChoiceList, default=str(orbposDisabled))
		else:
			setattr(config.plugins.epgsearch, name, ConfigSatlist(choiceList, default=orbposDisabled))
	if save:
		doSave()
	return len(choiceList)

# Set old items to default so that they will disappear from the settings file
def purgeOrbposConfig():
	for name, confItem in unusedOrbPosConfList():
		if confItem.value != confItem.default:
			confItem.value = confItem.default
	doSave()

def updateUnusedOrbposConfig(choiceList, save):
	setChoiceList = [(str(orbpos), desc) for (orbpos, desc, flags) in choiceList]
	for name, confItem in unusedOrbPosConfList():
		confItem.setChoices(setChoiceList, default=str(orbposDisabled))
	if save:
		doSave()

def getOrbposConfList(includeDisabled=False):
	return [
		getattr(config.plugins.epgsearch, "orbpos" + str(filt))
		for filt in range(int(config.plugins.epgsearch.numorbpos.value))
		if (
			includeDisabled or
			getattr(config.plugins.epgsearch, "orbpos" + str(filt)).orbital_position != orbposDisabled
		)
	]

def updateNumOrbpos(choiceList, save):
	maxEntries = max(len(choiceList) - 1, 0)
	oldVal = int(config.plugins.epgsearch.numorbpos.value)
	choices = [str(i) for i in range(maxEntries + 1)]
	oldMax = len(config.plugins.epgsearch.numorbpos.choices) - 1
	if oldVal > maxEntries:
		config.plugins.epgsearch.numorbpos.value = str(maxEntries)
	config.plugins.epgsearch.numorbpos.setChoices(choices, default="1")
	updateUnusedOrbposConfig(choiceList, save)

initOrbposConfigs()
updateOrbposConfig(save=True)
purgeOrbposConfig()

config.plugins.epgsearch.enableorbpos = ConfigYesNo(default=False)
config.plugins.epgsearch.invertorbpos = ConfigSelection(choices=[_("include"), _("exclude")], default=_("include"))
