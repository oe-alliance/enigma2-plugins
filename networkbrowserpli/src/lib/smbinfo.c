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
#include <stdlib.h>
#include <string.h>     
#include <unistd.h> 
#include <stddef.h>
#include <ctype.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/fcntl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <time.h>
#include <errno.h>

#include "smb.h"
#include "smbinfo.h"

/****************************************************************************
lokal prototype
****************************************************************************/
BOOL get_myname(char *myname,struct in_addr *ip);
struct hostent *Get_Hostbyname(char *name);
void strlower(char *s);
void strupper(char *s);
void browse_host(shareinfo *sInfo);
void ssval(char *buf,int pos,uint16 val);
uint32 ival(char *buf,int pos);
void *object_byte_swap(void *obj,int size);
int smb_buflen(char *buf);
int smb_numwords(char *buf);
char *skip_string(char *buf,int n);
uint16 sval(char *buf,int pos);
char *smb_buf(char *buf);
int smb_buf_ofs(char *buf);
BOOL send_login(char *inbuf,char *outbuf,BOOL use_setup);
int name_len(char *s);
char *smb_errstr(char *inbuf);
time_t make_unix_date2(void *date_ptr);
int TimeDiff(void);
time_t TimeLocal(struct tm *tm,int timemul);
void interpret_dos_date(uint32 date,int *year,int *month,int *day,int *hour,int *minute,int *second);
struct tm *LocalTime(time_t *t,int timemul);
void sival(char *buf,int pos,uint32 val);
time_t make_unix_date(void *date_ptr);
void send_logout(char *inbuf,char *outbuf );
BOOL send_smb(char *buffer);
int smb_len(char *buf);
void log_out(char *buffer,int len);
void close_sockets(void );
int write_socket(int fd,char *buf,int len);
int set_message(char *buf,int num_words,int num_bytes,BOOL zero);
void smb_setlen(char *buf,int len);
void setup_pkt(char *outbuf);
BOOL receive_smb(char *buffer,int timeout);
void log_in(char *buffer,int len);
int read_smb_length(int fd,char *inbuf,int timeout);
int read_with_timeout(int fd,char *buf,int mincnt,int maxcnt,long time_out,BOOL exact);
int set_blocking(int fd, BOOL set);
int tval_sub( struct timeval *retval, struct timeval *val1, struct timeval *val2);
BOOL read_data(int fd,char *buffer,int N);
BOOL send_keepalive(void);
BOOL open_sockets(int port );
int open_socket_out(struct in_addr *addr, int port );
BOOL big_endian(void );
int name_mangles(char *In,char *Out);
/****************************************************************************
globale variablen
****************************************************************************/
shareinfo	*sInfo = 0;
struct in_addr myip;
struct in_addr dest_ip;
struct timezone tz;
pstring myname = "";
pstring service="";
pstring desthost="";
pstring password = "";
pstring username = "";
pstring scope ="";
time_t servertime = 0;
int max_xmit = BUFFER_SIZE;
int Protocol = PROTOCOL_COREPLUS;
int extra_time_offset = 0;
BOOL readbraw_supported = False;
BOOL writebraw_supported = False;
BOOL got_pass = False;
BOOL passive = False;
BOOL have_ip = False;

/****************************************************************************
speicher allocieren  
****************************************************************************/
shareinfo * newShareInfo()
{
	shareinfo *sInfo = malloc(sizeof(shareinfo)*128);
	if(!sInfo)
	{
		printf("ERROR MALLOC !!!!!!!\n");
		exit(0); // TODO: besser machen
	} 
	memset(sInfo,0,sizeof(shareinfo)*128);
	return sInfo;
}
/****************************************************************************
speicher freigeben
****************************************************************************/
void freeShareInfo(shareinfo *sInfo)
{
	free(sInfo); 
}
/****************************************************************************
hier gehts los 
****************************************************************************/
int smbInfo(char *pythonIp , char *pythonrName, char *pythonUser, char *pythonPass, shareinfo *sInfo) 
{
	int port = 139;
	have_ip = True;
	NeedSwap = big_endian();
	myip.s_addr= inet_addr(pythonrName);
	dest_ip.s_addr= inet_addr(pythonIp);
	strcpy(username,pythonUser);
	strupper(username);
	strcpy(password,pythonPass);
	get_myname(*myname?NULL:myname,&myip);
	strupper(myname);
	sprintf(service,"\\\\%s\\IPC$",pythonrName);
	strupper(service);
#if DEBUG
	printf("service = %s\n", service);
#endif
	if (open_sockets(port))
	{
		browse_host(sInfo);
		close_sockets();
		return(0);
	}
	return 0;
}

/****************************************************************************
get my own name and IP
****************************************************************************/
BOOL get_myname(char *myname,struct in_addr *ip)
{
  struct hostent *hp;
  pstring myhostname="";

  /* get my host name */
  if (gethostname(myhostname, sizeof(myhostname)) == -1) 
    {
#if DEBUG
      printf("gethostname failed\n");
#endif
      return False;
    } 

  /* get host info */
  if ((hp = Get_Hostbyname(myhostname)) == 0) 
    {
#if DEBUG
      printf( "Get_Hostbyname: Unknown host %s.\n",myhostname);
#endif
      return False;
    }

  if (myname)
    {
      /* split off any parts after an initial . */
      char *p = strchr(myhostname,'.');
      if (p) *p = 0;

      strcpy(myname,myhostname);
    }

  if (ip)
    memcpy((char *)ip,(char *)hp->h_addr,4);

  return(True);
}

