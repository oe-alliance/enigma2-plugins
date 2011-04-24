from Plugins.Plugin import PluginDescriptor
from NTIVirtualKeyBoard import NTIVirtualKeyBoard
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox

def vkCallback(csel, searchString=None):
	if not csel: return
	if not searchString:
		return csel.reloadList()

	movieList = csel["list"].list
	newList = []
	for movie in movieList:
		name = movie[1].getName(movie[0])
		if searchString.lower() in name.lower(): # force case-insensitive for now
			newList.append(movie)
	csel["list"].list = newList
	csel["list"].l.setList(newList)

def main(session, service, **kwargs):
	try:
		csel = session.current_dialog.csel
	except Exception:
		csel = None

	if csel is not None:
		session.openWithCallback(
				boundFunction(vkCallback, csel),
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

