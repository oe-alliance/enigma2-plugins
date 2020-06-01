from __future__ import print_function
import httplib
import xml.dom.minidom
import time
import re
import os
from urllib import quote
from operator import itemgetter#, attrgetter
from Plugins.Extensions.SubsDownloader2.SourceCode.archives_extractor import zip_extractor
from Plugins.Extensions.SubsDownloader2.SourceCode.periscope import SubtitleDatabase

#  Copyright (C) 2011 Dawid Bankowski <enigma2subsdownloader at gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

class XML_to_Dict():
    def __init__(self):
	pass
    
    def xmltodict(self, xmlstring):
	doc = xml.dom.minidom.parseString(xmlstring)
	self.remove_whilespace_nodes(doc.documentElement)
	return self.elementtodict(doc.documentElement)

    def elementtodict(self, parent):
	child = parent.firstChild
	if (not child):
		return None
	elif (child.nodeType == xml.dom.minidom.Node.TEXT_NODE):
		return child.nodeValue
	
	d={}
	while child is not None:
		if (child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE):
			try:
				d[child.tagName]
			except KeyError:
				d[child.tagName]=[]
			d[child.tagName].append(self.elementtodict(child))
		child = child.nextSibling
	return d

    def remove_whilespace_nodes(self, node, unlink=True):
	remove_list = []
	for child in node.childNodes:
		if child.nodeType == xml.dom.Node.TEXT_NODE and not child.data.strip():
			remove_list.append(child)
		elif child.hasChildNodes():
			self.remove_whilespace_nodes(child, unlink)
	for node in remove_list:
		node.parentNode.removeChild(node)
		if unlink:
			node.unlink()

class Napisy24_pl(XML_to_Dict, zip_extractor):    
    def __init__(self,moviePath, movieNameString= None):
	if movieNameString== None:
	    self.MovieName = ((moviePath.rsplit("/", 1))[-1]).rsplit(".", 1)[0]
	else:
	    self.MovieName = (movieNameString)
        self.MovieDir = (moviePath.rsplit("/", 1))[0]
        self.ZipFilePath = self.MovieDir+'/'+((moviePath.rsplit("/", 1))[-1]).rsplit(".", 1)[0]+'.zip'
	self.subtitle_dict = []
	self.NAPISY24_url = "napisy24.pl"
    
    def IMDB_idenifier_search(self):
	""" Try to find nfo file in movie directory and search in nfo IMDB idetifier"""
	dir_list = os.listdir(self.MovieDir)
	dir_count = 0
	for x in dir_list:
	    if x.split(".")[-1].lower()=="nfo":
		print("find NFO in %i list" % dir_count)
		break
	    dir_count=dir_count+1
	try:	
	    nfo_file = open(self.MovieDir+"/"+dir_list[dir_count], "r")
	    buffor = nfo_file.read()
	    nfo_file.close
	    #IMDB line in nfo: iMDB: http://www.imdb.com/title/tt1219289/	    
	    char_count = 0
	    while (char_count+len("http://www.imdb.com/title/")) < len(buffor):
		if buffor[char_count:(char_count+len("http://www.imdb.com/title/"))] == "http://www.imdb.com/title/":
		    #print "%s" % str(char_count+len("http://www.imdb.com/title/"))
		    self.dd11 = IMDB_begining = char_count+len("http://www.imdb.com/title/")
		    break
		char_count=char_count+1
	    char_count=IMDB_begining+1   
	    while char_count < len(buffor):
		if buffor[char_count:(char_count+1)] == "/":
		    #print "%s" % str(char_count)
		    self.dd22 = IMDB_ending = char_count
		    break
		char_count=char_count+1
	    return buffor[IMDB_begining:IMDB_ending]	
	#tutaj trzeba sprawdzienia IMDB numeru jesli jest oka to zwraca informacje jesli jest nie oka to zwraca blad
	except:	    
	    print("blad IMBN")
	    return False
    
    def __connect_with_server(self, get_operatoin, server_reuest_type):
	"""Function connect with server and downloades avaliable subtitle
	list or avaliable subtitle zip file	
	"""
	what_is_downloaded = server_reuest_type
	self.XML_String = None
	self.zip_string = None
	try:
	    conn = httplib.HTTPConnection(self.NAPISY24_url)
	    conn.request("GET", get_operatoin)
	    r1 = conn.getresponse()
	    print(r1.status, r1.reason)
	    if what_is_downloaded == "downloada_subtitle_list_by_film_name" or what_is_downloaded == "downloada_subtitle_list_by_IMDB":
		self.XML_String = r1.read()
	    elif what_is_downloaded  == "download_subtilte_zip":		
		self.zip_string = r1.read()
	    return r1.status#, r1.reason
	except (IOError, OSError) as e:
	    print("Napisy24.pl server connection error.", file=sys.stderr)
	    time.sleep(0.5)
        
    def getNapisy24_SubtitleListXML(self, subtitle_list_reuest_type):
	"""Napisy 24 GET request for:
	- downloada_subtitle_list_by_film_name - downloading subtitle list by movie name,
	- downloada_subtitle_list_by_IMDB - downloading subtitle list by IMDB identifier found by:
	   IMDB_idenifier_search
	"""
        repeat = 3
	if subtitle_list_reuest_type == "downloada_subtitle_list_by_film_name":
	    request_subtitle_list = "/libs/webapi.php?title=%s" % quote(self.MovieName)		
	elif subtitle_list_reuest_type == "downloada_subtitle_list_by_IMDB":
	    IMDB_search_answer = self.IMDB_idenifier_search()
	    if IMDB_search_answer != False:
		request_subtitle_list = "/libs/webapi.php?imdb=%s" % IMDB_search_answer
	    else:
		repeat = 0
		r1_status = None
