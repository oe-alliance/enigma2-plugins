#!/usr/bin/python
# based on code from pyLoad: http://pyload.org/
from Crypto.Cipher import AES
from DLC import DLC
from MultipartPostHandler import MultipartPostHandler
import base64, binascii, os, random, re, urllib2

def decryptDlc(infile):
	dlc = DLC(None)
	dlc.proceed(infile, "/tmp")
	return dlc.links

def decryptCcf(infile):
	opener = urllib2.build_opener(MultipartPostHandler)
	tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', {"src": "ccf", "filename": "test.ccf", "upload": open(infile, "rb")}).read()
	random.seed()
	tempdlc_name = '/tmp/' + str(random.randint(0, 100)) + '-tmp.dlc'
	while os.path.exists(tempdlc_name):
		tempdlc_name = '/tmp/' + str(random.randint(0, 100)) + '-tmp.dlc'
	tempdlc = open(tempdlc_name, "w")
	tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
	tempdlc.close
	return tempdlc_name

def decryptRsdf(infile):
	links = []
	Key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')
	IV = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
	IV_Cipher = AES.new(Key, AES.MODE_ECB)
	IV = IV_Cipher.encrypt(IV)
	obj = AES.new(Key, AES.MODE_CFB, IV)
	rsdf = open(infile, 'r')
	data = rsdf.read()
	data = binascii.unhexlify(''.join(data.split()))
	data = data.splitlines()
	for link in data:
		link = base64.b64decode(link)
		link = obj.decrypt(link)
		decryptedUrl = link.replace('CCF: ', '')
		links.append(decryptedUrl)
	rsdf.close()
	return links

def decrypt(infile):
	if infile.lower().endswith(".rsdf"):
		return decryptRsdf(infile)
	elif infile.lower().endswith(".ccf"):
		infile = decryptCcf(infile)
		return decryptDlc(infile)
	elif infile.lower().endswith(".dlc"):
		return decryptDlc(infile)

##TESTS
#infile = "/tmp/container/test.dlc"
#print "Decrypting %s..."%infile
#links = decrypt(infile)
#print "Links:"
#print links
