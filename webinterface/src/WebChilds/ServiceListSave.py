from twisted.web import resource, http, server
from enigma import eDVBDB
import os
from xml.dom.minidom import parseString as xml_dom_minidom_parseString
from urllib import unquote as urllib_unquote
##########################
class ServiceList(resource.Resource):
	def __init__(self, session):
		
		self.session = session
		resource.Resource.__init__(self)
		self.putChild("reload", ServiceListReload())
		self.putChild("save", ServiceListSave())

class ServiceListReload(resource.Resource):
	def render(self, request):
		request.setHeader('Content-type', 'application; xhtml+xml;' )
		request.setHeader('charset', 'UTF-8')
				
		try:
			db = eDVBDB.getInstance()
			#db.reloadServicelist() # reloading only lamedb
			db.reloadBouquets() # reloading *.tv and *.radio

			request.setResponseCode(http.OK)
			
			return """<?xml version="1.0" encoding="UTF-8"?>
						<e2simplexmlresult>	
							<e2state>True</e2state>
							<e2statetext>Servicelist reloaded</e2statetext>	
						</e2simplexmlresult>"""
						
		except Exception, e:
			request.setResponseCode(http.OK)

			return """<?xml version="1.0" encoding="UTF-8"?>
						<e2simplexmlresult>	
							<e2state>False</e2state>
							<e2statetext>Error while loading Servicelist!</e2statetext>	
						</e2simplexmlresult>"""

class ServiceListSave(resource.Resource):
	TYPE_TV = 0
	TYPE_RADIO = 1
	EXTENSIONS = ['.tv', '.radio']
	DIR = "/etc/enigma2/"
	undefinded_tag = "%n/a%"
	undefinded_and = "%und%"

