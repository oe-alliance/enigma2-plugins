/*###########################################################################
#
# written by :	Stephen J. Friedl
#		Software Consultant
#		steve@unixwiz.net
#
# Copyright (C) 2007 - 2008 by
# nixkoenner <nixkoenner@newnigma2.to>
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

#ifndef LIST_H
#define LIST_H

#define ERROR 12345

struct list_item {
	struct list_item* next;
	struct list_item* prev;
	unsigned long content;
};

struct list {
	struct list_item* head;
};

struct list* new_list(); 
struct list_item* new_list_item(unsigned long content);
void delete_list(struct list* list);	
int compare(struct list_item* item1, struct list_item* item2);
int insert(struct list* lst, unsigned long content);
int in_list(struct list* lst, unsigned long content);

#endif

