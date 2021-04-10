import sys
import urllib
import tempfile
import time
import os
import getopt


#  Copyright (C) 2009 Arkadiusz Miskiewicz <arekm@pld-linux.org>
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

prog = "NapiProjekt"
i = 0
i_total = 0
try:
    from hashlib import md5 as md5
except ImportError:
    from md5 import md5
    
languages = {'pl': 'PL', 'en': 'ENG'}

class NapiProjekt():
    def __init__(self):
        self.error_ = 0
        pass
        
    def f(self,z):
        idx = [0xe, 0x3, 0x6, 0x8, 0x2]
        mul = [2, 2, 5, 4, 3]
        add = [0, 0xd, 0x10, 0xb, 0x5]
        
        b = []
        for i in xrange(len(idx)):
            a = add[i]
            m = mul[i]
            i = idx[i]
            
            t = a + int(z[i], 16)
            v = int(z[t:t + 2], 16)
            b.append(("%x" % (v * m))[-1])

        return ''.join(b)
    
    def getnapi(self, filename):
        self.filename = filename
        self.d = md5()
        
        self.d.update(open(self.filename).read(10485760))
        
        self.lang = 'pl'
        
        self.url = "http://napiprojekt.pl/unit_napisy/dl.php?l=%s&f=%s&t=%s&v=pynapi&kolejka=false&nick=&pass=&napios=%s" % \
            (languages[self.lang], self.d.hexdigest(), self.f(self.d.hexdigest()), os.name)
        
        repeat = 3
        self.sub = None
        http_code = 200
        
        while repeat > 0:
            repeat = repeat - 1
            try:
                self.sub = urllib.urlopen(self.url)
                if hasattr(self.sub, 'getcode'):
                    http_code = self.sub.getcode() 
                    self.sub = self.sub.read()
                    self.error_ = 0
            except (IOError, OSError), e:
                print >> sys.stderr, "%s: %d/%d: Fetching subtitle failed: %s" % (prog, i, i_total, e)
                time.sleep(0.5)
                self.error_ = 1
                continue

            if http_code != 200:
                print >> sys.stderr, "%s: %d/%d: Fetching subtitle failed, HTTP code: %s" % (prog, i, i_total, str(http_code))
                time.sleep(0.5)
                self.error_ = 1
                continue
    
            if self.sub.startswith('NPc'):
                print >> sys.stderr, "%s: %d/%d: Subtitle NOT FOUND" % (prog, i, i_total)
                repeat = -1
                self.error_ = 1
                continue
                repeat = 0

            if self.sub is None or self.sub == "":
                print >> sys.stderr, "%s: %d/%d: Subtitle download FAILED" % (prog, i, i_total)
                self.error_ = 1
                continue

            if repeat == -1:
                self.error_ = 1
                continue
        
    def save(self):
        if self.error_ == 1:
            return "None"
        else:
            #subFilePath = str(self.filename).split(".")[0]+'.srt'
            subFilePath = str(self.filename).rsplit(".", 1)[0] + '.srt'
            savefile = open(subFilePath,"w")
            savefile.write(self.sub)
            savefile.close()
            return subFilePath


    

"""file = '/home/silelis/Pulpit/Reservoir Dogs_1992_DVDrip_XviD-Ekolb/Reservoir Dogs_1992_DVDrip_XviD-Ekolb.avi'
a=NapiProjekt(file)
a.getnapi()
a.saveSRT()"""
