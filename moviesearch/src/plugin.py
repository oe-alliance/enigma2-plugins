from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from enigma import eServiceCenter, eServiceReference, \
		iStaticServiceInformationPtr

titleCmp = lambda x, y: x.lower() in y.lower()  # force case-insensitive for now


def vkCallback(movieContextMenu, searchString=None):
	isEmc = False
	if not movieContextMenu:
		return
	else:
		if hasattr(movieContextMenu, 'csel'):
			csel = movieContextMenu.csel
		else:  # if hasattr(cur_dialog, 'mlist'):
			csel = movieContextMenu.mlist
			isEmc = True
	if not searchString:
		if isEmc:
			csel.reload(csel.loadPath)
		else:
			csel.reloadList()
		return movieContextMenu.close()

	if isEmc:
		serviceHandler = eServiceCenter.getInstance()
		movieList = csel.list
		newList = []
		for movie in movieList:
			# we have no idea what this input could be, just add it back
			if len(movie) != 8:
				newList.append(movie)
			else:
				if not isinstance(movie[0], eServiceReference):
					newList.append(movie)
				else:
					info = serviceHandler.info(movie[0])
					if not info:
						newList.append(movie)
					else:
						name = info.getName(movie[0])
						if titleCmp(searchString, name):
							newList.append(movie)
		csel.list = newList
		csel.l.setList(newList)
	else:
		movieList = csel["list"].list
		newList = []
		for movie in movieList:
			# we have no idea what this input could be, just add it back
			if len(movie) < 2:
				newList.append(movie)
			else:
				if len(movie) == 4 and isinstance(movie[3], list):  # assume serienfilm-plugin
					tinfo = movie[3]
					type = tinfo[0]
					if type == 0:
						name = movie[1].getName(movie[0])
						if titleCmp(searchString, name):
							newList.append(movie)
					elif type == 4:
						if titleCmp(searchString, tinfo[2]):
							newList.append(movie)
					else:
						newList.append(movie)
				elif isinstance(movie[0], eServiceReference) and isinstance(movie[1], iStaticServiceInformationPtr):
					name = movie[1].getName(movie[0])
					if titleCmp(searchString, name):
						newList.append(movie)
				else:
					newList.append(movie)
		csel["list"].list = newList
		csel["list"].l.setList(newList)
	movieContextMenu.close()


def main(session, service, **kwargs):
	cur_dialog = session.current_dialog
	if hasattr(cur_dialog, 'csel'):
		csel = session.current_dialog.csel
		if not "list" in csel:
			print("[MovieSearch] No list, goodbye!")
			csel = None
	elif hasattr(cur_dialog, 'mlist'):
		csel = cur_dialog.mlist
	else:
		print("[MovieSearch] Unknown current dialog of type", type(cur_dialog))
		csel = None

	if csel is not None:
		session.openWithCallback(
				boundFunction(vkCallback, session.current_dialog),
				NTIVirtualKeyBoard,
				title=_("Enter text to search for")
		)
	else:
		session.open(
			MessageBox,
			_("Improperly launched plugin.\nAborting!"),
			type=MessageBox.TYPE_ERROR
		)


def Plugins(**kwargs):
	return PluginDescriptor(name="MovieSearch", description=_("search..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart=False)