/****************************************************************************
a wrapper for gethostbyname() that tries with all lower and all upper case 
if the initial name fails
****************************************************************************/
struct hostent *Get_Hostbyname(char *name)
{
  char *name2 = strdup(name);
  struct hostent *ret;

  if (!name2)
    {
#if DEBUG
      printf("Memory allocation error in Get_Hostbyname! panic\n");
#endif
      return (NULL);
    }

  ret = gethostbyname(name2);
  if (ret != NULL)
    {
      free(name2);
      return(ret);
    }

  /* try with all lowercase */
  strlower(name2);
  ret = gethostbyname(name2);
  if (ret != NULL)
    {
      free(name2);
      return(ret);
    }

  /* try with all uppercase */
  strupper(name2);
  ret = gethostbyname(name2);
  if (ret != NULL)
    {
      free(name2);
      return(ret);
    }
  
  /* nothing works :-( */
  free(name2);
  return(NULL);
}

/*******************************************************************
  convert a string to lower case
********************************************************************/
void strlower(char *s)
{
	while (*s)
	{
		if (isupper(*s))
			*s = tolower(*s);
			s++;
	}
}

/*******************************************************************
  convert a string to upper case
********************************************************************/
void strupper(char *s)
{
	while (*s)
	{
		if (islower(*s))
			*s = toupper(*s);
			s++;
	}
}

