from __future__ import absolute_import
from .__init__ import _, _debug, _log

from enigma import iServiceInformation, iPlayableService, eSocketNotifier, getDesktop, ePoint, eSize, eServiceReference

from Screens.ChannelSelection import service_types_tv
from Screens.HelpMenu import HelpMenu
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList 
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config, configfile, getConfigListEntry, ConfigSubsection, ConfigEnableDisable, ConfigSlider, ConfigSelection, ConfigSequence
from GlobalActions import globalActionMap
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard 
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

import array
import socket
import struct

import NavigationInstance

from os import unlink
from select import POLLIN, POLLPRI, POLLHUP, POLLERR

from enigma import Teletext as TeletextInterface
from enigma import DISABLED, BILINEAR, ANISOTROPIC, SHARP, SHARPER, BLURRY, ANTI_FLUTTER, ANTI_FLUTTER_BLURRY, ANTI_FLUTTER_SHARP

from ConfigParser import ConfigParser, DuplicateSectionError 

PLUGIN_VERSION = "20120807"

CMD_CTL_CACHE = 1
CMD_SHOW_PAGE = 2
CMD_PAGE_NEXT = 3
CMD_PAGE_PREV = 4
CMD_SUBP_NEXT = 5
CMD_SUBP_PREV = 6
CMD_COLKEY_RD = 7
CMD_COLKEY_GN = 8
CMD_COLKEY_YE = 9
CMD_COLKEY_BL = 10
CMD_CATCHPAGE = 11
CMD_CONCEALED = 12
CMD_SET_BRIGH = 13
CMD_SET_CONTR = 14
CMD_RQ_UPDATE = 15
CMD_RZAP_PAGE = 16
CMD_OPAQUE = 17
CMD_TRANSPARENCY = 18
CMD_FLOF = 19
CMD_PAGEINPUT = 20
CMD_EDGE_CUT = 21
CMD_TEXTLEVEL = 22
CMD_REGION = 23
CMD_VERSION = 24
CMD_CLOSE_DMN = 99

SPLIT_MODE_PAT = "pat"
SPLIT_MODE_TAP = "tap"
SPLIT_MODE_TIP = "tip"
splittingModeList = [(SPLIT_MODE_PAT, _("picture and teletext")), (SPLIT_MODE_TAP, _("teletext and picture")), (SPLIT_MODE_TIP, _("teletext in picture"))]
textlevelModeList = [("0", "1.0"), ("1", "1.5"), ("2", "2.5"), ("3", "3.5")]
regionList = [("0", _("Western and Central Europe")), ("8", _("Eastern Europe")), ("16", _("Western Europe and Turkey")), ("24", _("Central and Southeast Europe")), ("32", _("Cyrillic")), ("48", _("Turkish / Greek")), ("64", _("Arabic")), ("80", _("Hebrew / Arabic"))]
filterList = [("%d" % DISABLED, _("Disabled")), ("%d" % BILINEAR, _("bilinear")), ("%d" % ANISOTROPIC, _("anisotropic")), ("%d" % SHARP, _("sharp")), ("%d" % SHARPER, _("sharper"))]

HELP_TEXT_POS = _("Enter values (left, top, right, bottom) or press TEXT to move and resize the teletext graphically.")
HELP_TEXT_TIP_POS = _("Enter values (left, top, right, bottom) or press TEXT to move and resize the teletext graphically.")
HELP_TEXT_SPLITTING = _("Select splitting mode.")
HELP_TEXT_BRIGHTNESS = _("Select brightness.")
HELP_TEXT_CONTRAST = _("Select contrast.")
HELP_TEXT_TRANSPARENCY = _("Select transparency.")
HELP_TEXT_EDGE_CUT = _("Display first and last row.")
HELP_TEXT_DEBUG = _("Print debug messages to /tmp/dbttcp.log.")
HELP_TEXT_TEXTLEVEL = _("Select teletext version to use.")
HELP_TEXT_REGION = _("Select your region to use the proper font.")
HELP_TEXT_SCALE_FILTER = _("Select your favourite scale filter.")
HELP_TEXT_CACHING = _("If caching is disabled, each teletext page will searched when you entered its number.")

dsk_size = getDesktop(0).size()
dsk_width = dsk_size.width()
dsk_height = dsk_size.height()

MIN_W = 400
MIN_H = 300

NAV_MODE_TEXT = 0
NAV_MODE_SIZE_TEXT = 1
NAV_MODE_SIZE_TIP_TEXT = 2

# i.d.R. bezeichnet man 90% der vollen Aufloesung als "Title-Safe-Area" --> Default

DEF_TOP = dsk_height / 20
DEF_LEFT = dsk_width / 20
DEF_RIGHT = dsk_width - DEF_LEFT
DEF_BOTTOM = dsk_height - DEF_TOP

config.plugins.TeleText = ConfigSubsection()
config.plugins.TeleText.scale_filter = ConfigSelection(filterList, default="%d" % BILINEAR)
config.plugins.TeleText.scale_filter_zoom = ConfigSelection(filterList, default="%d" % BILINEAR)
config.plugins.TeleText.brightness = ConfigSlider(default=8, increment=1, limits=(0, 15))
config.plugins.TeleText.contrast = ConfigSlider(default=12, increment=1, limits=(0, 15))
config.plugins.TeleText.transparency = ConfigSlider(default=8, increment=1, limits=(0, 15))
config.plugins.TeleText.edge_cut = ConfigEnableDisable(default=False)
config.plugins.TeleText.splitting_mode = ConfigSelection(splittingModeList, default=SPLIT_MODE_PAT)
config.plugins.TeleText.textlevel = ConfigSelection(textlevelModeList, default="2")
config.plugins.TeleText.region = ConfigSelection(regionList, default="16")
config.plugins.TeleText.debug = ConfigEnableDisable(default=False)
config.plugins.TeleText.pos = ConfigSequence(default=[DEF_LEFT, DEF_TOP, DEF_RIGHT, DEF_BOTTOM], seperator=",", limits=[(0, dsk_width >> 3), (0, dsk_height >> 3), (dsk_width - (dsk_width >> 3), dsk_width), (dsk_height - (dsk_height >> 3), dsk_height)])
config.plugins.TeleText.tip_pos = ConfigSequence(default=[(dsk_width >> 1) + (dsk_width >> 2), (dsk_height >> 1) + (dsk_height >> 2), dsk_width, dsk_height], seperator=",", limits=[(0, dsk_width - MIN_W), (0, dsk_height - MIN_H), (MIN_W, dsk_width), (MIN_H, dsk_height)])
# state
config.plugins.TeleText.textOnly = ConfigEnableDisable(default=True)
config.plugins.TeleText.opaque = ConfigEnableDisable(default=False)
config.plugins.TeleText.background_caching = ConfigEnableDisable(default=True)

# global functions


def log(message):
  _log(message)
  if config.plugins.TeleText.debug.value:
    _debug(message)

# ----------------------------------------


