# -*- coding: utf-8 -*-

# for localized messages
from __future__ import print_function
from __future__ import absolute_import
from . import _x

from Plugins.Plugin import PluginDescriptor
from .SerienFilm import SerienFilmVersion, SerienFilmCfg
from traceback import print_exc
from sys import stdout, exc_info
from Screens.InfoBar import MoviePlayer
from .MovieSelection import MovieSelection


def pluginConfig(session, **kwargs):
	print("[SF-Plugin] Config\n")
	try:
		session.open(SerienFilmCfg)
	except Exception as e:
		print("[SF-Plugin] pluginConfig Config exception:\n" + str(e))


gLeavePlayerConfirmed = None


def showMoviesSF(self):
	try:
#		print "[SF-Plugin] showMoviesSF.InfoBar"
		self.session.openWithCallback(self.movieSelected, MovieSelection)
	except Exception as e:
		print("[SF-Plugin] showMoviesSF exception:\n" + str(e))


def showMoviesMP(self):
	ref = self.session.nav.getCurrentlyPlayingServiceReference()
#	print "[SF-Plugin] SF:MoviePlayer.showMoviesMP"
#	print "[SF-Plugin] SF:MoviePlayer.showMoviesMP, ref=" + str(ref)
	self.session.openWithCallback(self.movieSelected, MovieSelection, ref)


def leavePlayerConfirmedMP(self, answer):
	answer1 = answer and answer[1]

	if answer1 == "movielist":
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.returning = True
		self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
		self.session.nav.stopService()
	else:
		gLeavePlayerConfirmed(self, answer)


from skin import readSkin


def doInstantiateDialogSF(self, screen, arguments, kwargs, desktop):
	# create dialog

	try:
		dlg = self.create(screen, arguments, **kwargs)
	except:
		print('EXCEPTION IN DIALOG INIT CODE, ABORTING:')
		print('-' * 60)
		print_exc(file=stdout)
		from enigma import quitMainloop
		quitMainloop(5)
		print('-' * 60)

	if dlg is None:
		return

	# read skin data
	readSkin(dlg, None, dlg.skinName, desktop)

	# create GUI view of this dialog
	assert desktop is not None

	dlg.setDesktop(desktop)
	dlg.applySkin()

	return dlg


RUNPLUGIN = 1


def autostart(reason, **kwargs):
	if RUNPLUGIN != 1:
		return
	if reason == 0: # start
		if "session" in kwargs:
			global gLeavePlayerConfirmed
			Session = kwargs["session"]
			print("[SF-Plugin] autostart, Session = " + str(Session) + "\n")
			try:
				from Screens.InfoBar import InfoBar
				InfoBar.showMovies = showMoviesSF
				MoviePlayer.showMovies = showMoviesMP
				if gLeavePlayerConfirmed is None:
					gLeavePlayerConfirmed = MoviePlayer.leavePlayerConfirmed
				MoviePlayer.leavePlayerConfirmed = leavePlayerConfirmedMP

				Session.doInstantiateDialog.__self__.__class__.doInstantiateDialog = doInstantiateDialogSF
				modname = Session.doInstantiateDialog.__module__
				print("[SF-Plugin] mytest.Session.doInstantiateDialog modname = %s = %s" % (str(type(modname)), str(modname)))
				
			except Exception as e:
				print("[SF-Plugin] autostart MovieList launch override exception:\n" + str(e))

		else:
			print("[SF-Plugin] autostart without session\n")


def Plugins(**kwargs):
	descriptors = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)]
	descriptors.append(PluginDescriptor(
		name ="SerienFilm " + SerienFilmVersion,
		description=_("group movies of a series to virtual directories"),
		icon="SerienFilm.png",
		where=PluginDescriptor.WHERE_PLUGINMENU,
		fnc=pluginConfig))
	print("[SF-Plugin] autostart descriptors = " + str(descriptors))
	return descriptors
