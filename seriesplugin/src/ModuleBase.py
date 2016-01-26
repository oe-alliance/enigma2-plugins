# -*- coding: utf-8 -*-
# by betonme @2012


class ModuleBase(object):
	def __init__(self):
		pass


	################################################
	# Base classmethod functions
	@classmethod
	def getClass(cls):
		# Return the Class
		return cls.__name__


	################################################
	# Base functions
	def getName(self):
		# Return the Class Name
		return self.__class__.__name__
