#Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/plugin.py
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from enigma import eTimer, getDesktop, loadPic
from Plugins.Plugin import PluginDescriptor
from re import findall, search, split, sub
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from string import find, strip
from Tools.Directories import fileExists
from twisted.internet import reactor
from twisted.web import client, error
from twisted.web.client import getPage
import os, re, sys, time, urllib

def getAspect():
    val = AVSwitch().getAspectRatioSetting()
    return val / 2


def transHTML(text):
    text = text.replace('&nbsp;', ' ').replace('&#034;', '"').replace('&#039;', "'").replace('&szlig;', 'ss').replace('&quot;', '"').replace('&ndash;', '-').replace('&Oslash;', '').replace('&bdquo;', '"').replace('&ldquo;', '"').replace('&#8211;', '-').replace('&rdquo;', '"').replace('&sup2;', '\xc2\xb2').replace('&bull;', '\xe2\x80\xa2')
    text = text.replace('&copy;.*', ' ').replace('&amp;', '&').replace('&uuml;', '\xc3\xbc').replace('&auml;', '\xc3\xa4').replace('&ouml;', '\xc3\xb6').replace('&eacute;', '\xc3\xa9').replace('&hellip;', '...').replace('&egrave;', '\xc3\xa8').replace('&agrave;', '\xc3\xa0').replace('&deg;', '\xc2\xb0').replace('&acute;', "'").replace('&lt;', '\xe2\x97\x84').replace('&gt;', '\xe2\x96\xba')
    text = text.replace('&Uuml;', '\xc3\x9c').replace('&Auml;', '\xc3\x84').replace('&Ouml;', '\xc3\x96').replace('&#34;', '"').replace('&#38;', 'und').replace('&#39;', "'").replace('&#196;', 'Ae').replace('&#214;', 'Oe').replace('&#220;', 'Ue').replace('&#223;', 'ss').replace('&#228;', '\xc3\xa4').replace('&#243;', '\xc3\xb3').replace('&#246;', '\xc3\xb6').replace('&#252;', '\xc3\xbc')
    return text


