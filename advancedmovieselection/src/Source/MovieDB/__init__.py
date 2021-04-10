import os
import urllib
#from ..StopWatch import clockit

#@clockit
def downloadCover(url, filename, overwrite=False):
    try:
        if not os.path.exists(filename) or overwrite:
            print "Try loading: ", str(url), "->", str(filename)
            urllib.urlretrieve(url, filename)
        else:
            print "Download skipped:", str(url), "->", str(filename)
    except:
        import sys
        import traceback
        print '-' * 50
        traceback.print_exc(file=sys.stdout)
        print '-' * 50
        return False
    return True
