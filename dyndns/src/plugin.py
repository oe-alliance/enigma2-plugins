# -*- coding: utf-8 -*-
from __future__ import print_function

import re

from base64 import b64encode
from socket import timeout as socket_timeout

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from enigma import eTimer
from Components.ConfigList import ConfigListScreen
from Components.config import (
    config,
    getConfigListEntry,
    ConfigText,
    ConfigSelection,
    ConfigSubsection,
    ConfigYesNo,
)
from twisted.internet import reactor

from six import ensure_binary
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import Request, urlopen


global sessions
sessions = []

CHECK_IP4_URL = "http://checkip4.spdyn.de/"
CHECK_IP6_URL = "http://checkip6.spdyn.de/"
UPDATE_URL = "https://update.spdyn.de/nic/update"
USER_AGENT = "Enigma2 SPDyn Plugin/1.7"
REQUEST_TIMEOUT = 15
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}\b")
SUCCESS_CODES = ("good", "nochg")

config.plugins.SPDyn = ConfigSubsection()
config.plugins.SPDyn.enable = ConfigYesNo(default=False)
config.plugins.SPDyn.interval = ConfigSelection(
    default="10",
    choices=[
        ("5", _("5 min.")),
        ("10", _("10 min.")),
        ("15", _("15 min.")),
        ("30", _("30 min.")),
        ("60", _("60 min.")),
    ],
)
config.plugins.SPDyn.hostname = ConfigText(default="", fixed_size=False)
config.plugins.SPDyn.token = ConfigText(default="", fixed_size=False)
config.plugins.SPDyn.ipversion = ConfigSelection(
    default="4",
    choices=[
        ("4", _("IPv4")),
        ("6", _("IPv6")),
        ("46", _("IPv4 + IPv6")),
    ],
)


class SPDynScreenMain(ConfigListScreen, Screen):
    skin = """
        <screen position="100,100" size="550,400" title="SPDyn Setup" >
        <widget name="config" position="0,0" size="550,300" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        </screen>"""

    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("activate SPDyn"), config.plugins.SPDyn.enable))
        self.list.append(getConfigListEntry(_("Interval to check IP-Address"), config.plugins.SPDyn.interval))
        self.list.append(getConfigListEntry(_("Hostname"), config.plugins.SPDyn.hostname))
        self.list.append(getConfigListEntry(_("Update Token"), config.plugins.SPDyn.token))
        self.list.append(getConfigListEntry(_("IP version"), config.plugins.SPDyn.ipversion))
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("cancel"))
        self["buttongreen"] = Label(_("ok"))
        self["setupActions"] = ActionMap(["SetupActions"],
        {
            "green": self.save,
            "red": self.cancel,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)

    def save(self):
        print("[SPDyn] saving config")
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)


class SPDynService(object):
    enabled = False
    sessions = []
    lastip = ""

    def __init__(self):
        self.timer = eTimer()
        self.timer.timeout.get().append(self.checkCurrentIP)

    def enable(self):
        if config.plugins.SPDyn.enable.value and not self.enabled:
            self.enabled = True
            reactor.callLater(1, self.checkCurrentIP)

    def disable(self):
        if self.enabled:
            self.timer.stop()
            self.enabled = False

    def addSession(self, session):
        self.sessions.append(session)

    def checkCurrentIP(self):
        print("[SPDyn] checking IP")
        try:
            current_ip = self._get_configured_ip_value()
            print("[SPDyn] current external IP:", current_ip)

            if self.lastip != current_ip:
                self.lastip = current_ip
                reactor.callLater(1, self.onIPchanged)
        except Exception as e:
            print("[SPDyn] could not get external IP:", e)
        finally:
            if self.enabled:
                self.timer.start(int(config.plugins.SPDyn.interval.value) * 60000)

    def onIPchanged(self):
        print("[SPDyn] IP change, setting new one", self.lastip)
        try:
            params = urlencode({
                "hostname": config.plugins.SPDyn.hostname.value,
                "myip": self.lastip,
            })
            response = self.getURL("%s?%s" % (UPDATE_URL, params), auth=True).strip()
            status = response.split()[0] if response else ""

            if status in SUCCESS_CODES:
                print("[SPDyn] update accepted:", response)
            else:
                print("[SPDyn] update rejected:", response)
        except Exception as e:
            print("[SPDyn] IP was not changed:", e)

    def _get_configured_ip_value(self):
        ipversion = config.plugins.SPDyn.ipversion.value

        if ipversion == "4":
            return self._extract_ipv4(self.getURL(CHECK_IP4_URL, auth=False))
        if ipversion == "6":
            return self._extract_ipv6(self.getURL(CHECK_IP6_URL, auth=False))
        if ipversion == "46":
            ipv4 = self._extract_ipv4(self.getURL(CHECK_IP4_URL, auth=False))
            ipv6 = self._extract_ipv6(self.getURL(CHECK_IP6_URL, auth=False))
            return "%s,%s" % (ipv4, ipv6)

        raise ValueError("unsupported IP version setting: %s" % ipversion)

    def _extract_ipv4(self, response_text):
        match = IPV4_RE.search(response_text)
        if not match:
            raise ValueError("could not parse IPv4 address from response")
        return match.group(0)

    def _extract_ipv6(self, response_text):
        match = IPV6_RE.search(response_text)
        if not match:
            raise ValueError("could not parse IPv6 address from response")
        return match.group(0)

    def _build_basic_auth_header(self):
        credentials = "%s:%s" % (config.plugins.SPDyn.hostname.value, config.plugins.SPDyn.token.value)
        encoded = b64encode(ensure_binary(credentials)).decode("ascii")
        return "Basic %s" % encoded

    def getURL(self, url, auth=True):
        request = Request(url)
        request.add_header("User-Agent", USER_AGENT)
        if auth:
            request.add_header("Authorization", self._build_basic_auth_header())

        try:
            html_file = urlopen(request, timeout=REQUEST_TIMEOUT)
            try:
                html_data = html_file.read()
            finally:
                html_file.close()
        except HTTPError as e:
            body = e.read()
            if isinstance(body, bytes):
                body = body.decode("utf-8", "replace")
            raise RuntimeError("HTTP error %s: %s" % (e.code, body))
        except URLError as e:
            raise RuntimeError("URL error: %s" % e)
        except socket_timeout:
            raise RuntimeError("request timed out")

        if isinstance(html_data, bytes):
            html_data = html_data.decode("utf-8", "replace")
        return html_data


def onPluginStart(session, **kwargs):
    session.openWithCallback(onPluginStartCB, SPDynScreenMain)


def onPluginStartCB(changed):
    print("[SPDyn] config changed=", changed)
    global spdynservice
    if changed:
        spdynservice.disable()
        spdynservice.enable()


global spdynservice
spdynservice = SPDynService()


def onSessionStart(reason, **kwargs):
    global spdynservice
    if config.plugins.SPDyn.enable.value is not False:
        if "session" in kwargs:
            spdynservice.addSession(kwargs["session"])
        if reason == 0:
            spdynservice.enable()
        elif reason == 1:
            spdynservice.disable()


def Plugins(path, **kwargs):
    return [
        PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=onSessionStart),
        PluginDescriptor(name=_("SPDyn"), description=_("update your Securepoint Dynamic DNS host"), where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=onPluginStart, icon="icon.png")
    ]
