// Aufruf mit vps [demux] [mode] [onid] [tsid] [sid] [Event-ID] [Timer-ID] [PDC-Time day] [PDC-Time month] [PDC-Time hour] [PDC-Time min]
//
// mode
// 0 Event überwachen
// 1 in "other transport stream, present/following" nach Event suchen und bei running_status 2 <= x <= 4 beenden
// 2 nach PDC-Zeit suchen und Event-ID zurückgeben
// 3 in "other transport stream, present/following" nach PDC suchen und Event-ID zurückgeben
// 4 in allen EIT-Tabellen nach PDC suchen und alle gefundenen Event-IDs zurückgeben, ausschließlich der Event-ID im Aufruf
// 5 in allen EIT-Tabellen nach der Event-ID schauen und nach weiteren Events mit gleicher PDC suchen
// 10 prüfen, ob überhaupt PDC vorhanden
//


#include <sys/ioctl.h>
#include <fcntl.h>
#include <linux/dvb/dmx.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <iostream>
#include <cstdlib>
#include <time.h>
#include <set>

using std::cout;
using std::endl;
using std::atoi;
using std::flush;
using std::set;



#define READ_BUF_SIZE (8*1024)

int main(int argc, char *argv[]);

// 0x12 EIT-PID
// 0x4e EIT - actual transport stream, present/following
int open_read_demux(unsigned short pid = 0x12, u_char table_id = 0x4e, u_char table_mask = 0xff, int timeout = 15000);

void process_eit(u_char *b, u_char table_id, u_char table_mask);
void process_monitoring(u_char *b, int section_length, int section_number);
void process_monitoring2(u_char *b, int section_length, int section_number);
void process_search_pdc(u_char *b, int section_length, int section_number);
void process_search_multiple_pdc(u_char *b, int section_length, int section_number);
void process_search_pdc_available(u_char *b, int section_length, int section_number);

inline void setNowNext(int section_number, int nevent);

static long sect_read(int fd, u_char *buf, long buflen);
unsigned long getBits(u_char *buf, int byte_offset, int startbit, int bitlen);
//time_t time_mjd_utc(u_long mjd, u_long utc);
//time_t time_utc(u_long utc);

void abort_program(int signal);

const time_t max_wait_time = 20 * 60;

// vars
bool isAbort = false;
char *f_demux;
char mode = 0;
int pdc_time = 0;
unsigned short onid = 0;
unsigned short tsid = 0;
unsigned short sid = 0;
unsigned short event_id = 0;
unsigned short timer_id = 0;

unsigned short service_event_now = 0;
unsigned short service_event_next = 0;
bool service_event_checked_now = false;
bool service_event_checked_next = false;

//int event_last_start_time_MJD = -1;
//int event_last_start_time_UTC = -1;
//int event_last_duration = -1;
char event_last_running_status = -1;

time_t received_event_last_time;
set<unsigned short> pdc_exclude_event_ids;


int main(int argc, char *argv[])
{
	signal(SIGINT, abort_program);
	signal(SIGTERM, abort_program);

	if (argc < 8)
	{
		cout << "too few arguments" << endl;
		return 0;
	}
	
	f_demux = argv[1];
	mode = atoi(argv[2]);
	onid = atoi(argv[3]);
	tsid = atoi(argv[4]);
	sid = atoi(argv[5]);
	event_id = atoi(argv[6]);
	timer_id = atoi(argv[7]);
	
	if (mode > 1 && mode < 10 && argc >= 12)
	{
		pdc_time = atoi(argv[8]) << 15; // day
		pdc_time += (atoi(argv[9]) << 11); // month
		pdc_time += (atoi(argv[10]) << 6); // hour
		pdc_time += atoi(argv[11]); // minute
	}
	
	int n = 0;
	
	// Startzeit
	time(&received_event_last_time);
	
	if (mode == 0 || mode == 2)
	{
		n = open_read_demux();
	}
	else if (mode == 1 || mode == 3)
	{
		n = open_read_demux(18, 0x4f, 0xff, 30000);
		if (n == -2)
			n = open_read_demux(3218, 0x4f, 0xff, 30000); // Kabel Deutschland
	}
	else if (mode == 4 || mode == 5)
	{
		if (event_id > 0)
			pdc_exclude_event_ids.insert(event_id);
		
		n = open_read_demux(18, 0x4f, 0x00);
	}
	else if (mode == 10)
	{
		n = open_read_demux(18, 0x4e, 0xff, 6000);
	}
	
	if (n == -2)
		cout << timer_id << " DMX_ERROR_TIMEOUT\n" << flush;
	
	return 0;
}

