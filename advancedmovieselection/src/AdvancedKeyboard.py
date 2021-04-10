#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel and cmikula (c)2012
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
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigText, KEY_0, KEY_TIMEOUT, KEY_NUMBERS
from Tools.NumericalTextInput import NumericalTextInput
from enigma import eTimer
from Source.Globals import SkinResolutionHelper

from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog


class AdvancedTextInputHelpDialog(NumericalTextInputHelpDialog, SkinResolutionHelper):
    def __init__(self, session, textinput):
        NumericalTextInputHelpDialog.__init__(self, session, textinput)
        SkinResolutionHelper.__init__(self)


class AdvancedKeyBoard(VirtualKeyBoard, NumericalTextInput, SkinResolutionHelper):
    KEYBOARD = 0x01
    NUM_KEYB = 0x02
    BOTH = KEYBOARD | NUM_KEYB

    def __init__(self, session, title="", text=""):
        #VirtualKeyBoard.__init__(self, session, title, text) Changed by Topfi, added parameter names
        VirtualKeyBoard.__init__(self, session, title=title, text=text)
        NumericalTextInput.__init__(self, nextFunc=self.nextFunc)
        SkinResolutionHelper.__init__(self)
        self.configText = None
        if config.AdvancedMovieSelection.keyboard.value == "virtual":
            use = self.KEYBOARD
        elif config.AdvancedMovieSelection.keyboard.value == "numerical":
            use = self.NUM_KEYB
        else:
            use = self.BOTH
        if not use & self.KEYBOARD:
            # hide the keyboard
            self["list"].hide()
            # overwrite VirtualKeyBoard actions
            # make sure not overwrite any action of base class
            self["actions"] = ActionMap(["OkCancelActions", "WizardActions", "ColorActions", "KeyboardInputActions", "InputBoxActions", "InputAsciiActions"],
            {
                "ok": self.__ok,
                "cancel": self.__cancel,
                "left": self.dummy,
                "right": self.dummy,
                "up": self.dummy,
                "down": self.dummy,
                "red": self.__cancel,
                "green": self.__ok,
                "yellow": self.dummy,
                "deleteBackward": self.dummy,
                "back": self.dummy                
            }, -2)

        if use & self.NUM_KEYB:
            self.timer = eTimer()
            self.timer.callback.append(self.timeout)
            self.configText = ConfigText("", False)
            if text:
                self.configText.text = text
                self.configText.marked_pos = len(text)
            self["config_actions"] = NumberActionMap(["SetupActions", "InputAsciiActions", "KeyboardInputActions"],
            {
                "1": self.keyNumberGlobal,
                "2": self.keyNumberGlobal,
                "3": self.keyNumberGlobal,
                "4": self.keyNumberGlobal,
                "5": self.keyNumberGlobal,
                "6": self.keyNumberGlobal,
                "7": self.keyNumberGlobal,
                "8": self.keyNumberGlobal,
                "9": self.keyNumberGlobal,
                "0": self.keyNumberGlobal
            }, -1) # to prevent left/right overriding the listbox
            if use & self.KEYBOARD:
                self.selectedKey = self.getKeyIndex(u"OK") 
            
        self.onLayoutFinish.append(self.__onLayoutFinish)
        self.onClose.append(self.__onClose)

    def __onLayoutFinish(self):
        self.setTitle(_("Advanced Movie Selection - Input help"))
        if self.configText:
            self.configText.help_window = self.session.instantiateDialog(AdvancedTextInputHelpDialog, self)
            self.configText.help_window.show()
                
    def __onClose(self):
        if self.configText and self.configText.help_window:
            self.session.deleteDialog(self.configText.help_window)
            self.configText.help_window = None
    
    def getKeyIndex(self, key):
        index = 0
        for x in self.keys_list:
            for k in x:
                if k == key:
                    return index
                index += 1
        return index
    
    def buildVirtualKeyBoard(self, selectedKey=0):
        #VirtualKeyBoard.buildVirtualKeyBoard(self, selectedKey=self.selectedKey) changed by Topfi: removed parameter
        VirtualKeyBoard.buildVirtualKeyBoard(self)

    def dummy(self):
        pass
    
    def __ok(self):
        self.close(self["text"].getText())

    def __cancel(self):
        self.close(None)

    def timeout(self):
        self.handleKey(KEY_TIMEOUT)
        self["text"].setMarkedPos(-1)

    def handleKey(self, key):
        if self.configText:
            self.configText.handleKey(key)
            if key in KEY_NUMBERS:
                self.timer.start(1000, 1)

    def keyNumberGlobal(self, number):
        self.handleKey(KEY_0 + number)
        self.getKey(number)
        #self.text = self.configText.getText() removed by Topfi
        self["text"].setText(self.configText.getText())
        self["text"].setMarkedPos(self.configText.marked_pos)

    def okClicked(self):
        VirtualKeyBoard.okClicked(self)
        self["text"].setMarkedPos(-1)
        if self.configText:
            #self.configText.text = self.text # Changed by Topfi (replaced self.text)
            self.configText.text = self["text"].getText()
            #self.configText.marked_pos = len(self.text) Changed by Topfi (replaced self.text)
            self.configText.marked_pos = len(self["text"].getText())

    def nextFunc(self):
        self["text"].setMarkedPos(-1)
