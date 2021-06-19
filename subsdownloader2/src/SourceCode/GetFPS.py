import sys
import struct

# GetFPS function by areq propably
#found on http://www.mail-archive.com/pld-cvs-commit@lists.pld-linux.org/msg215309.html


class GetFPS(object):
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        return self.fps

    #def fps_round_to3(self):
    #    return round(self.fps(),3)

    def fps(self):
        self.file = open(self.filename, "r+b")
        s = self.file.read(4)
        if s == "\x1a\x45\xdf\xa3":
            return self.get_mkv_fps()
        elif s == "RIFF":
            self.file.seek(32)
            return 1000000.0 / float(struct.unpack('<I', self.file.read(4))[0])
        else:
            raise Exception('Error: Unknown file format not AVI/MKV')

    def __exit__(self, type, value, traceback):
        try:
            self.file.close()
        except:
            pass

    def eblm(self, bits=0xf0):
        suma = 0x00
        mask = 0x01
        while not (suma & mask):
            suma = (suma << 8) + ord(self.file.read(1))
            if (mask == 0x01) and not (suma & bits):
                raise Exception('Error: MKV stream is broken')
            mask <<= 7
        if bits == 0xf0:
            return (suma, self.eblm(bits=0xff))
        else:
            return suma ^ mask

    def get_mkv_fps(self):
        track = 0
        self.file.seek(0)
        while True:
                class_id, length = self.eblm()
                # print "class_id: %X length %i position:%i" % (class_id, length,self.file.tell())
                if (class_id == 0x83):
                        track = ord(self.file.read(1))
                elif (class_id == 0x23E383 and track == 1):
                        break
                elif (class_id not in [0x18538067, 0x1654AE6B, 0xAE, 0x83]):
#Segment,Tracks,TrackEntry,TrackType
                        self.file.seek(length, 1)

        return (1000000000 / float(struct.unpack('>I', self.file.read(4))[0]))
