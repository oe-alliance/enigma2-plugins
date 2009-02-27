from os import listdir
from os.path import abspath, splitext

def importExternalModules():
	for file in listdir(abspath("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebChilds/External/")):
		module_name, ext = splitext(file) # Handles no-extension files, etc.

		if ext == '.py' and module_name != "__init__":				
			try:
				exec "import " + module_name
				print '[Toplevel.importExternalModules] Imported external module: %s' % (module_name)
		
			except ImportError:
				print '[Toplevel.importExternalModules] Could NOT import external module!'