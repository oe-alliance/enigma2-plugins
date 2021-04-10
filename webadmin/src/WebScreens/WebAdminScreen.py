# -*- coding: utf-8 -*-
from Plugins.Extensions.WebInterface.WebScreens import WebScreen


class WebAdminScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.StaticText import StaticText
		from Plugins.Extensions.WebAdmin.WebComponents.Sources.PkgList import PkgList
		from Plugins.Extensions.WebAdmin.WebComponents.Sources.PkgConfList import PkgConfList
		from Plugins.Extensions.WebAdmin.WebComponents.Sources.WebScriptList import WebScriptList
		
		self["PkgList"] = PkgList(session)
		self["PkgListWap"] = PkgList(session, wap=True)
		
		self["PkgConfList"] = PkgConfList(session, func=PkgConfList.LIST)
		
		self["WebScriptList"] = WebScriptList(session, func=WebScriptList.LIST)
		#self["PkgConfListWap"] = PkgConfList(session, wap=True)
		self["SwitchFeed"] = PkgConfList(session, func=PkgConfList.SWITCH)
		self["BoxMem"] = PkgConfList(session, func=PkgConfList.MEM)
		
		self["Install_txt"] = StaticText(_("install"))
		self["Update_txt"] = StaticText(_("update"))
		self["Delete_txt"] = StaticText(_("delete"))
		
		
