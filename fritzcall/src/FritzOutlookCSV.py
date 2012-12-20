# -*- coding: utf-8 -*-
'''
$Author: michael $
$Revision: 699 $
$Date: 2012-10-25 19:04:03 +0200 (Do, 25. Okt 2012) $
$Id: FritzOutlookCSV.py 699 2012-10-25 17:04:03Z michael $
'''
#
# needs python-textutils for csv
#
try:
	from . import _, debug, normalizePhoneNumber #@UnresolvedImport # pylint: disable-msg=W0613,F0401
except ValueError:
	def _(string): # pylint: disable-msg=C0103
		return string
	
	def debug(text):
		print text
	
	import re
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

def out(number, name):
	print number + '#' + name

import csv
#
# 31: Telefon geschäftlich
# 37: Telefon privat
# 40: Mobiltelefon
# 1: Vorname
# 3: Nachname
# 5: Firma
# 8: Straße geschäftlich
# 11: Ort geschäftlich
# 13: Postleitzahl geschäftlich
# 14: Land/Region geschäftlich
# 15: Straße privat
# 18: Ort privat
# 20: Postleitzahl privat
# 21: Land/Region privat
#

def findNumber(number, filename):
	fileD = open(filename)
	if not fileD:
		return
	addrs = csv.reader(fileD, delimiter=',', quotechar='"')
	addrs.next() # skip header
	for row in addrs:
		row = map(lambda w: w.decode('cp1252').encode('utf-8'), row)
		name = u""
		nameB = u""
		address = u""
		addressB = u""
		try: # this is just to catch wrong lines
			if row[31] or (row[37] and number == normalizePhoneNumber(row[37])) or (row[40] and number == normalizePhoneNumber(row[40])): # Telefon geschäftlich
				no = normalizePhoneNumber(row[31])
				# debug("[FritzOutlookCSV] findNumber compare (business) %s with %s for %s" %(no,number,name))
				if no == number or (row[37] and number == normalizePhoneNumber(row[37])) or (row[40] and number == normalizePhoneNumber(row[40])):
					if row[3]:
						name = row[3] # Nachname
					if row[1]:
						if name:
							name = row[1] + ' ' + name # Vorname
						else:
							name = row[1]
					if row[5]: # Firma
						if name:
							nameB = name
							addressB = row[5]
						else:
							nameB = row[5]
					else:
						nameB = name
					if not nameB:
						continue
					nameB = (nameB + ' (' + _('work') + ')')
					if row[11]: # Ort geschäftlich
						addressB = row[11]
						if row[13]:
							addressB =  row[13] + ' ' + addressB# Postleitzahl geschäftlich
						if row[14]:
							addressB = addressB + ', ' + row[14] # Land/Region geschäftlich
						if row[8]:
							addressB = row[8] + ', ' + addressB# Stra￟e gesch￤ftlich
						nameB = (nameB + ', ' + addressB).replace('\n', ', ').replace('\r', '').replace('#', '')
	
					if no == number:
						debug("[FritzCallPhonebook] findNumber result: " + no + ' ' + nameB)
						fileD.close()
						return nameB
			for i in [37, 40]:
				if row[i]:
					number = normalizePhoneNumber(row[i])
					# debug("[FritzOutlookCSV] findNumber compare (home,mobile) %s with %s for %s" %(number,number,name))
					if number == number:
						if row[3]:
							name = row[3] # Nachname
						if row[1]:
							if name:
								name = row[1] + ' ' + name # Vorname
							else:
								name = row[1]
						if i == 40: # Mobiltelefon
							nameHM = name + ' (' + _('mobile') + ')'
						else:
							nameHM = name + ' (' + _('home') + ')'
						if row[18]: # Ort privat
							address = row[18]
							if row[20]:
								address = row[20] + ' ' + address # Postleitzahl privat
							if row[21]:
								address = address + ', ' + row[21] # Land/Region privat
							if row[15]:
								address = row[15] + ', ' + address # Straße privat
						if not address:
							address = addressB
						if address:
							nameHM = nameHM + ', ' + address
						nameHM = nameHM.replace('\n', ', ').replace('\r', '').replace('#', '')
						fileD.close()
						debug("[FritzCallPhonebook] findNumber result: " + number + ' ' + nameHM)
						return nameHM
		except IndexError:
			continue
	fileD.close()
	return ""
	
def readNumbers(filename, outFun):
	fileD = open(filename, "rb")
	if not fileD:
		return
	addrs = csv.reader(fileD, delimiter=',', quotechar='"')
	addrs.next() # skip header
	for row in addrs:
		row = map(lambda w: w.decode('cp1252'), row)
		name = u""
		nameB = u""
		address = u""
		addressB = u""
		try:
			if row[31] or row[37] or row[40]:
				if row[3]:
					name = row[3] # Nachname
				if row[1]:
					if name:
						name = row[1] + ' ' + name # Vorname
					else:
						name = row[1]
				if row[5]: # Firma
					if name:
						nameB = name
						addressB = row[5]
					else:
						nameB = row[5]
				else:
					nameB = name
				if not nameB:
					continue
				nameB = (nameB + ' (' + _('work') + ')')
				if row[11]: # Ort gesch￤ftlich
					addressB = row[11]
					if row[13]:
						addressB =  row[13] + ' ' + addressB# Postleitzahl gesch￤ftlich
					if row[14]:
						addressB = addressB + ', ' + row[14] # Land/Region gesch￤ftlich
					if row[8]:
						addressB = row[8] + ', ' + addressB# Stra?e gesch?ftlich
					nameB = (nameB + ', ' + addressB).replace('\n', ', ').replace('\r', '').replace('#', '')
				if row[31]:
					number = normalizePhoneNumber(row[31])
					outFun(number, nameB)

			for i in [37, 40]:
				if row[i]:
					number = normalizePhoneNumber(row[i])
					nameHM = nameB
					if row[3]:
						nameHM = row[3] # Nachname
					if row[1]:
						if nameHM:
							nameHM = row[1] + ' ' + nameHM # Vorname
						else:
							nameHM = row[1]
					if i == 40: # Mobiltelefon
						nameHM = nameHM + ' (' + _('mobile') + ')'
					else:
						nameHM = nameHM + ' (' + _('home') + ')'
					if row[18]: # Ort privat
						address = row[18]
						if row[20]:
							address = row[20] + ' ' + address # Postleitzahl privat
						if row[21]:
							address = address + ', ' + row[21] # Land/Region privat
						if row[15]:
							address = row[15] + ', ' + address # Stra￟e privat
					if not address:
						address = addressB
					if address:
						nameHM = nameHM + ', ' + address
					nameHM = nameHM.replace('\n', ', ').replace('\r', '').replace('#', '')
					outFun(number, nameHM)

		except IndexError:
			continue
	fileD.close()

if __name__ == '__main__':
	import os, sys
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 1):
		readNumbers("Kontakte.csv", out)
	elif (len(sys.argv) == 2):
		# nrzuname.py Nummer
		findNumber(sys.argv[1], "Kontakte.csv")
