# -*- coding: utf-8 -*-
from __future__ import absolute_import
from twisted.web import resource, http
from .globals import *
from .plugin import *
from .Sensors import sensors
from .__init__ import _
from Components.config import configfile, config

import os
import datetime

########################################################


class FC2web(resource.Resource):

	title = "FanControl2 Webinterface"
	isLeaf = False

	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd", None)

		html = "<html>"
		html += "<head>\n"
		html += "<meta http-equiv=\"Content-Language\" content=\"de\">\n"
		html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">\n"
		html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />\n"
		html += "<meta http-equiv=\"expires\" content=\"0\">\n"
		html += "<meta http-equiv=\"refresh\" content=\"20\">\n"
		html += "<title>Fan Control 2 - Info</title>\n"
		html += "</head>"
		html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
		html += "<form method=\"POST\" action=\"--WEBBOT-SELF--\">\n"
		html += "<table border=\"1\" width=\"500\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\" cellspacing=\"1\"><tr><td bgcolor=\"#000000\" width=\"200\">\n"
		html += "<p align=\"center\"><img border=\"0\" src=\"/fancontrol/FC2dreambox.png\" width=\"181\" height=\"10\">\n"
		html += "<font color=\"#FFFFFF\"><BR><b>Fan Control 2 - Info</b></font></p>\n"
		html += "</td><td bgcolor=\"#000000\">\n"
		html += "<p align=\"right\">"
		html += BoxStatus()
		if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
			html += "<a href=\"/fancontrol/chart\"><img border=\"0\" src=\"/fancontrol/FC2Chart.png\" width=\"100\" height=\"40\"></a>\n"
		html += "<a href=\"/fancontrol/log\"><img border=\"0\" src=\"/fancontrol/FC2Setup.png\" width=\"100\" height=\"40\"></a></td></tr></table>\n"
		html += "<table border=\"1\" width=\"500\" id=\"table1\">\n"
		html += "<tr>\n"
		html += "<td>%s: <b><font color=\"#FFCC00\">%4.1f °C</font></b></td>\n" % (_("Temperature"), FC2werte[0])
		html += "<td>%s: <font color=\"#FFCC00\"><b>%4d rpm</b></font></td>\n" % (_("Speed"), FC2werte[1])
		html += "<td>%s: <font color=\"#FFCC00\"><b>%03d</b></font></td>\n" % (_("Voltage"), FC2werte[2])
		html += "<td>PWM: <font color=\"#FFCC00\"><b>%03d</b></font></td>\n" % FC2werte[3]
		html += "</tr>\n"
		html += "</table>\n"

		html += "<table border=\"1\" width=\"500\">\n"
		html += "<tr>\n"
		html += "<td>%s °C</td>\n" % _("Sensors")
		templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
		tempcount = len(templist)
		for count in list(range(tempcount)):
			if sensors.getSensorName(count) == "undefined":
				N = TempName[count]
			else:
				N = sensors.getSensorName(count)
			html += "<td><font color=\"#FFCC00\" title=\"%s\">%d</font></td>" % (N, sensors.getSensorValue(count))
		if FC2werte[4] > 0:
			html += "<td><font size=\"1\">HDD </font><font color=\"#FFCC00\">%d</font></td>\n" % FC2werte[4]
		html += "</tr>\n"
		html += "</table>\n"

		html += "<table border=\"1\" width=\"500\">\n"
		html += "<tr>\n"
		for count in list(range(0, 12)):
			tmp = ("<BR>-" if FC2stunde[count] == "-" else FC2stunde[count])
			html += "<td><p align=\"center\"><font size=\"1\">%02d:00<br><font color=\"#FFCC00\">%s</font></font></td>\n" % (count, tmp)
		html += "</tr><tr>\n"
		for count in list(range(12, 24)):
			tmp = ("<BR>-" if FC2stunde[count] == "-" else FC2stunde[count])
			html += "<td><p align=\"center\"><font size=\"1\">%02d:00<br><font color=\"#FFCC00\">%s</font></font></td>\n" % (count, tmp)
		html += "</tr></table>\n"

		html += "<script type=\"text/javascript\">\n"
		html += "function doLogWrite() {\n"
		html += "var iFrameWin = window.myIFrameName;\n"
		html += "iFrameWin.document.write('<html><head><title>FC2 Log Window</title></head><body bgcolor=\"#D3D3D3\">');\n"
		html += "iFrameWin.document.write('<font size=\"-1\">');\n"
		for L in FC2Log:
			html += "iFrameWin.document.write('" + L + "<br>');\n"
		html += "iFrameWin.document.write('</font>');\n"
		html += "iFrameWin.document.write('</body></html>');\n"
		html += "iFrameWin.document.close();\n"
		html += "}\n"
		html += "</script>\n"
		html += "<iframe id=\"myIFrameId\" name=\"myIFrameName\" width=\"500\" height=\"320\" marginwidth=\"5\" vspace=\"2\" marginheight=\"5\" frameborder=\"1\" scrolling=\"auto\"></iframe>\n"
		html += "<script>doLogWrite();\n"
		html += "myIFrameName.document.body.scrollTop = myIFrameName.document.body.scrollHeight*100;\n"
		html += "</script>\n"

		html += "<table border=\"1\" width=\"500\">\n"
		html += "<tr>\n"
		html += "<td>Version: %s </td>\n" % Version
		html += "<td>Settings: %s-%s °C</td>\n" % (config.plugins.FanControl.temp.value, config.plugins.FanControl.tempmax.value)
		html += "<td>%s-%s rpm</td>\n" % (config.plugins.FanControl.minRPM.value, config.plugins.FanControl.maxRPM.value)
		html += "</tr>\n"
		html += "</table>\n"
		html += "</body>\n"
		html += "</html>\n"

		html += "</form>\n"

		return html

