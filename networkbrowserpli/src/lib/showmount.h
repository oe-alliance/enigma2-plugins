/*###########################################################################
#
# http://newnigma2.to
#
# $Id$ 
#
# Copyright (C) 2008 by nixkoenner <nixkoenner@newnigma2.to>
# 
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

#ifndef SHOWMOUNT_H
#define SHOWMOUNT_H

typedef struct {
	char share[256];
	char ip[41];
} nfsinfo;

nfsinfo * newNfsInfo();
void freeNfsInfo(nfsinfo *nfsInfo);


#endif

