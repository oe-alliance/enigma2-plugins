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

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <sys/time.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#if HAVE_STDINT_H
#include <stdint.h>
#endif

#include "nbtscan.h"

int quiet=0;
netinfo	*nInfo = 0;

int set_range(char* range_str, struct ip_range* range_struct) {
  if(is_ip(range_str, range_struct)) return 1;
  if(is_range1(range_str, range_struct)) return 1;
  if(is_range2(range_str, range_struct)) return 1;
  return 0;
};

int print_header() {
  printf("%-17s%-17s%-10s%-17s%-17s\n", "IP address", "NetBIOS Name", 
	 "Server", "User", "MAC address");
  printf("------------------------------------------------------------------------------\n");
  return 0;
};

int python_hostinfo(struct in_addr addr, const struct nb_host_info* hostinfo, netinfo *nInfo, int pos)
{
	int unique;
  my_uint8_t service;

	sleep(1);
	service = hostinfo->names[0].ascii_name[15];
	unique = !(hostinfo->names[0].rr_flags & 0x0080);
	strncpy(nInfo[pos].name, hostinfo->names[0].ascii_name, 15);
	strncpy(nInfo[pos].domain, hostinfo->names[1].ascii_name, 15);
	sprintf(nInfo[pos].service,"%s", (char*)getnbservicename(service, unique, hostinfo->names[0].ascii_name));
	if(hostinfo->footer) {
		sprintf(nInfo[pos].mac,"%02x:%02x:%02x:%02x:%02x:%02x",
		hostinfo->footer->adapter_address[0], hostinfo->footer->adapter_address[1],
		hostinfo->footer->adapter_address[2], hostinfo->footer->adapter_address[3],
		hostinfo->footer->adapter_address[4], hostinfo->footer->adapter_address[5]);
	}
	strcpy(nInfo[pos].ip, inet_ntoa(addr));
	return 0;
}

netinfo * newNetInfo()
{
	netinfo *nInfo = malloc(sizeof(netinfo)*255);
	if(!nInfo)
		exit(0); // TODO: besser machen 
	memset(nInfo,0,sizeof(netinfo)*255);
	return nInfo;
}

void freeNetInfo(netinfo *nInfo)
{
	free(nInfo); 
}


#define BUFFSIZE 1024
#define MAX 255

