import Plugins.Plugin
from Components.config import config
from Components.config import ConfigSubsection
from Components.config import ConfigSelection
from Components.config import ConfigInteger
from Components.config import ConfigSubList
from Components.config import ConfigSubDict
from Components.config import ConfigText
from Components.config import configfile
from Components.config import ConfigYesNo

config.plugins.vlcplayer = ConfigSubsection()
config.plugins.vlcplayer.vcodec = ConfigSelection({"mp1v": "MPEG1", "mp2v": "MPEG2"}, "mp2v")
config.plugins.vlcplayer.vb = ConfigInteger(1000, (100, 9999))
config.plugins.vlcplayer.acodec = ConfigSelection({"mpga":"MP1", "mp2a": "MP2", "mp3": "MP3"}, "mp2a")
config.plugins.vlcplayer.ab = ConfigInteger(128, (64, 320))
config.plugins.vlcplayer.samplerate = ConfigSelection({"0":"as Input", "44100": "44100", "48000": "48000"}, "0")
config.plugins.vlcplayer.channels = ConfigInteger(2, (1, 9))
config.plugins.vlcplayer.width = ConfigSelection(["352", "704", "720"])
config.plugins.vlcplayer.height = ConfigSelection(["288", "576"])
config.plugins.vlcplayer.fps = ConfigInteger(25, (1, 99))
config.plugins.vlcplayer.soverlay = ConfigYesNo()

config.plugins.vlcplayer.servercount = ConfigInteger(0)
config.plugins.vlcplayer.servers = ConfigSubList()

def addVlcServerConfig():
	i = len(config.plugins.vlcplayer.servers)
	config.plugins.vlcplayer.servers.append(ConfigSubsection())
	config.plugins.vlcplayer.servers[i].host = ConfigText("", False)
	config.plugins.vlcplayer.servers[i].httpport = ConfigInteger(8080, (0,65535))
	config.plugins.vlcplayer.servers[i].basedir = ConfigText("/", False)
	config.plugins.vlcplayer.servers[i].method = ConfigSelection({"http": "HTTP Interface", "telnet": "Telnet/VLM"})
	config.plugins.vlcplayer.servers[i].adminport = ConfigInteger(4212, (0,65535))
	config.plugins.vlcplayer.servers[i].adminpwd = ConfigText("admin", False)
	config.plugins.vlcplayer.servercount.value = i+1
	return i

for i in range(0, config.plugins.vlcplayer.servercount.value):
	addVlcServerConfig()
