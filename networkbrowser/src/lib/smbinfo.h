/*###########################################################################
#
# http://newnigma2.to
#
# $Id$ 
#
# Copyright (C) 2007 - 2008 by
# e2board Team <team@newnigma2.to>
# License: GPL
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
###########################################################################*/

#ifndef SMBINFO_H
#define SMBINFO_H

typedef struct {
	char sharename[128];
	char typ[20];
	char comment[128];
} shareinfo;

int smbInfo(char *pythonIp , char *pythonrName, char *pythonUser, char *pythonPass, shareinfo *sInfo);
shareinfo * newShareInfo();
void freeShareInfo(shareinfo *sInfo);

#endif