/****************************************************************************
try and browse available connections on a host
****************************************************************************/
void browse_host(shareinfo *sInfo)
{
  char *p;
  char *params;
  char *inbuf = (char *)malloc(BUFFER_SIZE + SAFETY_MARGIN);
  char *outbuf = (char *)malloc(BUFFER_SIZE + SAFETY_MARGIN);
  if ((inbuf == NULL) || (outbuf == NULL)) 
    return;
  
  memset(outbuf,0,smb_size);

  if (!send_login(inbuf,outbuf,True))
    return;

  /* now send a SMBtrans command with api RNetShareEnum */
  memset(outbuf,0,smb_size);
  set_message(outbuf,14,0,True);
  CVAL(outbuf,smb_com) = SMBtrans;
  SSVAL(outbuf,smb_tid,cnum);
  setup_pkt(outbuf);

  SSVAL(outbuf,smb_vwv1,0); /* data count */
  SSVAL(outbuf,smb_vwv2,1024); /* mprcnt */
  SSVAL(outbuf,smb_vwv3,4096); /* mdrcnt */
  SSVAL(outbuf,smb_vwv4,10); /* msrcnt */
  SSVAL(outbuf,smb_vwv5,0); /* flags */
  SSVAL(outbuf,smb_vwv11,0); /* dscnt */
  SSVAL(outbuf,smb_vwv12,0); /* dsoff */
  CVAL(outbuf,smb_vwv13) = 0; /* suwcnt */

  p = smb_buf(outbuf);

  strcpy(p,"\\PIPE\\LANMAN");

  params = skip_string(p,1);

  SSVAL(params,0,0); /* RNetShareEnum */
  
  p = params+2;

  strcpy(p,"WrLeh");
  p = skip_string(p,1);
  strcpy(p,"B13BWz");
  p = skip_string(p,1);
  SSVAL(p,0,1);
  SSVAL(p,2,SVAL(outbuf,smb_vwv3));

  p += 4;


  set_message(outbuf,14,PTR_DIFF(p,smb_buf(outbuf)),False);

  SSVAL(outbuf,smb_vwv0,PTR_DIFF(p,params)); /* param count */
  SSVAL(outbuf,smb_vwv9,SVAL(outbuf,smb_vwv0)); /* pscnt */
  SSVAL(outbuf,smb_vwv10,PTR_DIFF(params,outbuf)-4); /* psoff */

  send_smb(outbuf);
  receive_smb(inbuf,0);

  if (CVAL(inbuf,smb_rcls) == 0)
    {
      int ofs_param = SVAL(inbuf,smb_vwv4);
      int ofs_data = SVAL(inbuf,smb_vwv7);
      char *param = inbuf+4 + ofs_param;
      char *data = inbuf+4 + ofs_data;
      int count=SVAL(param,4);
      int converter=SVAL(param,2);
      int i;

      p = data;
#if DEBUG
  if (count > 0)
	{
	  printf("\n\tSharename      Type      Comment\n");
	  printf("\t---------      ----      -------\n");
	}
#endif

      for (i=0;i<count;i++)
	{
	  char *sname = p;
	  int type = SVAL(p,14);
	  int comment_offset = IVAL(p,16) & 0xFFFF;
	  fstring typestr="";

	  switch (type)
	    {
	    case 0:
	      strcpy(typestr,"Disk"); break;
	    case 1:
	      strcpy(typestr,"Printer"); break;	      
	    case 2:
	      strcpy(typestr,"Device"); break;
	    case 3:
	      strcpy(typestr,"IPC"); break;      
	    }
		strcpy(sInfo[i].sharename,sname);
		strcpy(sInfo[i].typ,typestr);
		strcpy(sInfo[i].comment,comment_offset?data+comment_offset-converter:"");
#if DEBUG
	  printf("\t%-15.15s%-10.10s%s\n",
		 sname,
		 typestr,
		 comment_offset?data+comment_offset-converter:"");
#endif
	  p += 20;
	}
    }
  send_logout(inbuf,outbuf);
}
/****************************************************************************
  set a value at buf[pos] to int16 val
****************************************************************************/
void ssval(char *buf,int pos,uint16 val)
{
  SWP(&val,sizeof(val));
  memcpy(buf + pos,(char *)&val,sizeof(int16));
}
/****************************************************************************
  get a 32 bit integer value
****************************************************************************/
uint32 ival(char *buf,int pos)
{
  uint32 val;
  memcpy((char *)&val,buf + pos,sizeof(int));
  SWP(&val,sizeof(val));
  return(val);
}
/*******************************************************************
  byte swap an object - the byte order of the object is reversed
********************************************************************/
void *object_byte_swap(void *obj,int size)
{
  int i;
  char c;
  char *p1 = (char *)obj;
  char *p2 = p1 + size - 1;
  
  size /= 2;
  
  for (i=0;i<size;i++)
    {
      c = *p1;
      *p1 = *p2;
      *p2 = c;
      p1++;
      p2--;
    }
  return(obj);
}
/*******************************************************************
return the size of the smb_buf region of a message
********************************************************************/
int smb_buflen(char *buf)
{
  return(SVAL(buf,smb_vwv0 + smb_numwords(buf)*2));
}
/*******************************************************************
return the number of smb words
********************************************************************/
int smb_numwords(char *buf)
{
  return (CVAL(buf,smb_wct));
}
/*******************************************************************
skip past some strings in a buffer
********************************************************************/
char *skip_string(char *buf,int n)
{
  while (n--)
    buf += strlen(buf) + 1;
  return(buf);
}
/****************************************************************************
  get a int16 value
****************************************************************************/
uint16 sval(char *buf,int pos)
{
  uint16 val;
  memcpy((char *)&val,buf + pos,sizeof(uint16));
  SWP(&val,sizeof(val));
  return(val);
}
/*******************************************************************
  return a pointer to the smb_buf data area
********************************************************************/
char *smb_buf(char *buf)
{
  return (buf + smb_buf_ofs(buf));
}
/*******************************************************************
  return a pointer to the smb_buf data area
********************************************************************/
int smb_buf_ofs(char *buf)
{
  return (smb_size + CVAL(buf,smb_wct)*2);
}
/****************************************************************************
send a login command
****************************************************************************/
BOOL send_login(char *inbuf,char *outbuf,BOOL use_setup)
{
  int sesskey=0;
  struct {
    int prot;
    char *name;
  }
  prots[] = 
    {
#if CORE
      {PROTOCOL_CORE,"PC NETWORK PROGRAM 1.0"},
      {PROTOCOL_COREPLUS,"MICROSOFT NETWORKS 1.03"},
#endif
//#if LANMAN1
      {PROTOCOL_LANMAN1,"MICROSOFT NETWORKS 3.0"},
      {PROTOCOL_LANMAN1,"LANMAN1.0"},
//#endif
#if LANMAN2
      {PROTOCOL_LANMAN2,"LM1.2X002"},
#endif
      {-1,NULL}
    };
  char *pass = NULL;  
  pstring dev = "A:";
  char *p;
  int len = 4;
  int numprots;
	/* mal auskommentiert
  if (connect_as_printer)
    strcpy(dev,"LPT1:");
  if (connect_as_ipc)*/
    strcpy(dev,"IPC");

  /* send a session request (RFC 8002) */
  CVAL(outbuf,0) = 0x81;

  /* put in the destination name */
  p = outbuf+len;
  name_mangles(desthost,p);
  len += name_len(p);

  /* and my name */
  p = outbuf+len;
  name_mangles(myname,p);
  len += name_len(p);

  /* setup the packet length */
  /* We can't use smb_setlen here as it assumes a data
     packet and will trample over the name data we have copied
     in (by adding 0xFF 'S' 'M' 'B' at offsets 4 - 7 */

  SSVAL(outbuf,2,len);
  BSWP(outbuf+2,2);

  if (len >= (1 << 16))
    CVAL(outbuf,1) |= 1;

  send_smb(outbuf);

  receive_smb(inbuf,0);
 
  if (CVAL(inbuf,0) != 0x82)
    {
      int ecode = CVAL(inbuf,4);
#if DEBUG
      printf("Session request failed (%d,%d) with username=%s myname=%s destname=%s\n",
	    CVAL(inbuf,0),ecode,username,myname,desthost);
#endif
      switch (ecode)
	{
	case 0x80: 
#if DEBUG
	  printf("Not listening on called name\n"); 
	  printf("Try to connect to another name (instead of %s)\n",desthost);
	  printf("You may find the -I option useful for this\n");
#endif
	  break;
	case 0x81: 
#if DEBUG
	  printf("Not listening for calling name\n"); 
	  printf("Try to connect as another name (instead of %s)\n",myname);
	  printf("You may find the -n option useful for this\n");
#endif
	  break;
	case 0x82: 
#if DEBUG
	  printf("Called name not present\n"); 
	  printf("Try to connect to another name (instead of %s)\n",desthost);
	  printf("You may find the -I option useful for this\n");
#endif
	  break;
	case 0x83: 
#if DEBUG
	  printf("Called name present, but insufficient resources\n"); 
	  printf("Perhaps you should try again later?\n"); 
#endif
	  break;
	case 0x8F:
#if DEBUG
	  printf("Unspecified error 0x%X\n",ecode); 
	  printf("Your server software is being unfriendly\n");
#endif
	  break;	  
	}
      return(False);
    }      

  memset(outbuf,0,smb_size);

  /* setup the protocol strings */
  {
    int plength;
    char *p;

    for (numprots=0,plength=0;prots[numprots].name;numprots++)
      plength += strlen(prots[numprots].name)+2;
    
    set_message(outbuf,0,plength,True);

    p = smb_buf(outbuf);
    for (numprots=0;prots[numprots].name;numprots++)
      {
	*p++ = 2;
	strcpy(p,prots[numprots].name);
	p += strlen(p) + 1;
      }
  }

  CVAL(outbuf,smb_com) = SMBnegprot;
  setup_pkt(outbuf);

  CVAL(smb_buf(outbuf),0) = 2;

  send_smb(outbuf);
  receive_smb(inbuf,0);

  if (CVAL(inbuf,smb_rcls) != 0 || ((int)SVAL(inbuf,smb_vwv0) >= numprots))
    {
#if DEBUG
      printf("SMBnegprot failed. myname=%s destname=%s - %s \n",
	    myname,desthost,smb_errstr(inbuf));
#endif
      return(False);
    }

  max_xmit = MIN(max_xmit,(int)SVAL(inbuf,smb_vwv2));
#if DEBUG
  printf("Sec mode %d\n",SVAL(inbuf,smb_vwv1));
  printf("max xmt %d\n",SVAL(inbuf,smb_vwv2));
  printf("max mux %d\n",SVAL(inbuf,smb_vwv3));
  printf("max vcs %d\n",SVAL(inbuf,smb_vwv4));
  printf("max blk %d\n",SVAL(inbuf,smb_vwv5));
  printf("time zone %d\n",SVAL(inbuf,smb_vwv10));
#endif
  sesskey = IVAL(inbuf,smb_vwv6);

  servertime = make_unix_date(inbuf+smb_vwv8);
#if DEBUG
  printf("Chose protocol [%s]\n",prots[SVAL(inbuf,smb_vwv0)].name);
#endif
  Protocol = prots[SVAL(inbuf,smb_vwv0)].prot;
  if (Protocol >= PROTOCOL_COREPLUS)
    {
      readbraw_supported = ((SVAL(inbuf,smb_vwv5) & 0x1) != 0);
      writebraw_supported = ((SVAL(inbuf,smb_vwv5) & 0x2) != 0);
    }

#if DEBUG
  if (Protocol >= PROTOCOL_LANMAN1)
    {
      printf("Server time is %sTimezone is UTC%+d\n",
	       asctime(LocalTime(&servertime,0)),
	       -(int16)SVAL(inbuf,smb_vwv10)/60);
    }
#endif
  if (!got_pass)
    pass = password;
  else
    pass = (char *)getpass("Password: ");

  if (Protocol >= PROTOCOL_LANMAN1 && use_setup)
    {
      /* send a session setup command */
      memset(outbuf,0,smb_size);
      set_message(outbuf,10,2 + strlen(username) + strlen(pass),True);
      CVAL(outbuf,smb_com) = SMBsesssetupX;
      setup_pkt(outbuf);

      CVAL(outbuf,smb_vwv0) = 0xFF;
      SSVAL(outbuf,smb_vwv2,max_xmit);
      SSVAL(outbuf,smb_vwv3,2);
      SSVAL(outbuf,smb_vwv4,getpid());
      SIVAL(outbuf,smb_vwv5,sesskey);
      SSVAL(outbuf,smb_vwv7,strlen(pass)+1);
      p = smb_buf(outbuf);
      strcpy(p,pass);
      p += strlen(pass)+1;
      strcpy(p,username);

      send_smb(outbuf);
      receive_smb(inbuf,0);      

      if (CVAL(inbuf,smb_rcls) != 0)
	{
#if DEBUG
	  printf("Session setup failed for username=%s myname=%s destname=%s   %s\n",
		username,myname,desthost,smb_errstr(inbuf));
	  printf("You might find the -U or -n options useful\n");
	  printf("Sometimes you have to use `-n USERNAME' (particularly with OS/2)\n");
	  printf("Some servers also insist on uppercase-only passwords\n");
#endif
	  return(False);
	}

      /* use the returned uid from now on */
	if (SVAL(inbuf,smb_uid) != uid)
#if DEBUG
		printf("Server gave us a UID of %d. We gave %d\n",
	  SVAL(inbuf,smb_uid),uid);
#endif
    uid = SVAL(inbuf,smb_uid);
    }

  /* now we've got a connection - send a tcon message */
  memset(outbuf,0,smb_size);
#if 0
  if (Protocol >= PROTOCOL_LANMAN1)
    strcpy(pass,"");
#endif
#if DEBUG
  if (strncmp(service,"\\\\",2) != 0)
    {
      printf("\nWarning: Your service name doesn't start with \\\\. This is probably incorrect.\n");
      printf("Perhaps try replacing each \\ with \\\\ on the command line?\n\n");
    }
#endif

 again:
  set_message(outbuf,0,6 + strlen(service) + strlen(pass) + strlen(dev),True);
  CVAL(outbuf,smb_com) = SMBtcon;
  setup_pkt(outbuf);

  p = smb_buf(outbuf);
  *p++ = 4;
  strcpy(p,service);
  p += strlen(p) + 1;
  *p++ = 4;
  strcpy(p,pass);
  p += strlen(p) + 1;
  *p++ = 4;
  strcpy(p,dev);

  send_smb(outbuf);
  receive_smb(inbuf,0);

  /* trying again with a blank password */
  if (CVAL(inbuf,smb_rcls) != 0 && 
      strlen(pass) > 0 && 
      Protocol >= PROTOCOL_LANMAN1)
    {
#if DEBUG
      printf("first SMBtcon failed, trying again. %s\n",smb_errstr(inbuf));
#endif
      strcpy(pass,"");
      goto again;
    }  

  if (CVAL(inbuf,smb_rcls) != 0)
    {
#if DEBUG
      printf("SMBtcon failed. %s\n",smb_errstr(inbuf));
      printf("Perhaps you are using the wrong sharename, username or password?\n");
      printf("Some servers insist that these be in uppercase\n");
#endif
      return(False);
    }
  

  max_xmit = SVAL(inbuf,smb_vwv0);
  max_xmit = MIN(max_xmit,BUFFER_SIZE-4);
  if (max_xmit <= 0)
    max_xmit = BUFFER_SIZE - 4;

  cnum = SVAL(inbuf,smb_vwv1);
#if DEBUG
  printf("Connected with cnum=%d max_xmit=%d\n",cnum,max_xmit);
#endif
  /* wipe out the password from memory */
  if (got_pass)
    memset(password,0,strlen(password));

  return True;

}
/****************************************************************************
return the total storage length of a mangled name
****************************************************************************/
int name_len(char *s)
{
  unsigned char c = *(unsigned char *)s;
  if ((c & 0xC0) == 0xC0)
    return(2);
  return(strlen(s) + 1);
}
/****************************************************************************
return a SMB error string from a SMB buffer
****************************************************************************/
char *smb_errstr(char *inbuf)
{
  static pstring ret;
  int class = CVAL(inbuf,smb_rcls);
  int num = SVAL(inbuf,smb_err);
  int i,j;

  for (i=0;err_classes[i].class;i++)
    if (err_classes[i].code == class)
      {
	if (err_classes[i].err_msgs)
	  {
	    err_code_struct *err = err_classes[i].err_msgs;
	    for (j=0;err[j].name;j++)
	      if (num == err[j].code)
		{
		    sprintf(ret,"%s - %s (%s)",err_classes[i].class,
			    err[j].name,err[j].message);
		  return ret;
		}
	  }

	sprintf(ret,"%s - %d",err_classes[i].class,num);
	return ret;
      }
  
  sprintf(ret,"ERROR: Unknown error (%d,%d)",class,num);
  return(ret);
}
/*******************************************************************
  create a unix date from a dos date
********************************************************************/
time_t make_unix_date2(void *date_ptr)
{
  uint32 dos_date;
  struct tm t;
  unsigned char *p = (unsigned char *)&dos_date;
  unsigned char c;

  memcpy(&dos_date,date_ptr,4);

  if (dos_date == 0) return(0); 

  c = p[0];
  p[0] = p[2];
  p[2] = c;
  c = p[1];
  p[1] = p[3];
  p[3] = c;

  
  interpret_dos_date(dos_date,&t.tm_year,&t.tm_mon,
		     &t.tm_mday,&t.tm_hour,&t.tm_min,&t.tm_sec);
  t.tm_wday = 1;
  t.tm_yday = 1;
  t.tm_isdst = 0;
#if DEBUG
  printf("year=%d month=%d day=%d hr=%d min=%d sec=%d\n",t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec);
#endif
  return (TimeLocal(&t,GMT_TO_LOCAL));
}
/****************************************************************************
return the difference between local and GMT time
****************************************************************************/
int TimeDiff(void)
{
  static BOOL initialised = False;
  static int timediff = 0;

  if (!initialised)
    {
      /* There are four ways of getting the time difference between GMT and
	 local time. Use the following defines to decide which your system
	 can handle */
#ifdef HAVE_GETTIMEOFDAY
      struct timeval tv;
      struct timezone tz;

      gettimeofday(&tv, &tz);
      timediff = 60 * tz.tz_minuteswest;
#else
      time_t t=time(NULL);

#ifdef HAVE_TIMELOCAL
      timediff = timelocal(gmtime(&t)) - t;
#else
#ifdef HAVE_TIMEZONE
      localtime(&t);
      timediff = timezone;
#else
      timediff = - (localtime(&t)->tm_gmtoff);
#endif
#endif
#endif
#if DEBUG
      printf("timediff=%d\n",timediff);
#endif
      initialised = True;
    }

return(timediff + (extra_time_offset*60));
}


