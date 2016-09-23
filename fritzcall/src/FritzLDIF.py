# -*- coding: utf-8 -*-
'''
$Author: michael $
$Revision: 1290 $
$Date: 2016-05-01 18:09:29 +0200 (Sun, 01 May 2016) $
$Id: FritzLDIF.py 1290 2016-05-01 16:09:29Z michael $
'''
#
# needs python-ldap for ldif
#

import ldif, re
try:
	from . import _, normalizePhoneNumber #@UnresolvedImport # pylint: disable-msg=F0401
except ValueError:
	def _(string): # pylint: disable-msg=C0103
		return string
	
	def normalizePhoneNumber(intNo):
		found = re.match('^\+49(.*)', intNo)
		if found:
			intNo = '0' + found.group(1)
		found = re.match('^\+(.*)', intNo)
		if found:
			intNo = '00' + found.group(1)
		intNo = intNo.replace('(', '').replace(')', '').replace(' ', '').replace('/', '').replace('-', '')
		found = re.match('^49(.*)', intNo) # this is most probably an error
		if found:
			intNo = '0' + found.group(1)
		found = re.match('.*?([0-9]+)', intNo)
		if found:
			return found.group(1)
		else:
			return '0'

import logging
logger = logging.getLogger("[FritzCall] LDIF")
debug = logger.debug

def out(number, name):
	print number + '#' + name

class FindNumber(ldif.LDIFParser):
	def __init__(self, number, inp, outFun):
		ldif.LDIFParser.__init__(self, inp)
		self.outFun = outFun
		self.number = number
		try:
			self.parse()
		except ValueError:
			# this is to exit the parse loop
			pass

	def handle(self, dn, entry):
		# debug("[FritzCallPhonebook] LDIF handle: " + dn)
		found = re.match('.*cn=(.*),', str(dn))
		if found:
			name = found.group(1)
		else:
			return
	
		address = ""
		addressB = ""
		if entry.has_key('telephoneNumber') or (entry.has_key('homePhone') and self.number == normalizePhoneNumber(entry['homePhone'][0])) or (entry.has_key('mobile') and self.number == normalizePhoneNumber(entry['mobile'][0])):
			# debug("[FritzCallPhonebook] LDIF get address")
			if entry.has_key('telephoneNumber'):
				no = normalizePhoneNumber(entry['telephoneNumber'][0])
			else:
				no = 0
			if self.number == no or (entry.has_key('homePhone') and self.number == normalizePhoneNumber(entry['homePhone'][0])) or (entry.has_key('mobile') and self.number == normalizePhoneNumber(entry['mobile'][0])):
				nameB = (name + ' (' + _('business') + ')') if name else ""
				if entry.has_key('company'):
					nameB = (nameB + ', ' + entry['company'][0]) if nameB else entry['company'][0]
				if entry.has_key('l'):
					addressB = entry['l'][0]
					if entry.has_key('postalCode'):
						addressB = entry['postalCode'][0] + ' ' + addressB
					if entry.has_key('c'):
						addressB = addressB + ', ' + entry['c'][0]
					if entry.has_key('street'):
						addressB = entry['street'][0] + ', ' + addressB
					# debug("[FritzCallPhonebook] LDIF address: " + addressB)
					if self.number == no:
						result = nameB + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
				else:
					if self.number == no:
						result = nameB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
		for i in ['homePhone', 'mobile']:
			if entry.has_key(i):
				no = normalizePhoneNumber(entry[i][0])
				if self.number == no:
					if i == 'mobile':
						name = name + ' (' + _('mobile') + ')'
					else:
						name = name + ' (' + _('home') + ')'
					if entry.has_key('mozillaHomeLocalityName'):
						address = entry['mozillaHomeLocalityName'][0]
						if entry.has_key('mozillaHomePostalCode'):
							address = entry['mozillaHomePostalCode'][0] + ' ' + address
						if entry.has_key('mozillaHomeCountryName'):
							address = address + ', ' + entry['mozillaHomeCountryName'][0]
							debug("[FritzCallPhonebook] LDIF home address: " + addressB)
						result = name + ', ' + address.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
					else:
						if addressB:
							name = name + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + name)
						self.outFun(no, name)
						self._input_file.close()
						return

class ReadNumbers(ldif.LDIFParser):
	def __init__(self, inPut, outFun):
		ldif.LDIFParser.__init__(self, inPut)
		self.outFun = outFun
		try:
			self.parse()
		except ValueError:
			#
			# this is to exit the parse loop:
			# we close the input file as soon as we have a result...
			#
			pass

	def handle(self, dn, entry):
		# debug("[FritzCallPhonebook] LDIF handle: " + dn)
		found = re.match('.*cn=(.*),', str(dn))
		if found:
			name = found.group(1)
		else:
			return
	
		address = ""
		addressB = ""
		if entry.has_key('telephoneNumber') or entry.has_key('homePhone') or entry.has_key('mobile'):
			# debug("[FritzCallPhonebook] LDIF get address")
			nameB = (name + ' (' + _('business') + ')') if name else ""
			if entry.has_key('company'):
				nameB = (nameB + ', ' + entry['company'][0]) if nameB else entry['company'][0]
			if entry.has_key('l'):
				addressB = entry['l'][0]
				if entry.has_key('postalCode'):
					addressB = entry['postalCode'][0] + ' ' + addressB
				if entry.has_key('c'):
					addressB = addressB + ', ' + entry['c'][0]
				if entry.has_key('street'):
					addressB = entry['street'][0] + ', ' + addressB
				# debug("[FritzCallPhonebook] LDIF address: " + addressB)
				if entry.has_key('telephoneNumber'):
					no = normalizePhoneNumber(entry['telephoneNumber'][0])
					result = nameB + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
			else:
				if entry.has_key('telephoneNumber'):
					no = normalizePhoneNumber(entry['telephoneNumber'][0])
					result = nameB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
		for i in ['homePhone', 'mobile']:
			if entry.has_key(i):
				no = normalizePhoneNumber(entry[i][0])
				if i == 'mobile':
					nameHM = name + ' (' + _('mobile') + ')'
				else:
					nameHM = name + ' (' + _('home') + ')'
				if entry.has_key('mozillaHomeLocalityName'):
					address = entry['mozillaHomeLocalityName'][0]
					if entry.has_key('mozillaHomePostalCode'):
						address = entry['mozillaHomePostalCode'][0] + ' ' + address
					if entry.has_key('mozillaHomeCountryName'):
						address = address + ', ' + entry['mozillaHomeCountryName'][0]
					result = nameHM + ', ' + address.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
				else:
					if addressB:
						nameHM = nameHM + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, nameHM)

def lookedUp(number, name):
	print number + ' ' + name

if __name__ == '__main__':
	import os, sys
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 1):
		ReadNumbers(open("Kontakte.ldif"), out)
	elif (len(sys.argv) == 2):
		# nrzuname.py Nummer
		FindNumber(sys.argv[1], open("Kontakte.ldif"), lookedUp)
