# -*- coding: utf-8 -*-

import re

class TagStrip():
	convertables = {
		"&#228;": u"ä",
		"&auml;": u"ä",
		"&#252;": u"ü",
		"&uuml;": u"ü",
		"&#246;": u"ö",
		"&ouml;": u"ö",
		"&#196;": u"Ä",
		"&Auml;": u"Ä",
		"&#220;": u"Ü",
		"&Uuml;": u"Ü",
		"&#214;": u"Ö",
		"&Ouml;": u"Ö",
		"&#223;": u"ß",
		"&szlig;": u"ß",
		"&#038;": u"&",
		"&#8230;": u"...",
		"&#8211;": u"-",
		"&#160;": u" ",
    
		"&lt;": u"<",
		"&gt;": u">",
		"&nbsp;": u" ",
		"&amp;": u"&",
		"&quot;": u"\"",
	}

	def strip(self, html):
		# Convert htmlspecialchars
		for escaped, unescaped in self.convertables.iteritems():
			html = html.replace(escaped, unescaped)

		# Strip everything of form <a>CONTENT</a>, but keep CONTENT (elements with content)
		html = re.sub('<(?P<tag>.*?)>(?P<content>.*?)</(?P=tag)>', '\g<content>', html)

		# Strip everything of form <a /> (elements without conent)
		html = re.sub('<(.*?) />', '', html)
		return html