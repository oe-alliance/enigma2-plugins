import os
import re
import sys
import hashlib
#import shutil
import urllib
import codecs
#from Screens.MessageBox import MessageBox

""" Convert subtitles to SRT format based on napi2srt.py by 2009-11-02 Pawel Sternal <sternik@gmail.com>
modification by 2011-05-20 SileliS <silelis@tlen.pl>
"""


class SubConv():
    #def __init__(self, subtitle_path):
    def __init__(self, subtitle_path, encoding):
	self.encodeing = encoding
	self.subtitle = subtitle_path
	file = codecs.open(self.subtitle, 'r', self.encodeing, errors="ignore")
        self.subs_file = file.readlines()
        file.close()

    def detect_format(self, list):
        """Detects format of readed subtittes and return information about format if unknown returns: "" """
        re_mdvd = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
        re_srt = re.compile("^(\d+):(\d+):(\d+),\d+\s*-->.*")
        re_tmp = re.compile("^(\d+):(\d+):(\d+):(.*)")
        re_sub2 = re.compile("^(\d+):(\d+):(\d+)\.\d+\s*\,.*")
        re_mpl2 = re.compile("\[(?P<start>\d+)\]\[(?P<stop>\d+)\](?P<line>.*)", re.S)
        #for line in list:
        while len(list) > 0:
            line = list.pop(0)
            if re_mdvd.match(line):
                return "mdvd"
                break
	    elif re_srt.match(line):
                return "srt"
	        break
            elif re_tmp.match(line):
                return "tmp"
	        break
            elif re_sub2.match(line):
                return "sub2"
	        break
            elif re_mpl2.match(line):
                return "mpl2"
	        break
	    #becouse file is saved as mdvd returns mdvd value
        print "Unsupported subtitle format appears. Please send this subtitle to developer."
        ####################################################
        #"""KOMUNIKAT message box"""
        ####################################################
        return "None"

    def read_mdvd(self, list, fps):
        """
    Read micro-dvd subtitles.
    input: contents of a file as list
    returns: list of subtitles in form: [[time_start in secs, time_end in secs, line1, ...],....]
    """
        re1 = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
        subtitles = []
        while len(list) > 0:
	    try:
		m = re1.match(list.pop(0), 0)
		if m:
		    subt = [int(m.group(1)) / float(fps)]
		    if m.group(2):
			subt.append(int(m.group(2)) / float(fps))
		    else:
			subt.append(int(m.group(1)) / float(fps) + 3)
		    subt.extend(m.group(3).strip().split("|"))
		    subtitles.append(subt)
	    except:
		sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
        return subtitles

    def read_sub2(self, list):
        """
Reads subviewer 2.0 format subtitles, e.g. :
00:01:54.75,00:01:58.54
You shall not pass!
input: contents of a file as list
returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
"""
        re1 = re.compile("^(\d+):(\d+):(\d+)\.(\d+)\s*\,\s*(\d+):(\d+):(\d+)\.(\d+).*$")
        subtitles = []
	while len(list) > 0:
	    try:
                m = re1.match(list.pop(0), 0)
                if m:
                    subt = [int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 100.0]
                    subt.append(int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 100.0)
                    l = list.pop(0).strip()
                    lines = l.split("[br]")
                    for i in range(0, len(lines)):
                        subt.append(lines[i])
                    subtitles.append(subt)
	    except:
		sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
	return subtitles

