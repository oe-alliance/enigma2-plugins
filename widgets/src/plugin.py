from Screens.Screen import Screen
from Screens.InfoBarGenerics import InfoBarPlugins
from Screens.InfoBar import InfoBar
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigSubDict, ConfigText, ConfigBoolean
from Components.Element import cached
from enigma import eTimer
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import getDesktop, eSize, ePoint, eEnv
from skin import applyAllAttributes, dom_skins

		
from Widget import Widget
from widgets import importWidgets, importSingleWidget
		

SIBbase__init__ = None
SIB_StartOnlyOneTime = False
SIB_TOGGLE_SHOW = InfoBar.toggleShow
SIB_SWOFF = InfoBar.hide
SIB_STATE = -1

config.plugins.Widgets = ConfigSubsection()
config.plugins.Widgets.show_empty_positions = ConfigBoolean(default=True, descriptions={False: _("hide"), True: _("show")})
config.plugins.Widgets.active_widgets = ConfigSubDict()
for x in range(0, 16):
	for y in range(0, 16):
		config.plugins.Widgets.active_widgets["w%i_%i" % (x, y)] = ConfigText("")


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=SIBautostart)]


class ReplaceInfoBar():
	def __init__(self):
		pass

	@cached
	def Replace(self):
		return True
	boolean = property(Replace)


def SIBautostart(reason, **kwargs):
	global SIBbase__init__
	if "session" in kwargs:
		if SIBbase__init__ is None:
			SIBbase__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.switch = switch
		InfoBarPlugins.swOff = swOff


def InfoBarPlugins__init__(self):
	global SIB_StartOnlyOneTime
	if not SIB_StartOnlyOneTime: 
		SIB_StartOnlyOneTime = True
		self["SIBActions"] = ActionMap(["WidgetStartActions"], {"ok_but": self.switch, "exit_but": self.swOff}, -1)
		self.SIBtimer = eTimer()
		self.SIBtimer.callback.append(self.swOff)
		self.SIBtimer.start(4000, True)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.switch = None
		InfoBarPlugins.swOff = None
	SIBbase__init__(self)


def switch(self):
	if InfoBar and InfoBar.instance and ReplaceInfoBar.Replace:
		global SIB_STATE
		if (SIB_STATE == 0):
			SIB_STATE = 1
			idx = config.usage.infobar_timeout.index
			if idx:
				self.SIBtimer.start(idx * 1000, True)
			SIB_TOGGLE_SHOW(InfoBar.instance)
		elif (SIB_STATE == 1):
			SIB_STATE = 0
			self.SIBtimer.stop()
			SIB_SWOFF(InfoBar.instance)
			self.session.open(WidgetDesktop)
		else:
			SIB_STATE = 0
			self.SIBtimer.stop()
			SIB_SWOFF(InfoBar.instance)


def swOff(self):
	if InfoBar and InfoBar.instance and ReplaceInfoBar.Replace:
		global SIB_STATE
		SIB_STATE = 0
		self.SIBtimer.stop()
		SIB_SWOFF(InfoBar.instance)
####


def lookupScreenSkin(screenname):
	for skin in dom_skins:
		for scr in skin[1].findall("screen"):
			if scr.get("name") == screenname:
				return scr
	return False
####


def lookupWidgetConfig():
	for skin in dom_skins:
		for scr in skin[1].findall("widgetconfig"):
			if scr.findall("num_widgets"):
				return scr
	return False
	

def getWidgetForPosition(session, positionname):
	#print "positionname value",config.plugins.Widgets.active_widgets[positionname].value
	wpath = config.plugins.Widgets.active_widgets[positionname].value
	if wpath == "":
		return False
	else:
		return importSingleWidget(session, wpath)
	

