# -*- coding: utf-8 -*-
# CurlyTx Atom feed parser
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from twisted.web.client import getPage
from xml.etree.cElementTree import fromstring

class AtomFeed:
    """ Simple XML parser that extracts pages from a atom feed """
    ns = "{http://www.w3.org/2005/Atom}"
    def __init__(self, url, callback, errorCallback):
        """ Fetches the URL

        Parsed pages are sent back to callback by parse()
        """
        getPage(url).addCallback(self.parse, callback).addErrback(errorCallback)

    def parse(self, data, callback):
        """ Parse atom feed data into pages list and run callback """
        xml = fromstring(data)
        pages = []
        for entry in xml.findall("{0}entry".format(self.ns)):
            titleE = entry.find("{0}title".format(self.ns))
            url = self.bestLink(entry.findall("{0}link".format(self.ns)))
            if titleE != None and titleE.text != "" and url != None:
                pages.append({"title": titleE.text, "url": url})

        callback(pages)

    def bestLink(self, list):
        """ Fetch the best matching link from an atom feed entry """
        foundLevel = -1
        foundHref = None
        for link in list:
            if link.get("rel") != "alternate" and link.get("rel") != "":
                continue
            level = self.level(link)
            if foundLevel > level:
                continue
            foundLevel = level
            foundHref = link.get("href")
        return foundHref

    def level(self, link):
        """ Determines the level of a link

        "text/plain" type links are best, links without type are second.
        All others have the lowest level 1.
        """
        type = link.get("type")
        if type == "text/plain":
            return 3
        elif type == "":
            return 2
        return 1
