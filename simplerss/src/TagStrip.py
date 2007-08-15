# -*- coding: utf-8 -*-

from re import sub

class TagStrip():
	"""Simple class to Strip HTML-Tags and convert common entities."""
	# Entities to be converted
	convertables = [
		# ISO-8895-1 (most common)
		("&#228;", u"ä"),
		("&auml;", u"ä"),
		("&#252;", u"ü"),
		("&uuml;", u"ü"),
		("&#246;", u"ö"),
		("&ouml;", u"ö"),
		("&#196;", u"Ä"),
		("&Auml;", u"Ä"),
		("&#220;", u"Ü"),
		("&Uuml;", u"Ü"),
		("&#214;", u"Ö"),
		("&Ouml;", u"Ö"),
		("&#223;", u"ß"),
		("&szlig;", u"ß"),

		# Rarely used entities
		("&#8230;", u"..."),
		("&#8211;", u"-"),
		("&#160;", u" "),
		("&#038;", u"&"),

    	# Common entities
		("&lt;", u"<"),
		("&gt;", u">"),
		("&nbsp;", u" "),
		("&amp;", u"&"),
		("&quot;", u"\""),
	]

	def strip(self, html):
		# Replace <p> and </p> with newline
		html = sub('</?p>', u"\n", html)

		# Strip enclosed tags
		html = sub('<(.*?)>', '', html)

		# Convert html entities
		for escaped, unescaped in self.convertables:
			html = html.replace(escaped, unescaped)

		# Return result with leading/trailing whitespaces removed
		return html.strip()