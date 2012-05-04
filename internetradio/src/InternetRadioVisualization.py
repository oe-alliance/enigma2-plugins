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

from Components.ProgressBar import ProgressBar
from Components.Pixmap import Pixmap
from enigma import ePoint
import time

class InternetRadioVisualization(object):
	BANDS = 16
	def __init__(self):
		self.pegelvalues = {}
		self.bars = {}
		self.topbars = {}
		i = 0
		while True:
			self["progress_%d" % i] = ProgressBar()
			self["top_%d" % i] = Pixmap()
			self["top_%d" % i].hide()
			self.pegelvalues[i] = (0, time.time(),0, 1)
			i  += 1
			if i == self.BANDS:
				break

	def setProperties(self):
		i = 0
		while True:
			self.bars[i] = (self["progress_%d"%i].instance.size().height(), self["progress_%d"%i].instance.size().height() + self["progress_%d"%i].instance.position().y(), self["top_%d"%i].instance.size().height())
			i  += 1
			if i == self.BANDS:
				break

	def setPBtoNull(self):
		i = 0
		while True:
			self["progress_%d" % i].setValue(0)
			i  += 1
			if i == self.BANDS:
				break

	def hideControls(self):
		i = 0
		while True:
			self["progress_%d" % i].setValue(0)
			self["top_%d" % i].hide()
			self.pegelvalues[i] = (0, time.time(),0, 1)
			i  += 1
			if i == self.BANDS:
				break

	def setValues(self, v):
		i = 0
		while True:
			barvalues = self.bars.get(i,(0,0,0))
			progressbarHeight = barvalues[0]
			value = int(1.25 * (v[i] + 80))
			currentvalue = int(value*progressbarHeight/100)
			oldvalue = self.pegelvalues.get(i,None)
			if currentvalue <= 0:
				hide = 1
			else:
				hide = 0
			if oldvalue:
				if oldvalue[0] < currentvalue:
					self.pegelvalues[i] = (currentvalue, time.time(),0,hide)
					if hide:
						self["top_%d" % i].hide()
					else:
						if oldvalue[3]:
							self["top_%d" % i].show()
						self["top_%d" % i].instance.move(ePoint(self["top_%d" % i].instance.position().x(), barvalues[1] - currentvalue - barvalues[2]))
				elif oldvalue[0] > currentvalue:
					d = time.time()
					if (d - oldvalue[1] > 0.7 and oldvalue[2] == 0) or (d - oldvalue[1] > 0.1 and oldvalue[2] == 1) or (oldvalue[2] >= 2):
						if oldvalue[2] > 4:
							currentvalue = oldvalue[0] - int(0.1 * progressbarHeight)
						elif oldvalue[2] > 2:
							currentvalue = oldvalue[0] - int(0.06 * progressbarHeight)
						else:
							currentvalue = oldvalue[0] - int(0.03 * progressbarHeight)
						if currentvalue <= 0:
							hide = 1
						else:
							hide = 0
						self.pegelvalues[i] = (currentvalue, d,oldvalue[2]+1,hide)
						if hide:
							self["top_%d" % i].hide()
						else:
							self["top_%d" % i].instance.move(ePoint(self["top_%d" % i].instance.position().x(), barvalues[1] - currentvalue - barvalues[2]))
				else:
					self.pegelvalues[i] = (currentvalue, time.time(),0,hide)
			else:
				self.pegelvalues[i] = (currentvalue, time.time(),0, hide)
				if hide:
					self["top_%d" % i].hide()
				else:	
					self["top_%d" % i].instance.move(ePoint(self["top_%d" % i].instance.position().x(), barvalues[1] - currentvalue - barvalues[2]))
			self["progress_%d" % i].setValue(value)
			i += 1
			if i == len(v):
				break

	def needCleanup(self):
		cleanup = False
		i = 0
		while True:
			oldvalue = self.pegelvalues.get(i,None)
			if oldvalue and oldvalue[3] == 0:
				cleanup = True
				break
			i  += 1
			if i == self.BANDS:
				break
		return cleanup
