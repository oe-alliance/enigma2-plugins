#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Screens.Screen import Screen
from Components.ProgressBar import ProgressBar
from Components.Pixmap import Pixmap
from Components.Label import Label
from InternetRadioVisualization import InternetRadioVisualization

class InternetRadioOledDisplay(Screen, InternetRadioVisualization):

		# helper for skinning
#		skincontent = ""
#		skincontent2 = ""
#		count = 16
#		x = 0
#		posx = 1
#		skinid = 0
#		while True:
#			skincontent += "<widget name=\"progress_%d\" zPosition=\"3\" position=\"%d,5\" size=\"5,50\" transparent=\"1\" orientation=\"orBottomToTop\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png\" />\n" % (x,posx)
#			skincontent2 += "<widget name=\"top_%d\" position=\"%d,5\" zPosition=\"6\" size=\"5,2\" transparent=\"1\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png\" />\n" % (x,posx)
#			posx += 6
#			x += 1
#			if x == count:
#				break

	skin = ("""
		<screen name="InternetRadioOledDisplay" position="0,0" size="96,64" id="2">
			<widget name="text1" position="4,0" size="96,14" font="Regular;12" halign="center" valign="center"/>
			<widget name="text2" position="4,14" size="96,49" font="Regular;10" halign="center" valign="center"/>
			<widget name="progress_0" zPosition="3" position="1,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_1" zPosition="3" position="7,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_2" zPosition="3" position="13,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_3" zPosition="3" position="19,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_4" zPosition="3" position="25,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_5" zPosition="3" position="31,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_6" zPosition="3" position="37,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_7" zPosition="3" position="43,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_8" zPosition="3" position="49,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_9" zPosition="3" position="55,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_10" zPosition="3" position="61,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_11" zPosition="3" position="67,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_12" zPosition="3" position="73,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_13" zPosition="3" position="79,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_14" zPosition="3" position="85,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="progress_15" zPosition="3" position="91,5" size="5,50" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled-fs8.png" />
			<widget name="top_0" position="1,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_1" position="7,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_2" position="13,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_3" position="19,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_4" position="25,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_5" position="31,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_6" position="37,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_7" position="43,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_8" position="49,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_9" position="55,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_10" position="61,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_11" position="67,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_12" position="73,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_13" position="79,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_14" position="85,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
			<widget name="top_15" position="91,5" zPosition="6" size="5,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_oled_top-fs8.png" />
		</screen>""","""
		<screen name="InternetRadioOledDisplay" position="0,0" size="132,64" id="1">
			<widget name="text1" position="4,0" size="132,14" font="Regular;12" halign="center" valign="center"/>
			<widget name="text2" position="4,14" size="132,49" font="Regular;10" halign="center" valign="center"/>
			<widget name="progress_0" zPosition="3" position="2,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_1" zPosition="3" position="10,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_2" zPosition="3" position="18,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_3" zPosition="3" position="26,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_4" zPosition="3" position="34,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_5" zPosition="3" position="42,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_6" zPosition="3" position="50,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_7" zPosition="3" position="58,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_8" zPosition="3" position="66,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_9" zPosition="3" position="74,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_10" zPosition="3" position="82,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_11" zPosition="3" position="90,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_12" zPosition="3" position="98,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_13" zPosition="3" position="106,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_14" zPosition="3" position="114,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="progress_15" zPosition="3" position="122,5" size="7,50" transparent="1" orientation="orBottomToTop" />
			<widget name="top_0" position="2,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_1" position="10,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_2" position="18,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_3" position="26,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_4" position="34,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_5" position="42,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_6" position="50,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_7" position="58,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_8" position="66,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_9" position="74,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_10" position="82,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_11" position="90,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_12" position="98,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_13" position="106,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_14" position="114,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
			<widget name="top_15" position="122,5" zPosition="6" size="7,2" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/topvalue-lcd-fs8.png" />
		</screen>""")


	def __init__(self, session, parent):
		Screen.__init__(self, session)
		InternetRadioVisualization.__init__(self)
		self["text1"] =  Label(_("Internet Radio"))
		self["text2"] = Label("")
		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		self.setProperties()
		self.hideControls()
		self["text1"].hide()
		self["text2"].hide()

	def setText(self, text):
		self["text2"].setText(text)

	def setLabelVisibility(self,value):
		if value:
			self["text1"].show()
			self["text2"].show()
			self.hideControls()
			
		else:
			self["text1"].hide()
			self["text2"].hide()