#	    IMDB_search_answer = self.IMDB_idenifier_search()
#	    if IMDB_search_answer != False:
#		request_subtitle_list = "/libs/webapi.php?imdb=%s" % IMDB_search_answer		
        while repeat > 0:  
            repeat = repeat - 1
	    r1_status = self.__connect_with_server(request_subtitle_list, "downloada_subtitle_list_by_film_name")            
            if r1_status != 200 and r1_status != 400:
                print("Fetching subtitle list failed, HTTP code: %s" % (str(r1_status)))
                time.sleep(0.5)
                continue
	    elif r1_status == 400:
		print("Fetching subtitle list failed, HTTP code: %s \n Bad request in string: %s." % (str(r1_status), request_subtitle_list))
		repeat = -1
            else:
                repeat = 0
    
            if self.XML_String == ('brak wynikow'):
                print("Subtitle list NOT FOUND")
                repeat = 0
                continue

            if self.XML_String is None or self.XML_String == "":
                print("Subtitle list download FAILED")
                continue
                
        if r1_status != 200 or self.XML_String == 'brak wynikow' or self.XML_String == "" or self.XML_String is None:
            return False
        else:
	    if self.return_xml_dict() == True:
		return True
	    else:
		return False
              
    def Correct_MultiRoot_XML(self):
	"""Downloaded XML string isn't compatybil with XML standard in which minidom is written.
	This function corrects  in downloaded string  stringsome known errors e.g.: multiroot, & char in data, CP1252 encodeing."""
        if self.XML_String[0] == "\n":
            self.XML_String=self.XML_String[1:]
        SECONDLINE_CHAR = 0
        for x in self.XML_String:
            SECONDLINE_CHAR = SECONDLINE_CHAR+1
            if x =="\n":
                break
        self.XML_String = self.XML_String[0:SECONDLINE_CHAR] + "<lista>"+ self.XML_String[(SECONDLINE_CHAR+1):]+"</lista>"
	self.XML_String = re.sub("&", "and", self.XML_String)
	self.XML_String = self.XML_String.decode("CP1252").encode("UTF-8")
    
    def return_xml_dict(self):
	"""Function returns subtitle dictionary which is computed from correct xml string."""
	try:
	    self.Correct_MultiRoot_XML()
	    self.subtitle_dict = sorted(self.xmltodict(self.XML_String)['subtitle'], key=itemgetter('imdb', 'cd'))
	    #self.subtitle_dict = self.xmltodict(self.XML_String)['subtitle']
	    print("XML subtitle list downloaded and converted to dict")
	    return True
	except:
	    print("XML subtitle list  not downloaded or converterd.")
	    return False
	    
    
    def return_xml_dict_entry_value(self, dict_entry, dict_entry_position):
	"""From subtitle dictionary function returns value."""
	value = self.subtitle_dict[dict_entry][dict_entry_position]
	return value[0]

    def extract_zip_file(self):
	extractor = zip_extractor(self.ZipFilePath, None, ("txt", "sub", "srt"))
	# return false if nothing extracted
	return extractor.extract_zipped_file()
	#os.remove(self.ZipFilePath)

	
    def save_downloaded_zip(self, dict_entry_to_download):
	"""Function saves downloaded zip string on given path anf destroy 
	self.zip_string if saveing is succesfull."""
	if self.download_subtitle_zip(dict_entry_to_download) == True:
	    try:
		zip_file = open(self.ZipFilePath, "wb")
		zip_file.write(self.zip_string)
		zip_file.close		
		print("Zipfile: %s saved on hdd." % self.ZipFilePath)
		del self.zip_string
		return True
	    except:
		print("Problems with Zipfile: %s saveing on hdd." % self.ZipFilePath)
		return False
	
    def download_subtitle_zip(self, dict_entry_to_download):
	"""Napisy 24 GET request for subtitle zip downloading. Data is stored in self.zip_string."""
	#request_subtitle_list = "http://napisy24.pl/download/%s/" % str(self.return_xml_dict_entry_value(dict_entry_to_download,'id'))
	request_subtitle_list = "http://napisy.me/download/sr/%s/" % str(self.return_xml_dict_entry_value(dict_entry_to_download, 'id'))
	
	repeat = 3
	while repeat > 0:  
            repeat = repeat - 1
	    #request_subtitle_list = "/libs/webapi.php?title=%s" % self.MovieName
	    r1_status = self.__connect_with_server(request_subtitle_list, "download_subtilte_zip")            
            if r1_status != 302:
                print("Fetching subtitle failed, HTTP code: %s" % (str(r1_status)))
                time.sleep(0.5)
                continue
            else:
                repeat = 0
    
            if self.zip_string == None:
                print("Subtitle NOT DOWNLOADED")
                repeat = 0
                continue

            if self.zip_string is None or self.zip_string == "":
                print("Subtitle NOT DOWNLOADED")
                continue
                
        if self.zip_string[0:2] == 'PK':
	    print("Success to download subtitle zip.")
            return True
        else:
	    print("Feild to download subtitle zip.")
            return False