class msnWetterDateMain(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="920,175" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="110,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="210,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="310,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="410,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="510,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="610,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="710,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="810,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date1" position="10,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date2" position="110,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date3" position="210,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date4" position="310,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date5" position="410,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date6" position="510,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date7" position="610,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date8" position="710,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date9" position="810,30" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="32,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="132,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="232,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="332,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="432,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="532,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="632,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="732,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="832,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="minmax1" position="10,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax2" position="110,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax3" position="210,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax4" position="310,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax5" position="410,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax6" position="510,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax7" position="610,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax8" position="710,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax9" position="810,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="110,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="210,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="310,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="410,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="510,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="610,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="710,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="810,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="1190,210" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="140,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="270,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="400,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="530,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="660,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="790,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="920,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="1050,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date1" position="10,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date2" position="140,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date3" position="270,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date4" position="400,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date5" position="530,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date6" position="660,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date7" position="790,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date8" position="920,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date9" position="1050,35" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="42,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="172,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="302,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="432,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="562,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="692,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="822,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="952,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="1082,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="minmax1" position="10,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax2" position="140,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax3" position="270,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax4" position="400,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax5" position="530,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax6" position="660,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax7" position="790,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax8" position="920,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax9" position="1050,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="140,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="270,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="400,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="530,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="660,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="790,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="920,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="1050,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinblack = '\n\t\t\t<screen position="center,center" size="920,175" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="110,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="210,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="310,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="410,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="510,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="610,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="710,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="810,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date1" position="10,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date2" position="110,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date3" position="210,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date4" position="310,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date5" position="410,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date6" position="510,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date7" position="610,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date8" position="710,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date9" position="810,30" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="32,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="132,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="232,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="332,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="432,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="532,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="632,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="732,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="832,55" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="minmax1" position="10,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax2" position="110,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax3" position="210,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax4" position="310,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax5" position="410,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax6" position="510,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax7" position="610,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax8" position="710,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax9" position="810,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="110,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="210,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="310,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="410,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="510,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="610,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="710,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="810,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHDblack = '\n\t\t\t<screen position="center,center" size="1190,210" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="140,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="270,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="400,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="530,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="660,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="790,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="920,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="1050,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date1" position="10,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date2" position="140,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date3" position="270,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date4" position="400,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date5" position="530,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date6" position="660,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date7" position="790,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date8" position="920,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="date9" position="1050,35" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="42,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="172,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="302,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="432,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="562,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="692,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="822,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="952,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="1082,63" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="minmax1" position="10,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax2" position="140,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax3" position="270,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax4" position="400,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax5" position="530,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax6" position="660,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax7" position="790,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax8" position="920,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="minmax9" position="1050,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="140,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="270,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="400,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="530,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="660,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="790,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="920,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="1050,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'

    def __init__(self, session):
        self.loadinginprogress = False
        self.colorfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/color'
        if fileExists(self.colorfile):
            f = open(self.colorfile, 'r')
            data = f.readline()
            f.close()
            if 'blackdate' in data:
                self.black = True
            elif 'blacknodate' in data:
                self.black = True
            else:
                self.black = False
        else:
            self.black = False
        deskWidth = getDesktop(0).size().width()
        if deskWidth == 1280 and self.black == False:
            self.skin = msnWetterDateMain.skinHD
            self.hd = True
        elif deskWidth == 1280 and self.black == True:
            self.skin = msnWetterDateMain.skinHDblack
            self.hd = True
        elif deskWidth <= 1025 and self.black == False:
            self.skin = msnWetterDateMain.skin
            self.hd = False
        elif deskWidth <= 1025 and self.black == True:
            self.skin = msnWetterDateMain.skinblack
            self.hd = False
        self.session = session
        Screen.__init__(self, session)
        self.aspect = getAspect()
        self.hideflag = True
        self.count = 1
        self.maxlines = 0
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['pic7'] = Pixmap()
        self['pic8'] = Pixmap()
        self['pic9'] = Pixmap()
        self['tag1'] = Label('')
        self['tag2'] = Label('')
        self['tag3'] = Label('')
        self['tag4'] = Label('')
        self['tag5'] = Label('')
        self['tag6'] = Label('')
        self['tag7'] = Label('')
        self['tag8'] = Label('')
        self['tag9'] = Label('')
        self['date1'] = Label('')
        self['date2'] = Label('')
        self['date3'] = Label('')
        self['date4'] = Label('')
        self['date5'] = Label('')
        self['date6'] = Label('')
        self['date7'] = Label('')
        self['date8'] = Label('')
        self['date9'] = Label('')
        self['minmax1'] = Label('')
        self['minmax2'] = Label('')
        self['minmax3'] = Label('')
        self['minmax4'] = Label('')
        self['minmax5'] = Label('')
        self['minmax6'] = Label('')
        self['minmax7'] = Label('')
        self['minmax8'] = Label('')
        self['minmax9'] = Label('')
        self['text1'] = Label('')
        self['text2'] = Label('')
        self['text3'] = Label('')
        self['text4'] = Label('')
        self['text5'] = Label('')
        self['text6'] = Label('')
        self['text7'] = Label('')
        self['text8'] = Label('')
        self['text9'] = Label('')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'MenuActions'], {'ok': self.ok,
         'cancel': self.exit,
         'red': self.red,
         'green': self.green,
         'yellow': self.yellow,
         'blue': self.hideScreen,
         'menu': self.cities}, -1)
        self.cityfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/city'
        if fileExists(self.cityfile):
            f = open(self.cityfile, 'r')
            city = f.readline()
            self.city = city.strip()
            f.seek(0, 0)
            for line in f:
                self.maxlines += 1

            f.close()
        if self.maxlines == 0:
            self.count = 0
            self.city = 'http://wetter.msn.com/local.aspx?wealocations=wc:GMXX0185&q=Frankfurt%2fMain%2c+HE'
        self.makeWetterTimer = eTimer()
        self.makeWetterTimer.callback.append(self.download(self.city, self.makeWetter))
        self.makeWetterTimer.start(500, True)

    def makeWetter(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<span class="text">5 Tage Vorhersage</span>')
        endpos = find(output, '</div><div id="weatherdetailedforecast_error">')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        title = re.findall('<title>(.*?)</title>', output)
        title = sub(' [(]weatherlocation[)] - Aktuelle Wetterlage, Wettervorhersage, Niederschlagsvorhersage und Temperaturen bei MSN Wetter.', '', title[0])
        title = transHTML(title)
        self.setTitle(title)
        tag = re.findall('<div class="dayDate">\n            <span class="dfbold">(.*?)</span>', bereich)
        if tag is not None:
            try:
                self['tag1'].setText(tag[0])
                self['tag2'].setText(tag[1])
                self['tag3'].setText(tag[2])
                self['tag4'].setText(tag[3])
                self['tag5'].setText(tag[4])
                self['tag6'].setText(tag[5])
                self['tag7'].setText(tag[6])
                self['tag8'].setText(tag[7])
                self['tag9'].setText(tag[8])
            except IndexError:
                pass

            self['tag1'].show()
            self['tag2'].show()
            self['tag3'].show()
            self['tag4'].show()
            self['tag5'].show()
            self['tag6'].show()
            self['tag7'].show()
            self['tag8'].show()
            self['tag9'].show()
        else:
            self['tag1'].setText('')
            self['tag2'].setText('')
            self['tag3'].setText('')
            self['tag4'].setText('')
            self['tag5'].setText('')
            self['tag6'].setText('')
            self['tag7'].setText('')
            self['tag8'].setText('')
            self['tag9'].setText('')
        date = re.findall('</div>\n          <div>(.*?)</div>', bereich)
        if date is not None:
            try:
                self['date1'].setText(date[0])
                self['date2'].setText(date[1])
                self['date3'].setText(date[2])
                self['date4'].setText(date[3])
                self['date5'].setText(date[4])
                self['date6'].setText(date[5])
                self['date7'].setText(date[6])
                self['date8'].setText(date[7])
                self['date9'].setText(date[8])
            except IndexError:
                pass

            self['date1'].show()
            self['date2'].show()
            self['date3'].show()
            self['date4'].show()
            self['date5'].show()
            self['date6'].show()
            self['date7'].show()
            self['date8'].show()
            self['date9'].show()
        else:
            self['date1'].setText('')
            self['date2'].setText('')
            self['date3'].setText('')
            self['date4'].setText('')
            self['date5'].setText('')
            self['date6'].setText('')
            self['date7'].setText('')
            self['date8'].setText('')
            self['date9'].setText('')
        max = re.findall('<div>Max : <span class="dfbold">(.*?)</span></div>', bereich)
        min = re.findall('<div>Min : <span class="dfbold">(.*?)</span></div>', bereich)
        if max is not None:
            try:
                self['minmax1'].setText(max[0] + '|' + min[0])
                self['minmax2'].setText(max[1] + '|' + min[1])
                self['minmax3'].setText(max[2] + '|' + min[2])
                self['minmax4'].setText(max[3] + '|' + min[3])
                self['minmax5'].setText(max[4] + '|' + min[4])
                self['minmax6'].setText(max[5] + '|' + min[5])
                self['minmax7'].setText(max[6] + '|' + min[6])
                self['minmax8'].setText(max[7] + '|' + min[7])
                self['minmax9'].setText(max[8] + '|' + min[8])
            except IndexError:
                pass

            self['minmax1'].show()
            self['minmax2'].show()
            self['minmax3'].show()
            self['minmax4'].show()
            self['minmax5'].show()
            self['minmax6'].show()
            self['minmax7'].show()
            self['minmax8'].show()
            self['minmax9'].show()
        else:
            self['minmax1'].setText('')
            self['minmax2'].setText('')
            self['minmax3'].setText('')
            self['minmax4'].setText('')
            self['minmax5'].setText('')
            self['minmax6'].setText('')
            self['minmax7'].setText('')
            self['minmax8'].setText('')
            self['minmax9'].setText('')
        text = re.findall('<span class="temptext">(.*?)</span>', bereich)
        if text is not None:
            try:
                self['text1'].setText(text[0])
                self['text2'].setText(text[1])
                self['text3'].setText(text[2])
                self['text4'].setText(text[3])
                self['text5'].setText(text[4])
                self['text6'].setText(text[5])
                self['text7'].setText(text[6])
                self['text8'].setText(text[7])
                self['text9'].setText(text[8])
            except IndexError:
                pass

            self['text1'].show()
            self['text2'].show()
            self['text3'].show()
            self['text4'].show()
            self['text5'].show()
            self['text6'].show()
            self['text7'].show()
            self['text8'].show()
            self['text9'].show()
        else:
            self['text1'].setText('')
            self['text2'].setText('')
            self['text3'].setText('')
            self['text4'].setText('')
            self['text5'].setText('')
            self['text6'].setText('')
            self['text7'].setText('')
            self['text8'].setText('')
            self['text9'].setText('')
        pic = re.findall('<img src="http://.*?msn.com/as/wea3/i/de/law/(.*?)[.]gif" height', bereich)
        pic1 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[0] + '.png'
        if fileExists(pic1):
            self.showPic1(pic1)
            self['pic1'].show()
        pic2 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[1] + '.png'
        if fileExists(pic2):
            self.showPic2(pic2)
            self['pic2'].show()
        pic3 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[2] + '.png'
        if fileExists(pic3):
            self.showPic3(pic3)
            self['pic3'].show()
        pic4 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[3] + '.png'
        if fileExists(pic4):
            self.showPic4(pic4)
            self['pic4'].show()
        pic5 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[4] + '.png'
        if fileExists(pic5):
            self.showPic5(pic5)
            self['pic5'].show()
        pic6 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[5] + '.png'
        if fileExists(pic6):
            self.showPic6(pic6)
            self['pic6'].show()
        pic7 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[6] + '.png'
        if fileExists(pic7):
            self.showPic7(pic7)
            self['pic7'].show()
        pic8 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[7] + '.png'
        if fileExists(pic8):
            self.showPic8(pic8)
            self['pic8'].show()
        pic9 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[8] + '.png'
        if fileExists(pic9):
            self.showPic9(pic9)
            self['pic9'].show()

    def ok(self):
        if self.count == 1:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count += 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 2:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count += 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 3:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count += 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 4:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count += 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 5:
            self.count = 1
            if fileExists(self.cityfile):
                f = open(self.cityfile, 'r')
                city = f.readline()
                self.city = city.strip()
                f.close()
        elif self.count == 0:
            self.session.openWithCallback(self.citiesReturn, msnCities)
        self.makeWetterTimer.callback.append(self.download(self.city, self.makeWetter))

    def green(self):
        self.session.openWithCallback(self.cityback, msnCity, self.city)

    def yellow(self):
        if self.black == True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('blacknodate')
                f.close()
        elif self.black == False:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('bluenodate')
                f.close()
        self.session.openWithCallback(self.exit, msnWetterMain)

    def cities(self):
        self.session.openWithCallback(self.citiesReturn, msnCities)

    def citiesReturn(self):
        if fileExists(self.cityfile):
            f = open(self.cityfile, 'r')
            city = f.readline()
            self.city = city.strip()
            f.seek(0, 0)
            self.maxlines = 0
            for line in f:
                self.maxlines += 1

            f.close()
            self.count = 1
            if self.maxlines == 0:
                self.count = 0

    def red(self):
        if self.black == False:
            self.session.openWithCallback(self.blackcolor, MessageBox, _('\nFarbe zu Schwarz wechseln?'), MessageBox.TYPE_YESNO)
        elif self.black == True:
            self.session.openWithCallback(self.bluecolor, MessageBox, _('\nFarbe zu Blau wechseln?'), MessageBox.TYPE_YESNO)

    def blackcolor(self, answer):
        if answer is True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('blackdate')
                f.close()
                self.session.openWithCallback(self.exit, msnWetterDateMain)

    def bluecolor(self, answer):
        if answer is True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('bluedate')
                f.close()
                self.session.openWithCallback(self.exit, msnWetterDateMain)

    def showPic1(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic1'].instance.setPixmap(currPic)

    def showPic2(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic2'].instance.setPixmap(currPic)

    def showPic3(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic3'].instance.setPixmap(currPic)

    def showPic4(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic4'].instance.setPixmap(currPic)

    def showPic5(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic5'].instance.setPixmap(currPic)

    def showPic6(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic6'].instance.setPixmap(currPic)

    def showPic7(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic7'].instance.setPixmap(currPic)

    def showPic8(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic8'].instance.setPixmap(currPic)

    def showPic9(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic9'].instance.setPixmap(currPic)

    def download(self, link, name):
        self.loadinginprogress = True
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.loadinginprogress = False

    def cityback(self):
        pass

    def hideScreen(self):
        if self.hideflag == True:
            self.hideflag = False
            self.hide()
        else:
            self.hideflag = True
            self.show()

    def exit(self):
        self.close()


class msnWetterMain(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="920,175" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="110,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="210,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="310,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="410,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="510,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="610,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="710,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="810,5" size="100,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="32,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="132,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="232,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="332,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="432,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="532,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="632,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="732,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="832,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="max1" position="10,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max2" position="110,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max3" position="210,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max4" position="310,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max5" position="410,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max6" position="510,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max7" position="610,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max8" position="710,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max9" position="810,85" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min1" position="10,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min2" position="110,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min3" position="210,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min4" position="310,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min5" position="410,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min6" position="510,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min7" position="610,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min8" position="710,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min9" position="810,105" size="100,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="110,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="210,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="310,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="410,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="510,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="610,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="710,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="810,130" size="100,45" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="1190,210" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="140,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="270,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="400,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="530,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="660,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="790,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="920,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="1050,5" size="130,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="42,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="172,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="302,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="432,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="562,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="692,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="822,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="952,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="1082,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="max1" position="10,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max2" position="140,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max3" position="270,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max4" position="400,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max5" position="530,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max6" position="660,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max7" position="790,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max8" position="920,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max9" position="1050,100" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min1" position="10,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min2" position="140,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min3" position="270,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min4" position="400,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min5" position="530,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min6" position="660,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min7" position="790,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min8" position="920,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min9" position="1050,128" size="130,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="140,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="270,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="400,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="530,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="660,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="790,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="920,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="1050,158" size="130,50" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinblack = '\n\t\t\t<screen position="center,center" size="920,175" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="110,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="210,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="310,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="410,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="510,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="610,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="710,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="810,5" size="100,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="32,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="132,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="232,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="332,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="432,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="532,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="632,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="732,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="832,32" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="max1" position="10,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max2" position="110,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max3" position="210,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max4" position="310,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max5" position="410,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max6" position="510,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max7" position="610,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max8" position="710,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max9" position="810,85" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min1" position="10,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min2" position="110,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min3" position="210,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min4" position="310,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min5" position="410,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min6" position="510,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min7" position="610,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min8" position="710,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min9" position="810,105" size="100,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="110,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="210,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="310,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="410,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="510,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="610,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="710,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="810,130" size="100,45" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHDblack = '\n\t\t\t<screen position="center,center" size="1190,210" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="tag1" position="10,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag2" position="140,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag3" position="270,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag4" position="400,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag5" position="530,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag6" position="660,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag7" position="790,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag8" position="920,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="tag9" position="1050,5" size="130,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic1" position="42,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic2" position="172,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic3" position="302,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic4" position="432,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic5" position="562,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic6" position="692,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic7" position="822,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic8" position="952,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pic9" position="1082,35" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="max1" position="10,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max2" position="140,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max3" position="270,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max4" position="400,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max5" position="530,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max6" position="660,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max7" position="790,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max8" position="920,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="max9" position="1050,100" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min1" position="10,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min2" position="140,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min3" position="270,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min4" position="400,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min5" position="530,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min6" position="660,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min7" position="790,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min8" position="920,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="min9" position="1050,128" size="130,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text1" position="10,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text2" position="140,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text3" position="270,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text4" position="400,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text5" position="530,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text6" position="660,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text7" position="790,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text8" position="920,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="text9" position="1050,158" size="130,50" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'

    def __init__(self, session):
        self.loadinginprogress = False
        self.colorfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/color'
        if fileExists(self.colorfile):
            f = open(self.colorfile, 'r')
            data = f.readline()
            f.close()
            if 'blackdate' in data:
                self.black = True
            elif 'blacknodate' in data:
                self.black = True
            else:
                self.black = False
        else:
            self.black = False
        deskWidth = getDesktop(0).size().width()
        if deskWidth == 1280 and self.black == False:
            self.skin = msnWetterMain.skinHD
            self.hd = True
        elif deskWidth == 1280 and self.black == True:
            self.skin = msnWetterMain.skinHDblack
            self.hd = True
        elif deskWidth <= 1025 and self.black == False:
            self.skin = msnWetterMain.skin
            self.hd = False
        elif deskWidth <= 1025 and self.black == True:
            self.skin = msnWetterMain.skinblack
            self.hd = False
        self.session = session
        Screen.__init__(self, session)
        self.aspect = getAspect()
        self.hideflag = True
        self.count = 1
        self.maxlines = 0
        self['pic1'] = Pixmap()
        self['pic2'] = Pixmap()
        self['pic3'] = Pixmap()
        self['pic4'] = Pixmap()
        self['pic5'] = Pixmap()
        self['pic6'] = Pixmap()
        self['pic7'] = Pixmap()
        self['pic8'] = Pixmap()
        self['pic9'] = Pixmap()
        self['tag1'] = Label('')
        self['tag2'] = Label('')
        self['tag3'] = Label('')
        self['tag4'] = Label('')
        self['tag5'] = Label('')
        self['tag6'] = Label('')
        self['tag7'] = Label('')
        self['tag8'] = Label('')
        self['tag9'] = Label('')
        self['max1'] = Label('')
        self['max2'] = Label('')
        self['max3'] = Label('')
        self['max4'] = Label('')
        self['max5'] = Label('')
        self['max6'] = Label('')
        self['max7'] = Label('')
        self['max8'] = Label('')
        self['max9'] = Label('')
        self['min1'] = Label('')
        self['min2'] = Label('')
        self['min3'] = Label('')
        self['min4'] = Label('')
        self['min5'] = Label('')
        self['min6'] = Label('')
        self['min7'] = Label('')
        self['min8'] = Label('')
        self['min9'] = Label('')
        self['text1'] = Label('')
        self['text2'] = Label('')
        self['text3'] = Label('')
        self['text4'] = Label('')
        self['text5'] = Label('')
        self['text6'] = Label('')
        self['text7'] = Label('')
        self['text8'] = Label('')
        self['text9'] = Label('')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions', 'MenuActions'], {'ok': self.ok,
         'cancel': self.exit,
         'red': self.red,
         'green': self.green,
         'yellow': self.yellow,
         'blue': self.hideScreen,
         'menu': self.cities}, -1)
        self.cityfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/city'
        if fileExists(self.cityfile):
            f = open(self.cityfile, 'r')
            city = f.readline()
            self.city = city.strip()
            f.seek(0, 0)
            for line in f:
                self.maxlines += 1

            f.close()
        if self.maxlines == 0:
            self.count = 0
            self.city = 'http://wetter.msn.com/local.aspx?wealocations=wc:GMXX0185&q=Frankfurt%2fMain%2c+HE'
        self.makeWetterTimer = eTimer()
        self.makeWetterTimer.callback.append(self.download(self.city, self.makeWetter))
        self.makeWetterTimer.start(500, True)

    def makeWetter(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<span class="text">5 Tage Vorhersage</span>')
        endpos = find(output, '</div><div id="weatherdetailedforecast_error">')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        title = re.findall('<title>(.*?)</title>', output)
        title = sub(' [(]weatherlocation[)] - Aktuelle Wetterlage, Wettervorhersage, Niederschlagsvorhersage und Temperaturen bei MSN Wetter.', '', title[0])
        title = transHTML(title)
        self.setTitle(title)
        tag = re.findall('<div class="dayDate">\n            <span class="dfbold">(.*?)</span>', bereich)
        if tag is not None:
            try:
                self['tag1'].setText(tag[0])
                self['tag2'].setText(tag[1])
                self['tag3'].setText(tag[2])
                self['tag4'].setText(tag[3])
                self['tag5'].setText(tag[4])
                self['tag6'].setText(tag[5])
                self['tag7'].setText(tag[6])
                self['tag8'].setText(tag[7])
                self['tag9'].setText(tag[8])
            except IndexError:
                pass

            self['tag1'].show()
            self['tag2'].show()
            self['tag3'].show()
            self['tag4'].show()
            self['tag5'].show()
            self['tag6'].show()
            self['tag7'].show()
            self['tag8'].show()
            self['tag9'].show()
        else:
            self['tag1'].setText('')
            self['tag2'].setText('')
            self['tag3'].setText('')
            self['tag4'].setText('')
            self['tag5'].setText('')
            self['tag6'].setText('')
            self['tag7'].setText('')
            self['tag8'].setText('')
            self['tag9'].setText('')
        max = re.findall('<div>Max : <span class="dfbold">(.*?)</span></div>', bereich)
        if max is not None:
            try:
                self['max1'].setText('Max : ' + max[0])
                self['max2'].setText('Max : ' + max[1])
                self['max3'].setText('Max : ' + max[2])
                self['max4'].setText('Max : ' + max[3])
                self['max5'].setText('Max : ' + max[4])
                self['max6'].setText('Max : ' + max[5])
                self['max7'].setText('Max : ' + max[6])
                self['max8'].setText('Max : ' + max[7])
                self['max9'].setText('Max : ' + max[8])
            except IndexError:
                pass

            self['max1'].show()
            self['max2'].show()
            self['max3'].show()
            self['max4'].show()
            self['max5'].show()
            self['max6'].show()
            self['max7'].show()
            self['max8'].show()
            self['max9'].show()
        else:
            self['max1'].setText('')
            self['max2'].setText('')
            self['max3'].setText('')
            self['max4'].setText('')
            self['max5'].setText('')
            self['max6'].setText('')
            self['max7'].setText('')
            self['max8'].setText('')
            self['max9'].setText('')
        min = re.findall('<div>Min : <span class="dfbold">(.*?)</span></div>', bereich)
        if min is not None:
            try:
                self['min1'].setText('Min : ' + min[0])
                self['min2'].setText('Min : ' + min[1])
                self['min3'].setText('Min : ' + min[2])
                self['min4'].setText('Min : ' + min[3])
                self['min5'].setText('Min : ' + min[4])
                self['min6'].setText('Min : ' + min[5])
                self['min7'].setText('Min : ' + min[6])
                self['min8'].setText('Min : ' + min[7])
                self['min9'].setText('Min : ' + min[8])
            except IndexError:
                pass

            self['min1'].show()
            self['min2'].show()
            self['min3'].show()
            self['min4'].show()
            self['min5'].show()
            self['min6'].show()
            self['min7'].show()
            self['min8'].show()
            self['min9'].show()
        else:
            self['min1'].setText('')
            self['min2'].setText('')
            self['min3'].setText('')
            self['min4'].setText('')
            self['min5'].setText('')
            self['min6'].setText('')
            self['min7'].setText('')
            self['min8'].setText('')
            self['min9'].setText('')
        text = re.findall('<span class="temptext">(.*?)</span>', bereich)
        if text is not None:
            try:
                self['text1'].setText(text[0])
                self['text2'].setText(text[1])
                self['text3'].setText(text[2])
                self['text4'].setText(text[3])
                self['text5'].setText(text[4])
                self['text6'].setText(text[5])
                self['text7'].setText(text[6])
                self['text8'].setText(text[7])
                self['text9'].setText(text[8])
            except IndexError:
                pass

            self['text1'].show()
            self['text2'].show()
            self['text3'].show()
            self['text4'].show()
            self['text5'].show()
            self['text6'].show()
            self['text7'].show()
            self['text8'].show()
            self['text9'].show()
        else:
            self['text1'].setText('')
            self['text2'].setText('')
            self['text3'].setText('')
            self['text4'].setText('')
            self['text5'].setText('')
            self['text6'].setText('')
            self['text7'].setText('')
            self['text8'].setText('')
            self['text9'].setText('')
        pic = re.findall('<img src="http://.*?msn.com/as/wea3/i/de/law/(.*?)[.]gif" height', bereich)
        pic1 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[0] + '.png'
        if fileExists(pic1):
            self.showPic1(pic1)
            self['pic1'].show()
        pic2 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[1] + '.png'
        if fileExists(pic2):
            self.showPic2(pic2)
            self['pic2'].show()
        pic3 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[2] + '.png'
        if fileExists(pic3):
            self.showPic3(pic3)
            self['pic3'].show()
        pic4 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[3] + '.png'
        if fileExists(pic4):
            self.showPic4(pic4)
            self['pic4'].show()
        pic5 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[4] + '.png'
        if fileExists(pic5):
            self.showPic5(pic5)
            self['pic5'].show()
        pic6 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[5] + '.png'
        if fileExists(pic6):
            self.showPic6(pic6)
            self['pic6'].show()
        pic7 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[6] + '.png'
        if fileExists(pic7):
            self.showPic7(pic7)
            self['pic7'].show()
        pic8 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[7] + '.png'
        if fileExists(pic8):
            self.showPic8(pic8)
            self['pic8'].show()
        pic9 = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[8] + '.png'
        if fileExists(pic9):
            self.showPic9(pic9)
            self['pic9'].show()

    def ok(self):
        if self.count == 1:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count = 2
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 2:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count = 3
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 3:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count = 4
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 4:
            if self.count == self.maxlines:
                self.count = 1
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
            else:
                self.count = 5
                if fileExists(self.cityfile):
                    f = open(self.cityfile, 'r')
                    f.readline()
                    f.readline()
                    f.readline()
                    f.readline()
                    city = f.readline()
                    self.city = city.strip()
                    f.close()
        elif self.count == 5:
            self.count = 1
            if fileExists(self.cityfile):
                f = open(self.cityfile, 'r')
                city = f.readline()
                self.city = city.strip()
                f.close()
        elif self.count == 0:
            self.session.openWithCallback(self.citiesReturn, msnCities)
        self.makeWetterTimer.callback.append(self.download(self.city, self.makeWetter))

    def green(self):
        self.session.openWithCallback(self.cityback, msnCity, self.city)

    def yellow(self):
        if self.black == True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('blackdate')
                f.close()
        elif self.black == False:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('bluedate')
                f.close()
        self.session.openWithCallback(self.exit, msnWetterDateMain)

    def cities(self):
        self.session.openWithCallback(self.citiesReturn, msnCities)

    def citiesReturn(self):
        if fileExists(self.cityfile):
            f = open(self.cityfile, 'r')
            city = f.readline()
            self.city = city.strip()
            f.seek(0, 0)
            self.maxlines = 0
            for line in f:
                self.maxlines += 1

            f.close()
            self.count = 1
            if self.maxlines == 0:
                self.count = 0

    def red(self):
        if self.black == False:
            self.session.openWithCallback(self.blackcolor, MessageBox, _('\nFarbe zu Schwarz wechseln?'), MessageBox.TYPE_YESNO)
        elif self.black == True:
            self.session.openWithCallback(self.bluecolor, MessageBox, _('\nFarbe zu Blau wechseln?'), MessageBox.TYPE_YESNO)

    def blackcolor(self, answer):
        if answer is True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('blacknodate')
                f.close()
                self.session.openWithCallback(self.exit, msnWetterMain)

    def bluecolor(self, answer):
        if answer is True:
            if fileExists(self.colorfile):
                f = open(self.colorfile, 'w')
                f.write('bluenodate')
                f.close()
                self.session.openWithCallback(self.exit, msnWetterMain)

    def showPic1(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic1'].instance.setPixmap(currPic)

    def showPic2(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic2'].instance.setPixmap(currPic)

    def showPic3(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic3'].instance.setPixmap(currPic)

    def showPic4(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic4'].instance.setPixmap(currPic)

    def showPic5(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic5'].instance.setPixmap(currPic)

    def showPic6(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic6'].instance.setPixmap(currPic)

    def showPic7(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic7'].instance.setPixmap(currPic)

    def showPic8(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic8'].instance.setPixmap(currPic)

    def showPic9(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic9'].instance.setPixmap(currPic)

    def download(self, link, name):
        self.loadinginprogress = True
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.loadinginprogress = False

    def cityback(self):
        pass

    def hideScreen(self):
        if self.hideflag == True:
            self.hideflag = False
            self.hide()
        else:
            self.hideflag = True
            self.show()

    def exit(self):
        self.close()


class msnCity(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="360,465" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="city" position="10,10" size="340,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="aktuell" position="10,50" size="340,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic" position="57,80" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pictext" position="15,135" size="140,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temp" position="165,90" size="180,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temptext" position="165,135" size="180,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="baro" position="20,175" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="barotext" position="220,175" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tau" position="20,200" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tautext" position="220,200" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="luft" position="20,225" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="lufttext" position="220,225" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sicht" position="20,250" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sichttext" position="220,250" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="nieder" position="20,275" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niedertext" position="220,275" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletzte" position="20,300" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletztetext" position="220,300" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="wind" position="20,325" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="windtext" position="220,325" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauf" position="20,350" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauftext" position="220,350" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneunter" position="20,375" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneuntertext" position="220,375" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uv" position="20,400" size="170,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uvtext" position="220,400" size="130,20" font="Regular;18" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="messstation" position="0,434" size="360,20" font="Regular;16" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="420,540" backgroundColor="#20009ADA" title=" ">\n\t\t\t\t<widget name="city" position="10,10" size="400,30" font="Regular;24" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="aktuell" position="10,55" size="400,25" font="Regular;22" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic" position="77,90" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pictext" position="40,150" size="140,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temp" position="195,100" size="180,30" font="Regular;24" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temptext" position="180,150" size="210,25" font="Regular;20" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="baro" position="20,195" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="barotext" position="260,195" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tau" position="20,225" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tautext" position="260,225" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="luft" position="20,255" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="lufttext" position="260,255" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sicht" position="20,285" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sichttext" position="260,285" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="nieder" position="20,315" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niedertext" position="260,315" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletzte" position="20,345" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletztetext" position="260,345" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="wind" position="20,375" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="windtext" position="260,375" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauf" position="20,405" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauftext" position="260,405" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneunter" position="20,435" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneuntertext" position="260,435" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uv" position="20,465" size="220,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uvtext" position="260,465" size="150,25" font="Regular;20" backgroundColor="#20009ADA" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="messstation" position="0,504" size="420,20" font="Regular;18" backgroundColor="#20009ADA" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinblack = '\n\t\t\t<screen position="center,center" size="360,465" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="city" position="10,10" size="340,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="aktuell" position="10,50" size="340,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic" position="57,80" size="55,45" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pictext" position="15,135" size="140,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temp" position="165,90" size="180,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temptext" position="165,135" size="180,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="baro" position="20,175" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="barotext" position="220,175" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tau" position="20,200" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tautext" position="220,200" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="luft" position="20,225" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="lufttext" position="220,225" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sicht" position="20,250" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sichttext" position="220,250" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="nieder" position="20,275" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niedertext" position="220,275" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletzte" position="20,300" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletztetext" position="220,300" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="wind" position="20,325" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="windtext" position="220,325" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauf" position="20,350" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauftext" position="220,350" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneunter" position="20,375" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneuntertext" position="220,375" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uv" position="20,400" size="170,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uvtext" position="220,400" size="130,20" font="Regular;18" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="messstation" position="0,434" size="360,20" font="Regular;16" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'
    skinHDblack = '\n\t\t\t<screen position="center,center" size="420,540" backgroundColor="#20000000" title=" ">\n\t\t\t\t<widget name="city" position="10,10" size="400,30" font="Regular;24" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="aktuell" position="10,55" size="400,25" font="Regular;22" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="pic" position="77,90" size="66,54" alphatest="blend" zPosition="1" /> \n\t\t\t\t<widget name="pictext" position="40,150" size="140,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temp" position="195,100" size="180,30" font="Regular;24" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="temptext" position="180,150" size="210,25" font="Regular;20" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t\t<widget name="baro" position="20,195" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="barotext" position="260,195" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tau" position="20,225" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="tautext" position="260,225" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="luft" position="20,255" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="lufttext" position="260,255" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sicht" position="20,285" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sichttext" position="260,285" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="nieder" position="20,315" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niedertext" position="260,315" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletzte" position="20,345" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="niederletztetext" position="260,345" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="wind" position="20,375" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="windtext" position="260,375" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauf" position="20,405" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneauftext" position="260,405" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneunter" position="20,435" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="sonneuntertext" position="260,435" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uv" position="20,465" size="220,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="uvtext" position="260,465" size="150,25" font="Regular;20" backgroundColor="#20000000" halign="left" zPosition="1" /> \n\t\t\t\t<widget name="messstation" position="0,504" size="420,20" font="Regular;18" backgroundColor="#20000000" halign="center" zPosition="1" /> \n\t\t\t</screen>'

    def __init__(self, session, link):
        self.loadinginprogress = False
        self.colorfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/color'
        if fileExists(self.colorfile):
            f = open(self.colorfile, 'r')
            data = f.readline()
            f.close()
            if 'blackdate' in data:
                self.black = True
            elif 'blacknodate' in data:
                self.black = True
            else:
                self.black = False
        else:
            self.black = False
        deskWidth = getDesktop(0).size().width()
        if deskWidth == 1280 and self.black == False:
            self.skin = msnCity.skinHD
            self.hd = True
        elif deskWidth == 1280 and self.black == True:
            self.skin = msnCity.skinHDblack
            self.hd = True
        elif deskWidth <= 1025 and self.black == False:
            self.skin = msnCity.skin
            self.hd = False
        elif deskWidth <= 1025 and self.black == True:
            self.skin = msnCity.skinblack
            self.hd = False
        self.session = session
        Screen.__init__(self, session)
        self.aspect = getAspect()
        self.hideflag = True
        self.link = link
        self['pic'] = Pixmap()
        self['city'] = Label('')
        self['aktuell'] = Label('')
        self['pictext'] = Label('')
        self['temp'] = Label('')
        self['temptext'] = Label('')
        self['baro'] = Label('')
        self['barotext'] = Label('')
        self['tau'] = Label('')
        self['tautext'] = Label('')
        self['luft'] = Label('')
        self['lufttext'] = Label('')
        self['sicht'] = Label('')
        self['sichttext'] = Label('')
        self['nieder'] = Label('')
        self['niedertext'] = Label('')
        self['niederletzte'] = Label('')
        self['niederletztetext'] = Label('')
        self['wind'] = Label('')
        self['windtext'] = Label('')
        self['sonneauf'] = Label('')
        self['sonneauftext'] = Label('')
        self['sonneunter'] = Label('')
        self['sonneuntertext'] = Label('')
        self['uv'] = Label('')
        self['uvtext'] = Label('')
        self['messstation'] = Label('')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.exit,
         'cancel': self.exit,
         'green': self.infoScreen,
         'red': self.infoScreen,
         'yellow': self.infoScreen,
         'blue': self.hideScreen}, -1)
        self.makeCityTimer = eTimer()
        self.makeCityTimer.callback.append(self.download(self.link, self.makeCity))
        self.makeCityTimer.start(500, True)

    def makeCity(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<?xml version="1.0" encoding="utf-16"?><span class="location"')
        endpos = find(output, '<span class="boldtext">Vorhersage heute</span>')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        title = re.findall('<title>(.*?)</title>', output)
        title = sub(' [(]weatherlocation[)] - Aktuelle Wetterlage, Wettervorhersage, Niederschlagsvorhersage und Temperaturen bei MSN Wetter.', '', title[0])
        title = transHTML(title)
        self.setTitle(title)
        pic = re.findall('<img src="http://.*?msn.com/as/wea3/i/de/law/(.*?)[.]gif" height', bereich)
        pic = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/' + pic[0] + '.png'
        if fileExists(pic):
            self.showPic(pic)
            self['pic'].show()
        city = re.findall('xmlns:msn="Microsoft.Msn.Composition.Rendering">(.*?)</span></span></h1>', bereich)
        if city is not None:
            try:
                self['city'].setText(city[0])
            except IndexError:
                pass

            self['city'].show()
        aktuell = re.findall('<span class="boldtext">Aktuelle Bedingungen</span>(.*?)</div>', bereich)
        if aktuell is not None:
            try:
                self['aktuell'].setText('Aktuelle Bedingungen' + aktuell[0])
            except IndexError:
                pass

            self['aktuell'].show()
        temp = re.findall('<div class="temperature boldtext">(.*?)</div>', bereich)
        if temp is not None:
            try:
                self['temp'].setText(temp[0])
            except IndexError:
                pass

            self['temp'].show()
        text = re.findall('<div>(.*?)</div>', bereich)
        if text is not None:
            try:
                self['pictext'].setText(text[0])
                self['temptext'].setText(text[1])
            except IndexError:
                pass

            self['pictext'].show()
            self['temptext'].show()
        other = re.findall(' <li class="rgtspace">(.*?)</li>', bereich)
        if other is not None:
            try:
                self['baro'].setText(other[0])
                self['tau'].setText(other[1])
                self['luft'].setText(other[2])
                self['sicht'].setText(other[3])
                self['nieder'].setText(other[4])
                self['niederletzte'].setText(other[5])
                self['wind'].setText(other[6])
                self['sonneauf'].setText(other[7])
                self['sonneunter'].setText(other[8])
                self['uv'].setText(other[9])
            except IndexError:
                pass

            self['baro'].show()
            self['tau'].show()
            self['luft'].show()
            self['sicht'].show()
            self['nieder'].show()
            self['niederletzte'].show()
            self['wind'].show()
            self['sonneauf'].show()
            self['sonneunter'].show()
            self['uv'].show()
        othertext = re.findall(' <li>(.*?)</li>', bereich)
        if othertext is not None:
            try:
                self['barotext'].setText(othertext[0])
                self['tautext'].setText(othertext[1])
                self['lufttext'].setText(othertext[2])
                self['sichttext'].setText(othertext[3])
                self['niedertext'].setText(othertext[4])
                self['niederletztetext'].setText(othertext[5])
                self['windtext'].setText(othertext[6])
                self['sonneauftext'].setText(othertext[7])
                self['sonneuntertext'].setText(othertext[8])
                self['uvtext'].setText(othertext[9])
            except IndexError:
                pass

            self['barotext'].show()
            self['tautext'].show()
            self['lufttext'].show()
            self['sichttext'].show()
            self['niedertext'].show()
            self['niederletztetext'].show()
            self['windtext'].show()
            self['sonneauftext'].show()
            self['sonneuntertext'].show()
            self['uvtext'].show()
        messstation = re.findall('<div class="observedat firstleft">\n      <div>(.*?)</div>', bereich)
        if messstation is not None:
            try:
                self['messstation'].setText(messstation[0])
            except IndexError:
                pass

            self['messstation'].show()

    def showPic(self, pic):
        if self.hd == False:
            currPic = loadPic(pic, 55, 45, self.aspect, 0, 0, 1)
        else:
            currPic = loadPic(pic, 66, 54, self.aspect, 0, 0, 1)
        if currPic != None:
            self['pic'].instance.setPixmap(currPic)

    def download(self, link, name):
        self.loadinginprogress = True
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.loadinginprogress = False

    def infoScreen(self):
        self.session.open(infoMSNWetter)

    def hideScreen(self):
        if self.hideflag == True:
            self.hideflag = False
            self.hide()
        else:
            self.hideflag = True
            self.show()

    def exit(self):
        self.close()


class msnCities(Screen):
    skin = '\n\t\t\t<screen position="center,center" size="300,500" backgroundColor="#20000000" title="msn Wetter: Stadt hinzuf\xc3\xbcgen">\n\t\t\t\t<widget name="list" position="0,0" size="300,500" scrollbarMode="showNever" zPosition="1" />\n\t\t\t</screen>'
    skinHD = '\n\t\t\t<screen position="center,center" size="400,600" backgroundColor="#20000000" title="msn Wetter: Stadt hinzuf\xc3\xbcgen">\n\t\t\t\t<widget name="list" position="0,0" size="400,600" scrollbarMode="showNever" zPosition="1" />\n\t\t\t</screen>'

    def __init__(self, session):
        self.loadinginprogress = False
        deskWidth = getDesktop(0).size().width()
        if deskWidth == 1280:
            self.skin = msnCities.skinHD
        elif deskWidth <= 1025:
            self.skin = msnCities.skin
        Screen.__init__(self, session)
        self.hideflag = True
        self.count = 1
        self['list'] = MenuList([])
        self.listentries = []
        self.citylinks = []
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {'ok': self.ok,
         'cancel': self.exit,
         'right': self.rightDown,
         'left': self.leftUp,
         'down': self.down,
         'up': self.up,
         'red': self.infoScreen,
         'green': self.infoScreen,
         'yellow': self.infoScreen,
         'blue': self.hideScreen}, -1)
        self.cityfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/city'
        self.link = 'http://wetter.msn.com/'
        self.link2 = ''
        self.link3 = ''
        self.link4 = ''
        self.link5 = ''
        self.name = 'Keine Stadt'
        self.index1 = 0
        self.index2 = 0
        self.index3 = 0
        self.makeCityTimer = eTimer()
        self.makeCityTimer.callback.append(self.download(self.link, self.makeAreaList))
        self.makeCityTimer.start(500, True)

    def makeAreaList(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<span class="text">Weltwetter nach Region</span>')
        endpos = find(output, '</ul></div></div></div><div id="wetterwiki"')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        link = re.findall('<a href="(.*?)">', bereich)
        name = re.findall('">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                self.listentries.append(name[i])
                self.citylinks.append(link[i])
            except IndexError:
                pass

        self.listentries.sort()
        self.citylinks.sort()
        self['list'].l.setList(self.listentries)
        self['list'].moveToIndex(self.index1)

    def makeRegion2List(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<div class="wn_links cf">')
        endpos = find(output, '<span class="text">Ausgew\xc3\xa4hlte St\xc3\xa4dte</span>')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        bereich = sub('"><div ', '', bereich)
        bereich = sub('"><ul ', '', bereich)
        bereich = sub('"><li ', '', bereich)
        bereich = sub('"><span ', '', bereich)
        bereich = sub('locationname">', '', bereich)
        lnk = re.findall('<a href="(.*?)">', bereich)
        name = re.findall('">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://wetter.msn.com/' + lnk[i]
                self.listentries.append(name[i])
                self.citylinks.append(link)
            except IndexError:
                pass

        self.listentries.sort()
        self.citylinks.sort()
        self['list'].l.setList(self.listentries)
        self['list'].moveToIndex(self.index2)

    def makeRegion3List(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<div class="wn_links cf">')
        endpos = find(output, '<span class="text">Ausgew\xc3\xa4hlte St\xc3\xa4dte</span>')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        bereich = sub('"><div ', '', bereich)
        bereich = sub('"><ul ', '', bereich)
        bereich = sub('"><li ', '', bereich)
        bereich = sub('"><span ', '', bereich)
        bereich = sub('locationname">', '', bereich)
        lnk = re.findall('<a href="(.*?)">', bereich)
        name = re.findall('">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                link = 'http://wetter.msn.com/' + lnk[i]
                self.listentries.append(name[i])
                self.citylinks.append(link)
            except IndexError:
                pass

        self.listentries.sort()
        self.citylinks.sort()
        self['list'].l.setList(self.listentries)
        self['list'].moveToIndex(self.index3)

    def makeCityList(self, output):
        self.loadinginprogress = False
        startpos = find(output, '<div class="weacities cf">')
        endpos = find(output, '<script type="text/javascript">/*<![CDATA[*/$.weatherWorldCities')
        bereich = output[startpos:endpos]
        bereich = transHTML(bereich)
        bereich = sub('"><ul ', '', bereich)
        bereich = sub('"><li ', '', bereich)
        bereich = sub('"><span ', '', bereich)
        bereich = sub('city">', '', bereich)
        bereich = sub('temp">', '', bereich)
        link = re.findall('<a href="(.*?)">', bereich)
        name = re.findall('">(.*?)</a>', bereich)
        idx = 0
        for x in name:
            idx += 1

        for i in range(idx):
            try:
                self.listentries.append(name[i])
                self.citylinks.append(link[i])
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)
        self['list'].moveToIndex(0)

    def ok(self):
        if self.count == 1:
            self.count += 1
            try:
                c = self['list'].getSelectedIndex()
                self.index1 = c
                self.link2 = self.citylinks[c]
                self.download(self.link2, self.makeRegionOrCityLink2)
            except IndexError:
                pass

        elif self.count == 2:
            self.count += 1
            try:
                c = self['list'].getSelectedIndex()
                self.index2 = c
                self.link3 = self.citylinks[c]
                self.download(self.link3, self.makeRegionOrCityLink3)
            except IndexError:
                pass

        elif self.count == 3:
            self.count += 1
            try:
                c = self['list'].getSelectedIndex()
                self.link4 = self.citylinks[c]
                self.listentries = []
                self.citylinks = []
                self.makeCityTimer.callback.append(self.download(self.link4, self.makeCityList))
            except IndexError:
                pass

        elif self.count == 4:
            try:
                c = self['list'].getSelectedIndex()
                self.link5 = self.citylinks[c]
                self.name = self.listentries[c]
                f = open(self.cityfile, 'a')
                f.write(self.link5)
                f.write(os.linesep)
                f.close()
                self.session.open(MessageBox, _('\n%s wurde hinzugef\xc3\xbcgt.') % self.name, MessageBox.TYPE_INFO, timeout=5)
                f = open(self.cityfile, 'r')
                count = 0
                for line in f:
                    count += 1

                if count >= 6:
                    f.seek(0)
                    lines = f.readlines()
                    fnew = open(self.cityfile + '.new', 'w')
                    fnew.writelines(lines[-5:])
                    fnew.close()
                    f.close()
                    os.rename(self.cityfile + '.new', self.cityfile)
                else:
                    f.close()
                self.close()
            except IndexError:
                pass

    def makeRegionOrCityLink2(self, output):
        self.listentries = []
        self.citylinks = []
        if search('<[?]xml version="1.0" encoding="utf-16"[?]><div class="wn_links cf">', output) is not None:
            self.makeCityTimer.callback.append(self.download(self.link2, self.makeRegion2List))
        else:
            self.count += 2
            self.makeCityTimer.callback.append(self.download(self.link2, self.makeCityList))

    def makeRegionOrCityLink3(self, output):
        self.listentries = []
        self.citylinks = []
        if search('<[?]xml version="1.0" encoding="utf-16"[?]><div class="wn_links cf">', output) is not None:
            self.makeCityTimer.callback.append(self.download(self.link3, self.makeRegion3List))
        else:
            self.count += 1
            self.makeCityTimer.callback.append(self.download(self.link3, self.makeCityList))

    def down(self):
        self['list'].down()

    def up(self):
        self['list'].up()

    def rightDown(self):
        self['list'].pageDown()

    def leftUp(self):
        self['list'].pageUp()

    def download(self, link, name):
        self.loadinginprogress = True
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        self.loadinginprogress = False

    def infoScreen(self):
        self.session.open(infoMSNWetter)

    def hideScreen(self):
        if self.hideflag == True:
            self.hideflag = False
            self.hide()
        else:
            self.hideflag = True
            self.show()

    def exit(self):
        if self.count >= 3:
            self.count = 2
            self.listentries = []
            self.citylinks = []
            self.download(self.link2, self.makeRegion2List)
        elif self.count == 2:
            self.count = 1
            self.listentries = []
            self.citylinks = []
            self.download(self.link, self.makeAreaList)
        else:
            self.close()


class infoMSNWetter(Screen):
    skin = '\n\t\t\t\t<screen position="center,center" size="229,196" title="msn Wetter 0.4" >\n\t\t\t\t\t<ePixmap position="0,0" size="229,196" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/icons/wetter/msnlogo.png" zPosition="1"/>\n\t\t\t\t\t<widget name="label" position="22,174" size="200,20" font="Regular;16" foregroundColor="#FCFCFC" backgroundColor="#14547C" halign="right" valign="center" transparent="1" zPosition="2" />\n\t\t\t\t</screen>'

    def __init__(self, session):
        self.skin = infoMSNWetter.skin
        Screen.__init__(self, session)
        self['label'] = Label('2012 by kashmir')
        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.close,
         'cancel': self.close}, -1)


def main(session, **kwargs):
    colorfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/color'
    if fileExists(colorfile):
        f = open(colorfile, 'r')
        data = f.readline()
        f.close()
        if 'bluedate' in data:
            session.open(msnWetterDateMain)
        elif 'blackdate' in data:
            session.open(msnWetterDateMain)
        elif 'bluenodate' in data:
            session.open(msnWetterMain)
        elif 'blacknodate' in data:
            session.open(msnWetterMain)


def Plugins(**kwargs):
    return [PluginDescriptor(name='msn Wetter', description='msn Wettervorhersage', where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main), PluginDescriptor(name='msn Wetter', description='msn Wettervorhersage', where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]