##########################################################


class FC2webLog(resource.Resource):

	title = "FanControl2 Webinterface"
	isLeaf = True

	def render(self, req):
		command = req.args.get("cmd", None)
		html = ""
		if command is None:
			req.setHeader('Content-type', 'text/html')
			req.setHeader('charset', 'UTF-8')

			""" rendering server response """

			html = "<html>"
			html += "<head>"
			html += "<meta http-equiv=\"Content-Language\" content=\"de\">"
			html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">"
			html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />"
			html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />"
			html += "<meta http-equiv=\"expires\" content=\"0\">"
			html += "<meta http-equiv=\"refresh\" content=\"30\">"
			html += "<title>Fan Control 2 - Logging</title>"
			html += "</head>"
			html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
			html += "<table border=\"1\" width=\"500\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\" cellspacing=\"1\"><tr><td bgcolor=\"#000000\" width=\"200\">\n"
			html += "<p align=\"center\"><img border=\"0\" src=\"/fancontrol/FC2dreambox.png\" width=\"181\" height=\"10\">\n"
			html += "<font color=\"#FFFFFF\"><BR><b>Fan Control 2 - Logging</b></font></p>\n"
			html += "</td><td bgcolor=\"#000000\">\n"
			html += "<p align=\"right\">"
			html += BoxStatus()
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
				html += "<a href=\"/fancontrol/chart\"><img border=\"0\" src=\"/fancontrol/FC2Chart.png\" width=\"100\" height=\"40\"></a>\n"
			html += "<a href=\"/fancontrol\"><img border=\"0\" src=\"/fancontrol/FC2Info.png\" width=\"100\" height=\"40\"></a></td></tr></table>\n"

			html += "<table border=\"1\" width=\"500\">"
			html += "<tr><td width=\"50%\" align=\"center\" valign=\"top\">Data Logging "
			if config.plugins.FanControl.EnableDataLog.value:
				html += "<font color=\"#00FF00\">%s</font>" % _("active")
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"dataenable\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("turn off")
				html += "</form>"
			else:
				html += "<font color=\"#FF0000\">%s</font>" % _("not active")
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"dataenable\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("turn on")
				html += "</form>"
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
				s = os.stat(config.plugins.FanControl.LogPath.value + "FC2data.csv")
				if int(s.st_size / 1024) == 0:
					html += "<BR>" + _("Filesize : %d %sByte") % (int(s.st_size), "")
				else:
					html += "<BR>" + _("Filesize : %d %sByte") % (int(s.st_size / 1024), "k")
				s = os.statvfs(config.plugins.FanControl.LogPath.value)
				html += "<BR>" + _("Disk free : %d MByte") % (int(s.f_bsize * s.f_bavail / 1024 / 1024))
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"data\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("Download")
				html += "</form>"
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"datadel\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("Delete")
				html += "</form>"
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"datadel48h\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("Delete older 48h")
				html += "</form>"
			else:
				html += "<BR>" + _("File %s does not exists") % "FC2data.csv"

			html += "</td><td width=\"50%\" align=\"center\" valign=\"top\">Event Logging "
			if config.plugins.FanControl.EnableEventLog.value:
				html += "<font color=\"#00FF00\">%s</font>" % _("active")
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"eventsenable\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("turn off")
				html += "</form>"
			else:
				html += "<font color=\"#FF0000\">%s</font>" % _("not active")
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"eventsenable\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("turn on")
				html += "</form>"
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2events.txt"):
				s = os.stat(config.plugins.FanControl.LogPath.value + "FC2events.txt")
				if int(s.st_size / 1024) == 0:
					html += "<BR>" + _("Filesize : %d %sByte") % (int(s.st_size), "")
				else:
					html += "<BR>" + _("Filesize : %d %sByte") % (int(s.st_size / 1024), "k")
				s = os.statvfs(config.plugins.FanControl.LogPath.value)
				html += "<BR>" + _("Disk free : %d MByte") % (int(s.f_bsize * s.f_bavail / 1024 / 1024))
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"events\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("Download")
				html += "</form>"
				html += "<form method=\"GET\">"
				html += "<input type=\"hidden\" name=\"cmd\" value=\"eventsdel\">"
				html += "<input type=\"submit\" value=\"%s\">" % _("Delete")
				html += "</form>"
