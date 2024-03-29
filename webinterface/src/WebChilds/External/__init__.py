from __future__ import print_function
from os import listdir
from os.path import abspath, splitext
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import six


def importExternalModules():
	dir = abspath(resolveFilename(SCOPE_PLUGINS) + "Extensions/WebInterface/WebChilds/External/")
	for file in listdir(dir):
		module_name, ext = splitext(file)  # Handles no-extension files, etc.

		if ext == '.py' and module_name != "__init__":
			try:
				six.exec_("import " + module_name)
				print('[Toplevel.importExternalModules] Imported external module: %s' % (module_name))

			except ImportError as e:
				print('[Toplevel.importExternalModules] Could NOT import external module: %s' % (module_name))
				print('[Toplevel.importExternalModules] Exception Caught\n%s' % e)
