#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import threading
from urllib.request import urlopen

#flag_counter_url = "http://s10.flagcounter.com/count/gEB/bg_FFFFFF/txt_000000/border_CCCCCC/columns_9/maxflags_50/viewers_Plugin+Users/labels_1/pageviews_1/flags_0/"
URL_text_file = "http://subs-downloader.googlecode.com/svn/commertial_banners.txt"
Subtitle_Downloader_temp_dir = '/tmp/SubsDownloader_cache/'


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
            URL_file = urlopen(URL_text_file)
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
                flag = urlopen(x,)
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