#				html += "<form method=\"GET\">"
#				html += "<input type=\"hidden\" name=\"cmd\" value=\"eventsdel48h\">"
#				html += "<input type=\"submit\" value=\"%s\">" % _("Delete older 48h")
#				html += "</form>"

			else:
				html += "<BR>" + _("File %s does not exists") % "FC2events.txt"
			html += "</td></tr></table>"
			html += _("Logging-Path: %s") % config.plugins.FanControl.LogPath.value
			html += "<BR>" + _("Auto-Delete older %s Days") % config.plugins.FanControl.DeleteData.value
			html += "</html>"

		elif command[0] == "data":
			req.setResponseCode(http.OK)
#			req.setHeader('Content-type', 'application/octet-stream')
			req.setHeader('Content-type', 'application/vnd.ms-excel')
			req.setHeader('Content-Disposition', 'attachment;filename=FC2data.csv')
			req.setHeader('Content-Length', os.stat(config.plugins.FanControl.LogPath.value + "FC2data.csv").st_size)
#			req.setHeader('Content-Disposition', 'inline;filename=FC2data.csv')
			req.setHeader('charset', 'UTF-8')
			f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "r")
			html = f.read()
			f.close()
		elif command[0] == "datadel":
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
				os.remove(config.plugins.FanControl.LogPath.value + "FC2data.csv")
			CreateDataHead()
			html = LogRefresh()
		elif command[0] == "datadel48h":
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv") and os.stat(config.plugins.FanControl.LogPath.value + "FC2data.csv").st_size > 10000:
				f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "a")
				s = f.tell()
				f.close()
				f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "r")
				f.seek(s - 100)
				line = f.readline()
				line = f.readline()
				DT = line.split(";")
				DT = DT[0].split(" ")
				DD = DT[0].split(".")
				DD48h = datetime.date(int(DD[0]), int(DD[1]), int(DD[2])) - datetime.timedelta(2)
				Dfind = "%04d.%02d.%02d %s" % (DD48h.year, DD48h.month, DD48h.day, DT[1])
				f.seek(0)
				line = f.readline()
				fw = open(config.plugins.FanControl.LogPath.value + "FC2data.csv.tmp", "w")
				fw.write(HeadLine)
				for line in f.readlines():
					DT = line.split(";")
					if DT[0] > Dfind:
						fw.write(line)
				f.close()
				fw.close()
				if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
					os.remove(config.plugins.FanControl.LogPath.value + "FC2data.csv")
				if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv.tmp"):
					os.rename(config.plugins.FanControl.LogPath.value + "FC2data.csv.tmp", config.plugins.FanControl.LogPath.value + "FC2data.csv")
			html = LogRefresh()
		elif command[0] == "dataenable":
			config.plugins.FanControl.EnableDataLog.value = not config.plugins.FanControl.EnableDataLog.value
			CreateDataHead()
			config.plugins.FanControl.EnableDataLog.save()
			html = LogRefresh()

		elif command[0] == "events":
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'application/octet-stream')
			req.setHeader('Content-Disposition', 'attachment;filename=FC2events.txt')
			req.setHeader('Content-Length', os.stat(config.plugins.FanControl.LogPath.value + "FC2events.txt").st_size)