int netzInfo(char *pythonIp, netinfo *nInfo) {
  int timeout=10000, verbose=0, use137=0, bandwidth=0, send_ok=0, hr=0;
  extern char *optarg;
  extern int optind;
  char* target_string;
  char* sf=NULL;
  char* filename =NULL;
  struct ip_range range;
  void *buff;
  int sock;
	unsigned int addr_size;
  struct sockaddr_in src_sockaddr, dest_sockaddr;
  struct  in_addr *prev_in_addr=NULL;
  struct  in_addr *next_in_addr;
  struct timeval select_timeout, last_send_time, current_time, diff_time, send_interval;
  struct timeval transmit_started, now, recv_time;
  struct nb_host_info* hostinfo;
  fd_set* fdsr;
  fd_set* fdsw;
  int size;
	int pos =0;
  struct list* scanned;
  my_uint32_t rtt_base; /* Base time (seconds) for round trip time calculations */
  float rtt; /* most recent measured RTT, seconds */
  float srtt=0; /* smoothed rtt estimator, seconds */
  float rttvar=0.75; /* smoothed mean deviation, seconds */ 
  double delta; /* used in retransmit timeout calculations */
  int rto, retransmits=0, more_to_send=1, i;
  char errmsg[80];
  char str[80];
  FILE* targetlist=NULL;
	hr =0;
	sf=optarg;
	verbose = 1;

	if((target_string=strdup(pythonIp))==NULL)
	{ 
		err_die("Malloc failed.\n", quiet);
	}
	if(!set_range(target_string, &range)) {
		printf("Error: %s is not an IP address or address range.\n", target_string);
		free(target_string);
	};
  /* Finished with options */
  /*************************/

  /* Prepare socket and address structures */
  /*****************************************/
  sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
  if (sock < 0) 
    err_die("Failed to create socket", quiet);

  bzero((void*)&src_sockaddr, sizeof(src_sockaddr));
  src_sockaddr.sin_family = AF_INET;
  if(use137) src_sockaddr.sin_port = htons(NB_DGRAM);
  if (bind(sock, (struct sockaddr *)&src_sockaddr, sizeof(src_sockaddr)) == -1) 
    err_die("Failed to bind", quiet);
        
  fdsr=malloc(sizeof(fd_set));
  if(!fdsr)  err_die("Malloc failed", quiet);
  FD_ZERO(fdsr);
  FD_SET(sock, fdsr);
        
  fdsw=malloc(sizeof(fd_set));
  if(!fdsw) err_die("Malloc failed", quiet);
  FD_ZERO(fdsw);
  FD_SET(sock, fdsw);

  /* timeout is in milliseconds */
  //select_timeout.tv_sec = timeout / 1000;
  //select_timeout.tv_usec = (timeout % 1000) * 1000; /* Microseconds */
	select_timeout.tv_sec = 60; /* Default 1 min to survive ARP timeouts */
	select_timeout.tv_usec = 0;

  addr_size = sizeof(struct sockaddr_in);

  next_in_addr = malloc(sizeof(struct  in_addr));
  if(!next_in_addr) err_die("Malloc failed", quiet);

  buff=malloc(BUFFSIZE);
  if(!buff) err_die("Malloc failed", quiet);
	
  /* Calculate interval between subsequent sends */

  timerclear(&send_interval);
  if(bandwidth) send_interval.tv_usec = 
		  (NBNAME_REQUEST_SIZE + UDP_HEADER_SIZE + IP_HEADER_SIZE)*8*1000000 /
		  bandwidth;  /* Send interval in microseconds */
  else /* Assuming 10baseT bandwidth */
    send_interval.tv_usec = 1; /* for 10baseT interval should be about 1 ms */
  if (send_interval.tv_usec >= 1000000) {
    send_interval.tv_sec = send_interval.tv_usec / 1000000;
    send_interval.tv_usec = send_interval.tv_usec % 1000000;
  }
	
  gettimeofday(&last_send_time, NULL); /* Get current time */

  rtt_base = last_send_time.tv_sec; 

  /* Send queries, receive answers and print results */
  /***************************************************/
	
  scanned = new_list();

  for(i=0; i <= retransmits; i++) {
    gettimeofday(&transmit_started, NULL);
    while ( (select(sock+1, fdsr, fdsw, NULL, &select_timeout)) > 0) {
      if(FD_ISSET(sock, fdsr)) {
	if ( (size = recvfrom(sock, buff, BUFFSIZE, 0,
			      (struct sockaddr*)&dest_sockaddr, &addr_size)) <= 0 ) {
	  snprintf(errmsg, 80, "%s\tRecvfrom failed", inet_ntoa(dest_sockaddr.sin_addr));
	  err_print(errmsg, quiet);
	  continue;
	};
	gettimeofday(&recv_time, NULL);
	memset(&hostinfo, 0, sizeof(hostinfo));
	hostinfo = (struct nb_host_info*)parse_response(buff, size);
	if(!hostinfo) {
	  err_print("parse_response returned NULL", quiet);
	  continue;
	};
				/* If this packet isn't a duplicate */
	if(insert(scanned, ntohl(dest_sockaddr.sin_addr.s_addr))) {
	  rtt = recv_time.tv_sec + 
	    recv_time.tv_usec/1000000 - rtt_base - 
	    hostinfo->header->transaction_id/1000;
	  /* Using algorithm described in Stevens' 
	     Unix Network Programming */
	  delta = rtt - srtt;
	  srtt += delta / 8;
	  if(delta < 0.0) delta = - delta;
	  rttvar += (delta - rttvar) / 4 ;
		if (hostinfo->names == 0x0) {
			printf("hostinfo->names == NULL\n");
		} else {
			python_hostinfo(dest_sockaddr.sin_addr, hostinfo, nInfo, pos);
			pos ++;
		}
	};
	free(hostinfo);
  };

  FD_ZERO(fdsr);
  FD_SET(sock, fdsr);		

      /* check if send_interval time passed since last send */
      gettimeofday(&current_time, NULL);
      timersub(&current_time, &last_send_time, &diff_time);
      send_ok = timercmp(&diff_time, &send_interval, >=);
			
		
      if(more_to_send && FD_ISSET(sock, fdsw) && send_ok) {
	if(targetlist) {
	  if(fgets(str, 80, targetlist)) {
	    if(!inet_aton(str, next_in_addr)) {
            /* if(!inet_pton(AF_INET, str, next_in_addr)) { */
	      fprintf(stderr,"%s - bad IP address\n", str);
	    } else {
	      if(!in_list(scanned, ntohl(next_in_addr->s_addr))) 
	        send_query(sock, *next_in_addr, rtt_base);
	    }
	  } else {
	    if(feof(targetlist)) {
	      more_to_send=0; 
	      FD_ZERO(fdsw);
              /* timeout is in milliseconds */
	      select_timeout.tv_sec = timeout / 1000;
              select_timeout.tv_usec = (timeout % 1000) * 1000; /* Microseconds */
	      continue;
	    } else {
	      snprintf(errmsg, 80, "Read failed from file %s", filename);
	      err_die(errmsg, quiet);
	    }
	  }
	} else if(next_address(&range, prev_in_addr, next_in_addr) ) {
	  if(!in_list(scanned, ntohl(next_in_addr->s_addr))) 
	    send_query(sock, *next_in_addr, rtt_base);
	  prev_in_addr=next_in_addr;
	  /* Update last send time */
	  gettimeofday(&last_send_time, NULL); 
	} else { /* No more queries to send */
	  more_to_send=0; 
	  FD_ZERO(fdsw);
          /* timeout is in milliseconds */
          select_timeout.tv_sec = timeout / 1000;
          select_timeout.tv_usec = (timeout % 1000) * 1000; /* Microseconds */
	  continue;
	};
      };	
      if(more_to_send) {
	FD_ZERO(fdsw);
	FD_SET(sock, fdsw);
      };
    };

    if (i>=retransmits) break; /* If we are not going to retransmit
				 we can finish right now without waiting */

    rto = (srtt + 4 * rttvar) * (i+1);

    if ( rto < 2.0 ) rto = 2.0;
    if ( rto > 60.0 ) rto = 60.0;
    gettimeofday(&now, NULL);
		
    if(now.tv_sec < (transmit_started.tv_sec+rto)) 
      sleep((transmit_started.tv_sec+rto)-now.tv_sec);
    prev_in_addr = NULL ;
    more_to_send=1;
    FD_ZERO(fdsw);
    FD_SET(sock, fdsw);
    FD_ZERO(fdsr);
    FD_SET(sock, fdsr);
  };

  delete_list(scanned);
	if(buff) {
		free(buff);
	}
	return 0;
  exit(0);
};

