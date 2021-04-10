from __future__ import print_function
############################################################################
#    Copyright (C) 2008 by Volker Christian                                #
#    Volker.Christian@fh-hagenberg.at                                      #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

import socket

from six.moves.urllib.parse import quote
from six.moves import http_client


class GoogleSuggestions():
	def __init__(self, callback, ds=None, json=None, hl=None):
		self.callback = callback
		self.conn = http_client.HTTPConnection("google.com")
		self.prepQuerry = "/complete/search?"
		if ds is not None:
			self.prepQuerry = self.prepQuerry + "ds=" + ds + "&"
		if json is not None:
			self.prepQuerry = self.prepQuerry + "json=" + json + "&"
		if hl is not None:
			self.prepQuerry = self.prepQuerry + "hl=" + hl + "&"
		self.prepQuerry = self.prepQuerry + "jsonp=self.gotSuggestions&q="

	def gotSuggestions(self, suggestslist):
		self.callback(suggestslist)

	def getSuggestions(self, querryString):
		if querryString != "":
			querry = self.prepQuerry + quote(querryString)
			try:
				self.conn.request("GET", querry)
			except (http_client.CannotSendRequest, socket.gaierror, socket.error):
				print("[YTB] Can not send request for suggestions")
				self.callback(None)
			else:
				try:
					response = self.conn.getresponse()
				except http_client.BadStatusLine:
					print("[YTB] Can not get a response from google")
					self.callback(None)
				else:
					if response.status == 200:
						data = response.read()
						exec(data)
					else:
						self.callback(None)
			self.conn.close()
		else:
			self.callback(None)


#class GoogleSuggestions():
#	def __init__(self, callback, ds = None, json = None, hl = None):
#		self.callback = callback
#		self.prepQuerry = "http://www.google.com/complete/search?"
#		if ds is not None:
#			self.prepQuerry = self.prepQuerry + "ds=" + ds + "&"
#		if json is not None:
#			self.prepQuerry = self.prepQuerry + "json=" + json + "&"
#		if hl is not None:
#			self.prepQuerry = self.prepQuerry + "hl=" + hl + "&"
#		self.prepQuerry = self.prepQuerry + "jsonp=self.gotSuggestions&q="
#
#
#	def gotSuggestions(self, suggestslist):
#		self.callback(suggestslist)
#
#		
#	def getSuggestions(self, querryString):
#		if querryString is not "":
#			querry = self.prepQuerry + urllib.quote(querryString)
#			try:
#				filehandler = urllib.urlopen(url = querry)
#			except IOError e:
#				print "[YTB] Error during urlopen: ", e
#				self.callback(None)
#			else:
#				try:
#					content = filehandler.read()
#					filehandler.close()
#				except IOError e:
#					print "[YTB] Error during read: ", e
#					self.callback(None)
#				else:
#					exec content
#		else:
#			self.callback(None)