class GuessFileData_from_FileName(SubtitleDatabase.SubtitleDB):
    def __init__(self, tvshowRegex, tvshowRegex2, movieRegex):
        self.tvshowRegex = SubtitleDatabase.tvshowRegex
        self.tvshowRegex2 = SubtitleDatabase.tvshowRegex2
        self.movieRegex = SubtitleDatabase.movieRegex

    def return_data_string(self, file_path):
        file_data = self.guessFileData(file_path)
        if file_data['type'] == 'tvshow':
            return str(file_data['name']+" "+str(file_data['season'])+"x"+str(file_data['episode']))
        elif file_data['type'] =='movie' or file_data['type'] == 'unknown':
            return str(file_data['name'])
    
    def return_movie_data_to_XBMC(self, file_path):
	fileData = self.guessFileData(file_path)
	if fileData['type'] == 'tvshow':
            tvShow = fileData['name']
            season = fileData['season']
            episode = fileData['episode']
            #print fileData
        elif fileData['type'] =='movie' or fileData['type'] =='unknown':
            tvShow = []
            season = []
            episode = []  
            #print fileData
	return fileData['name'], tvShow, season, episode
	
	
class CompareMovie_and_Subtite_FileData(GuessFileData_from_FileName):
    def __init__(self, tvshowRegex, tvshowRegex2, movieRegex, file_extentions):
        self.tvshowRegex = SubtitleDatabase.tvshowRegex
        self.tvshowRegex2 = SubtitleDatabase.tvshowRegex2
        self.movieRegex = SubtitleDatabase.movieRegex
        self.__file_extentions = file_extentions
    
    def __movie_file_extensions(self, extensions_dict):
        movie_file_extensions = []
        for x in extensions_dict:
            if extensions_dict[x] == "movie":
                movie_file_extensions.append(x)        
        return movie_file_extensions

    
    def __return_movie_file_list(self, movie_path):
        """Funstion takes movie file path and based on EXTENSIONS from myListy.pl
        returns list of movies in movie file directory"""
        movie_dir = movie_path.rsplit("/", 1)[0]
        movie_file_list =[]
        movie_extentionds = self.__movie_file_extensions(self.__file_extentions)
        for x in os.listdir(movie_dir):
            if x.rsplit(".", 1)[-1]in movie_extentionds:
                movie_file_list.append(movie_dir+"/"+x)		
	#USUNAC URL Z NAPISY24
        return movie_file_list

    def moviePath_and_movieFileData(self, file_path):
        self.__file_path = file_path
        """Function returns structure (file_path, {guesseFileData})"""
        movie_file_list = self.__return_movie_file_list(file_path)
        movie_file_data = []
        for x in movie_file_list:
            movie_file_data.append((x, self.guessFileData(x)))
        return movie_file_data
    
    def subtitlePath_and_subtitleFileData(self, file_path_list):
        """Function returns structure (file_path, {guesseFileData})"""
        subtile_file_data = []        
        for x in file_path_list:
            subtile_file_data.append((x, self.guessFileData(x)))
        return subtile_file_data
    
    def compare_movie_and_subtitle_FileData(self, movie_file_data, subtitle_file_data):
        compare_result = []
        for x in movie_file_data:
	    wynik = 0
            for y in subtitle_file_data:
                wynik = 0
                #Cause and effect for subtitle and movie guesseFileData results
                if 'type' in x[1] and 'type' in y[1]:
                    if x[1]['type'] == y[1]['type']:
                        #wynik = wynik + 0.1600
			wynik = wynik +0.0900
                if 'name' in x[1] and 'name' in y[1]:
                    if x[1]['name'] == y[1]['name']:
                        #wynik = wynik +0.0900
			wynik = wynik + 0.1600
                if 'season' in x[1] and 'season' in y[1]:   
                    if x[1]['season'] == y[1]['season']:
                        wynik = wynik +0.0225
                if 'episode' in x[1] and 'episode' in y[1]:  
                    if x[1]['episode'] == y[1]['episode']:
                        wynik = wynik +0.0225
                if 'season' in x[1] and 'part' in y[1]: 
                    if x[1]['season'] == y[1]['part']:
                        wynik = wynik +0.0060
                if 'episode' in x[1] and 'part' in y[1]: 
                    if x[1]['episode'] == y[1]['part']:
                        wynik = wynik +0.0060
                if 'part' in x[1] and 'part' in y[1]: 
                    if x[1]['part'] == y[1]['part']:
                        wynik = wynik +0.0400
                if 'teams' in x[1] and 'teams' in y[1]:
                    if x[1]['teams'] == y[1]['teams']:
                        wynik = wynik +0.0025
                if 'year' in x[1] and 'year' in y[1]:
                    if x[1]['year'] == y[1]['year']:
                        wynik = wynik +0.0049
                #Cause and effect for subtitle and movie guesseFileData results
                compare_result.append({"movie":x[0],"subtitle":y[0],"propability": wynik})                       
               # print x[0], y[0], wynik
        return compare_result
        #musi sprawdzic czy film jest najbardziej prawdopodobny
            
        
    def give_movie_subtitle_consistent_data(self, movie_file_data, subtitle_file_data):
        """Returns best matching movie <--> subtitle table."""
        m_s_temp_data = []
        preliminary_movie_subtitle_list = self.compare_movie_and_subtitle_FileData(movie_file_data, subtitle_file_data)
        for x in preliminary_movie_subtitle_list:
            """ Delete 0 'propability' registry"""
            if x['propability'] != 0:
                m_s_temp_data.append(x)

        temp_movieList = []
        for x in m_s_temp_data:
            """Check what movies are still in registry"""
            if x['movie'] not in temp_movieList:
                temp_movieList.append(x['movie'])
                
        final_movie_subtitle_list = []
        matching_movie = False
        for x in temp_movieList:
            """For all movies in temp_movieList checks best subtitles"""
            final_propability = 0
            for y in preliminary_movie_subtitle_list:
                if y['movie'] == x and  y['propability'] > final_propability:
                    if self.__file_path == y['movie']:
                        """Check it primary movie is in results matching_movie = True"""
                        matching_movie = True
                    best_entry = y
                    final_propability = y['propability']
            final_movie_subtitle_list.append(best_entry)   
	    
	"""Filtering by subtitle name - if there is no multiple subtitles"""
	preliminary_movie_subtitle_list = final_movie_subtitle_list
	temp_movieList = [] #now subtile
	for x in preliminary_movie_subtitle_list:
            """Check what movies are still in registry"""
            if x['subtitle'] not in temp_movieList:
                temp_movieList.append(x['subtitle'])
				
	final_movie_subtitle_list = []	
	matching_movie = False
        for x in temp_movieList: #now subtile
            """For all subtitles in temp_movieList which now is subtitle checks best movie
	    This makes that one subtitle don't belong to multi movies.	    
	    """
            final_propability = 0
            for y in preliminary_movie_subtitle_list:
                if y['subtitle'] == x and  y['propability'] > final_propability:
                    if self.__file_path == y['movie']:
                        """Check it primary movie is in results matching_movie = True"""
                        matching_movie = True
                    best_entry = y
                    final_propability = y['propability']
            final_movie_subtitle_list.append(best_entry)
	
        if  matching_movie == True:
            return final_movie_subtitle_list
        else:
            return []