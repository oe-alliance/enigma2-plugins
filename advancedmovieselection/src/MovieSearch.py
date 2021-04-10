#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Movie Search for Dreambox-Enigma2
#
#  Coded by cmikula(c)2012
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
from Screens.Screen import Screen
from Components.config import ConfigText, KEY_0, KEY_TIMEOUT, KEY_NUMBERS
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Tools.NumericalTextInput import NumericalTextInput
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import eTimer


class PopupInputHelpDialog(NumericalTextInputHelpDialog):
    pass


class PopupInputDialog(InputBox):
    def __init__(self, session):
        InputBox.__init__(self, session)
        self.numti = NumericalTextInput()
        self.configText = ConfigText("", False)
        self.configText.help_window = self.session.instantiateDialog(PopupInputHelpDialog, self.numti)
        self.setTitle(_("Search:"))

    def keyNumberGlobal(self, number):
        self.configText.handleKey(KEY_0 + number)
        self["input"].number(number)

    def show(self):
        self["input"].setText("")
        self.configText.setValue("")
        self.configText.help_window.show()
        return Screen.show(self)

    def hide(self):
        self.configText.help_window.hide()
        return Screen.hide(self)


class MovieSearch():
    def __init__(self):
        self.popup = self.session.instantiateDialog(PopupInputDialog)
        self["config_actions"] = NumberActionMap(["SetupActions"],
        {
            "1": self.keyNumberPressed,
            "2": self.keyNumberPressed,
            "3": self.keyNumberPressed,
            "4": self.keyNumberPressed,
            "5": self.keyNumberPressed,
            "6": self.keyNumberPressed,
            "7": self.keyNumberPressed,
            "8": self.keyNumberPressed,
            "9": self.keyNumberPressed,
            "0": self.keyNumberPressed,
        }, -1) # to prevent left/right overriding the listbox
        # we use extra actions to disable them
        self["SetupActions"] = NumberActionMap(["SetupActions"],
        {
            "cancel": self.hidePopup,
            "deleteForward": self.keyBackspace,
        }, -1)
        self["InputAsciiActions"] = ActionMap(["InputAsciiActions"],
        {
            "gotAsciiCode": self.keyGotAscii
        }, -2)
        self.last_result = -1
        self.__timer = eTimer()
        self.__timer.callback.append(self.__timeout)
        self.__timer_reload = eTimer()
        self.__timer_reload.callback.append(self.__timeout_reload)
        self.onClose.append(self.__onClose)
        self.onLayoutFinish.append(self.__onLayoutFinish)

    def __onLayoutFinish(self):
        self.hidePopup()
        self.setKeyboardModeAscii()

    def __onClose(self):
        self.setKeyboardModeNone()
        self.popup.close()
        self.session.deleteDialog(self.popup)
        self.popup = None

    def __timeout(self):
        self.popup.configText.handleKey(KEY_TIMEOUT)
        self.__timer_reload.start(100, 1)

    def __timeout_reload(self):
        self.buildNewList(self.popup["input"].getText())

    def hidePopup(self):
        self["SetupActions"].setEnabled(False)
        self.popup.hide()
        if self.last_result == 0:
            self["list"].l.setList(self["list"].list)

    def showPopup(self):
        if not self.popup.shown:
            self["SetupActions"].setEnabled(True)
            self.popup.show()

    def okPressed(self):
        if self.popup.shown:
            self.hidePopup()

    def keyNumberPressed(self, number):
        self.showPopup()
        self.popup.keyNumberGlobal(number)
        if KEY_0 + number in KEY_NUMBERS:
            self.__timer.start(1000, 1)

    def buildNewList(self, search):
        if search == "" or search is None:
            self["list"].l.setList(self["list"].list)
            self["list"].moveToIndex(0)
            return
        newList = []
        for movie_tuple in self["list"].list:
            mi = movie_tuple[0]
            if search.lower() in mi.name.lower():
                if not movie_tuple in newList:
                    newList.append(movie_tuple)
        #if len(newList) == 0:
        #    return
        self.last_result = len(newList)
        self["list"].l.setList(newList)
        self["list"].moveToIndex(0)
    
    def clearSearch(self):
        if self.last_result > 0:
            self.last_result = 0
            self["list"].l.setList(self["list"].list)
            return True
        
    def keyBackspace(self):
        self.popup.keyBackspace()
        self.__timer_reload.start(100, 1)

    def keyGotAscii(self):
        self.showPopup()
        self.popup.gotAsciiCode()
        self.__timer.start(1000, 1)