int open_read_demux(unsigned short pid, u_char table_id, u_char table_mask, int timeout)
{
	// vorbereiten
	int fd;
	u_char buf[READ_BUF_SIZE];
	bool timeout_error = false;
	
	if ((fd = open(f_demux, O_RDWR)) < 0)
	{
      return -1;
  }
  
  struct dmx_sct_filter_params flt;
  memset(&flt, 0, sizeof (struct dmx_sct_filter_params));
  
  flt.pid = pid;
  
  flt.filter.filter[0] = table_id;
  flt.filter.mask[0] = table_mask;
  
  // Service-ID als Filter setzen
  flt.filter.filter[1] = sid >> 8;
  flt.filter.mask[1] = 0xff;
  flt.filter.filter[2] = sid & 0xff;
  flt.filter.mask[2] = 0xff;
  
  
  flt.flags = DMX_IMMEDIATE_START | DMX_CHECK_CRC;
  flt.timeout = timeout;
  
  if (ioctl(fd, DMX_SET_FILTER, &flt) < 0)
	{
		cout << "DMX_SET_FILTER_ERROR" << endl;
	 	close(fd);
		return -1;
  }
  
  
  // lesen
  while (!isAbort)
  {
		long n;
		
		n = sect_read(fd, buf, sizeof(buf));
		
		if (n == 0) continue;
		
		if (n < 0)
		{
			if (errno == ETIMEDOUT)
			{
				timeout_error = true;
				break;
			}
			
			continue;
		}
		
		// Daten auswerten
		process_eit(buf, table_id, table_mask);
	}
  
  // schließen
  ioctl(fd, DMX_STOP, 0);
  close(fd);
  
  if (timeout_error)
  	return -2;
  
  return 0;
  
}


void process_eit(u_char *b, u_char table_id, u_char table_mask)
{
	// überprüfe Table-ID
	if ((b[0] & table_mask) != (table_id & table_mask))
		return;
	
	// überprüfe SID, TSID, ONID
	if (getBits(b, 0, 24, 16) != sid)
		return;
	if (getBits(b, 0, 80, 16) != onid)
		return;
	if (getBits(b, 0, 64, 16) != tsid)
		return;
	
	// current_next_indicator
	if (getBits(b, 0, 47, 1) == 0)
		return;
		
	int section_length = getBits(b, 0, 12, 12);
	int section_number = getBits(b, 0, 48, 8);
	
	
	b += 14;
	if (mode == 0)
		process_monitoring(b, section_length, section_number);
	else if (mode == 1)
		process_monitoring2(b, section_length, section_number);
	else if (mode == 2 || mode == 3)
		process_search_pdc(b, section_length, section_number);
	else if (mode == 4 || mode == 5)
		process_search_multiple_pdc(b, section_length, section_number);
	else if (mode == 10)
		process_search_pdc_available(b, section_length, section_number);
	
	cout << flush;
}

inline void setNowNext(int section_number, int nevent)
{
	if (section_number == 0)
	{	
		if (service_event_now != nevent)
		{
			service_event_now = nevent;
		}
	}
	else if (section_number == 1)
	{
		if (service_event_next != nevent)
		{
			service_event_next = nevent;
		}
	}
	
	if (service_event_now != event_id && service_event_next != event_id && event_last_running_status >= 0)
	{
		if (section_number == 0)
			service_event_checked_now = true;
		else if (section_number == 1)
			service_event_checked_next = true;
		
		if (service_event_checked_now && service_event_checked_next)
		{
			cout << timer_id << " EVENT_ENDED \n" << flush;
			//event_last_running_status = -1;
			abort_program(1);
		}
	}
	else if ((service_event_checked_now || service_event_checked_next) && (service_event_now == event_id || service_event_next == event_id))
	{
		service_event_checked_now = false;
		service_event_checked_next = false;
	}
	else if (event_last_running_status == -1 && service_event_now != event_id && service_event_next != event_id && service_event_now != 0 && service_event_next != 0)
	{
		cout << timer_id << " EVENT_CURRENTLY_NOT_FOUND \n" << flush;
		event_last_running_status = -2;
	}
}

