#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import threading
import urllib
import os
from Screens.Console import Console
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from enigma import quitMainloop
from Screens.MessageBox import MessageBox
try:
    from Components.Opkg import OpkgComponent as IpkgComponent
    from Screens.Opkg import Opkg as Ipkg
except ImportError:
    from Components.Ipkg import IpkgComponent
    from Screens.Ipkg import Ipkg

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

zlib_link = "http://subs-downloader.googlecode.com/files/libzen_0.4.22-0.0_all.ipk"
libmediainfo_link = "http://subs-downloader.googlecode.com/files/libmediainfo_0.7.50-0.0_all.ipk"
unrar_link = "http://subs-downloader.googlecode.com/files/unrar_1.0.1_all.ipk"

#flag_counter_url = "http://s10.flagcounter.com/count/gEB/bg_FFFFFF/txt_000000/border_CCCCCC/columns_9/maxflags_50/viewers_Plugin+Users/labels_1/pageviews_1/flags_0/"
URL_text_file = "http://subs-downloader.googlecode.com/svn/commertial_banners.txt"
Subtitle_Downloader_temp_dir = '/tmp/SubsDownloader_cache/'


class IsNewVersionCheck(threading.Thread):
    def __init__(self, session):
        self.session = session
        threading.Thread.__init__(self)
        self.__latest_version_info_url = "http://subs-downloader.googlecode.com/svn/current_version.txt"
        self.__installed_version_info_file = "/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/about.nfo"

    def run(self):
        error_detected = 0
        latest_vestion_data = None
        try:
            current_vestion_data = open(self.__installed_version_info_file, "r")
            current_verion = current_vestion_data.readline()
            current_vestion_data.close()
            print("Current version: %s" % str(current_verion))
        except:
            error_detected = 1
        try:
            latest_vestion_data = urllib.urlopen(self.__latest_version_info_url)
            latest_verion = latest_vestion_data.readlines()
            latest_vestion_data.close()
            print("Latest version: %s" % str(latest_verion[0]))
        except:
            error_detected = 1

        if error_detected == 1:
            return False
        else:
            if latest_verion[0] > current_verion:
                print("Jest nowa wersja pluginu")
                self.session.open(PluginIpkUpdate, latest_verion[1])
            else:
                print("Posiadasz najnowsza wersje pluginu")
                return False


class InstallDownloadableContent():
    def __init__(self, session, url_to_download):
        self.session = session
        self.cmdList = []
        for item in url_to_download:
            self.cmdList.append((IpkgComponent.CMD_INSTALL, {"package": item}))

    def __install__(self):
        self.session.openWithCallback(self.__restartMessage__, Ipkg, cmdList=self.cmdList)

    def __restartMessage__(self):
        self.session.openWithCallback(self.__restartGUI__, MessageBox, _("Do You want to restart GUI to apply changes?"), MessageBox.TYPE_YESNO, default=False)

    def __restartGUI__(self, callback=None):
        if callback == True:
            quitMainloop(3)
        elif callback == False:
            pass


class PluginIpkUpdate(Screen):  # , IsNewVersionCheck):
    skin = """
		<screen position="150,200" size="460,250" title="New plugin version is avaliable." >
			<widget name="myMenu" position="10,10" size="420,240" scrollbarMode="showOnDemand" />
		</screen>"""
        #def __init__(self, session, args = 0):

    def __init__(self, session, new_version_url):
        self.session = session
        self.new_wersion_url = new_version_url
        list = []
        #self.autoupdate = IsNewVersionCheck()
        list.append((_("Install plugin"), "install"))
        list.append((_("Not now"), "exit"))

        Screen.__init__(self, session)
        self["myMenu"] = MenuList(list)
        self["myActionMap"] = ActionMap(["SetupActions"],
        {
            "ok": self.go  # ,
			#"cancel": self.close(None)
		}, -1)
        #self.new_wersion_url = self.autoupdate.run()

    def go(self):
        returnValue = self["myMenu"].l.getCurrentSelection()[1]
        if returnValue is not None:
            if returnValue == "install":
                if self.new_wersion_url != False:
                    self.libmediaInfoInstallation = InstallDownloadableContent(self.session, [self.new_wersion_url])
                    self.libmediaInfoInstallation.__install__()
                else:
                    self.session.openWithCallback(self.__close_screen__, MessageBox, _("There is problem with server connection. \n Please try again later."), MessageBox.TYPE_INFO)
            elif returnValue == "exit":
                self.__close_screen__()

    def __close_screen__(self, callback=None):
        self.close(None)


#def flagcounetr(CallBackFunction):
#    flag = urllib.urlopen(flag_counter_url,)
#    #Subtitle_Downloader_temp_dir = '/tmp/SubsDownloader_cache/' # Sprawdzac czy sciezka jest taka sama jak w plugin.py
#    picture_file = open(Subtitle_Downloader_temp_dir+"plugin_users.png", "wb")
#    picture_file.write(flag.read())
#    flag.close()
#    picture_file.close()
#    CallBackFunction

class CommertialBannerDownload(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def __download_picture_urls(self):
        picture_links = []
        try:
            URL_file = urllib.urlopen(URL_text_file)
            picture_links = URL_file.readlines()
            URL_file.close()
        except:
            print("Failed to download picture URLS from online text file")
            picture_URLS_dict = []
            for x in picture_links:
                if x[0:3] == "\xef\xbb\xbf":
                    x = x[3:]
                    if x[-1:] == '\n':
                        x = x[0:-1]
                picture_URLS_dict.append(x)
            return picture_URLS_dict

    def __download_pictures(self):
        pictures_URLS = self.__download_picture_urls()
        picture_counter = 0
        for x in pictures_URLS:
            try:
                flag = urllib.urlopen(x,)
                picture_file = open((Subtitle_Downloader_temp_dir + "%s.png" % picture_counter), "wb")
                picture_file.write(flag.read())
                flag.close()
                picture_file.close()
                picture_counter = picture_counter + 1
            except:
                print("Failed to download picture no %i", picture_counter)
        return True

    def run(self):
        return self.__download_pictures()
