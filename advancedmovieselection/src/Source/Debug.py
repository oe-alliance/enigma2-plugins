#!/usr/bin/python
'''
Copyright (C) 2011 cmikula

Redirect sys.stdout to file for AdvancedMovieSelection

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

from time import localtime
import sys 

saved_stdout = None


class writer: 
    def __init__(self, *writers): 
        self.writers = writers 
 
    def write(self, text): 
        for w in self.writers:
            if isinstance(w, str):
                try:
                    f = open(w, "a")
                    f.write(text)
                    f.close()
                except:
                    pass
                    #Debug.disable()
                continue
            w.write(text) 
 

class Debug():
    @staticmethod
    def enable(file_name):
        global saved_stdout
        if saved_stdout:
            Debug.disable() 
        saved_stdout = sys.stdout
        sys.stdout = writer(sys.stdout, file_name) 
        try:
            ltim = localtime()
            print()
            print("%04d.%02d.%02d %02d:%02d:%02d: Debug started: %s" % (ltim[0], ltim[1], ltim[2], ltim[3], ltim[4], ltim[5], file_name))
        except:
            pass

    @staticmethod
    def disable():
        try:
            ltim = localtime()
            print()
            print("%04d.%02d.%02d %02d:%02d:%02d: Debug stopped!" % (ltim[0], ltim[1], ltim[2], ltim[3], ltim[4], ltim[5]))
        except:
            pass
        global saved_stdout
        if saved_stdout: 
            sys.stdout = saved_stdout
            saved_stdout = None

