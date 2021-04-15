/*###########################################################################
#
# Copyright (C) 1993 by Rick Sladkey <jrs@world.std.com>
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

#include <stdio.h>
#include <rpc/rpc.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <memory.h>
#include <stdlib.h>

#include <netdb.h>
#include <arpa/inet.h>
#include <errno.h>
#include <getopt.h>
#include <unistd.h>

#include "showmount.h"

#define MOUNTPROG 100005
#define MOUNTVERS 1
#define MOUNTPROC_EXPORT 5
#define MOUNTPROC_DUMP 2
#define MNTPATHLEN 1024
#define MNTNAMLEN 255

static int	headers = 1;

typedef char *dirpath;
typedef char *name;

typedef struct mountbody *mountlist;
struct mountbody {
	name ml_hostname;
	dirpath ml_directory;
	mountlist ml_next;
};
typedef struct mountbody mountbody;

typedef struct groupnode *groups;
struct groupnode {
	name gr_name;
	groups gr_next;
};
typedef struct groupnode groupnode;

typedef struct exportnode *exports;
struct exportnode {
	dirpath ex_dir;
	groups ex_groups;
	exports ex_next;
};
typedef struct exportnode exportnode;
/****************************************************************************
lokal prototype
****************************************************************************/
bool_t xdr_mountbody (XDR *xdrs, mountbody *objp);
bool_t xdr_mountlist (XDR *xdrs, mountlist *objp);
bool_t xdr_exports (XDR *xdrs, exports *objp);
bool_t xdr_exportnode (XDR *xdrs, exportnode *objp);
bool_t xdr_name (XDR *xdrs, name *objp);
bool_t xdr_dirpath (XDR *xdrs, dirpath *objp);
bool_t xdr_groups (XDR *xdrs, groups *objp);
bool_t xdr_groupnode (XDR *xdrs, groupnode *objp);
int dump_cmp(char **p, char **q);

#define MAXHOSTLEN 256

int dump_cmp(char **p, char **q)
{
	return strcmp(*p, *q);
}


bool_t xdr_mountlist (XDR *xdrs, mountlist *objp)
{
	 if (!xdr_pointer (xdrs, (char **)objp, sizeof (struct mountbody), (xdrproc_t) xdr_mountbody))
		 return FALSE;
	return TRUE;
}

bool_t xdr_mountbody (XDR *xdrs, mountbody *objp)
{
	 if (!xdr_name (xdrs, &objp->ml_hostname))
		 return FALSE;
	 if (!xdr_dirpath (xdrs, &objp->ml_directory))
		 return FALSE;
	 if (!xdr_mountlist (xdrs, &objp->ml_next))
		 return FALSE;
	return TRUE;
}

bool_t xdr_exports (XDR *xdrs, exports *objp)
{
	 if (!xdr_pointer (xdrs, (char **)objp, sizeof (struct exportnode), (xdrproc_t) xdr_exportnode))
		 return FALSE;
	return TRUE;
}

bool_t xdr_exportnode (XDR *xdrs, exportnode *objp)
{
	 if (!xdr_dirpath (xdrs, &objp->ex_dir))
		 return FALSE;
	 if (!xdr_groups (xdrs, &objp->ex_groups))
		 return FALSE;
	 if (!xdr_exports (xdrs, &objp->ex_next))
		 return FALSE;
	return TRUE;
}

bool_t xdr_dirpath (XDR *xdrs, dirpath *objp)
{
	 if (!xdr_string (xdrs, objp, MNTPATHLEN))
		 return FALSE;
	return TRUE;
}

bool_t xdr_name (XDR *xdrs, name *objp)
{
	 if (!xdr_string (xdrs, objp, MNTNAMLEN))
		 return FALSE;
	return TRUE;
}

