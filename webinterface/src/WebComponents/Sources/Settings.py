from Components.config import config
from Components.Sources.Source import Source

class Settings(Source):
	def __init__(self, session):
		self.cmd = []
		self.session = session
		Source.__init__(self)

	def handleCommand(self, cmd):
		self.cmd = cmd

	def do_func(self):
		result = []
		self.pickle_this("config", config.saved_value, result)
		return result

	def pickle_this(self, prefix, topickle, result):
		for (key, val) in topickle.items():
			name = prefix + "." + key
			if isinstance(val, dict):
				self.pickle_this(name, val, result)
			elif isinstance(val, tuple):
				result.append((name, val[0]))
			else:
				result.append((name, val))

	list = property(do_func)
	lut = {"Name": 0
			, "Value": 1
			}