class TeleText(Screen):

  pageInput = 0
  catchPage = False
  naviValue = True
  infoValue = False
  edgeValue = False
  opaqueValue = False
  nav_mode = NAV_MODE_TEXT
  zoom = TeletextInterface.MODE_FULL
  filter_mode = BILINEAR
  pid_list = []
  pid_index = 0
  pid_count = 0
  demux = -1
  txtpid = -1
  txtpid_origin = -1
  cur_page = "100-00/00"
  daemonVersion = "0.0"
  favorites = None
  read_data = False

  onChangedEntry = []

  def __init__(self, session):
    TeleText.skin = """<screen position="0,0" size="%d,%d" title="TeleText" flags="wfNoBorder"/>""" % (dsk_width, dsk_height)
    Screen.__init__(self, session)

    self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
      iPlayableService.evStart: self.serviceStarted,
      iPlayableService.evEnd: self.serviceStopped,
      iPlayableService.evUpdatedInfo: self.serviceInfoChanged,
    })

    self["actions"] = NumberActionMap(["OkCancelActions", "TeleTextActions"],
    {
      "ok": self.okPressed,
      "cancel": self.cancelPressed,
      "1": self.keyNumberGlobal,
      "2": self.keyNumberGlobal,
      "3": self.keyNumberGlobal,
      "4": self.keyNumberGlobal,
      "5": self.keyNumberGlobal,
      "6": self.keyNumberGlobal,
      "7": self.keyNumberGlobal,
      "8": self.keyNumberGlobal,
      "9": self.keyNumberGlobal,
      "0": self.keyNumberGlobal,
      "prev": self.prevPressed,
      "next": self.nextPressed,
      "prev_long": self.prevLongPressed,
      "next_long": self.nextLongPressed,
      "red": self.redPressed,
      "green": self.greenPressed,
      "yellow": self.yellowPressed,
      "blue": self.bluePressed,
      "right": self.rightPressed,
      "left": self.leftPressed,
      "down": self.downPressed,
      "up": self.upPressed,
      "info": self.infoPressed,
      "tv": self.tvPressed,
      "radio": self.radioPressed,
      "text": self.textPressed,
      "menu": self.menuPressed,
      "help": self.helpPressed,
      "video": self.videoPressed,
      "nextBouquet": self.nextBouquetPressed,
      "prevBouquet": self.prevBouquetPressed,
      "volUp": self.volumeUpPressed,
      "volDown": self.volumeDownPressed
    }, -1)
    self["actions"].setEnabled(True)

    self.helpList.append((self["actions"], "TeleTextActions", [("1", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("2", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("3", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("4", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("5", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("6", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("7", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("8", _("enter page number"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("9", _("enter page number / page 100"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("prev", _("prev channel / channel list"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("0", _("enter page number / rezap"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("next", _("next channel / channel list"))]))
    self.helpList.append((self["actions"], "OkCancelActions", [("cancel", _("exit"))]))
#    self.helpList.append((self["actions"], "TeleTextActions", [("volUp",_("increase width"))]))
#    self.helpList.append((self["actions"], "TeleTextActions", [("volDown",_("decrease width"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("nextBouquet", _("zoom / increase height"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("prevBouquet", _("favorites / decrease height"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("info", _("toggle info"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("menu", _("teletext settings"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("up", _("next page / catch page / move"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("left", _("prev sub page / move"))]))
    self.helpList.append((self["actions"], "OkCancelActions", [("ok", _("start page catching / select page"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("right", _("next sub page / move"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("down", _("prev page / catch page / move"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("video", _("toggle flof/top"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("red", _("red teletext link"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("green", _("green teletext link"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("yellow", _("yellow teletext link"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("blue", _("blue teletext link"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("tv", _("split screen"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("radio", _("toggle transparency"))]))
    self.helpList.append((self["actions"], "TeleTextActions", [("text", _("exit"))]))

    self.inMenu = False
    self.connected = False

    self.favorites = TeleTextFavorites()

    self.ttx = TeletextInterface()

    self.onLayoutFinish.append(self.__layoutFinished)
    self.onExecBegin.append(self.__execBegin)
    self.onClose.append(self.__closed)

    self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
      unlink('/tmp/dbttcp.socket')
    except:
      pass
    self.socket.bind('/tmp/dbttcp.socket')
    self.listen_sn = eSocketNotifier(self.socket.fileno(), POLLIN)
    self.listen_sn.callback.append(self.listen_data_avail)
    self.socket.listen(1)

  def socketSend(self, buf):
    log("send %s" % (buf))
    try:
      s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.settimeout(5.0)
      if config.plugins.TeleText.debug.value:
        log("... connecting")
      s.connect('/tmp/dbttcd.socket')
    except socket.error as msg:
      log("couldn't connect to /tmp/dbttcd.socket")
      log(msg)
      return

    try:
      msg_len = len(buf)
      totalsent = 0
      while totalsent < msg_len:
        if config.plugins.TeleText.debug.value:
          log("... sending")
        sent = s.send(buf[totalsent:])
        if sent == 0:
          raise RuntimeError("socket connection broken")
        elif config.plugins.TeleText.debug.value:
          log("    sent %s bytes" % sent)
        totalsent = totalsent + sent
      s.close()
      s = None
    except socket.error as msg:
      log("couldn't send data to /tmp/dbttcd.socket")
      log(msg)

  def getDaemonVersion(self):
    x = array.array('B')
    x.append(CMD_VERSION)
    self.socketSend(x)

  def listen_data_avail(self, what):
    conn, addr = self.socket.accept()
    buf = conn.recv(8, socket.MSG_WAITALL)
    x = array.array('H')
    x.fromstring(buf)
    if x[0] == 0:
      self.catchPage = False
    elif x[0] == 1:
      self.ttx.update(0, 0, 492, 250, self.zoom, self.filter_mode)
      if x[1] == 2303:
        x[1] = 0x0100
      self.cur_page = "%s%s%s-%s%s/%s%s" % ((x[1] & 0x0F00) >> 8, (x[1] & 0xF0) >> 4, x[1] & 0x0F, x[2] >> 4, x[2] & 0x0F, x[3] >> 4, x[3] & 0x0F)
      for i in self.onChangedEntry:
        i()
    elif x[0] == 2:
      self.daemonVersion = "%s.%s" % (x[1], x[2])
      log("daemon version %s" % self.daemonVersion)
    conn.close()

  def __execBegin(self):
    log("execBegin")

    if not (config.plugins.TeleText.background_caching.value or self.inMenu):
      self.checkServiceInfo(True)

    self.updateLayout()

    # send brightness, contrast and transparency...
    self.sendSettings()

    renderOffset = self.ttx.getRenderBufferOffset()
    stride = self.ttx.getRenderBufferStride()

    log("framebuffer offset is %08x stride is %08x" % (renderOffset, stride))
    x = array.array('B', (CMD_RQ_UPDATE, 1, (renderOffset & 0xFF000000) >> 24, (renderOffset & 0xFF0000) >> 16, (renderOffset & 0xFF00) >> 8, renderOffset & 0xFF, (stride & 0xFF00) >> 8, stride & 0xFF))
    self.socketSend(x)

    # get daemon version
    self.getDaemonVersion()

  def __closed(self):
    log("__closed")
    renderOffset = self.ttx.getRenderBufferOffset()
    stride = self.ttx.getRenderBufferStride()
    x = array.array('B', (CMD_RQ_UPDATE, 0, (renderOffset & 0xFF000000) >> 24, (renderOffset & 0xFF0000) >> 16, (renderOffset & 0xFF00) >> 8, renderOffset & 0xFF, (stride & 0xFF00) >> 8, stride & 0xFF))
    self.socketSend(x)

    if not (config.plugins.TeleText.background_caching.value or self.inMenu):
      self.stopCaching()

  def __layoutFinished(self):
    log("__layoutFinished")
    self.ttx.show(self.instance)

  def keyNumberGlobal(self, number):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage:
      return
    log("%s pressed" % (number))
    x = array.array('B')
    if self.pageInput == 0:
      if number == 0:
        if self.zoom == TeletextInterface.MODE_LOWER_HALF:
          self.zoom = TeletextInterface.MODE_UPPER_HALF
        x.append(CMD_RZAP_PAGE)
      elif number == 9:
        page = self.fav_list[self.fav_index]
        if self.fav_index == len(self.fav_list) - 1:
          self.fav_index = 0
        else:
          self.fav_index = self.fav_index + 1
        x.fromlist([CMD_SHOW_PAGE, page / 100, (((page % 100) / 10) << 4) + (page % 10), 0])
      else:
        x.fromlist([CMD_PAGEINPUT, number])
        self.pageInput = (self.pageInput + 1) % 3
    else:
      x.fromlist([CMD_PAGEINPUT, number])
      self.pageInput = (self.pageInput + 1) % 3
    self.socketSend(x)

  def upPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      if self.pageInput != 0:
        return
      log("up pressed")
      if self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 2, 2))
      else:
        if self.zoom == TeletextInterface.MODE_LOWER_HALF:
          self.zoom = TeletextInterface.MODE_UPPER_HALF
        x = array.array('B')
        x.append(CMD_PAGE_NEXT)
      self.socketSend(x)
    else:
      if self.nav_pos[1] > 0 and self.nav_pos[3] > self.nav_config.limits[3][0]:
        self.nav_pos[1] = self.nav_pos[1] - 1
        self.nav_pos[3] = self.nav_pos[3] - 1
      self.updateLayout()

  def downPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      if self.pageInput != 0:
        return
      log("down pressed")
      if self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 2, 3))
      else:
        if self.zoom == TeletextInterface.MODE_LOWER_HALF:
          self.zoom = TeletextInterface.MODE_UPPER_HALF
        x = array.array('B')
        x.append(CMD_PAGE_PREV)
      self.socketSend(x)
    else:
      if self.nav_pos[1] < self.nav_config.limits[1][1] and self.nav_pos[3] < dsk_height:
        self.nav_pos[1] = self.nav_pos[1] + 1
        self.nav_pos[3] = self.nav_pos[3] + 1
        self.updateLayout()

  def leftPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      if self.pageInput != 0:
        return
      log("left pressed")
      if self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 2, 0))
      else:
        if self.zoom == TeletextInterface.MODE_LOWER_HALF:
          self.zoom = TeletextInterface.MODE_UPPER_HALF
        x = array.array('B')
        x.append(CMD_SUBP_PREV)
      self.socketSend(x)
    else:
      if self.nav_pos[0] > 0 and self.nav_pos[2] > self.nav_config.limits[2][0]:
        self.nav_pos[0] = self.nav_pos[0] - 1
        self.nav_pos[2] = self.nav_pos[2] - 1
      self.updateLayout()

  def rightPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      if self.pageInput != 0:
        return
      log("right pressed")
      if self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 2, 1))
      else:
        if self.zoom == TeletextInterface.MODE_LOWER_HALF:
          self.zoom = TeletextInterface.MODE_UPPER_HALF
        x = array.array('B')
        x.append(CMD_SUBP_NEXT)
      self.socketSend(x)
    else:
      if self.nav_pos[0] < self.nav_config.limits[0][1] and self.nav_pos[2] < dsk_width:
        self.nav_pos[0] = self.nav_pos[0] + 1
        self.nav_pos[2] = self.nav_pos[2] + 1
        self.updateLayout()

  def nextBouquetPressed(self):
    log("bouqet+ pressed")
    if self.nav_mode == NAV_MODE_TEXT:
      if self.catchPage or self.pageInput != 0:
        return
      # zoom teletext
      if self.zoom == TeletextInterface.MODE_UPPER_HALF:
        self.zoom = TeletextInterface.MODE_LOWER_HALF
      elif self.zoom == TeletextInterface.MODE_LOWER_HALF:
        self.zoom = TeletextInterface.MODE_FULL
      else:
        self.zoom = TeletextInterface.MODE_UPPER_HALF

      if self.zoom:
        self.filter_mode = int(config.plugins.TeleText.scale_filter_zoom.value)
      else:
        self.filter_mode = int(config.plugins.TeleText.scale_filter.value)
    else:
      # position setup
      if self.nav_pos[3] < dsk_height:
        self.nav_pos[3] = self.nav_pos[3] + 1
      elif self.nav_pos[1] > 0:
        self.nav_pos[1] = self.nav_pos[1] - 1
    self.updateLayout()

  def prevBouquetPressed(self):
    log("bouqet- pressed")
    if self.nav_mode == NAV_MODE_TEXT:
      if self.catchPage or self.pageInput != 0:
        return
      # open favorites
      if len(self.pid_list) > 0:
        self.inMenu = True
        self.session.openWithCallback(self.favoritesResult, TeleTextFavoritesMenu, parent=self, service=self.pid_list[self.pid_index], page=self.cur_page.split("-", 1)[0], favorites=self.favorites)
    else:
      # position setup
      if self.nav_pos[3] > (self.nav_pos[1] + MIN_H):
        if self.nav_pos[3] > self.nav_config.limits[3][0]:
          self.nav_pos[3] = self.nav_pos[3] - 1
        elif self.nav_pos[1] < self.nav_config.limits[1][1]:
          self.nav_pos[1] = self.nav_pos[1] + 1
        self.updateLayout()

  def volumeUpPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      globalActionMap.action("TeleText", "volumeUp")
      return
    log("volume+ pressed")
    if self.nav_pos[2] < dsk_width:
      self.nav_pos[2] = self.nav_pos[2] + 1
    elif self.nav_pos[0] > 0:
      self.nav_pos[0] = self.nav_pos[0] - 1
    self.updateLayout()

  def volumeDownPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      globalActionMap.action("TeleText", "volumeDown")
      return
    log("volume- pressed")
    if self.nav_pos[2] > (self.nav_pos[0] + MIN_W):
      if self.nav_pos[2] > self.nav_config.limits[2][0]:
        self.nav_pos[2] = self.nav_pos[2] - 1
      elif self.nav_pos[0] < self.nav_config.limits[0][1]:
        self.nav_pos[0] = self.nav_pos[0] + 1
    self.updateLayout()

  def redPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("red pressed")
    x = array.array('B')
    x.append(CMD_COLKEY_RD)
    self.socketSend(x)

  def greenPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("green pressed")
    x = array.array('B')
    x.append(CMD_COLKEY_GN)
    self.socketSend(x)

  def yellowPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("yellow pressed")
    x = array.array('B')
    x.append(CMD_COLKEY_YE)
    self.socketSend(x)

  def bluePressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("blue pressed")
    x = array.array('B')
    x.append(CMD_COLKEY_BL)
    self.socketSend(x)

  def infoPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("info pressed")
    self.infoValue = not self.infoValue
    for i in self.onChangedEntry:
      i()
    x = array.array('B')
    x.append(CMD_CONCEALED)
    self.socketSend(x)

  def videoPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("video pressed")
    self.naviValue = not self.naviValue
    for i in self.onChangedEntry:
      i()
    x = array.array('B')
    x.append(CMD_FLOF)
    self.socketSend(x)

  def tvPressed(self):
    if self.nav_mode != NAV_MODE_TEXT:
      return
    log("tv pressed")
    if config.plugins.TeleText.textOnly.value:
      config.plugins.TeleText.textOnly.value = False
    else:
      config.plugins.TeleText.textOnly.value = True
    config.plugins.TeleText.textOnly.save()
    configfile.save()
    self.updateLayout()

  def radioPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("radio pressed")
    if config.plugins.TeleText.opaque.value:
      config.plugins.TeleText.opaque.value = False
    else:
      config.plugins.TeleText.opaque.value = True
    config.plugins.TeleText.opaque.save()
    configfile.save()
    self.opaqueValue = config.plugins.TeleText.opaque.value
    x = array.array('B')
    x.append(CMD_OPAQUE)
    self.socketSend(x)

  def textPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage:
      return
    log("text pressed")
    if self.pageInput != 0:
      self.pageInput = 0
      x = array.array('B')
      x.fromlist([CMD_PAGEINPUT, 0x0a])
      self.socketSend(x)
    self.resetVideo()
    self.__closed()
    if self.txtpid != self.txtpid_origin:
      self.txtpid = self.txtpid_origin
      self.switchChannel(True)
      self.readFavorites()
    self.close()

  def menuPressed(self):
    if self.nav_mode != NAV_MODE_TEXT or self.catchPage or self.pageInput != 0:
      return
    log("menu pressed")
    self.__closed()
    self.resetVideo()
    self.inMenu = True
    self.session.openWithCallback(self.menuResult, TeleTextMenu, parent=self)

  def menuResult(self, result):
    self.inMenu = False
    if result is None:
      config.plugins.TeleText.pos.load()
      config.plugins.TeleText.tip_pos.load()
      self.updateLayout()
      return

    self.nav_text_only = config.plugins.TeleText.textOnly.value
    self.nav_config = result
    self.nav_orig_pos = result.value
    self.nav_pos = result.value

    if result == config.plugins.TeleText.pos:
      self.nav_mode = NAV_MODE_SIZE_TEXT
      config.plugins.TeleText.textOnly.value = True
    elif result == config.plugins.TeleText.tip_pos:
      self.nav_mode = NAV_MODE_SIZE_TIP_TEXT
      config.plugins.TeleText.textOnly.value = False
      config.plugins.TeleText.textOnly.value = SPLIT_MODE_TIP
    self.updateLayout()

  def favoritesResult(self, result):
    # read favorites
    self.readFavorites()

    self.inMenu = False
    self.updateLayout()
    if result is None:
      return

    # open favorite page
    x = array.array('B')
    x.fromlist([CMD_SHOW_PAGE, result / 100, (((result % 100) / 10) << 4) + (result % 10), 0])
    self.socketSend(x)

  def updateLayout(self):
    if self.nav_mode == NAV_MODE_TEXT:
      pos = config.plugins.TeleText.pos.value
    else:
      pos = self.nav_pos
    right = pos[2]
    bottom = pos[3]
    mode = config.plugins.TeleText.splitting_mode.value

    if config.plugins.TeleText.textOnly.value == True:
      left = pos[0]
      width = right - left
      top = pos[1]
      height = bottom - top
      self.resetVideo()
    elif mode == SPLIT_MODE_PAT:
      left = dsk_width >> 1
      width = right - (dsk_width >> 1)
      top = pos[1]
      height = bottom - top
      log("splitting video")
      l = open("/proc/stb/vmpeg/0/dst_left", "w")
      l.write("%x" % 0)
      l.close()
      w = open("/proc/stb/vmpeg/0/dst_width", "w")
      w.write("%x" % 360)
      w.close()
    elif mode == SPLIT_MODE_TAP:
      left = pos[0]
      width = (dsk_width >> 1) - left
      top = pos[1]
      height = bottom - top
      log("splitting video")
      l = open("/proc/stb/vmpeg/0/dst_left", "w")
      l.write("%x" % 360)
      l.close()
      w = open("/proc/stb/vmpeg/0/dst_width", "w")
      w.write("%x" % 360)
      w.close()
    elif mode == SPLIT_MODE_TIP:
      if self.nav_mode == NAV_MODE_TEXT:
        pos = config.plugins.TeleText.tip_pos.value
      left = pos[0]
      width = pos[2] - left
      top = pos[1]
      height = pos[3] - top
      self.resetVideo()

    log("screen rect %s %s %s %s" % (left, top, width, height))
    self.instance.move(ePoint(left, top))
    self.instance.resize(eSize(*(width, height)))

    self.ttx.hide()
    self.ttx.show(self.instance)
    self.ttx.update(0, 0, 492, 250, self.zoom, self.filter_mode)

  def resetVideo(self):
    log("reset video")
    l = open("/proc/stb/vmpeg/0/dst_left", "w")
    l.write("%x" % 0)
    l.close()
    w = open("/proc/stb/vmpeg/0/dst_width", "w")
    w.write("%x" % 720)
    w.close()

  def sendSettings(self, result=True):
    if result:
      # region
      x = array.array('B')
      x.append(CMD_REGION)
      x.append(int(config.plugins.TeleText.region.value))
      self.socketSend(x)
      # Helligkeit
      x = array.array('B')
      x.append(CMD_SET_BRIGH)
      x.append(config.plugins.TeleText.brightness.value << 4)
      self.socketSend(x)
      # Kontrast
      x = array.array('B')
      x.append(CMD_SET_CONTR)
      x.append(config.plugins.TeleText.contrast.value << 4)
      self.socketSend(x)
      # Transparenz
      x = array.array('B')
      x.append(CMD_TRANSPARENCY)
      x.append(config.plugins.TeleText.transparency.value << 4)
      self.socketSend(x)
      # edge cut
      if self.edgeValue != config.plugins.TeleText.edge_cut.value:
        self.edgeValue = config.plugins.TeleText.edge_cut.value
        x = array.array('B')
        x.append(CMD_EDGE_CUT)
        self.socketSend(x)
      # teletext level
      x = array.array('B')
      x.append(CMD_TEXTLEVEL)
      x.append(int(config.plugins.TeleText.textlevel.value))
      self.socketSend(x)
      # opaque
      if self.opaqueValue != config.plugins.TeleText.opaque.value:
        self.opaqueValue = config.plugins.TeleText.opaque.value
        x = array.array('B')
        x.append(CMD_OPAQUE)
        self.socketSend(x)

  def prevPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      log("prev pressed")

      if len(self.pid_list) < 2:
        return

      new_pid = -1
      while new_pid == -1:
        if self.pid_index == 0:
          self.pid_index = len(self.pid_list) - 1
        else:
          self.pid_index = self.pid_index - 1
        new_pid = self.pid_list[self.pid_index][2]

      self.txtpid = new_pid
      log("new txtpid: %s" % new_pid)
      self.switchChannel(True)
      self.readFavorites()

  def nextPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      log("next pressed")

      if len(self.pid_list) < 2:
        return

      new_pid = -1
      while new_pid == -1:
        if self.pid_index == (len(self.pid_list) - 1):
          self.pid_index = 0
        else:
          self.pid_index = self.pid_index + 1
        new_pid = self.pid_list[self.pid_index][2]

      self.txtpid = new_pid
      log("new txtpid: %s" % new_pid)
      self.switchChannel(True)
      self.readFavorites()

  def prevLongPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      log("prev long pressed")
      if len(self.pid_list) > 0:
        self.__closed()
        self.resetVideo()
        self.session.openWithCallback(self.transponderResult, TeleTextTransponderMenu, self.pid_list, self.pid_index)

  def nextLongPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      log("next long pressed")
      self.prevLongPressed()

  def transponderResult(self, result):
    log("transponder result: %s" % result)
    if result > -1 and result != self.txtpid:
      self.txtpid = result
      log("new txtpid: %s" % result)
      self.switchChannel(True)
      self.readFavorites()
    self.updateLayout()

  def helpPressed(self):
    self.__closed()
    self.resetVideo()
    self.session.open(HelpMenu, self.helpList)

  def okPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      if self.pageInput != 0:
        return
      log("ok pressed")
      if self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 3, 1))
        self.catchPage = False
      else:
        x = array.array('B', (CMD_CATCHPAGE, 1, 0))
        self.catchPage = True
        self.zoom = TeletextInterface.MODE_FULL
        self.filter_mode = int(config.plugins.TeleText.scale_filter.value)
      self.socketSend(x)
    else:
      if self.nav_mode == NAV_MODE_SIZE_TEXT:
        config.plugins.TeleText.pos.value = self.nav_pos
        config.plugins.TeleText.pos.save()
      else:
        config.plugins.TeleText.tip_pos.value = self.nav_pos
        config.plugins.TeleText.tip_pos.save()
      config.plugins.TeleText.textOnly.value = self.nav_text_only
      del self.nav_text_only
      del self.nav_config
      del self.nav_orig_pos
      del self.nav_pos
      self.nav_mode = NAV_MODE_TEXT
      self.updateLayout()

  def cancelPressed(self):
    if self.nav_mode == NAV_MODE_TEXT:
      log("cancel pressed")
      if self.pageInput != 0:
        self.pageInput = 0
        x = array.array('B')
        x.fromlist([CMD_PAGEINPUT, 0x0a])
        self.socketSend(x)
      elif self.catchPage:
        x = array.array('B', (CMD_CATCHPAGE, 3, 0))
        self.socketSend(x)
        self.catchPage = False
      else:
        self.resetVideo()
        self.__closed()
        if self.txtpid != self.txtpid_origin:
          self.txtpid = self.txtpid_origin
          self.switchChannel(True)
          self.readFavorites()
        self.close()
    else:
      if self.nav_mode == NAV_MODE_SIZE_TEXT:
        config.plugins.TeleText.pos.cancel()
      else:
        config.plugins.TeleText.tip_pos.cancel()
      config.plugins.TeleText.textOnly.value = self.nav_text_only
      del self.nav_text_only
      del self.nav_config
      del self.nav_orig_pos
      del self.nav_pos
      self.nav_mode = NAV_MODE_TEXT
      self.updateLayout()

  def serviceStarted(self):
    log("service started")

  def serviceStopped(self):
    log("service stopped")
    self.stopCaching()

  def stopCaching(self):
    x = array.array('B', (CMD_CTL_CACHE, 0, 0, 0))
    self.socketSend(x)

  def serviceInfoChanged(self):
    log("serviceInfoChanged")
    self.checkServiceInfo(config.plugins.TeleText.background_caching.value or self.inMenu or self.execing)

  def checkServiceInfo(self, do_send=True):
    service = self.session.nav.getCurrentService()
    info = service and service.info()
    self.txtpid_origin = info and info.getInfo(iServiceInformation.sTXTPID)
    self.txtpid = self.txtpid_origin

    stream = service and service.stream()
    demux = stream and stream.getStreamingData()
    self.demux = demux and demux.get("demux", -1)
    log("TXT PID %s DEMUX %s" % (self.txtpid, self.demux))

    self.read_data = True
    self.switchChannel(do_send)

  def switchChannel(self, do_send=True):
    if self.demux > -1 and self.txtpid > -1 and do_send:
      x = array.array('B', (CMD_CTL_CACHE, (self.txtpid & 0xFF00) >> 8, (self.txtpid & 0xFF), self.demux))
      self.socketSend(x)

  def readTxtPids(self):
    log("reading data(%s)" % self.read_data)
    if self.read_data == False:
      return
      
    # read all txtpids and channels from transponder
    cur_ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
    self.pid_index = 0
    if cur_ref is None:
      self.pid_list = []
    else:
      pos = service_types_tv.rfind(':')
      refstr = '%s (channelID == %08x%04x%04x) && %s ORDER BY name' % (service_types_tv[:pos + 1],
          cur_ref.getUnsignedData(4), # NAMESPACE
          cur_ref.getUnsignedData(2), # TSID
          cur_ref.getUnsignedData(3), # ONID
          service_types_tv[pos + 1:])
      ref = eServiceReference(refstr)
      self.pid_list = self.ttx.getTextPidsAndName(ref)
    log("transponder: %s" % self.pid_list)

    i = 0
    available = 0
    for x in self.pid_list:
      if x[2] != -1:
        available = available + 1
      if x[2] == self.txtpid:
        self.pid_index = i
      i = i + 1
    self.pid_count = available
      
    self.read_data = False

    # read favorites
    self.readFavorites()

  def readFavorites(self):
    self.fav_index = 0
    self.fav_list = []
    hasStart = False
    log("pid_list: %s" % self.pid_list)
    log("pid_index: %s" % self.pid_index)
    if len(self.pid_list) > 0:
      service = self.pid_list[self.pid_index]
      log("get favorites of service %s [%s]" % (service[1], service[0]))
      for i in list(range(10)):
        text = self.favorites.getFavorite(service[0], i)
        if text is not None:
          page = int(text[0])
          self.fav_list.append(page)
          if page == 100:
            hasStart = True
    if hasStart == False:
      self.fav_list.append(100)
    log("favorites: %s" % self.fav_list)
  
  # ---- for summary (lcd) ----

  def createSummary(self):
    return TeleTextSummary

  def getCurrentPage(self):
    return self.cur_page

  def getAvailableTxtPidCount(self):
    return self.pid_count

  def naviEnabled(self):
    return self.naviValue

  def infoEnabled(self):
    return self.infoValue

# ----------------------------------------


class TeleTextSummary(Screen):

  def __init__(self, session, parent):
    onPic = resolveFilename(SCOPE_PLUGINS, "Extensions/TeleText/lcd_on.png")
    offPic = resolveFilename(SCOPE_PLUGINS, "Extensions/TeleText/lcd_off.png")

    TeleTextSummary.skin = ("""<screen name="TeleTextSummary" position="0,0" size="132,64" id="1">
      <widget name="page"     position="0,0"   size="132,20" font="Regular;20" valign="center" halign="center" zPosition="1"/>

      <widget name="navi_off" position="12,28"  size="20,20" pixmap="%s" zPosition="1"/>
      <widget name="info_off" position="100,28" size="20,20" pixmap="%s" zPosition="1"/>
      <widget name="navi_on"  position="12,28"  size="20,20" pixmap="%s" zPosition="2"/>
      <widget name="info_on"  position="100,28" size="20,20" pixmap="%s" zPosition="2"/>
      <widget name="tp_count" position="44,28"  size="44,20" font="Regular;16" valign="center" halign="center" zPosition="1"/>

      <widget name="navi_txt" position="0,50"  size="44,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
      <widget name="tp_txt"   position="44,50" size="44,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
      <widget name="info_txt" position="88,50" size="44,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
    </screen>""" % (offPic, offPic, onPic, onPic),
    """<screen name="TeleTextSummary" position="0,0" size="96,64" id="2">
      <widget name="page"     position="0,0"   size="96,20" font="Regular;20" valign="center" halign="center" zPosition="1"/>

      <widget name="navi_off" position="6,28"  size="20,20" pixmap="%s" zPosition="1"/>
      <widget name="info_off" position="70,28" size="20,20" pixmap="%s" zPosition="1"/>
      <widget name="navi_on"  position="6,28"  size="20,20" pixmap="%s" zPosition="2"/>
      <widget name="info_on"  position="70,28" size="20,20" pixmap="%s" zPosition="2"/>
      <widget name="tp_count" position="32,28" size="32,20" font="Regular;16" valign="center" halign="center" zPosition="1"/>

      <widget name="navi_txt" position="0,50"  size="32,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
      <widget name="tp_txt"   position="36,50" size="32,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
      <widget name="info_txt" position="64,50" size="32,12" font="Regular;12" valign="center" halign="center" zPosition="1"/>
    </screen>""" % (offPic, offPic, onPic, onPic))

    Screen.__init__(self, session, parent=parent)
    self["page"] = Label("")
    self["navi_txt"] = Label("NAVI")
    self["tp_txt"] = Label("TPT")
    self["tp_count"] = Label("<1>")
    self["info_txt"] = Label("INFO")
    self["navi_off"] = Pixmap()
    self["info_off"] = Pixmap()
    self["navi_on"] = Pixmap()
    self["info_on"] = Pixmap()
    self.onShow.append(self.addWatcher)
    self.onHide.append(self.removeWatcher)

  def addWatcher(self):
    self.parent.onChangedEntry.append(self.selectionChanged)
    self.selectionChanged()

  def removeWatcher(self):
    self.parent.onChangedEntry.remove(self.selectionChanged)

  def selectionChanged(self):
    self["tp_count"].setText("< %s >" % self.parent.getAvailableTxtPidCount())
    self["page"].setText(self.parent.getCurrentPage())
    if self.parent.naviEnabled():
      self["navi_off"].hide()
      self["navi_on"].show()
    else:
      self["navi_on"].hide()
      self["navi_off"].show()

    if self.parent.infoEnabled():
      self["info_off"].hide()
      self["info_on"].show()
    else:
      self["info_on"].hide()
      self["info_off"].show()

# ----------------------------------------


class TeleTextTransponderMenu(Screen):

  ch_list = []
  ch_index = 0

  cur_service = ""
  new_service = ""

  onChangedEntry = []

  def __init__(self, session, list, index):
    log("[transponder] __init__")

    self.ch_list = list
    self.ch_index = index
    self.cur_service = self.ch_list[self.ch_index][1]

    width = 420
    height = 75
    left = (dsk_width - width) >> 1
    top = (dsk_height - height) >> 1
    log("[transponder] screen rect %s %s %s %s" % (left, top, width, height))
    TeleTextTransponderMenu.skin = """<screen position="%d,%d" size="%d,%d" title="%s">
        <widget name="prev"    position="0,5"   size="35,25"  zPosition="4" pixmap="%s" alphatest="on"/>
        <widget name="channel" position="40,7"  size="325,20" zPosition="5" valign="center" halign="left"  font="Regular;21" transparent="1" foregroundColor="white"/>
        <widget name="zapped"  position="365,7" size="20,20"  zPosition="5" valign="center" halign="right" font="Regular;21" transparent="1" foregroundColor="#888888"/>
        <widget name="next"    position="385,5" size="35,25"  zPosition="4" pixmap="%s" alphatest="on"/>

        <ePixmap pixmap="skin_default/div-h.png" position="0,32" zPosition="1" size="420,2" />

        <ePixmap pixmap="skin_default/buttons/red.png"    position="0,35"   zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png"  position="280,35" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_r" position="0,35"   size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_g" position="280,35" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
      </screen>""" % (left, top, width, height, _("Select teletext"), resolveFilename(SCOPE_PLUGINS, "Extensions/TeleText/key_lt.png"), resolveFilename(SCOPE_PLUGINS, "Extensions/TeleText/key_gt.png"))
    Screen.__init__(self, session)

    self["actions"] = ActionMap(["OkCancelActions", "TeleTextActions"],
    {
      "ok": self.okPressed,
      "cancel": self.cancelPressed,
      "red": self.cancelPressed,
      "green": self.okPressed,
      "left": self.prevPressed,
      "right": self.nextPressed,
      "prev": self.prevPressed,
      "next": self.nextPressed,
      "prev_long": self.prevPressed,
      "next_long": self.nextPressed
    }, -2)
    self["actions"].setEnabled(True)

    self["key_r"] = Label(_("Cancel"))
    self["key_g"] = Label(_("OK"))

    self["channel"] = Label("")
    self["prev"] = Pixmap()
    self["next"] = Pixmap()
    self["zapped"] = Label("*")
    self["zapped"].hide()
    if len(self.ch_list) == 1:
      self["prev"].hide()
      self["next"].hide()
    else:
      self["prev"].show()
      self["next"].show()
    self.updateLayout()

  def updateLayout(self):
    if self.ch_list[self.ch_index][2] == -1:
      self["zapped"].show()
      self["key_g"].setText("")
    else:
      self["zapped"].hide()
      self["key_g"].setText(_("OK"))
    self.new_service = self.ch_list[self.ch_index][1]
    self["channel"].setText(self.new_service)
    for i in self.onChangedEntry:
      i()

  def prevPressed(self):
    log("[transponder] prev pressed")
    if self.ch_index == 0:
      self.ch_index = len(self.ch_list) - 1
    else:
      self.ch_index = self.ch_index - 1
    self.updateLayout()

  def nextPressed(self):
    log("[transponder] next pressed")
    if self.ch_index == (len(self.ch_list) - 1):
      self.ch_index = 0
    else:
      self.ch_index = self.ch_index + 1
    self.updateLayout()

  def okPressed(self):
    log("[transponder] ok pressed")
    if self.ch_list[self.ch_index][2] > -1:
      self.close(self.ch_list[self.ch_index][2])

  def cancelPressed(self):
    log("[transponder] cancel pressed")
    self.close(-1)

  # ---- for summary (lcd) ----

  def createSummary(self):
    return TeleTextTransponderSummary

  def getCurrentService(self):
    return self.cur_service

  def getNewService(self):
    return self.new_service

# ----------------------------------------


class TeleTextTransponderSummary(Screen):

  def __init__(self, session, parent):

    TeleTextTransponderSummary.skin = ("""<screen name="TeleTextTransponderSummary" position="0,0" size="132,64" id="1">
      <widget name="c_service" position="0,5"   size="100,20" font="Regular;20" halign="left"/>
      <ePixmap pixmap="skin_default/div-h.png" position="46,32" size="40,2" zPosition="1"/>
      <widget name="n_service" position="32,39" size="100,20" font="Regular;20" halign="right"/>
    </screen>""",
    """<screen name="TeleTextTransponderSummary" position="0,0" size="96,64" id="2">
      <widget name="c_service" position="0,5"   size="90,20" font="Regular;20" halign="left"/>
      <ePixmap pixmap="skin_default/div-h.png" position="28,32" size="40,2" zPosition="1"/>
      <widget name="n_service" position="6,39" size="90,20" font="Regular;20" halign="right"/>
    </screen>""")

    Screen.__init__(self, session, parent=parent)
    self["c_service"] = Label(self.parent.getCurrentService())
    self["n_service"] = Label(self.parent.getNewService())
    self.onShow.append(self.addWatcher)
    self.onHide.append(self.removeWatcher)

  def addWatcher(self):
    self.parent.onChangedEntry.append(self.selectionChanged)
    self.selectionChanged()

  def removeWatcher(self):
    self.parent.onChangedEntry.remove(self.selectionChanged)

  def selectionChanged(self):
    self["n_service"].setText(self.parent.getNewService())

# ----------------------------------------


class TeleTextMenu(ConfigListScreen, Screen):

  onChangedEntry = []
  isInitialized = False
  parent = None

  def __init__(self, session, parent):
    width = 492
    height = 460
    left = (dsk_width - width) >> 1
    top = (dsk_height - height) >> 1
    log("[menu] screen rect %s %s %s %s" % (left, top, width, height))
    TeleTextMenu.skin = """<screen position="%d,%d" size="%d,%d" title="%s">
        <widget name="config" position="0,0"   size="492,335" scrollbarMode="showOnDemand" zPosition="1"/>
        <ePixmap pixmap="skin_default/div-h.png" position="0,338" zPosition="1" size="492,2" />
        <widget name="label"  position="0,340" size="492,70" font="Regular;16" zPosition="1" halign="left" valign="top"/>
        <ePixmap pixmap="skin_default/div-h.png" position="0,415" zPosition="1" size="492,2" />
        <ePixmap pixmap="skin_default/buttons/red.png"    position="0,420"   zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png"  position="176,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="352,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_r" position="0,420"   size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_g" position="176,420" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_y" position="352,420" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
      </screen>""" % (left, top, width, height, _("TeleText settings"))

    Screen.__init__(self, session, parent)

    # create config list
    self.list = []
    ConfigListScreen.__init__(self, self.list)
    self.createConfigList()

    self["actions"] = ActionMap(["OkCancelActions", "TeleTextActions"],
    {
      "ok": self.okPressed,
      "cancel": self.cancelPressed,
      "red": self.cancelPressed,
      "green": self.okPressed,
      "yellow": self.resetPressed,
      "menu": self.cancelPressed,
      "text": self.textPressed,
      "info": self.infoPressed
    }, -2)
    self["actions"].setEnabled(True)

    self["label"] = Label("Info")
    self["key_r"] = Label(_("Cancel"))
    self["key_y"] = Label(_("Default"))
    self["key_g"] = Label(_("OK"))
    self.onLayoutFinish.append(self.__layoutFinished)

  def __layoutFinished(self):
    self.isInitialized = True
    if not self.selectionChanged in self["config"].onSelectionChanged:
      self["config"].onSelectionChanged.append(self.selectionChanged)
    self.selectionChanged()

  def selectionChanged(self):
    configele = self["config"].getCurrent()[1]
    if configele == config.plugins.TeleText.pos:
      self["label"].setText(HELP_TEXT_POS)
    elif configele == config.plugins.TeleText.brightness:
      self["label"].setText(HELP_TEXT_BRIGHTNESS)
    elif configele == config.plugins.TeleText.contrast:
      self["label"].setText(HELP_TEXT_CONTRAST)
    elif configele == config.plugins.TeleText.transparency:
      self["label"].setText(HELP_TEXT_TRANSPARENCY)
    elif configele == config.plugins.TeleText.splitting_mode:
      self["label"].setText(HELP_TEXT_SPLITTING)
    elif configele == config.plugins.TeleText.tip_pos:
      self["label"].setText(HELP_TEXT_TIP_POS)
    elif configele == config.plugins.TeleText.debug:
      self["label"].setText(HELP_TEXT_DEBUG)
    elif configele == config.plugins.TeleText.edge_cut:
      self["label"].setText(HELP_TEXT_EDGE_CUT)
    elif configele == config.plugins.TeleText.textlevel:
      self["label"].setText(HELP_TEXT_TEXTLEVEL)
    elif configele == config.plugins.TeleText.region:
      self["label"].setText(HELP_TEXT_REGION)
    elif configele == config.plugins.TeleText.scale_filter:
      self["label"].setText(HELP_TEXT_SCALE_FILTER)
    elif configele == config.plugins.TeleText.scale_filter_zoom:
      self["label"].setText(HELP_TEXT_SCALE_FILTER)
    elif configele == config.plugins.TeleText.background_caching:
      self["label"].setText(HELP_TEXT_CACHING)

  def createConfig(self, configele):
    if not self.isInitialized:
      return
    self.createConfigList()

  def createConfigList(self):
    self.isInitialized = False

    # remove notifiers
    for x in self["config"].list:
      x[1].clearNotifiers()

    self.list = [
      getConfigListEntry(_("Scale filter"), config.plugins.TeleText.scale_filter),
      getConfigListEntry(_("Scale filter zoom"), config.plugins.TeleText.scale_filter_zoom),
      getConfigListEntry(_("Brightness"), config.plugins.TeleText.brightness),
      getConfigListEntry(_("Contrast"), config.plugins.TeleText.contrast),
      getConfigListEntry(_("Transparency"), config.plugins.TeleText.transparency),
      getConfigListEntry(_("Text level"), config.plugins.TeleText.textlevel),
      getConfigListEntry(_("Region"), config.plugins.TeleText.region),
      getConfigListEntry(_("Position and size"), config.plugins.TeleText.pos),
      getConfigListEntry(_("Display edges"), config.plugins.TeleText.edge_cut),
      getConfigListEntry(_("Splitting mode"), config.plugins.TeleText.splitting_mode)
    ]
    if config.plugins.TeleText.splitting_mode.value == SPLIT_MODE_TIP:
      self.list.append(getConfigListEntry("... %s" % _("Position and size"), config.plugins.TeleText.tip_pos))
    self.list.append(getConfigListEntry(_("Background caching"), config.plugins.TeleText.background_caching))
    self.list.append(getConfigListEntry(_("Debug"), config.plugins.TeleText.debug))

    self["config"].list = self.list

    # add notifiers (lcd, info)
    for x in self["config"].list:
      x[1].addNotifier(self.changedEntry)
    # add notifiers (menu)
    config.plugins.TeleText.splitting_mode.addNotifier(self.createConfig)

    self.isInitialized = True

  def resetPressed(self):
    log("[menu] reset pressed")
    config.plugins.TeleText.scale_filter.setValue("%d" % BILINEAR)
    config.plugins.TeleText.scale_filter_zoom.setValue("%d" % BILINEAR)
    config.plugins.TeleText.brightness.setValue(8)
    config.plugins.TeleText.contrast.setValue(12)
    config.plugins.TeleText.transparency.setValue(8)
    config.plugins.TeleText.edge_cut.setValue(False)
    config.plugins.TeleText.splitting_mode.setValue(SPLIT_MODE_PAT)
    config.plugins.TeleText.textlevel.setValue("2")
    config.plugins.TeleText.region.setValue("16")
    config.plugins.TeleText.debug.setValue(False)
    config.plugins.TeleText.pos.setValue([DEF_LEFT, DEF_TOP, DEF_RIGHT, DEF_BOTTOM])
    config.plugins.TeleText.tip_pos.setValue([(dsk_width >> 1) + (dsk_width >> 2), (dsk_height >> 1) + (dsk_height >> 2), dsk_width, dsk_height])
    config.plugins.TeleText.background_caching.setValue(True)
    self["config"].selectionChanged()

  def infoPressed(self):
    log("[menu] info pressed")
    self.session.open(TeleTextAboutScreen, self.parent.daemonVersion)

  def textPressed(self):
    log("[menu] text pressed")
    if self["config"].getCurrent()[1] == config.plugins.TeleText.pos:
      self.close(config.plugins.TeleText.pos)
    elif self["config"].getCurrent()[1] == config.plugins.TeleText.tip_pos:
      self.close(config.plugins.TeleText.tip_pos)

  def okPressed(self):
    log("[menu] ok pressed")
    self.checkPositionValues(config.plugins.TeleText.pos)
    self.checkPositionValues(config.plugins.TeleText.tip_pos)
    for x in self["config"].list:
      x[1].save()
    configfile.save()
    self.close(None)

  def checkPositionValues(self, configele):
    pos = configele.value
    log("... old pos: %s %s %s %s" % (pos[0], pos[1], pos[2], pos[3]))
    update = False
    if pos[0] > pos[2]:
      i = pos[0]
      pos[0] = pos[2]
      pos[2] = i
      update = True
    if pos[1] > pos[3]:
      i = pos[1]
      pos[1] = pos[3]
      pos[3] = i
      update = True
    if (pos[2] - pos[0]) < MIN_W:
      pos[2] = pos[0] + MIN_W
      update = True
    if (pos[3] - pos[1]) < MIN_H:
      pos[3] = pos[1] + MIN_H
      update = True
    if pos[2] > dsk_width:
      pos[0] = pos[0] + dsk_width - pos[2]
      pos[2] = dsk_width
      update = True
    if pos[3] > dsk_height:
      pos[1] = pos[1] + dsk_height - pos[3]
      pos[3] = dsk_height
      update = True
    log("... new pos: %s %s %s %s" % (pos[0], pos[1], pos[2], pos[3]))

    if update:
      configele.setValue(pos)

  def cancelPressed(self):
    log("[menu] cancel pressed")
    confirm = False
    for x in self["config"].list:
      confirm = confirm or x[1].isChanged()
    if confirm:
      self.session.openWithCallback(self.DiscardConfirm, MessageBox, _("Discard changes?"))
    else:
      self.close(None)

  def DiscardConfirm(self, result):
    if result:
      for x in self["config"].list:
        if x[1].isChanged():
          x[1].cancel()
      self.close(None)

  # ---- for summary (lcd) ----

  def changedEntry(self, element=None):
    for x in self.onChangedEntry:
      x()

  def getCurrentEntry(self):
    return self["config"].getCurrent()[0]

  def getCurrentValue(self):
    return str(self["config"].getCurrent()[1].getText())

  def createSummary(self):
    return TeleTextMenuSummary

# ----------------------------------------


class TeleTextMenuSummary(Screen):

  skin = ("""<screen name="TeleTextMenuSummary" position="0,0" size="132,64" id="1">
      <widget name="SetupTitle" position="6,4"  size="120,20" font="Regular;20" halign="center"/>
      <widget name="SetupEntry" position="6,30" size="120,12" font="Regular;12" halign="left"/>
      <widget name="SetupValue" position="6,48" size="120,12" font="Regular;12" halign="right"/>
    </screen>""",
    """<screen name="TeleTextMenuSummary" position="0,0" size="96,64" id="2">
      <widget name="SetupTitle" position="3,4"  size="90,20" font="Regular;20" halign="center"/>
      <widget name="SetupEntry" position="3,30" size="90,12" font="Regular;12" halign="left"/>
      <widget name="SetupValue" position="3,48" size="90,12" font="Regular;12" halign="right"/>
    </screen>""")

  def __init__(self, session, parent):
    Screen.__init__(self, session, parent=parent)
    self["SetupTitle"] = Label(_("TeleText settings"))
    self["SetupEntry"] = Label("")
    self["SetupValue"] = Label("")
    self.onShow.append(self.addWatcher)
    self.onHide.append(self.removeWatcher)

  def addWatcher(self):
    self.parent.onChangedEntry.append(self.selectionChanged)
    self.parent["config"].onSelectionChanged.append(self.selectionChanged)
    self.selectionChanged()

  def removeWatcher(self):
    self.parent.onChangedEntry.remove(self.selectionChanged)
    self.parent["config"].onSelectionChanged.remove(self.selectionChanged)

  def selectionChanged(self):
    self["SetupEntry"].text = self.parent.getCurrentEntry()
    self["SetupValue"].text = self.parent.getCurrentValue()

# ----------------------------------------


class TeleTextAboutScreen(Screen):

  daemonVersion = "0.1"

  def __init__(self, session, dVersion):
    self.daemonVersion = dVersion

    width = 360
    height = 240
    left = (dsk_width - width) >> 1
    top = (dsk_height - height) >> 1
    log("[about] screen rect %s %s %s %s" % (left, top, width, height))
    TeleTextAboutScreen.skin = """<screen position="%d,%d" size="%d,%d" flags="wfNoBorder">
        <widget name="pic"    position="0,0"    size="360,240" zPosition="1" pixmap="%s" alphatest="on"/>
        <widget name="text"   position="12,16"  size="336,36"  zPosition="2" font="Console;36" halign="center" backgroundColor="blue"  foregroundColor="white" />
        <widget name="daemon" position="12,64"  size="336,24"  zPosition="2" font="Console;20" halign="left"   backgroundColor="white" foregroundColor="black" />
        <widget name="plugin" position="12,200" size="336,24"  zPosition="2" font="Console;20" halign="right"  backgroundColor="white" foregroundColor="black" />
      </screen>""" % (left, top, width, height, resolveFilename(SCOPE_PLUGINS, "Extensions/TeleText/teletext.png"))

    Screen.__init__(self, session)

    self["actions"] = ActionMap(["OkCancelActions"],
    {
      "ok": self.okPressed,
      "cancel": self.cancelPressed
    }, -2)
    self["actions"].setEnabled(True)

    self["pic"] = Pixmap()
    self["text"] = Label("TeleText")
    self["daemon"] = Label("Daemon v%s" % self.daemonVersion)
    self["plugin"] = Label("Plugin v%s" % PLUGIN_VERSION)

  def okPressed(self):
    log("[about] ok pressed")
    self.close(None)

  def cancelPressed(self):
    log("[about] cancel pressed")
    self.close(None)

  # ---- for summary (lcd) ----

  def getDaemonVersion(self):
    return self.daemonVersion

  def createSummary(self):
    return TeleTextAboutSummary

# ----------------------------------------


class TeleTextAboutSummary(Screen):

  skin = ("""<screen name="TeleTextAboutSummary" position="0,0" size="132,64" id="1">
      <widget name="title"  position="6,4"  size="120,24" font="Regular;20" halign="center"/>
      <widget name="daemon" position="6,30" size="120,16" font="Regular;12" halign="left"/>
      <widget name="plugin" position="6,48" size="120,16" font="Regular;12" halign="left"/>
    </screen>""",
    """<screen name="TeleTextAboutSummary" position="0,0" size="96,64" id="2">
      <widget name="title"  position="3,4"  size="90,20" font="Regular;20" halign="center"/>
      <widget name="daemon" position="3,30" size="90,16" font="Regular;12" halign="left"/>
      <widget name="plugin" position="3,48" size="90,16" font="Regular;12" halign="left"/>
    </screen>""")

  def __init__(self, session, parent):
    Screen.__init__(self, session, parent=parent)
    self["title"] = Label("TeleText")
    self["daemon"] = Label("Daemon v%s" % parent.getDaemonVersion())
    self["plugin"] = Label("Plugin v%s" % PLUGIN_VERSION)

# ----------------------------------------


class TeleTextFavorites():

  configFile = "/etc/enigma2/teletext.fav"

  def __init__(self):
    log("[favorites] reading")
    self.parser = ConfigParser()
    self.parser.read(self.configFile)

  def write(self):
    log("[favorites] writing")
    fp = open(self.configFile, "w")
    self.parser.write(fp)
    fp.close()   

  def getFavorite(self, service, index):
    index = str(index)
    if self.parser.has_option(service, index) is False:
      return None
    return self.parser.get(service, index).split(";", 1)

  def getFavorites(self, service):
    result = []
    if self.parser.has_section(service) is True:
      for x in self.parser.options(service):
        result.append(self.getFavorite(service, x))
    return result

  def setFavorite(self, service, index, page, text):
    index = str(index)
    page = str(page)
    if self.parser.has_section(service) is False:
      self.parser.add_section(service)
    self.parser.set(service, index, "%s;%s" % (page, text))

  def removeFavorite(self, service, index):
    index = str(index)
    self.parser.remove_option(service, index)
    if len(self.parser.options(service)) == 0:
      self.parser.remove_section(service)

  def removeService(self, service):
    self.parser.remove_section(service)

# ----------------------------------------


class TeleTextFavoritesMenu(Screen):

  onChangedEntry = []

  def __init__(self, session, parent, service, page, favorites):
    width = 590
    height = 300
    left = (dsk_width - width) >> 1
    top = (dsk_height - height) >> 1
    log("[fav-menu] screen rect %s %s %s %s" % (left, top, width, height))
    TeleTextFavoritesMenu.skin = """<screen position="%d,%d" size="%d,%d" title="%s [%s]">
        <ePixmap pixmap="skin_default/buttons/key_1.png" position="0,0"   zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_2.png" position="0,25"  zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_3.png" position="0,50"  zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_4.png" position="0,75"  zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_5.png" position="0,100" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_6.png" position="0,125" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_7.png" position="0,150" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_8.png" position="0,175" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_9.png" position="0,200" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <ePixmap pixmap="skin_default/buttons/key_0.png" position="0,225" zPosition="1" size="35,25" transparent="1" alphatest="on"/>
        <widget name="fav_list" position="40,0"   size="550,250" zPosition="1"/>

        <ePixmap pixmap="skin_default/div-h.png" position="0,255" zPosition="1" size="590,2"/>

        <ePixmap pixmap="skin_default/buttons/red.png"    position="0,260"   zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png"  position="150,260" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="300,260" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png"   position="450,260" zPosition="0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_r" position="0,260"   size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_g" position="150,260" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_y" position="300,260" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="key_b" position="450,260" size="140,40" zPosition="5" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
      </screen>""" % (left, top, width, height, _("TeleText favorites"), service[1])

    self.service = service[0]
    self.page = page
    self.favorites = favorites

    Screen.__init__(self, session, parent)
    self["fav_list"] = MenuList([], enableWrapAround=True)
    self["fav_list"].onSelectionChanged.append(self.updateLayout)

    self["actions"] = NumberActionMap(["OkCancelActions", "TeleTextActions"],
    {
      "1": self.keyNumberGlobal,
      "2": self.keyNumberGlobal,
      "3": self.keyNumberGlobal,
      "4": self.keyNumberGlobal,
      "5": self.keyNumberGlobal,
      "6": self.keyNumberGlobal,
      "7": self.keyNumberGlobal,
      "8": self.keyNumberGlobal,
      "9": self.keyNumberGlobal,
      "0": self.keyNumberGlobal,
      "ok": self.okPressed,
      "cancel": self.cancelPressed,
      "red": self.redPressed,
      "green": self.okPressed,
      "yellow": self.yellowPressed,
      "blue": self.bluePressed
    }, -2)
    self["actions"].setEnabled(True)

    self["key_r"] = Label("")
    self["key_g"] = Label("")
    self["key_y"] = Label("")
    self["key_b"] = Label(_("Clear all"))

    self.updateList()
    self.updateLayout()

  def keyNumberGlobal(self, number):
    log("[favorites] %s pressed" % number)
    if number == 0:
      index = 9
    else:
      index = number - 1

    if self.pages[index] != -1:
      self.close(self.pages[index])

  def updateList(self):
    list = []
    self.pages = []

    while len(list) < 10:
      text = self.favorites.getFavorite(self.service, len(list))
      if text is None:
        self.pages.append(-1)
        list.append(_("<empty>"))
      else:
        self.pages.append(int(text[0]))
        list.append("[%s] %s" % (text[0], text[1]))
    self["fav_list"].setList(list)

  def updateLayout(self):
    value = self["fav_list"].getCurrent()
    self.sel_page = self.pages[self["fav_list"].getSelectedIndex()]
    if value == _("<empty>"):
      self["key_r"].setText("")
      self["key_g"].setText("")
      self["key_y"].setText(_("Add"))
    else:
      self["key_r"].setText(_("Delete"))
      self["key_g"].setText(_("Select"))
      self["key_y"].setText(_("Edit"))

    for i in self.onChangedEntry:
      i()

  def okPressed(self):
    if self.sel_page != -1:
      log("[favorites] ok pressed")
      self.close(self.sel_page)

  def cancelPressed(self):
    log("[fav-menu] cancel pressed")
    self.close(None)

  def yellowPressed(self):
    log("[fav-menu] yellow pressed")
    page = self.sel_page
    if page == -1:
      page = self.page
    value = self["fav_list"].getCurrent()
    if value == _("<empty>"):
      value = ""
    else:
      value = value.split(None, 1)[1]
    self.session.openWithCallback(
      self.addFavorite,
      NTIVirtualKeyBoard,
      title =_("Enter text for page %s") % page,
      text=value
    )     

  def addFavorite(self, text):
    if text:
      page = self.sel_page
      if page == -1:
        page = self.page
      self.favorites.setFavorite(self.service, self["fav_list"].getSelectedIndex(), page, text)
      self.favorites.write()
    self.updateList()
    self.updateLayout()

  def redPressed(self):
    log("[fav-menu] red pressed")
    if self.sel_page != -1:
      self.session.openWithCallback(self.deleteFavorite, MessageBox, _("Delete favorite?"))

  def deleteFavorite(self, result):
    if result:
      self.favorites.removeFavorite(self.service, self["fav_list"].getSelectedIndex())
      self.favorites.write()
      self.updateList()
      self.updateLayout()

  def bluePressed(self):
    log("[fav-menu] blue pressed")
    self.session.openWithCallback(self.cleanupService, MessageBox, _("Delete all favorites?"))

  def cleanupService(self, result):
    if result:    
      self.favorites.removeService(self.service)
      self.favorites.write()
      self.updateList()
      self.updateLayout()

  # ---- for summary (lcd) ----

  def getCurrentPage(self):
    page = self.sel_page
    if page == -1:
      page = ""
    return str(page)

  def getCurrentValue(self):
    return self["fav_list"].getCurrent()

  def createSummary(self):
    return TeleTextFavoritesSummary

# ----------------------------------------


class TeleTextFavoritesSummary(Screen):

  skin = ("""<screen name="TeleTextFavoritesSummary" position="0,0" size="132,64" id="1">
      <widget name="title"  position="6,4"  size="120,24" font="Regular;20" halign="center"/>
      <widget name="page"   position="6,30" size="120,16" font="Regular;12" halign="left"/>
      <widget name="text"   position="6,48" size="120,16" font="Regular;12" halign="left"/>
    </screen>""",
    """<screen name="TeleTextFavoritesSummary" position="0,0" size="96,64" id="2">
      <widget name="title"  position="3,4"  size="90,20" font="Regular;20" halign="center"/>
      <widget name="page"   position="3,30" size="90,16" font="Regular;12" halign="left"/>
      <widget name="text"   position="3,48" size="90,16" font="Regular;12" halign="left"/>
    </screen>""")

  def __init__(self, session, parent):
    Screen.__init__(self, session, parent=parent)
    self["title"] = Label(_("TeleText favorites"))
    self["page"] = Label()
    self["text"] = Label()

    self.onShow.append(self.addWatcher)
    self.onHide.append(self.removeWatcher)

  def addWatcher(self):
    self.parent.onChangedEntry.append(self.selectionChanged)
    self.selectionChanged()

  def removeWatcher(self):
    self.parent.onChangedEntry.remove(self.selectionChanged)

  def selectionChanged(self):
    self["page"].setText(self.parent.getCurrentPage())
    self["text"].setText(self.parent.getCurrentValue())

# ----------------------------------------


def sessionstart(reason, session):
  log("----- sessionstart(%s) -----" % session)
  # Plugin initialisieren
  global ttx_screen
  global my_session
  ttx_screen = session.instantiateDialog(TeleText)
  my_session = session


def autostart(reason, **kwargs):
  log("autostart(%s, %s)" % (reason, kwargs))
  if reason == 0:
    pass
  elif reason == 1:
    pass


def mainText(session, **kwargs):
  global ttx_screen
  log("mainText")
  ttx_screen.readTxtPids()
  if ttx_screen.txtpid != -1:
    session.execDialog(ttx_screen)
  else:
    if len(ttx_screen.pid_list) > 0:
      session.openWithCallback(selectText, TeleTextTransponderMenu, ttx_screen.pid_list, ttx_screen.pid_index)
    else:
      session.open(MessageBox, _("No teletext available."), MessageBox.TYPE_INFO, timeout=3)


def selectText(result):
  global my_session
  global ttx_screen
  if result > -1:
    ttx_screen.txtpid = result
    ttx_screen.txtpid_origin = result
    ttx_screen.switchChannel(True)
    ttx_screen.readFavorites()
    my_session.execDialog(ttx_screen)


def mainMenu(session, **kwargs):
  global ttx_screen
  log("mainMenu")
  session.open(TeleTextMenu)


def Plugins(**kwargs):
  log("plugins")
  return [
    PluginDescriptor(name="TeleText", description="teletext", where=PluginDescriptor.WHERE_TELETEXT, fnc=mainText),
    PluginDescriptor(needsRestart=False, where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
    PluginDescriptor(needsRestart=False, where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart)
    ]

# EOF
