AC3 = "AC3"
PCM = "PCM"
AC3PCM = (AC3,PCM)

lFileDelay = {}
lFileDelay[AC3] = "/proc/stb/audio/audio_delay_bitstream"
lFileDelay[PCM] = "/proc/stb/audio/audio_delay_pcm"

def dec2hex(n):
    """return the hexadecimal string representation of integer n"""
    return "%X" % n 

def hex2dec(s):
    """return the integer value of a hexadecimal string s"""
    return int(s, 16)
