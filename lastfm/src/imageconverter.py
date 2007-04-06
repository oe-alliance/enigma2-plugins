import Image
import urllib
import sys
print "loading image from",sys.argv[1]
s= urllib.urlopen(sys.argv[1])
data = s.read()
s.close()

print "wrting image to file"

fp = open("/tmp/x","w")
fp.write(data)
fp.close()
print "open image from file"
im = Image.open("/tmp/x")
print "making thumbnail"
im.thumbnail([116,116])
print "converting imagetype"
im = im.convert(mode="P")
print "saving new imagedata to file",sys.argv[2]
im.save(sys.argv[2],"PNG")
print "image saved",sys.argv[2]