class WidgetDesktop(Screen):
	
	selection_x = 0
	selection_y = 0
	
	def __init__(self, session):
		self.num_widgets_x = 3
		self.num_widgets_y = 3
		self.imported_widgets = []
		self.widgets_on_position = {}
		self.session = session
		Screen.__init__(self, session)
		
		loadSkinReal(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/Widgets/skin.xml"))
		
		cfg = lookupWidgetConfig()
		if cfg is not False:
			for config in cfg.getchildren():
				if config.tag == "num_widgets":
					self.num_widgets_x = int(config.get("x"))
					self.num_widgets_y = int(config.get("y"))
		print "init screen with", self.num_widgets_x, "x", self.num_widgets_y			
		self.initBackgrounds()
		
		self.positions = []
		for x in range(1, self.num_widgets_x + 1):
			for y in range(1, self.num_widgets_y + 1):
				self.positions.append("w%i_%i" % (x, y))
				
		scr = lookupScreenSkin("WidgetDesktop")
		if scr is not False:
			self.original_screen = scr
			self.original_screen_newchilds = []
			for wname in self.positions:
				twidget = getWidgetForPosition(session, wname)
				if twidget is not False:
					print "found widget for position", wname, twidget
					twidget[1].setPositionname(wname)
					self.importWidgetElements(twidget, wname)
					self.importWidgetSkin(scr, twidget, wname)
					self.imported_widgets.append(twidget)
					self.widgets_on_position[wname] = twidget
				else:
					print "position is empty", wname
					
		self["actions"] = ActionMap(["WidgetDesktopActions"], {
															  "ok": self.close,
															  "cancel": self.close,
															  "up": self.key_up,
															  "down": self.key_down,
															  "left": self.key_left,
															  "right": self.key_right,
															  "menu": self.key_menu,
															  "info": self.key_info,
															  }, -1)
		self.onLayoutFinish.append(self.restoreSkin)
		self.onLayoutFinish.append(self._onLoadFinished)
		self.onClose.append(self._onClose)
	
	def importWidgetElements(self, widget, wname):
		for elementname in widget[1].elements.keys():
			self[wname + "_e_" + elementname] = widget[1].elements[elementname]

	def importWidgetSkin(self, scr, widget, wname):
		x, y = self.getPositionOfBackgroundElement(scr, wname)
		for screenelement in widget[2].find("desktopwidget").getchildren():
			element = self.patchWidgetElementSkinPosition(screenelement, x, y, wname)
			self.original_screen_newchilds.append(element)
			scr.append(element)
		
	def getPositionOfBackgroundElement(self, screen, elementname):
		for w in screen.getchildren():
			if w.get("name") == elementname:
				xy = w.get("position").split(",")
				return int(xy[0]), int(xy[1])
		return 0, 0
		
	def restoreSkin(self):
		for old in self.original_screen_newchilds:
			self.original_screen.remove(old)
		
	def initBackgrounds(self):
		for x in range(1, self.num_widgets_x + 1):
			for y in range(1, self.num_widgets_y + 1):
				wname = "w%i_%i" % (x, y)
				self[wname] = Label()
				if not config.plugins.Widgets.show_empty_positions.value:
					self[wname].hide()
				self[wname + "_h"] = Label(_("press menu to edit"))
				self[wname + "_h"].hide()
				
	def patchWidgetElementSkinPosition(self, element, x1, y1, wname):
		pos1 = element.get("position").split(",")
		x2 = int(pos1[0]) + x1
		y2 = int(pos1[1]) + y1
		pos2 = "%i,%i" % (x2, y2)
		element.set("position", pos2)
		if element.get("name") is not None:
			element.set("name", wname + "_e_" + element.get("name"))
		return element

	def _onLoadFinished(self):
		for w in self.imported_widgets:
			try:
				w[1].onLoadFinished(self)
			except Exception, e:
				print "Exception in onLoadFinished of widget", w[0], e
				
	def _onClose(self):
		for w in self.imported_widgets:
			try:
				# notify the widget that it will be closed
				w[1].onClose()
				
				#deleting the instance of the widget
				#del w				
			except Exception, e:
				print "Exception in onClose of widget", w[0], e
				
	def key_up(self):
		self.selectionHide()
		self.selection_x -= 1
		if self.selection_x <= 0:
			self.selection_x = self.num_widgets_x
		self.selectionShow()		

	def key_down(self):
		self.selectionHide()
		self.selection_x += 1
		if self.selection_x > self.num_widgets_x:
			self.selection_x = 1		
		self.selectionShow()		
	
	def key_left(self):
		self.selectionHide()
		self.selection_y -= 1		
		if self.selection_y <= 0:
			self.selection_y = self.num_widgets_y
		self.selectionShow()		

	def key_right(self):
		self.selectionHide()
		self.selection_y += 1
		if self.selection_y > self.num_widgets_y:
			self.selection_y = 1		
		self.selectionShow()		
	
	def selectionShow(self):
		if self.selection_x == 0:
			self.selection_x = 1
		if self.selection_y == 0:
			self.selection_y = 1
		if self.selection_x in range(1, self.num_widgets_x + 1) and self.selection_y in range(1, self.num_widgets_y + 1):
			self["w%i_%i_h" % (self.selection_x, self.selection_y)].show()

	def selectionHide(self):
		if self.selection_x in range(1, self.num_widgets_x + 1) and self.selection_y in range(1, self.num_widgets_y + 1):
			self["w%i_%i_h" % (self.selection_x, self.selection_y)].hide()
				
	def key_menu(self):
		if self.selection_x != 0 and self.selection_y != 0:
			print "menukey on position", self.selection_x, self.selection_y
			w = self.getWidgetOnPosition(self.selection_x, self.selection_y)
			if w is not False:
				self.session.open(WidgetPositionConfigScreen, self.selection_x, self.selection_y, widget=w)
			else:
				self.session.open(WidgetPositionConfigScreen, self.selection_x, self.selection_y)
				
	def key_info(self):
		if self.selection_x != 0 and self.selection_y != 0:
			w = self.getWidgetOnPosition(self.selection_x, self.selection_y)
			if w is not False:
				print "infokey on widget", w[0]
				w[1].onInfo()
	
	def getWidgetOnPosition(self, x, y):
		try:
			return self.widgets_on_position["w%i_%i" % (self.selection_x, self.selection_y)]
		except KeyError:
			return False

###########


class WidgetPositionConfigScreen(Screen):
	def __init__(self, session, x, y, widget=False):
		self.session = session
		self.position_x = x
		self.position_y = y
		self.widget = widget
		Screen.__init__(self, session)
		list = []
		
		if widget is not False:
			list.append((_("clear position"), "remove"))
		
		for widget in importWidgets(session):
			list.append((widget[1].name, widget))
		
		self["list"] = MenuList(list)
		self["preview"] = Label("")
		self["description"] = Label("")
		self["version"] = Label("")
		self["author"] = Label("")
		self["homepage"] = Label("")
		self["key_green"] = Label(_("ok"))
		self["key_red"] = Label(_("cancel"))
		
		self["actions"] = ActionMap(["WidgetPositionConfigScreenActions"], {
															  "ok": self.ok,
															  "cancel": self.close,
															  "down": self.down,
				                                              "up": self.up,
				             				                  "left": self.left,
				             				             	  "right": self.right,
				             				             	  }, -1)
		
	def ok(self):
		if self["list"].getCurrent() is not None:
			self.setValue(self["list"].getCurrent()[1][3])

	def up(self):
		self["list"].up()
		self.update()
    
	def down(self):
		self["list"].down()
		self.update()
        
	def left(self):
		self["list"].pageUp()
		self.update()
    
	def right(self):
		self["list"].pageDown()
		self.update()
	
	def update(self):
		if self["list"].getCurrent() is not None:
			value = self["list"].getCurrent()[1]
			print "update", value
			if value == "remove":
				self["description"].setText("remove current widget")
				self["version"].setText("")
				self["author"].setText("")
				self["homepage"].setText("")
			else:
				self["description"].setText(value[1].description)
				self["version"].setText(value[1].version)
				self["author"].setText(value[1].author)
				self["homepage"].setText(value[1].homepage)
		
	def setValue(self, value):
		config.plugins.Widgets.active_widgets["w%i_%i" % (self.position_x, self.position_y)].value = value
		config.plugins.Widgets.active_widgets["w%i_%i" % (self.position_x, self.position_y)].save()
		self.close()
        

############################################################################
#    Copyright (C) 2008 by Volker Christian                                #
#    Volker.Christian@fh-hagenberg.at                                      #
from skin import loadSkin
import os


def loadSkinReal(skinPath):
    if os.path.exists(skinPath):
        print "[Widgets] Loading skin ", skinPath
        for skin in dom_skins:
        	print "skin", skin
        		
        	if skin[0] == skinPath.replace("skin.xml", ""):
        		dom_skins.remove(skin)
        loadSkin(skinPath)


def loadPluginSkin(pluginPath):
    pass #loadSkinReal(pluginPath + "/skin.xml")
                                                                          #
############################################################################



