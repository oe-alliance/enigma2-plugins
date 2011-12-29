#from XBMC.utilities import *
#from periscope.plugins.SubtitleDatabase import SubtitleDB
from Plugins.Extensions.SubsDownloader2.SourceCode.periscope.SubtitleDatabase import SubtitleDB
import os

def list_XBMC_Periscope_plugins(XMBC_periscope_plugin_path):
    plugin_list = []
    for x in os.listdir(XMBC_periscope_plugin_path):
        if os.path.isdir(XMBC_periscope_plugin_path+x) == True:
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
            

class XBMCSubtitle(SubtitleDB):
    def __init__(self,service, file_path):
        self.tvshowRegex = re.compile('(?P<show>.*)S(?P<season>[0-9]{2})E(?P<episode>[0-9]{2}).(?P<teams>.*)', re.IGNORECASE)
        self.tvshowRegex2 = re.compile('(?P<show>.*).(?P<season>[0-9]{1,2})x(?P<episode>[0-9]{1,2}).(?P<teams>.*)', re.IGNORECASE)
        self.movieRegex = re.compile('(?P<movie>.*)[\.|\[|\(| ]{1}(?P<year>(?:(?:19|20)[0-9]{2}))(?P<teams>.*)', re.IGNORECASE)
       
        
        exec ('from XBMC.services.%s import *' % service)
        exec ('from XBMC.services.%s import service as Service' % service)        
        self.service = Service
        self.file_path = file_path
        self.__subtitle_list = []
        self.__session_id = None
        self.__msg = None
    
    def XBMC_search_subtitles(self, lang1, lang2,lang3, year = None, set_temp = False, rar = False):
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
        self.__subtitles_list, self.__session_id, self.__msg = self.service.search_subtitles(file_path, fileData['name'], fileData['name'], year, fileData['season'], fileData['episode'], set_temp, rar, lang1, lang2, lang3)
        return self.__subtitles_list
    
    def XBMC_download_subtitles(self, pos):
        tmp_sub_dir = sub_folder = self.file_path.rsplit("/",1)[0]
        zipped_subs_path = self.file_path.rsplit(".",1)[0]+".zip"
        session_id = self.__session_id
        subtitles_list = self.__subtitles_list
        self.service.download_subtitles (subtitles_list, pos, zipped_subs_path, tmp_sub_dir, sub_folder, session_id)
            
        
"""       
file_path = "C:/!Roboczy/How.I.Met.Your.Mother.S07E11.HDTV.XviD-ASAP.[VTV].avi"
subtitle = XBMCSubtitle("Subscene", file_path)
bb = subtitle.XBMC_search_subtitles("Chinese" , "English","Polish")

before = list_directory_files("C:/!Roboczy/")
subtitle.XBMC_download_subtitles(0)
afeter = list_directory_files("C:/!Roboczy/")
new_file = new_file_in_directory(before, afeter)



XMBC_plugin_path= "C:/Python26/Lib/XBMC/services/"
cc = list_XBMC_plugins(XMBC_plugin_path)
before = list_directory_files("C:/Python26/Lib/XBMC/services/")
afeter = list_directory_files("C:/Python26/Lib/XBMC/services/")
new_file = new_file_in_directory(before, afeter)

a = ['1','2','3']
b =['4','5','6']

if '1' in a:
    print 'a'
elif '1' in b:
    print 'b'
    
"""
