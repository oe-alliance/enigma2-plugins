#pragma mark - Config
from Components.config import config, ConfigSubsection, ConfigText, ConfigPassword, ConfigLocations

from Tools.Directories import resolveFilename, SCOPE_HDD

config.plugins.ecasa = ConfigSubsection()
config.plugins.ecasa.google_username = ConfigText(default="", fixed_size=False)
config.plugins.ecasa.google_password = ConfigPassword(default="")
config.plugins.ecasa.cachedirs = ConfigLocations(default=[resolveFilename(SCOPE_HDD, "ecasa")])
config.plugins.ecasa.cache = ConfigText(default="/media/hdd/ecasa")
config.plugins.ecasa.user = ConfigText(default='default')
