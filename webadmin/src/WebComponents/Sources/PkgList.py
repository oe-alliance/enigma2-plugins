# -*- coding: utf-8 -*-
from Components.Sources.Source import Source


class PkgList(Source):
	LIST = 0
	UPDATE = 1
	INSTALL = 2
	DEL = 3

	def __init__(self, session, wap=False):
		Source.__init__(self)
		self.wap = wap
		self.session = session
		self.cmd = ""
		self.err = False

	def handleCommand(self, cmd):
		if cmd is not None:
			self.cmd = cmd

	def __getList(self):
		from os import popen as os_popen
		PKG_NAME = 0
		PKG_REL = 1
		PKG_INFO = 2
		map = {}
		try:
			out = os_popen("opkg update")
			for line in out:
				print "[loadOpkgfeed]", line

			out = os_popen("opkg list")
			for line in out:
				if line[0] == " ":
					continue
				#print "[PkgList] ",line
				package = line.split(' - ')
				if len(package) > 2:
					if "Collected errors:" in package:
						# Schleife
						self.err = True
						return

				if map.has_key(package[PKG_NAME]):
					if map[package[PKG_NAME]][0] > package[PKG_REL]:
						continue
				map.update({package[PKG_NAME]: [(package[PKG_REL][:-1] if len(package) < 3 else package[PKG_REL]),
					("" if len(package) < 3 else package[PKG_INFO][:-1]),
					 "0",
					 "0"]})
			out = os_popen("opkg list-installed")
			for line in out:
				package = line.split(' - ')
				if map.has_key(package[PKG_NAME]):
					map[package[PKG_NAME]][2] = "1"

			out = os_popen("opkg list-upgradable")
			for line in out:
				package = line.split(' - ')
				if map.has_key(package[PKG_NAME]):
					map[package[PKG_NAME]][0] = package[PKG_REL].replace("experimental-", "exp. ") + " -> " + package[PKG_INFO][:-1].replace("experimental-", "exp. ")
					map[package[PKG_NAME]][3] = "1"

			keys = map.keys()
			keys.sort()

			return [(name, map[name][0], map[name][1], map[name][2], map[name][3]) for name in keys]
		except Exception, e:
			print "[PkgList] except: ", str(e)
			return []

	def getOpkgfeed(self):
		#print "[WebAdmin] ", self.cmd
		if self.err:
			self.err = False
			return []

		PKGCACHE = self.__getList()

		if self.wap:
			# packagename starts with: filter=<one char>
			if len(self.cmd) == 1:
				return [p for p in PKGCACHE if p[0].startswith(self.cmd)]
			# static parameter "filter=installed"
			elif(self.cmd == "installed"):
				return [(p[0],
						p[1],
						p[2],
						(_("Yes") if p[3] == "1" else _("No")),
						(_("Yes") if p[4] == "1" else _("No"))
						) for p in PKGCACHE if p[3] == "1"]
			# static parameter "filter=upgradable"
			elif(self.cmd == "upgradable"):
				return [(p[0],
						p[1],
						p[2],
						(_("Yes") if p[3] == "1" else _("No")),
						(_("Yes") if p[4] == "1" else _("No"))
						) for p in PKGCACHE if p[4] == "1"]
			# packagename search filter=...
			else:
				return [(p[0],
						p[1],
						p[2],
						(_("Yes") if p[3] == "1" else _("No")),
						(_("Yes") if p[4] == "1" else _("No"))
						) for p in PKGCACHE if self.cmd in p[0] or self.cmd in p[2]]
		else:
			# packagename starts with: filter=<one char>
			#if len(self.cmd) == 1:
			#	return [ p for p in PKGCACHE if p[0].startswith(self.cmd) ]
			# static parameter "filter=installed"
			#elif(self.cmd == "installed"):
			#	return [ p for p in PKGCACHE if p[3] == "1" ]
			# static parameter "filter=upgradable"
			#elif(self.cmd == "upgradable"):
			#	return [ p for p in PKGCACHE if p[4] == "1" ]
			# packagename search filter=...
			#else:
			#	return [ p for p in PKGCACHE if self.cmd in p[0] or self.cmd in p[2] ]
			return PKGCACHE

	list = property(getOpkgfeed)
	lut = {"Packagename": 0,
		"Release": 1,
		"Info": 2,
		"State": 3,
		"Update": 4,
	}