/****************************************************************************
try to optimise the timelocal call, it can be quite expenive on some machines
****************************************************************************/
time_t TimeLocal(struct tm *tm,int timemul)
{
  return(mktime(tm) + timemul * TimeDiff());
}
/*******************************************************************
  interpret a 32 bit dos packed date/time to some parameters
********************************************************************/
void interpret_dos_date(uint32 date,int *year,int *month,int *day,int *hour,int *minute,int *second)
{
  unsigned char *p = (unsigned char *)&date;

  *second = 2*(p[0] & 0x1F);
  *minute = (p[0]>>5) + ((p[1]&0x7)<<3);
  *hour = (p[1]>>3);
  *day = p[2]&0x1F;
  *month = (p[2]>>5) + ((p[3]&0x1)<<3) - 1;
  *year = (p[3]>>1) + 80;
}
/****************************************************************************
try to optimise the localtime call, it can be quite expenive on some machines
timemul is normally LOCAL_TO_GMT, GMT_TO_LOCAL or 0
****************************************************************************/
struct tm *LocalTime(time_t *t,int timemul)
{
  time_t t2 = *t;

  t2 += timemul * TimeDiff();

  return(gmtime(&t2));
}
/****************************************************************************
  set a value at buf[pos] to integer val
****************************************************************************/
void sival(char *buf,int pos,uint32 val)
{
  SWP(&val,sizeof(val));
  memcpy(buf + pos,(char *)&val,sizeof(val));
}
/*******************************************************************
  create a unix date from a dos date
********************************************************************/
time_t make_unix_date(void *date_ptr)
{
  uint32 dos_date;
  struct tm t;

  memcpy(&dos_date,date_ptr,4);

  if (dos_date == 0) return(0);
  
  interpret_dos_date(dos_date,&t.tm_year,&t.tm_mon,
		     &t.tm_mday,&t.tm_hour,&t.tm_min,&t.tm_sec);
  t.tm_wday = 1;
  t.tm_yday = 1;
  t.tm_isdst = 0;
/*  DEBUG(4,("year=%d month=%d day=%d hr=%d min=%d sec=%d\n",t.tm_year,t.tm_mon,
	 t.tm_mday,t.tm_hour,t.tm_sec)); */
  return (TimeLocal(&t,GMT_TO_LOCAL));
}
/****************************************************************************
send a logout command
****************************************************************************/
void send_logout(char *inbuf,char *outbuf )
{
  set_message(outbuf,0,0,True);
  CVAL(outbuf,smb_com) = SMBtdis;
  SSVAL(outbuf,smb_tid,cnum);
  setup_pkt(outbuf);

  send_smb(outbuf);
  receive_smb(inbuf,0);
#if DEBUG
  if (CVAL(inbuf,smb_rcls) != 0)
    {
      printf("SMBtdis failed %s\n",smb_errstr(inbuf));
    }
#endif
 
#ifdef STATS
  stats_report();
#endif
}
/****************************************************************************
  send an smb to a fd 
****************************************************************************/
BOOL send_smb(char *buffer)
{
  int fd = Client;
  int len;
  int ret,nwritten=0;
  len = smb_len(buffer) + 4;

  log_out(buffer,len);

  while (nwritten < len)
    {
      ret = write_socket(fd,buffer+nwritten,len - nwritten);
      if (ret <= 0)
	{
#if DEBUG
	  printf("Error writing %d bytes to client. %d. Exiting\n",len,ret);
#endif
          close_sockets();
	  return False; 
	}
      nwritten += ret;
    }


  return True;
}
/*******************************************************************
  return the length of an smb packet
********************************************************************/
int smb_len(char *buf)
{
  int msg_flags = CVAL(buf,1);
  uint16 len = SVAL(buf,2);
  BSWP(&len,2);

  if (msg_flags & 1)
    len += 1<<16;

  return len;
}
/****************************************************************************
log a packet to logout
****************************************************************************/
void log_out(char *buffer,int len)
{   
#if DEBUG
  printf("logged %d bytes out\n",len);
#endif
}
/****************************************************************************
  close the socket communication
****************************************************************************/
void close_sockets(void )
{
  extern int Client;
  close(Client);
  Client = 0;
}
/****************************************************************************
write to a socket
****************************************************************************/
int write_socket(int fd,char *buf,int len)
{
  int ret=0;

  if (passive)
    return(len);
#if DEBUG
  printf("write_socket(%d,%d)\n",fd,len);
#endif
  ret = write(fd,buf,len);
#if DEBUG
  printf("write_socket(%d,%d) gave %d\n",fd,len,ret);
#endif
  return(ret);
}
/*******************************************************************
  setup the word count and byte count for a smb message
********************************************************************/
int set_message(char *buf,int num_words,int num_bytes,BOOL zero)
{
  if (zero)
    memset(buf + smb_size,0,num_words*2 + num_bytes);
  CVAL(buf,smb_wct) = num_words;
  SSVAL(buf,smb_vwv + num_words*sizeof(WORD),num_bytes);  
  smb_setlen(buf,smb_size + num_words*2 + num_bytes - 4);
  return (smb_size + num_words*2 + num_bytes);
}
/*******************************************************************
  set the length of an smb packet
********************************************************************/
void smb_setlen(char *buf,int len)
{
  SSVAL(buf,2,len);
  BSWP(buf+2,2);

/*
  CVAL(buf,3) = len & 0xFF;
  CVAL(buf,2) = (len >> 8) & 0xFF;
*/
  CVAL(buf,4) = 0xFF;
  CVAL(buf,5) = 'S';
  CVAL(buf,6) = 'M';
  CVAL(buf,7) = 'B';


  if (len >= (1 << 16))
    CVAL(buf,1) |= 1;
}
/****************************************************************************
setup basics in a outgoing packet
****************************************************************************/
void setup_pkt(char *outbuf)
{
  SSVAL(outbuf,smb_pid,pid);
  SSVAL(outbuf,smb_uid,uid);
  SSVAL(outbuf,smb_mid,mid);
  if (Protocol > PROTOCOL_CORE)
    {
      CVAL(outbuf,smb_flg) = 0x8;
      SSVAL(outbuf,smb_flg2,0x3);
    }
}
/****************************************************************************
  read an smb from a fd and return it's length
The timeout is in micro seconds
****************************************************************************/
BOOL receive_smb(char *buffer,int timeout)
{
  int len;
  int fd = Client;
  BOOL ok;

  memset(buffer,0,smb_size + 100);

  len = read_smb_length(fd,buffer,timeout);
  if (len == -1)
    return(False);

  if (len > BUFFER_SIZE)
    {
#if DEBUG
      printf("Invalid packet length! (%d bytes)\n",len);
#endif
      if (len > BUFFER_SIZE + (SAFETY_MARGIN/2))
	return False;
    }

  ok = read_data(fd,buffer+4,len);

  if (!ok)
    {
#if DEBUG
      printf("couldn't read %d bytes from client\n",len);
#endif
      close_sockets();
      return False;
    }

  log_in(buffer,len+4);
  return(True);
}
/****************************************************************************
log a packet to login
****************************************************************************/
void log_in(char *buffer,int len)
{
#if DEBUG    
  printf("logged %d bytes in\n",len);
#endif
}
/****************************************************************************
read 4 bytes of a smb packet and return the smb length of the packet
possibly store the result in the buffer
****************************************************************************/
int read_smb_length(int fd,char *inbuf,int timeout)
{
  char *buffer;
  char buf[4];
  int len=0, msg_type;
  BOOL ok=False;

  if (inbuf)
    buffer = inbuf;
  else
    buffer = buf;

  while (!ok)
    {
      if (timeout > 0)
	ok = (read_with_timeout(fd,buffer,4,4,timeout,False) == 4);
      else
	ok = read_data(fd,buffer,4);

      if (!ok)
	{
	  if (timeout>0)
	    {
#if DEBUG
	      printf("client timeout (timeout was %d)\n", timeout);
#endif
	      return(-1);
	    }
	  else
	    {
#if DEBUG
	      printf("couldn't read from client\n");
#endif
	      return(-1);
	    }
	}

      len = smb_len(buffer);
      msg_type = CVAL(buffer,0);

      if (msg_type == 0x85) 
	{
#if DEBUG
	  printf( "Got keepalive packet\n");
#endif
	  ok = False;
	}
    }

  return(len);
}
/****************************************************************************
read data from a device with a timout in msec.
mincount = if timeout, minimum to read before returning
maxcount = number to be read.
****************************************************************************/
int read_with_timeout(int fd,char *buf,int mincnt,int maxcnt,long time_out,BOOL exact)
{
  fd_set fds;
  int selrtn;
  int readret;
  int nread = 0;
  struct timeval timeout, tval1, tval2, tvaldiff;
  struct timezone tz;

  /* just checking .... */
  if (maxcnt <= 0) return(0);

  if(time_out == -2)
    time_out = DEFAULT_PIPE_TIMEOUT;

  /* Blocking read */
  if(time_out < 0) {
    return read(fd, buf, maxcnt);
  }
  
  /* Non blocking read */
  if(time_out == 0) {
    set_blocking(fd, False);
    nread = read(fd, buf, maxcnt);
    if(nread == -1 && errno == EWOULDBLOCK)
      nread = 0;
    set_blocking(fd,True);
    return nread;
  }

  /* Most difficult - timeout read */
  /* If this is ever called on a disk file and 
	 mincnt is greater then the filesize then
	 system performance will suffer severely as 
	 select always return true on disk files */

  /* Set initial timeout */
  timeout.tv_sec = time_out / 1000;
  timeout.tv_usec = 1000 * (time_out % 1000);

  /* As most UNIXes don't modify the value of timeout
     when they return from select we need to get the timeofday (in usec)
     now, and also after the select returns so we know
     how much time has elapsed */

  if (exact)
    gettimeofday( &tval1, &tz);
  nread = 0; /* Number of bytes we have read */

  for(;;) 
    {
      
      FD_ZERO(&fds);
      FD_SET(fd,&fds);
      
      do {    
	selrtn = select(255,SELECT_CAST &fds,NULL,NULL,&timeout);
      } 
      while( selrtn < 0  &&  errno == EINTR );
      
      /* Check if error */
      if(selrtn == -1)
	return -1;
      
      /* Did we timeout ? */
      if (selrtn == 0 )
	break; /* Yes */
      
      readret = read( fd, buf+nread, maxcnt-nread);
      if(readret == -1)
	return -1;

      if (readret == 0)
	break;
      
      nread += readret;
      
      /* If we have read more than mincnt then return */
      if( nread >= mincnt )
	break;

      /* We need to do another select - but first reduce the
	 time_out by the amount of time already elapsed - if
	 this is less than zero then return */
      if (exact)
	{
	  gettimeofday( &tval2, &tz);
	  (void)tval_sub( &tvaldiff, &tval2, &tval1);
      
	  if( tval_sub( &timeout, &timeout, &tvaldiff) <= 0) 
	    {
	      /* We timed out */
	      break;
	    }
	}
      
      /* Save the time of day as we need to do the select 
	 again (saves a system call)*/
      tval1 = tval2;
    }

  /* Return the number we got */
  return(nread);
}
/****************************************************************************
Set a fd into blocking/nonblocking mode. Uses POSIX O_NONBLOCK if available,
else
if SYSV use O_NDELAY
if BSD use FNDELAY
****************************************************************************/
int set_blocking(int fd, BOOL set)
{
int val;
#ifdef O_NONBLOCK
#define FLAG_TO_SET O_NONBLOCK
#else
#ifdef SYSV
#define FLAG_TO_SET O_NDELAY
#else /* BSD */
#define FLAG_TO_SET FNDELAY
#endif
#endif

  if((val = fcntl(fd, F_GETFL, 0))==-1)
	return -1;
  if(set) /* Turn blocking on - ie. clear nonblock flag */
	val &= ~FLAG_TO_SET;
  else
    val |= FLAG_TO_SET;
  return fcntl( fd, F_SETFL, val);
#undef FLAG_TO_SET
}
/****************************************************************************
Calculate the difference in timeout values. Return 1 if val1 > val2,
0 if val1 == val2, -1 if val1 < val2. Stores result in retval. retval
may be == val1 or val2
****************************************************************************/
int tval_sub( struct timeval *retval, struct timeval *val1, struct timeval *val2)
{
	long usecdiff = val1->tv_usec - val2->tv_usec;
	long secdiff = val1->tv_sec - val2->tv_sec;
	if(usecdiff < 0) {
		usecdiff = 1000000 + usecdiff;
		secdiff--;
	}
	retval->tv_sec = secdiff;
	retval->tv_usec = usecdiff;
	if(secdiff < 0)
		return -1;
	if(secdiff > 0)
		return 1;
	return (usecdiff < 0 ) ? -1 : ((usecdiff > 0 ) ? 1 : 0);
}
/****************************************************************************
  read data from the client, reading exactly N bytes. 
****************************************************************************/
BOOL read_data(int fd,char *buffer,int N)
{
  int maxtime = keepalive;
  int  nready;
  int nread = 0;  
 
  if (maxtime > 0)
    {
      fd_set fds;
      int selrtn;
      struct timeval timeout;
      
      FD_ZERO(&fds);
      FD_SET(fd,&fds);
            
      timeout.tv_sec = maxtime;
      timeout.tv_usec = 0;
      
      while ((selrtn = select(255,SELECT_CAST &fds,NULL,NULL,&timeout)) == 0)
	{
#if DEBUG
	  printf("Sending keepalive\n");
#endif
	  if (!send_keepalive())
	    {
#if DEBUG
	      printf("keepalive failed!\n");
#endif
	      return(False);
	    }
	  timeout.tv_sec = maxtime;
	  timeout.tv_usec = 0;
	  FD_ZERO(&fds);
	  FD_SET(fd,&fds);            
	}
    }

  while (nread < N)
    {
      nready = read(fd,buffer + nread,N - nread);
      if (nready <= 0)
	return False;
      nread += nready;
    }
  return True;
}
/****************************************************************************
send a keepalive packet (rfc1002)
****************************************************************************/
BOOL send_keepalive(void)
{
  unsigned char buf[4];
  int nwritten = 0;

  buf[0] = 0x85;
  buf[1] = buf[2] = buf[3] = 0;

  while (nwritten < 4)
    {
      int ret = write_socket(Client,(char *)&buf[nwritten],4 - nwritten);
      if (ret <= 0)
	return(False);
      nwritten += ret;
    }
  return(True);
}
/****************************************************************************
open the client sockets
****************************************************************************/
BOOL open_sockets(int port )
{
  char *host;
  pstring service2;
  extern int Client;

  strupper(service);

  strcpy(service2,service);
  host = strtok(service2,"\\/");
  strcpy(desthost,host);
#if DEBUG
  printf("Opening sockets\n");
#endif
  if (*myname == 0)
    {
      get_myname(myname,NULL);
      strupper(myname);
    }

  if (!have_ip)
    {
      struct hostent *hp;

      if ((hp = Get_Hostbyname(host)) == 0) 
	{
#if DEBUG
	  printf("Get_Hostbyname: Unknown host %s.\n",host);
#endif
	  return False;
	}

      memcpy((char *)&dest_ip,(char *)hp->h_addr,4);
    }

  Client = open_socket_out(&dest_ip, port);
  if (Client == -1)
    return False;
#if DEBUG
  printf("Connected\n");
#endif
  {
    int one=1;
    setsockopt(Client,SOL_SOCKET,SO_KEEPALIVE,(char *)&one,sizeof(one));
  }
#if DEBUG
  printf("Sockets open\n");
#endif
  return True;
}
/****************************************************************************
create an outgoing socket
****************************************************************************/
int open_socket_out(struct in_addr *addr, int port )
{
  struct sockaddr_in sock_out;
  int res;

  /* create a socket to write to */
  res = socket(PF_INET, SOCK_STREAM, 0);
  if (res == -1) 
	{ 
#if DEBUG
		printf("socket error\n");
#endif 
		return -1; 
	}
  
  memset((char *)&sock_out, 0, sizeof(sock_out));
  memcpy((char *)&sock_out.sin_addr,(char *)addr,4);
  
  sock_out.sin_port = htons( port );
  sock_out.sin_family = PF_INET;
#if DEBUG
  printf("Connecting to %s at port %d\n",inet_ntoa(*addr),port);
  #endif
  /* and connect it to the destination */
  if (connect(res,(struct sockaddr *)&sock_out,sizeof(sock_out))<0)
	{ 
#if DEBUG
		printf("connect error: %s\n",strerror(errno)); 
#endif
		close(res); 
		return -1; 
	}

  return res;
}
/*******************************************************************
  true if the machine is big endian
********************************************************************/
BOOL big_endian(void )
{
  int x = 2;
  char *s;
  s = (char *)&x;
  return(s[0] == 0);
}
/****************************************************************************
mangle a name into netbios format
****************************************************************************/
int name_mangles(char *In,char *Out)
{
  char *in = (char *)In;
  char *out = (char *)Out;
  char *p, *label;
  int len = 2*strlen((char *)in);
  int pad = 0;

  if (len/2 < 16)
    pad = 16 - (len/2);

  *out++ = 2*(strlen((char *)in) + pad);
  while (*in)
    {
      out[0] = (in[0]>>4) + 'A';
      out[1] = (in[0] & 0xF) + 'A';
      in++;
      out+=2;
    }
  
  while (pad--)
    {
      out[0] = 'C';
      out[1] = 'A';
      out+=2;
    }
  
  label = scope;
  while (*label)
    {
      p = strchr(label, '.');
      if (p == 0)
	p = label + strlen(label);
      *out++ = p - label;
      memcpy(out, label, p - label);
      out += p - label;
      label += p - label + (*p == '.');
    }
  *out = 0;
  return(name_len(Out));
}