#    try:
#            while len(list)>0:
#                m = re1.match(list.pop(0), 0)
#                if m:
#                    subt = [int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/100.0]
#                    subt.append(int(m.group(5))*3600 + int(m.group(6))*60 + int(m.group(7)) + int(m.group(8))/100.0)
#                    l = list.pop(0).strip()
#                    lines = l.split("[br]")
#                    for i in range(0,len(lines)):
#                        subt.append(lines[i])
#                    subtitles.append(subt)
#        except IndexError:
#            sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
#	return subtitles

    def read_srt(self, list):
        """
Reads srt subtitles.
input: contents of a file as list
returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
"""
        re1 = re.compile("^(\d+)\s*$")
        re2 = re.compile("^(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+).*$")
        re3 = re.compile("^\s*$")
        subtitles = []
        while len(list) > 0:
	    try:
                if re1.match(list.pop(0), 0):
                    m = re2.match(list.pop(0), 0)
                    if m:
                        subt = [int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000.0]
                        subt.append(int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 1000.0)
                        l = list.pop(0)
                        while not re3.match(l, 0):
                            subt.append(l.strip())
                            l = list.pop(0)
                        subtitles.append(subt)
        #except IndexError:
	    except:
		sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
	return subtitles

    def read_tmp(self, list):
        """
Reads tmplayer (tmp) subtitles.
input: contents of a file as list
returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
"""
        re1 = re.compile("^(\d+):(\d+):(\d+):(.*)")
        subtitles = []
        subs = {}
        while len(list) > 0:
            try:
		m = re1.match(list.pop(0), 0)
		if m:
		    time = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
		    if time in subs:
			subs[time].extend(m.group(4).strip().split("|"))
		    else:
			subs[time] = m.group(4).strip().split("|")
	    except:
		sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")

        times = subs.keys()
        times.sort()
        for i in range(0, len(times)):
            next_time = 1
            while times[i] + next_time not in subs and next_time < 4:
                next_time = next_time + 1
            subt = [times[i], times[i] + next_time]
            subt.extend(subs[times[i]])
            subtitles.append(subt)
        return subtitles

    def read_mpl2(self, list):
	    MPL2LINE = re.compile("\[(?P<start>\d+)\]\[(?P<stop>\d+)\](?P<line>.*)", re.S)
	    #FRAMERATE = float(fps)
	    subtitles = []
	    while len(list) > 0:
	    #for line in list:
		try:
		    group = MPL2LINE.match(list.pop(0)).groupdict()
		    start = float(float(group["start"]) / 10) #*0.1*FRAMERATE) or 1
		    stop = float(float(group["stop"]) / 10)#*0.1*FRAMERATE)
		    rest = group["line"]
		    temp = [float(start), float(stop), str(rest).replace('|', '\n')]
		    subtitles.append(temp)
		except:
		    sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
	    return subtitles

    def check_subs_long(self, subtitles_standard_list, fps):
        """takes list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
        and checks in end time of subtittle in not longer then next subtitle start time if yes correct this error"""
        loops = len(subtitles_standard_list) - 1
        x = 0
        while x < loops:
            if subtitles_standard_list[x][1] is None:
                subtitles_standard_list[x][1] = subtitles_standard_list[x][1] + 6 * fps
            if subtitles_standard_list[x][1] >= subtitles_standard_list[x + 1][0]:
                if (subtitles_standard_list[x][1] - 0.1) <= subtitles_standard_list[x][0]:
                    subtitles_standard_list[x][1] = (subtitles_standard_list[x][0] + subtitles_standard_list[x + 1][0]) / 2
                else:
                    subtitles_standard_list[x][1] = subtitles_standard_list[x][1] - 0.1
                print "Subtitle end time error detected. Line no. %d was corrected" % x
            x = x + 1
        return subtitles_standard_list

    def to_srt(self, list):
        """
        Converts list of subtitles (internal format) to srt format
        """
        outl = []
        count = 1
        for l in list:
            secs1 = l[0]
            h1 = int(secs1 / 3600)
            m1 = int(int(secs1 % 3600) / 60)
            s1 = int(secs1 % 60)
            f1 = (secs1 - int(secs1)) * 1000
            secs2 = l[1]
            h2 = int(secs2 / 3600)
            m2 = int(int(secs2 % 3600) / 60)
            s2 = int(secs2 % 60)
            f2 = (secs2 - int(secs2)) * 1000
            outl.append("%d\n%.2d:%.2d:%.2d,%.3d --> %.2d:%.2d:%.2d,%.3d\n%s\n\n" % (count, h1, m1, s1, f1, h2, m2, s2, f2, "\n".join(l[2:])))
	    count = count + 1
        return outl

#    def fileData_to_utf_8(self, input_coding):
#	"""convert string readed from file coding to UTF-8 managed by Dreambox
 #       input codint is string eg. 'iso-8859-2' 'utf-8' other"""
#	outPutList =[]
#	for x in self.subs_file:
#	    x.encode(input_coding)
#	    temp_list = unicode(x)
#	    outPutList.append(temp_list)
#	return outPutList

#    def to_utf_8(self, list):
#        """convert list coding to UTF-8 managed by Dreambox
#        input codint is string eg. 'iso-8859-2' 'utf-8' other"""
#
#        temporary_list=[]
#        for x in list:
#            try:
#                temp = x.decode(self.encodeing)
#            except :
#                print "The encode decode error appeared. Encodeing is not changed. Please notice about it developer."
#                temporary_list = list
#
#        ####################################################
#        #"""KOMUNIKAT message box"""
#        ####################################################
#
#                break
#	    unicode_string = unicode( temp )
#            temp = unicode_string.encode('utf-8',"ignore")
#            temporary_list.append(temp)
#        return temporary_list

    def ___utf8_to_utf_8_BOM(self):
	"""Function write 3 bytes xEF xBB xBF at the begining of UTF-8 srt file.
	This bytes are written by Windows Notepad for UTF-8 code page.
	Probably it means that codepage is UTF-8 BOM (I'm not sure).
	But without this 3 bytes polish chars are displayed badly after
	few minutes of movie watching
	http://www.howtofixcomputers.com/forums/windows-xp/extra-characters-beginning-file-ef-bb-bf-263070.html
	"""
	file_in = open(self.subtitle, 'rb')
	buffor = file_in.read()
	file_in.close()
	file_out = open(self.subtitle, 'wb')
	file_out.write("\xef\xbb\xbf" + buffor)
	file_out.close()

    def save_subtitle(self, list):
        """Save subtitle list in file"""
        sub_list = [list]
	try:
	    #dst = codecs.open(self.subtitle, 'w','UTF-8')
	    dst = codecs.open(self.subtitle, 'w', 'utf-8-sig')
	    for nsub in sub_list:
		s = self.to_srt(nsub)
		dst.writelines(s)
	    dst.close()
	    #self.___utf8_to_utf_8_BOM()
	except:
	    print "Can't save subtitles in file: %s" % file