void process_monitoring(u_char *b, int section_length, int section_number)
{
	// header data after length value
	if ((section_length - 11) <= 16) // 12 Bytes Event-Header + 4 Bytes CRC
	{
		setNowNext(section_number, 0);
		return;
	}
	
	int n_event_id = getBits(b, 0, 0, 16);
	setNowNext(section_number, n_event_id);
	
	if (n_event_id != event_id)
	{	
		time_t newtime;
		time(&newtime);
		if ((newtime - received_event_last_time) > max_wait_time)
		{
			cout << timer_id << " EVENT_ENDED TIMEOUT " << (newtime - received_event_last_time) << "\n" << flush;
			abort_program(1);
		}
		return;
	}
	
	// aktualisiere Zeit
	time(&received_event_last_time);
	
	//int start_time_MJD = getBits(b, 0, 16, 16);
	//int start_time_UTC = getBits(b, 0, 32, 24);
  //int duration = getBits(b, 0, 56, 24);
  char running_status = getBits(b, 0, 80, 3);
  
  if (running_status != event_last_running_status)
  {
  	cout << timer_id << " RUNNING_STATUS " << int(running_status) << " " << ((section_number) ? "FOLLOWING" : "PRESENT")<< "\n" << flush;
		event_last_running_status = running_status;
  }
}

void process_monitoring2(u_char *b, int section_length, int section_number)
{
	// header data after length value
	if ((section_length - 11) <= 16) // 12 Bytes Event-Header + 4 Bytes CRC
		return;
	
	int n_event_id = getBits(b, 0, 0, 16);
	
	if (n_event_id != event_id)
	{	
		time_t newtime;
		time(&newtime);
		if ((newtime - received_event_last_time) > max_wait_time)
		{
			cout << timer_id << " TIMEOUT\n" << flush;
			abort_program(1);
		}
		return;
	}
		
	// aktualisiere Zeit
	time(&received_event_last_time);
	
	//int start_time_MJD = getBits(b, 0, 16, 16);
	//int start_time_UTC = getBits(b, 0, 32, 24);
  //int duration = getBits(b, 0, 56, 24);
  char running_status = getBits(b, 0, 80, 3);
  
  if (running_status >= 2 && running_status <= 4)
  {
  	cout << timer_id << " OTHER_TS_RUNNING_STATUS " << int(running_status) << "\n" << flush;
		abort_program(1);
  }
}

void process_search_pdc(u_char *b, int section_length, int section_number)
{
	time_t newtime;
	time(&newtime);
	if ((newtime - received_event_last_time) > max_wait_time)
	{
		cout << timer_id << " TIMEOUT\n" << flush;
		abort_program(1);
	}
	
	// header data after length value
	if ((section_length - 11) <= 16) // 12 Bytes Event-Header + 4 Bytes CRC
		return;
	
	int n_event_id = getBits(b, 0, 0, 16);
	
	int descriptors_loop_length = getBits(b, 0, 84, 12);
	b += 12;
	while (descriptors_loop_length > 0)
	{
		if (getBits(b, 0, 0, 8) == 105) // PDC-Descriptor
		{
			if (getBits(b, 0, 20, 20) == pdc_time)
			{
				cout << timer_id << " PDC_FOUND_EVENT_ID " << n_event_id << "\n" << flush;
				abort_program(1);
				return;
			}
		}
		
		int desc_length = getBits(b, 0, 8, 8) + 2;
		b += desc_length;
		descriptors_loop_length -= desc_length;
	}
}

