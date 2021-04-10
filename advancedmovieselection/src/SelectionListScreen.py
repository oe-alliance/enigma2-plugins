#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2012 cmikula

SelectionListScreen for Advanced Movie Selection

In case of reuse of this source code please do not remove this copyright.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For more information on the GNU General Public License see:
<http://www.gnu.org/licenses/>.

For example, if you distribute copies of such a program, whether gratis or for a fee, you 
must pass on to the recipients the same freedoms that you received. You must make sure 
that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
'''
from __init__ import _
from Screens.Screen import Screen
from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText
from Components.SelectionList import SelectionList
from Screens.HelpMenu import HelpableScreen
from Source.Globals import SkinResolutionHelper


class SelectionListScreen(Screen, HelpableScreen, SkinResolutionHelper):
    def __init__(self, session, title, item_descr, selected_items):
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        SkinResolutionHelper.__init__(self)
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save/Close"))
        self["list"] = SelectionList([])
        self.selected_items = selected_items
        for l in item_descr:
            selected = False
            for x in selected_items:
                if l[0] in x:
                    selected = True
            self["list"].addSelection(l[1], l[0], 0, selected)

        self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
        {
            "ok": (self["list"].toggleSelection, _("Toggle selected")),
            "cancel": (self.cancel, _("Cancel")),
        })
        self["ColorActions"] = HelpableActionMap(self, "ColorActions",
        {
            "red": (self.cancel, _("Cancel")),
            "green": (self.accept, _("Save/Close"))
        })
        self.setTitle(title)

    def cancel(self):
        self.close(None)

    def accept(self):
        l = [x[1] for x in self["list"].getSelectionsList()]
        self.close(l)
