AC3 = "AC3"
PCM = "PCM"
AC3PCM = (AC3,PCM)

lFileDelay = {}
lFileDelay[AC3] = "/proc/stb/audio/audio_delay_bitstream"
lFileDelay[PCM] = "/proc/stb/audio/audio_delay_pcm"

def dec2hex(n):
    """return the signed hexadecimal string representation of integer n"""
    if n >= 0:
        s = "%X" % n
    else:
        n2 = 2**32 + n + 1
        s = "%X" % n2
    return s

def hex2dec(s):
    """return the signed integer value of a hexadecimal string s"""
    print "[AC3LipSync] hex2dec String: ",s
    if s[:2] == "0x":
        s = s[2:]
    if s[:1] < '8':
        i = int(s,16)
    else:
        i = int(long(s,16)-2**32)
    return i
