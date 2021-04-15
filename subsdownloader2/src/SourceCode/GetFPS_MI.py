from Plugins.Extensions.SubsDownloader2.SourceCode.MediaInfoDLL import *

"""
filename = u"/hdd/Net_HDD/Filmy/Water.For.Elephants.720p.BRRip.x264.Feel-Free//Water.For.Elephants.720p.BRRip.x264.Feel-Free.mp4"
from media.MediaInfoDLL import *
MI = MediaInfo()
MI.Open(filename)
float(MI.Get(Stream.Video, 0, "FrameRate")[0:6])
"""


class GetFPS(object):
    def __init__(self, filename):
        self.filename = filename

    def fps(self):
        MI = MediaInfo()
        MI.Open(self.filename)
        fps = float(MI.Get(Stream.Video, 0, "FrameRate"))
        MI.Close()
        return fps


"""
MI = MediaInfo()
To_Display = MI.Option(u"Info_Version", u"0.7.0.0;MediaInfoDLL_Example_MSVC;0.7.0.0")
To_Display += u"\r\n\r\nInfo_Parameters\r\n"
To_Display += MI.Option(u"Info_Parameters")
To_Display += u"\r\n\r\nInfo_Capacities\r\n"
To_Display += MI.Option(u"Info_Capacities")
To_Display += u"\r\n\r\nInfo_Codecs\r\n"
To_Display += MI.Option(u"Info_Codecs")

#An example of how to use the library
To_Display += u"\r\n\r\nOpen\r\n"
MI.Open(InputFile)

To_Display += u"\r\n\r\nInform with Complete=false\r\n"
MI.Option(u"Complete")
To_Display += MI.Inform()  #to to
To_Display += u"\r\n\r\nInform with Complete=true\r\n"
MI.Option(u"Complete", "1")
To_Display += MI.Inform()
To_Display += u"\r\n\r\nCustom Inform\r\n"
MI.Option(u"Inform", u"General;Example : FileSize=%FileSize%")
To_Display += MI.Inform()
To_Display += u"\r\n\r\nGet with Stream=General and Parameter=\"FileSize\"\r\n"
To_Display += MI.Get("Stream_General", 0, u"FileSize", "Info_Text", "Info_Name")
To_Display += u"\r\n\r\nGetI with Stream=General and Parameter=46\r\n"
To_Display += MI.GetI("Stream_General", 0, 46, "Info_Text")

To_Display += u"\r\n\r\nCount_Get with StreamKind=Stream_Audio\r\n"
To_Display += str(MI.Count_Get("Stream_Audio"));
To_Display += u"\r\n\r\nGet with Stream=General and Parameter=\"AudioCount\"\r\n"
To_Display += MI.Get("Stream_General", 0, u"AudioCount", "Info_Text", "Info_Name")
To_Display += u"\r\n\r\nGet with Stream=Audio and Parameter=\"StreamCount\"\r\n"
To_Display += MI.Get("Stream_Audio", 0, u"StreamCount", "Info_Text", "Info_Name")
To_Display += u"\r\n\r\nClose\r\n"

MI.Close()
aa = To_Display.encode('ascii','replace')
print To_Display.encode('ascii','replace')    # replaces non ASCII letters by ? so it can be printed on screen
"""