#			req.setHeader('Content-Disposition', 'inline;filename=FC2events.txt')
			req.setHeader('charset', 'UTF-8')
			f = open(config.plugins.FanControl.LogPath.value + "FC2events.txt", "r")
			html = f.read()
			f.close()
		elif command[0] == "eventsdel":
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2events.txt"):
				os.remove(config.plugins.FanControl.LogPath.value + "FC2events.txt")
			html = LogRefresh()
		elif command[0] == "eventsdel48h":
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2events.txt"):
				f = open(config.plugins.FanControl.LogPath.value + "FC2events.txt", "a")
				s = f.tell()
				f.close()
				f = open(config.plugins.FanControl.LogPath.value + "FC2events.txt", "r")
				f.seek(s - 100)
				line = f.readline()
				line = f.readline()
				DT = line.split(";")
				DT = DT[0].split(" ")
				DD = DT[0].split(".")
				DD48h = datetime.date(int(DD[0]), int(DD[1]), int(DD[2])) - datetime.timedelta(2)
				Dfind = "%04d.%02d.%02d %s" % (DD48h.year, DD48h.month, DD48h.day, DT[1])
				f.seek(0)
				line = f.readline()
				fw = open(config.plugins.FanControl.LogPath.value + "FC2events.txt.tmp", "w")
				fw.write(HeadLine)
				for line in f.readlines():
					DT = line.split(";")
					if DT[0] > Dfind:
						fw.write(line)
				f.close()
				fw.close()
				if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2events.txt"):
					os.remove(config.plugins.FanControl.LogPath.value + "FC2events.txt")
				if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2events.txt.tmp"):
					os.rename(config.plugins.FanControl.LogPath.value + "FC2events.txt.tmp", config.plugins.FanControl.LogPath.value + "FC2events.txt")
			html = LogRefresh()
		elif command[0] == "eventsenable":
			config.plugins.FanControl.EnableEventLog.value = not config.plugins.FanControl.EnableEventLog.value
			config.plugins.FanControl.EnableEventLog.save()
			html = LogRefresh()

		return html


def LogRefresh():
	h = "<html>"
	h += "<head>"
	h += "<meta http-equiv=\"refresh\" content=\"1; url=/fancontrol/log\">"
	h += "<a href=\"/fancontrol/log\">Execution completed... jump back...</a>"
	h += "</html>"
	h += "</head>"
	return h


def CreateDataHead():
	if not os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv") and config.plugins.FanControl.EnableDataLog.value and Free(config.plugins.FanControl.LogPath.value):
		try:
			f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "w")
			try:
				f.write(HeadLine)
			except:
				f.close()
		except IOError:
			pass

##########################################################


