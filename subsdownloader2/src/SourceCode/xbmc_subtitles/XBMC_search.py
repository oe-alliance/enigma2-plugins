#from XBMC.utilities import *
#from periscope.plugins.SubtitleDatabase import SubtitleDB
#from Plugins.Extensions.SubsDownloader2.SourceCode.periscope.SubtitleDatabase import SubtitleDB, tvshowRegex, tvshowRegex2, movieRegex
import os
#from XBMC.archives_extractor import zip_extractor
#from Plugins.Extensions.SubsDownloader2.SourceCode.archives_extractor import zip_extractor

def list_XBMC_Periscope_plugins(XBMC_periscope_plugin_path):
    plugin_list = []
    for x in os.listdir(XBMC_periscope_plugin_path):
        if os.path.isdir(XBMC_periscope_plugin_path+x) == True:
            plugin_list.append(x)    
    return plugin_list


def list_directory_files(dir_path):
    file_list = []
    for x in os.listdir(dir_path):
        if os.path.isdir(dir_path+x) == False:
            file_list.append(dir_path+x)    
    return file_list

def new_file_in_directory(files_before, files_after):
    new_file = []
    for x in files_after:
        if x in files_before:
            pass
        else:
            new_file.append(x)
    return new_file


"""
            
#XBMCSubtitle code for PC not USED in Enigma2
#from XBMC.services.Itasa import service as SERVICE
from periscope.plugins.SubtitleDatabase import SubtitleDB
from periscope.plugins.SubtitleDatabase import *


class XBMCSubtitle(SubtitleDB):
    def __init__(self,service):
        self.tvshowRegex = tvshowRegex
        self.tvshowRegex2 = tvshowRegex2
        self.movieRegex = movieRegex
        
        exec ('from XBMC.services.%s import *' % service)
        exec ('from XBMC.services.%s import service as Service' % service)        
        self.service = Service

    
    def XBMC_search_subtitles(self, file_path, lang1, lang2,lang3, year = None, set_temp = False, rar = False, stock = True):
        self.file_path = file_path
        self.__subtitle_list = []
        self.__session_id = None
        self.__msg = None        
        fileData = self.guessFileData(self.file_path)
        #===============================================================================
        # Public interface functions
        #===============================================================================
        
        # This function is called when the service is selected through the subtitles
        # addon OSD.
        # file_original_path -> Original system path of the file playing
        # title -> Title of the movie or episode name
        # tvshow -> Name of a tv show. Empty if video isn't a tv show (as are season and
        #           episode)
        # year -> Year
        # season -> Season number
        # episode -> Episode number
        # set_temp -> True iff video is http:// stream
        # rar -> True iff video is inside a rar archive
        # lang1, lang2, lang3 -> Languages selected by the user
        #return self..search_subtitles(self.file_path,fileData['name'],fileData['type'], year, fileData['season'],fileData['episode'],set_temp,rar, lang1, lang2, lang3, 1)
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
        self.__subtitles_list, self.__session_id, self.__msg = self.service.search_subtitles(file_path, fileData['name'], tvShow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stock)
        return self.__subtitles_list
    
    def XBMC_download_subtitles(self, pos):
        tmp_sub_dir = sub_folder = self.file_path.rsplit("/",1)[0]
        zipped_subs_path = self.file_path.rsplit(".",1)[0]+".zip"
        session_id = self.__session_id
        subtitles_list = self.__subtitles_list
        return self.service.download_subtitles (subtitles_list, pos, zipped_subs_path, tmp_sub_dir, sub_folder, session_id) #ZWRAA False, language, subs_file #standard output

    
file_path = "C:/!Roboczy/How.I.Met.Your.Mother.S07E12.HDTV.XviD-LOL.[VTV].avi"
SERVICE = XBMCSubtitle("Itasa") 
a, b, c = SERVICE.XBMC_search_subtitles(file_path, "all", "All","All")
"""
