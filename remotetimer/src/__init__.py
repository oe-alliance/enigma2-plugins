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
from Components.config import ConfigIP

config.plugins.rtc = ConfigSubsection()
config.plugins.rtc.httphost = ConfigText("", False)
config.plugins.rtc.httpport = ConfigInteger(80, (0,65535))