class FC2webChart(resource.Resource):

	title = "FanControl2 Webinterface"
	isLeaf = True

	def render(self, req):
		command = req.args.get("cmd", None)
		html = ""
		if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
			req.setHeader('Content-type', 'text/html')
			req.setHeader('charset', 'UTF-8')

			""" rendering server response """

			f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "a")
			s = f.tell()
			f.close()
			if s < 150:
				html = "<html><body><html>Not enough Data (wait 3min)!</body></html>"
				return html
			f = open(config.plugins.FanControl.LogPath.value + "FC2data.csv", "r")
			f.seek(s - 100)
			line = f.readline()
			line = f.readline()
			DT = line.split(";")
			DT = DT[0].split(" ")
			DD = DT[0].split(".")
			DD48h = datetime.date(int(DD[0]), int(DD[1]), int(DD[2])) - datetime.timedelta(2)
			Dfind = "%04d.%02d.%02d %s" % (DD48h.year, DD48h.month, DD48h.day, DT[1])
			f.seek(0)
			line = f.readline()
			Anzahl = 0
			for line in f.readlines():
				DT = line.split(";")
				if DT[0] > Dfind:
					Anzahl += 1
#			Anzahl -= 1
			html = "<html>"
			html += "<head>"
			html += "<meta http-equiv=\"Content-Language\" content=\"de\">"
			html += "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\">"
			html += "<meta http-equiv=\"cache-control\" content=\"no-cache\" />"
			html += "<meta http-equiv=\"pragma\" content=\"no-cache\" />"
			html += "<meta http-equiv=\"expires\" content=\"0\">"
			html += "<title>Fan Control 2 - Chart</title>"
			html += "</head>"
			html += "<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n"
			html += "<table border=\"1\" width=\"900\" bordercolorlight=\"#000000\" bordercolordark=\"#000000\"  cellspacing=\"1\"><tr><td bgcolor=\"#000000\" width=\"200\">\n"
			html += "<p align=\"center\"><img border=\"0\" src=\"/fancontrol/FC2dreambox.png\" width=\"181\" height=\"10\">\n"
			html += "<font color=\"#FFFFFF\"><BR><b>Fan Control 2 - Chart</b></font></p>\n"
			html += "</td><td bgcolor=\"#000000\">\n"
			html += "<p align=\"right\">"
			html += BoxStatus()
			if os.path.exists(config.plugins.FanControl.LogPath.value + "FC2data.csv"):
				html += "<a href=\"/fancontrol\"><img border=\"0\" src=\"/fancontrol/FC2Info.png\" width=\"100\" height=\"40\"></a>\n"
			html += "<a href=\"/fancontrol/log\"><img border=\"0\" src=\"/fancontrol/FC2Setup.png\" width=\"100\" height=\"40\"></a></td></tr></table>\n"

			html += "<applet code=\"diagram.class\" codebase=\"/fancontrol/\" name=\"DiaTemp\" "
			html += "align=\"baseline\" width=\"900\" height=\"250\" mayscript>\n"
			html += "<param name=\"title\" value=\"Temp  (48h - %s)\">\n" % DT[0]
			html += "<param name=\"bgcolor\" value=\"240; 240; 240\">\n"
			html += "<param name=\"ytitle\" value=\"Temp\">\n"
			html += "<param name=\"rolling\" value=\"%d\">\n" % Anzahl
			html += "<param name=\"show_xscale\" value=\"atText\">\n"
			html += "<param name=\"show_ygrid\" value=\"true\">\n"
			html += "<param name=\"show_xgrid\" value=\"true\">\n"

			html += "<param name=\"y0\" value=\"\">\n"
			html += "<param name=\"color0\" value=\"240; 0; 0\">\n"
			html += "<param name=\"style0\" value=\"LINE\">\n"
			html += "<param name=\"ylabel0\" value=\"Temp\">\n"

			html += "<param name=\"y1\" value=\"\">\n"
			html += "<param name=\"color1\" value=\"240; 0; 240\">\n"
			html += "<param name=\"style1\" value=\"LINE\">\n"
			html += "<param name=\"ylabel1\" value=\"HDD\">\n"

			html += "<param name=\"y2\" value=\"\">\n"
			html += "<param name=\"color2\" value=\"0; 255; 0\">\n"
			html += "<param name=\"style2\" value=\"LINE\">\n"
			html += "<param name=\"ylabel2\" value=\"BoxOn\">\n"

			html += "<param name=\"y3\" value=\"\">\n"
			html += "<param name=\"color3\" value=\"72; 118; 255\">\n"
			html += "<param name=\"style3\" value=\"LINE\">\n"
			html += "<param name=\"ylabel3\" value=\"HDDon\">\n"

			html += "<param name=\"y4\" value=\"\">\n"
			html += "<param name=\"color4\" value=\"255; 165; 0\">\n"
			html += "<param name=\"style4\" value=\"LINE\">\n"
			html += "<param name=\"ylabel4\" value=\"Record\">\n"

			html += "</applet>\n"