void process_search_multiple_pdc(u_char *b, int section_length, int section_number)
{
	time_t newtime;
	time(&newtime);
	if ((newtime - received_event_last_time) >= 45)
	{
		//cout << timer_id << " SEARCH_DONE\n" << flush;
		abort_program(1);
		return;
	}
	
	// header data after length value
	if ((section_length - 11) <= 16) // 12 Bytes Event-Header + 4 Bytes CRC
		return;
	
	
	int len1 = section_length - 11;
	while (len1 > 4)
	{
		int n_event_id = getBits(b, 0, 0, 16);
		//u_long start_time_MJD = getBits(b, 0, 16, 16);
		//u_long start_time_UTC = getBits(b, 0, 32, 24);
	  //u_long duration = getBits(b, 0, 56, 24);
		int descriptors_loop_length = getBits(b, 0, 84, 12);
		
		len1 -= 12 + descriptors_loop_length;
		b += 12;
		while (descriptors_loop_length > 0)
		{
			if (getBits(b, 0, 0, 8) == 105) // PDC-Descriptor
			{
				if (getBits(b, 0, 20, 20) == pdc_time && pdc_exclude_event_ids.count(n_event_id) == 0)
				{
					pdc_exclude_event_ids.insert(n_event_id);
					cout << timer_id << " PDC_MULTIPLE_FOUND_EVENT " << n_event_id << "\n" << flush;
				}
				else if (mode == 5 && n_event_id == event_id)
				{
					pdc_time = getBits(b, 0, 20, 20);
				}
			}
			
			int desc_length = getBits(b, 0, 8, 8) + 2;
			b += desc_length;
			descriptors_loop_length -= desc_length;
		}
	}
}

void process_search_pdc_available(u_char *b, int section_length, int section_number)
{
	time_t newtime;
	time(&newtime);
	if ((newtime - received_event_last_time) > 6)
	{
		cout << "NO_PDC_AVAILABLE\n" << flush;
		abort_program(1);
		return;
	}
	
	// header data after length value
	if ((section_length - 11) <= 16) // 12 Bytes Event-Header + 4 Bytes CRC
		return;
	
	bool found_pdc = false;
	
	int descriptors_loop_length = getBits(b, 0, 84, 12);
	b += 12;
	while (descriptors_loop_length > 0)
	{
		if (getBits(b, 0, 0, 8) == 105) // PDC-Descriptor
		{
			found_pdc = true;
		}
		
		int desc_length = getBits(b, 0, 8, 8) + 2;
		b += desc_length;
		descriptors_loop_length -= desc_length;
	}
	
	if (found_pdc)
		cout << "PDC_AVAILABLE\n" << flush;
	else
		cout << "NO_PDC_AVAILABLE\n" << flush;
	
	abort_program(1);

}


/**
 * sect_read und getBits übernommen von dvbsnoop
 * http://dvbsnoop.sourceforge.net/
 **/  

static long sect_read (int fd, u_char *buf, long buflen)
{
	int n;
	int sect_len;

	n = read(fd, buf, 3);				// read section header
	if (n <= 0) return n;			// error or strange, abort

	// section size
	// -- table_id 	8  uimsbf
	// -- some stuff   	4  bits
	// -- sectionlength 12 uimsbf

	sect_len = ((buf[1] & 0x0F) << 8) + buf[2];	// get section size
	if (sect_len > (buflen-3)) return -1;	// something odd?

	n = read(fd, buf+3, sect_len);		// read 1 section
	if (n >=0) n += 3;				// we already read header bytes

	return n;
}

unsigned long getBits(u_char *buf, int byte_offset, int startbit, int bitlen)
{
	u_char *b;
	unsigned long  v;
	unsigned long mask;
	unsigned long tmp_long;
	int bitHigh;


	b = &buf[byte_offset + (startbit >> 3)];
	startbit %= 8;

	switch ((bitlen-1) >> 3)
	{
		case -1:	// -- <=0 bits: always 0
		return 0L;
		break;

	case 0:		// -- 1..8 bit
		tmp_long = (unsigned long)(
			(*(b  )<< 8) +  *(b+1) );
		bitHigh = 16;
		break;

	case 1:		// -- 9..16 bit
		tmp_long = (unsigned long)(
		 	(*(b  )<<16) + (*(b+1)<< 8) +  *(b+2) );
		bitHigh = 24;
		break;

	case 2:		// -- 17..24 bit
		tmp_long = (unsigned long)(
		 	(*(b  )<<24) + (*(b+1)<<16) +
			(*(b+2)<< 8) +  *(b+3) );
		bitHigh = 32;
		break;

	default:	// -- 33.. bits: fail, deliver constant fail value
		//out_nl (1," Error: getBits() request out of bound!!!! (report!!) \n");
		return (unsigned long) 0xFEFEFEFE;
		break;
	}

	startbit = bitHigh - startbit - bitlen;
	tmp_long = tmp_long >> startbit;
	mask     = (1ULL << bitlen) - 1;  // 1ULL !!!
	v        = tmp_long & mask;

 return v;
}


void abort_program(int signal)
{
	isAbort = true;
}