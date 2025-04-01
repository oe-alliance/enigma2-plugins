#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Copyright (C) 2011 cmikula

Trashcan support for Advanced Movie Selection

In case of reuse of this source code please do not remove this copyright.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For more information on the GNU General Public License see:
<http://www.gnu.org/licenses/>.

For example, if you distribute copies of such a program, whether gratis or for a fee, you
must pass on to the recipients the same freedoms that you received. You must make sure
that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
'''
from __future__ import print_function
import os
import glob
import shutil
import time
from threading import Thread

TRASH_NAME = ".trash"
TRASH_EXCLUDE = ("DUMBO", "TIMOTHY", "swap", "ram", "ba")

trash_count = 0
trash_size = 0
async_trash = None


class AsynchTrash(Thread):
    def __init__(self, items, wait_ms=0, min_age=0):
        Thread.__init__(self)
        self.items = items
        self.wait_ms = wait_ms
        self.min_age = min_age
        global async_trash
        async_trash = self
        self.start()

    def run(self):
        self.cancel = False
        if (self.wait_ms > 0):
            seconds = self.wait_ms / 1000.0
            time.sleep(seconds)
        for service in self.items:
            if self.cancel:
                return
            try:
                Trashcan.delete(service.getPath(), self.min_age)
            except Exception as e:
                print(e)
        global async_trash
        async_trash = None


class eServiceReferenceTrash():
    def __init__(self, path):
        self.path = path
        p = path.replace(TRASH_NAME, "")
        if (p.endswith(".ts")):
            meta_path = p[:-3] + ".ts.meta"
        else:
            meta_path = p + ".ts.meta"
        if os.path.exists(meta_path):
            file = open(meta_path, "r")
            file.readline()
            self.setName(file.readline().rstrip("\r\n"))
            if len(self.name) == 0:
                self.setName(os.path.basename(p))
            self.short_description = file.readline().rstrip("\r\n")
            file.close()
        else:
            self.setName(os.path.basename(p))
            self.short_description = ""

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def setPath(self, path):
        self.path = path

    def getPath(self):
        return self.path

    def getShortDescription(self):
        return self.short_description


def updateInfo(path):
    global trash_count, trash_size
    trash_count = trash_count + 1
    if os.path.isfile(path):
        trash_size += os.path.getsize(path)
    else:
        from .ServiceUtils import getFolderSize
        trash_size += getFolderSize(os.path.dirname(path))


def resetInfo():
    global trash_count, trash_size
    trash_count = 0
    trash_size = 0


class Trashcan:
    @staticmethod
    def listAllMovies(root):
        resetInfo()
        list = []
        for (path, dirs, files) in os.walk(root):
            # Skip excluded directories here
            sp = path.split("/")
            if len(sp) > 2:
                if sp[2] in TRASH_EXCLUDE:
                    continue

            # This path detection is only for trashed DVD structures
            if path.endswith(TRASH_NAME):
                service = eServiceReferenceTrash(path)
                list.append(service)
                updateInfo(path)

            for filename in files:
                if filename.endswith(TRASH_NAME):
                    f = os.path.join(path, filename)
                    service = eServiceReferenceTrash(f)
                    list.append(service)
                    updateInfo(f)
        return list

    @staticmethod
    def listMovies(path):
        resetInfo()
        list = []
        for filename in glob.glob(os.path.join(path, "*" + TRASH_NAME)):
            service = eServiceReferenceTrash(filename)
            list.append(service)
            updateInfo(filename)
        return list

    @staticmethod
    def trash(filename):
        print("trash: ", filename)
        os.rename(filename, filename + TRASH_NAME)

    @staticmethod
    def restore(filename):
        print("restore: ", filename)
        os.rename(filename, filename.replace(TRASH_NAME, ""))

    @staticmethod
    def delete(filename, min_age=0):
        if min_age > 0:
            # Make sure the file/directory has a ctime that didn't
            # change for at least the intended removal minimum age
            print("check retention time", filename)
            nowSec = int(time.time())
            fCtime = os.path.getctime(filename)
            print("ctime:", str(fCtime), "now:", str(nowSec))
            if nowSec < (fCtime + min_age):
                print("skipped, too young: ", str(nowSec - fCtime), "<", str(min_age))
                return

        movie_ext = ["gm", "sc", "ap", "cuts"]
        print("delete: ", filename)
        #path = os.path.split(filename)[0]
        original_name = filename.replace(TRASH_NAME, "")
        if os.path.isfile(filename):
            file_extension = os.path.splitext(original_name)[-1]
            eit = os.path.splitext(original_name)[0] + ".eit"
            jpg = os.path.splitext(original_name)[0] + ".jpg"
        else:
            file_extension = ""
            eit = original_name + ".eit"
            jpg = original_name + ".jpg"

        if file_extension == ".ts":
            movie_ext.append("meta")
        else:
            movie_ext.append("ts.meta")
        for ext in movie_ext:
            to_delete = original_name + "." + ext
            if os.path.exists(to_delete):
                print(to_delete)
                os.remove(to_delete)

        if os.path.exists(jpg):
            print(jpg)
            os.remove(jpg)

        if os.path.exists(eit):
            print(eit)
            os.remove(eit)

        if os.path.exists(filename):
            if os.path.isfile(filename):
                os.rename(filename, original_name)
                filename = original_name
                from .ServiceProvider import ServiceCenter, eServiceReference
                service = eServiceReference(eServiceReference.idDVB, 0, filename)
                print("[erase file]", filename)
                serviceHandler = ServiceCenter.getInstance()
                offline = serviceHandler.offlineOperations(service)
                result = False
                if offline is not None:
                    # really delete!
                    if not offline.deleteFromDisk(0):
                        result = True

                if result is False:
                    print("Error")
            else:
                print("[erase dir]", filename)
                shutil.rmtree(filename)

    @staticmethod
    def deleteAsynch(trash, min_age=0):
        AsynchTrash(trash, 0, min_age)

    @staticmethod
    def isCurrentlyDeleting():
        return async_trash is not None

    @staticmethod
    def getTrashCount():
        global trash_count
        return trash_count

    @staticmethod
    def getTrashSize():
        global trash_size
        return float(trash_size / (1024 * 1024))
