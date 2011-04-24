from Plugins.Plugin import PluginDescriptor
from NTIVirtualKeyBoard import NTIVirtualKeyBoard
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from enigma import eServiceReference, iStaticServiceInformationPtr

def vkCallback(movieContextMenu, searchString=None):
	if not movieContextMenu: return
	else: csel = movieContextMenu.csel
	if not searchString:
		return csel.reloadList()

	movieList = csel["list"].list
	newList = []
	for movie in movieList:
		# we have no idea what this input could be, just add it back
		if len(movie) < 2: newList.append(movie)
		else:
			if isinstance(movie[0], eServiceReference) and isinstance(movie[1], iStaticServiceInformationPtr):
				name = movie[1].getName(movie[0])
				if searchString.lower() in name.lower(): # force case-insensitive for now
					newList.append(movie)
			else:
				newList.append(movie)
	csel["list"].list = newList
	csel["list"].l.setList(newList)
	movieContextMenu.close()

def main(session, service, **kwargs):
	try:
		csel = session.current_dialog.csel
		movieList = csel["list"].list # just to check for existence
	except Exception:
		csel = None

	if csel is not None:
		session.openWithCallback(
				boundFunction(vkCallback, session.current_dialog),
				NTIVirtualKeyBoard,
				title=_("Enter text to search for")
		)
	else:
		self.session.open(
			MessageBox,
			_("Improperly launched plugin.\nAborting!"),
			type = MessageBox.TYPE_ERROR
		)


def Plugins(**kwargs):
	return PluginDescriptor(name="MovieSearch", description=_("search..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)

