from __future__ import print_function
import os
from six.moves.urllib.request import urlretrieve
#from ..StopWatch import clockit

#@clockit
def downloadCover(url, filename, overwrite=False):
    try:
        if not os.path.exists(filename) or overwrite:
            print("Try loading: ", str(url), "->", str(filename))
            urlretrieve(url, filename)
        else:
            print("Download skipped:", str(url), "->", str(filename))
    except:
        import sys, traceback
        print('-' * 50)
        traceback.print_exc(file=sys.stdout)
        print('-' * 50)
        return False
    return True
