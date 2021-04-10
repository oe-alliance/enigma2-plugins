# -*- coding: utf-8 -*-
# CurlyTx configuration
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from Components.config import config, ConfigYesNo, ConfigSelection, ConfigNumber, ConfigText, ConfigSubsection, ConfigSubList, ConfigInteger

import six


def createPage():
    """ Create and return a configuration page object """
    s = ConfigSubsection()
    s.uri = ConfigText(default="http://", fixed_size=False)
    s.title = ConfigText(
        default="Page #" + str(len(config.plugins.CurlyTx.pages) + 1),
        fixed_size=False
        )
    s.fontSize = ConfigInteger(20, (1, 100))
    return s

def loadDefaultPageOptions():
    defaults = []
    for i in list(range(0, len(config.plugins.CurlyTx.pages))):
        defaults.append((str(i), config.plugins.CurlyTx.pages[i].title.value))
    if hasattr(config.plugins.CurlyTx, "defaultPage"):
        config.plugins.CurlyTx.defaultPage.setChoices(defaults, "0")
    else:
        config.plugins.CurlyTx.defaultPage = ConfigSelection(defaults, "0")

#configuration setup
config.plugins.CurlyTx = ConfigSubsection()
config.plugins.CurlyTx.menuMain = ConfigYesNo(default=True)
config.plugins.CurlyTx.menuExtensions = ConfigYesNo(default=False)
config.plugins.CurlyTx.menuTitle = ConfigText(default="CurlyTx", fixed_size=False)
config.plugins.CurlyTx.feedUrl = ConfigText(default="", fixed_size=False)
config.plugins.CurlyTx.pages = ConfigSubList()
for id, value in six.iteritems(config.plugins.CurlyTx.pages.stored_values):
    config.plugins.CurlyTx.pages.append(createPage())
loadDefaultPageOptions()
