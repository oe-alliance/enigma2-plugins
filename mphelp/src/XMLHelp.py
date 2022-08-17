from __future__ import absolute_import

# for localized messages
from . import _

from .MPHelp import HelpPage
from xml.etree.cElementTree import parse as cet_parse


class XMLHelpPage(HelpPage):
	def __init__(self, node):
		# calling HelpPage.__init__ is not required
		self.node = node

	def getText(self):
		node = self.node.find('text')
		if node is not None:
			text = _(node.get('value', ''))
			return text.replace('/n', '\n')
		return ""

	def getTitle(self):
		return _(self.node.get('title', ''))


class XMLHelpReader:
	def __init__(self, filename):
		# this may raise an exception, it is up to the caller to handle that
		self.__dom = cet_parse(filename).getroot()

	def __getitem__(self, index):
		if self.__dom:
			if index == 0:
				caption = self.__dom.get('caption', '')
				return lambda: _(caption)
			elif index == 1:
				return lambda: [XMLHelpPage(x) for x in self.__dom.findall('page')]
			elif index == 2:
				return self.__dom.get('skin', "")  # additional skin name
			raise IndexError('no more indices')
		raise RuntimeError('no valid dom')


__all__ = ['XMLHelpReader']
