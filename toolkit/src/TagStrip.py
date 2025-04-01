# -*- coding: utf-8 -*-
from re import sub, finditer

import six
import six


try:
	import htmlentitydefs
	iteritems = lambda d: six.iteritems(d)
except ImportError as ie:
	from html import entities as htmlentitydefs
	iteritems = lambda d: d.items()
	unichr = chr


def strip_readable(html):
	# Newlines are rendered as whitespace in html
	html = html.replace('\n', ' ')

	# Replace <br> by newlines
	html = sub(r'<br(\s*/)?>', '\n', html)

	# Replace <p>, <ul>, <ol> and end of these tags by newline
	html = sub(r'</?(p|ul|ol)(\s+.*?)?>', '\n', html)

	# Replace <li> by - and </li> by newline
	html = sub(r'<li(\s+.*?)?>', '-', html)
	html = html.replace('</li>', '\n')

	# Replace </div> by newline
	html = html.replace('</div>', '\n')

	# And 'normal' stripping
	return strip(html)


def strip(html):
	# Strip remaining enclosed tags
	html = sub('<.*?>', '', html)

	# Multiple whitespaces are rendered as a single one
	html = sub('[ \t\r\f\v]{2,}', ' ', html)
	html = html.replace('\n ', '\n')

	entitydict = {}

	entities = finditer(r'&([^#]\D{1,5}?);', html)
	for x in entities:
		key = x.group(0)
		if key not in entitydict:
			entitydict[key] = htmlentitydefs.name2codepoint[x.group(1)]

	entities = finditer('&#x([0-9A-Fa-f]{2,2}?);', html)
	for x in entities:
		key = x.group(0)
		if key not in entitydict:
			entitydict[key] = "%d" % int(key[3:5], 16)

	entities = finditer(r'&#(\d{1,5}?);', html)
	for x in entities:
		key = x.group(0)
		if key not in entitydict:
			entitydict[key] = x.group(1)

	for key, codepoint in iteritems(entitydict):
		html = html.replace(key, six.unichr(int(codepoint)))

	# Return result with leading/trailing whitespaces removed
	return html.strip()
