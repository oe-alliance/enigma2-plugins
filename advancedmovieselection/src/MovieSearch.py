#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel (c)2011
#  Support: www.i-have-a-dreambox.com
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from __init__ import _
from NTIVirtualKeyBoard import NTIVirtualKeyBoard
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from enigma import eServiceReference
from ServiceProvider import eServiceReferenceDvd

class MovieSearchScreen:
    def __init__(self, session):
        try:
            csel = session.current_dialog.csel
#            movieList = csel["list"].list # just to check for existence
        except Exception:
            csel = None

        if csel is not None:
            session.openWithCallback(boundFunction(vkCallback, session.current_dialog), NTIVirtualKeyBoard, title=_("Enter text to search for"))
        else:
            self.session.open(MessageBox, _("Improperly launched plugin.\nAborting!"), type=MessageBox.TYPE_ERROR)

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
            if not (movie[0].flags & eServiceReference.mustDescent and not isinstance(movie[0], eServiceReferenceDvd)):
                name = movie[1].getName(movie[0])
                if searchString.lower() in name.lower(): # force case-insensitive for now
                    newList.append(movie)
    csel["list"].list = newList
    csel["list"].l.setList(newList)
    movieContextMenu.close()