bool_t xdr_groups (XDR *xdrs, groups *objp)
{
	 if (!xdr_pointer (xdrs, (char **)objp, sizeof (struct groupnode), (xdrproc_t) xdr_groupnode))
		 return FALSE;
	return TRUE;
}

bool_t xdr_groupnode (XDR *xdrs, groupnode *objp)
{
	 if (!xdr_name (xdrs, &objp->gr_name))
		 return FALSE;
	 if (!xdr_groups (xdrs, &objp->gr_next))
		 return FALSE;
	return TRUE;
}

nfsinfo * newNfsInfo()
{
	nfsinfo *nfsInfo = malloc(sizeof(nfsinfo)*255);
	if(!nfsInfo)
		exit(0); // TODO: besser machen
		memset(nfsInfo,0,sizeof(nfsinfo)*255);
	return nfsInfo;
}

void freeNfsInfo(nfsinfo *nfsInfo)
{
	free(nfsInfo);
}

int showNfsShare(char *pythonIp, nfsinfo *nfsInfo) 
{
	char *hostname;
	enum clnt_stat clnt_stat;
	struct hostent *hp;
	struct sockaddr_in server_addr;
	int msock;
	struct timeval total_timeout;
	struct timeval pertry_timeout;
	CLIENT *mclient;
	groups grouplist;
	exports exportlist, exl;
	int n;
	int pos = 0;

	if (pythonIp != NULL)
	{
		hostname = pythonIp;
	}
	else
	{
		printf ("falscher aufruf showm ip, ergebnis ist showm 127.0.0.1\n");
		hostname = "127.0.0.1";
	}
	if (hostname[0] >= '0' && hostname[0] <= '9') {
		server_addr.sin_family = AF_INET;
		server_addr.sin_addr.s_addr = inet_addr(hostname);
	}
	else {
		if ((hp = gethostbyname(hostname)) == NULL) {
			exit(1);
		}
		server_addr.sin_family = AF_INET;
		memcpy(&server_addr.sin_addr, hp->h_addr, hp->h_length);
	}

	/* create mount deamon client */

	server_addr.sin_port = 0;
	msock = RPC_ANYSOCK;
	if ((mclient = clnttcp_create(&server_addr,
	    MOUNTPROG, MOUNTVERS, &msock, 0, 0)) == NULL) {
		server_addr.sin_port = 0;
		msock = RPC_ANYSOCK;
		pertry_timeout.tv_sec = 3;
		pertry_timeout.tv_usec = 0;
		if ((mclient = clntudp_create(&server_addr,
		    MOUNTPROG, MOUNTVERS, pertry_timeout, &msock)) == NULL) {
			//clnt_pcreateerror("mount clntudp_create");
			strcpy(nfsInfo[0].share, "ERROR: mount clntudp_create");
			return(1);
		}
	}
	mclient->cl_auth = authunix_create_default();
	total_timeout.tv_sec = 20;
	total_timeout.tv_usec = 0;

		memset(&exportlist, '\0', sizeof(exportlist));
		clnt_stat = clnt_call(mclient, MOUNTPROC_EXPORT,
			(xdrproc_t) xdr_void, NULL,
			(xdrproc_t) xdr_exports, (caddr_t) &exportlist,
			total_timeout);
		if (clnt_stat != RPC_SUCCESS) {
			//clnt_perror(mclient, "rpc mount export");
			strcpy(nfsInfo[0].share, "ERROR: mount clntudp_create");
			return(1);
		}
		pos = 0;
		while (exportlist) {
			strcpy(nfsInfo[pos].share, exportlist->ex_dir);
			grouplist = exportlist->ex_groups;
			//printf ("blubb ex %s, group %s\n", exportlist->ex_dir,grouplist->gr_name);
			if (grouplist)
				strcpy(nfsInfo[pos].ip, grouplist->gr_name);
			else
				strcpy(nfsInfo[pos].ip, "world");
			pos ++;
			exportlist = exportlist->ex_next;
		}
	return 0;

}
