/*###########################################################################
#
# Copyright (C) 2007 - 2009 by
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

#include <stdio.h>
#include <stdlib.h>

#include "nbtscan.h"
#include "smbinfo.h"
#include "showmount.h"
#include "Python.h"

static PyObject *error;

PyObject *_netzInfo(PyObject *self, PyObject *args)
{
	netinfo *nInfo;
	char *s;
	PyObject *plist, *name, *ip, *service, *mac, *result, *domain, *host;
	int i;

	if(!PyArg_ParseTuple(args, "s", &s)) {
		PyErr_SetString(error, "netzInfo(ip/24)");
		return NULL;
	}

	if(!(plist= PyList_New(0)))  return NULL;
	if(!(result= PyList_New(0)))  return NULL;
	nInfo = newNetInfo();
	netzInfo(s, nInfo);
	for (i=0; i<256; i++) 
	{ 
		if(nInfo[i].ip[0] == '\0') {
			break;
		}
		else
		{
			host = Py_BuildValue("s", "host");
			service = Py_BuildValue("s", nInfo[i].service);
			domain = Py_BuildValue("s", nInfo[i].domain);
			ip = Py_BuildValue("s", nInfo[i].ip);
			name = Py_BuildValue("s", nInfo[i].name); 
			mac = Py_BuildValue("s", nInfo[i].mac);
			PyList_Append(plist, host);
			PyList_Append(plist, name);
			PyList_Append(plist, ip);
			PyList_Append(plist, mac);
			PyList_Append(plist, domain);
			PyList_Append(plist, service);
			PyList_Append(result, plist);
			if(!(plist= PyList_New(0)))  return NULL;
			
		}
	} 
	freeNetInfo(nInfo);
	return result;
	//return Py_BuildValue("s", nInfo[0].name);
}

PyObject *_nfsShare(PyObject *self, PyObject *args)
{
	nfsinfo *nfsInfo;
	char *s;
	char *r;
	PyObject *plist, *result, *share, *ip, *nfsShare, *rech, *rechip, *leer;
	int i = 0;
	int err = 0;

	if(!PyArg_ParseTuple(args, "ss", &s, &r)) {
		PyErr_SetString(error, "nfsShare(ip,rechnername)");
		return NULL;
	}

	if(!(plist= PyList_New(0)))  return NULL;
	if(!(result= PyList_New(0)))  return NULL;

	nfsInfo = newNfsInfo();
	err = showNfsShare(s, nfsInfo);
	if (err == 0)
	{
		for (i=0; i<256; i++) 
		{ 
			if(nfsInfo[i].ip[0] == '\0') {
				break;
			}
			else
			{
				ip = Py_BuildValue("s", nfsInfo[i].ip);
				share = Py_BuildValue("s", nfsInfo[i].share);
				nfsShare = Py_BuildValue("s", "nfsShare");
				rech = Py_BuildValue("s",r);
				rechip = Py_BuildValue("s",s);
				leer = Py_BuildValue("s","");
				PyList_Append(plist, nfsShare);
				PyList_Append(plist, rech);
				PyList_Append(plist, rechip);
				PyList_Append(plist, ip);
				PyList_Append(plist, share);
				PyList_Append(plist, leer);
				PyList_Append(result, plist);
				if(!(plist= PyList_New(0)))  return NULL;		
			}
		}
	}
	else
	{
		share = Py_BuildValue("s", nfsInfo[0].share);
		PyList_Append(plist, share);
		PyList_Append(result, plist);
		if(!(plist= PyList_New(0)))  return NULL;
	}
	freeNfsInfo(nfsInfo);	
	return result;
}

PyObject *_smbShare(PyObject *self, PyObject *args)
{
	int i = 0;
	char *s;
	char *r;
	char *u;
	char *p;
	shareinfo *sInfo;
	PyObject *plist, *name, *typ, *comment, *result, *smbShare, *rech, *rechip;

	
	if(!PyArg_ParseTuple(args, "ssss", &s,&r,&u,&p)) {
		PyErr_SetString(error, "getInfo(ip, rechnername, username, passwort)");
		return NULL;
	}
	if(!(plist= PyList_New(0)))  return NULL;
	if(!(result= PyList_New(0)))  return NULL;

	sInfo = newShareInfo();
	smbInfo(s,r,u,p,sInfo);
	for (i=0; i<128; i++) 
	{ 
		if(sInfo[i].sharename[0] == '\0') {
			break;
		}
		else
		{
			name = Py_BuildValue("s", sInfo[i].sharename);
			typ = Py_BuildValue("s", sInfo[i].typ);
			comment = Py_BuildValue("s", sInfo[i].comment);
			smbShare = Py_BuildValue("s", "smbShare");
			rech = Py_BuildValue("s",r);
			rechip = Py_BuildValue("s",s);
			PyList_Append(plist, smbShare);
			PyList_Append(plist, rech);
			PyList_Append(plist, rechip);
			PyList_Append(plist, name);
			PyList_Append(plist, typ);
			PyList_Append(plist, comment);
			PyList_Append(result, plist);
			if(!(plist= PyList_New(0)))  return NULL;
		}
	}
	freeShareInfo(sInfo);
	return result;
	//return Py_BuildValue("s",s);
}

static PyMethodDef netscanmethods[] = {
	{"netzInfo", _netzInfo, METH_VARARGS},
	{"smbShare", _smbShare, METH_VARARGS},
	{"nfsShare", _nfsShare, METH_VARARGS},
	{NULL, NULL}
};

#if PY_MAJOR_VERSION >= 3
	static struct PyModuleDef moduledef = {
		PyModuleDef_HEAD_INIT,
		"netscan",					/* m_name */
		"Module for netscan",		/* m_doc */
		-1,									/* m_size */
		netscanmethods,			/* m_methods */
		NULL,								/* m_reload */
		NULL,								/* m_traverse */
		NULL,								/* m_clear */
		NULL,								/* m_free */
	};

PyMODINIT_FUNC PyInit_netscan(void)
{
    return PyModule_Create(&moduledef);
}
#else

void initnetscan(void)
{
	Py_InitModule("netscan", netscanmethods);
}
#endif