#			html += "<div style=\"position: absolute; width: 100px; height: 100px; z-index: 1; left: 910px; top: 146px\" id=\"Ebene1\">\n"
#			html += "<img border=\"0\" src=\"/web-data/fc2/FC2Status.png\" width=\"115\" height=\"168\"></div>\n"

			html += "<applet code=\"diagram.class\" codebase=\"/fancontrol/\" name=\"DiaRPM\" "
			html += "align=\"baseline\" width=\"900\" height=\"250\" mayscript>\n"
			html += "<param name=\"title\" value=\"RPM  (48h - %s)\">\n" % DT[0]
			html += "<param name=\"bgcolor\" value=\"240; 240; 240\">\n"
			html += "<param name=\"ytitle\" value=\"RPM\">\n"
			html += "<param name=\"rolling\" value=\"%d\">\n" % Anzahl
			html += "<param name=\"show_xscale\" value=\"atText\">\n"
			html += "<param name=\"show_ygrid\" value=\"true\">\n"
			html += "<param name=\"show_xgrid\" value=\"true\">\n"

			html += "<param name=\"y0\" value=\"\">\n"
			html += "<param name=\"color0\" value=\"240; 0; 0\">\n"
			html += "<param name=\"style0\" value=\"LINE\">\n"
			html += "<param name=\"ylabel0\" value=\"RPM\">\n"

			html += "</applet>\n"

			f.seek(0)
			line = f.readline()
			html += "<script language=javascript>\n"
			html += "dT = document.DiaTemp\n"
			html += "dR = document.DiaRPM\n"
			t = 0
			Xtime = int((Anzahl / 20))
			if Anzahl < 1000:
				Xtime += 1
			for line in f.readlines():
				DT = line.split(";")
				if DT[0] > Dfind:
					if Xtime > 0:
						tmp = ("\"" + DT[0].split(" ")[1] + "\"") if t % Xtime == 0 else "null"
					else:
						tmp = "null"
					t += 1
					if len(DT[6]) > 1:
						DT[6] = "0"
					B = 0
					H = 0
					R = 0
					S = int(DT[6])
					if (S & 1) > 0:
						B = 3
					if (S & 2) > 0:
						H = 6
					if (S & 4) > 0:
						R = 9
					html += "dT.AddPoint(\"%s; %s; %d; %d; %d\", %s, null);\n" % (DT[1].replace(",", "."), DT[5], B, H, R, tmp)
					html += "dR.AddPoint(\"%s\", %s, null);\n" % (DT[2], tmp)
			f.close()
			html += "dT.repaint();\ndR.repaint();\n"
			html += "</script>"
		else:
			html = "<html>no Data!"
		html += "</body>"
		html += "</html>"

		return html


def BoxStatus():
	h = ""
	S = int(FC2werte[5])
	if (S & 1) > 0:
		h += "<img border=\"0\" src=\"/fancontrol/FC2on.png\" width=\"20\" height=\"20\" title=\"Box On\" align=\"left\" hspace=\"2\" vspace=\"5\">\n"
	if (S & 2) > 0:
		h += "<img border=\"0\" src=\"/fancontrol/FC2hdd.png\" width=\"20\" height=\"20\" title=\"HDD On\" align=\"left\" hspace=\"2\" vspace=\"5\">\n"
	if (S & 4) > 0:
		h += "<img border=\"0\" src=\"/fancontrol/FC2record.png\" width=\"20\" height=\"20\" title=\"Recording\" align=\"left\" hspace=\"2\" vspace=\"5\">\n"
	return h