#	def http_POST(self, request):
#		"""
#		overwriten, because we need a custom parsePOSTData
#		"""
#		return self.parsePOSTData(request).addCallback(
#			lambda res: self.render(request))
#
#	def parsePOSTData(self, request):
#		"""
#		overridden, because we need to set higher values to fileupload.parse_urlencoded
#		"""
#		if request.stream.length == 0:
#			return defer.succeed(None)
#
#		parser = None
#		ctype = request.headers.getHeader('content-type')
#		print "#" * 20, ctype
#		if ctype is None:
#			return defer.succeed(None)
#
#		def updateArgs(data):
#			args = data
#			request.args.update(args)
#
#		def updateArgsAndFiles(data):
#			args, files = data
#			request.args.update(args)
#			request.files.update(files)
#
#		def error(f):
#			f.trap(fileupload.MimeFormatError)
#			raise http.HTTPError(responsecode.BAD_REQUEST)
#
#		if ctype.mediaType == 'application' and ctype.mediaSubtype == 'x-www-form-urlencoded':
#			d = fileupload.parse_urlencoded(request.stream, maxMem=100 * 1024 * 1024, maxFields=1024)
#			d.addCallbacks(updateArgs, error)
#			return d
#		else:
#			raise http.HTTPError(responsecode.BAD_REQUEST)

	def render(self, request):			
		request.setHeader('Content-type', 'application; xhtml+xml;' )
		request.setHeader('charset', 'UTF-8')
		
		try:
			content = request.args['content'][0].replace("<n/a>", self.undefinded_tag).replace('&', self.undefinded_and)
			if content.find('undefined') != -1:
				fp = open('/tmp/savedlist', 'w')
				fp.write(content)
				fp.close()
				result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
						<e2simplexmlresult>\n
							<e2state>False</e2state>
							<e2statetext>found string 'undefined' in XML DATA... a copy was saved to '/tmp/savedlist'.</e2statetext>
						</e2simplexmlresult>\n
					 """
				request.setResponseCode(http.OK)
				request.write(result)

			(bouquets_tv, bouquets_radio) = self.parseXML(content)
			#print "having num %i TV Bouquets and num %i Radio Bouquets" %(len(bouquets_tv),len(bouquets_radio))

			#deleting old files
			os.system("rm " + self.DIR + "userbouquet*.tv ")
			os.system("rm " + self.DIR + "userbouquet*.radio ")
			os.system("rm " + self.DIR + "bouquets.tv ")
			os.system("rm " + self.DIR + "bouquets.radio ")

			#writing new files
			self.createIndexFile(self.TYPE_TV, bouquets_tv)
			counter = 0
			for bouquet in bouquets_tv:
				self.createBouquetFile(self.TYPE_TV, bouquet['bname'], bouquet['services'], counter)
				counter = counter + 1

			self.createIndexFile(self.TYPE_RADIO, bouquets_radio)
			counter = 0
			for bouquet in bouquets_radio:
				self.createBouquetFile(self.TYPE_RADIO, bouquet['bname'], bouquet['services'], counter)
				counter = counter + 1

			# reloading *.tv and *.radio
			db = eDVBDB.getInstance()
			db.reloadBouquets()
			print "servicelists reloaded"
			result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
						<e2simplexmlresult>\n
							<e2state>True</e2state>
							<e2statetext>servicelist saved with %i TV und %i Radio Bouquets and was reloaded</e2statetext>
						</e2simplexmlresult>\n
					 """ % (len(bouquets_tv), len(bouquets_radio))
			
			request.setResponseCode(http.OK)	
			request.write(result)
			
		except Exception, e:
			print e
			result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
						<e2simplexmlresult>\n
							<e2state>False</e2state>
							<e2statetext>%s</e2statetext>
						</e2simplexmlresult>\n
					 """ % e
					 
			request.setResponseCode(http.OK)	
			request.write(result)	
			
		request.finish()	 
		return server.NOT_DONE_YET

	def parseXML(self, xmldata):
		print "parsing xmldata with length", len(xmldata)
		xmldoc = xml_dom_minidom_parseString(xmldata);
		blist = xmldoc.getElementsByTagName("e2bouquetlist")[0]
		print "Num TV Bouquets", len(blist.getElementsByTagName('e2tvbouquetlist')[0].getElementsByTagName('e2bouquet'))
		print "Num RADIO Bouquets", len(blist.getElementsByTagName('e2radiobouquetlist')[0].getElementsByTagName('e2bouquet'))

		bouquets_tv = self.parseBouquets(blist.getElementsByTagName('e2tvbouquetlist')[0])
		bouquets_radio = self.parseBouquets(blist.getElementsByTagName('e2radiobouquetlist')[0])
		return bouquets_tv, bouquets_radio

	def parseBouquets(self, xmlnode):
		#print "parsing Bouquets", xmlnode
		list = []
		for bouquet in xmlnode.getElementsByTagName('e2bouquet'):
			bref = urllib_unquote(bouquet.getElementsByTagName('e2bouquetreference')[0].childNodes[0].data)
			bname = urllib_unquote(bouquet.getElementsByTagName('e2bouquetname')[0].childNodes[0].data)
			#print "Bouquet",bref,bname
			list.append({'bname':bname, 'bref':bref, 'services':self.parseServices(bouquet)})
		return list

	def parseServices(self, xmlnode):
		#print "parsing Services", xmlnode
		list = []
		for service in xmlnode.getElementsByTagName('e2servicelist')[0].getElementsByTagName('e2service'):
			sref = urllib_unquote(service.getElementsByTagName('e2servicereference')[0].childNodes[0].data)
			sname = urllib_unquote(service.getElementsByTagName('e2servicename')[0].childNodes[0].data)
			sname = sname.replace(self.undefinded_tag, "<n/a>").replace(self.undefinded_and, "&")
			#print sref,sname
			list.append({'sref':sref, 'sname':sname})
		return list

	def createBouquetFile(self, type, bname, list_services, counter):
		print "creating file for bouquet", bname, "with", len(list_services), "services for type", type
		filename = self.getFilenameForBouquet(type, bname, counter)
		fcontent = "#NAME %s\n" % bname
		for service in list_services:
			fcontent += "#SERVICE %s\n" % service['sref']
			fcontent += "#DESCRIPTION %s\n" % service['sname']
		fcontent = fcontent.encode('utf-8')
		fp = open(self.DIR + filename, "w")
		fp.write(fcontent)
		fp.close()

	def createIndexFile(self, type, bouquets):
		print "creating Indexfile with", len(bouquets), "num bouquets for type", type
		filename = self.getFilenameForIndex(type)
		if(type == self.TYPE_TV):
			fcontent = "#NAME User - bouquets (TV)\n"
		else:
			fcontent = "#NAME User - bouquets (Radio)\n"
		counter = 0
		for bouquet in bouquets:
			fcontent += "#SERVICE: 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" % self.getFilenameForBouquet(type, bouquet['bname'], counter)
			counter = counter + 1

		fp = open(self.DIR + filename, "w")
		fp.write(fcontent)
		fp.close()

	def getFilenameForBouquet(self, type, bouquetname, counter):
		if bouquetname == "Favourites (TV)" and type == self.TYPE_TV:
			s = "userbouquet.favourites%s" % self.EXTENSIONS[type]
		elif bouquetname == "Favourites (Radio)" and type == self.TYPE_RADIO:
			s = "userbouquet.favourites%s" % self.EXTENSIONS[type]
		else:
			s = "userbouquet.%i%s" % (counter, self.EXTENSIONS[type])
		return s

	def getFilenameForIndex(self, type):
		return "bouquets" + self.EXTENSIONS[type]

