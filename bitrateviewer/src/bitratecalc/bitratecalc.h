#ifndef __bitratecalc_h
#define __bitratecalc_h

/*
#  BitrateCalculator E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
*/

#include <lib/dvb/idvb.h>
#include <lib/dvb/dvb.h>

class eBitrateCalc: public Object
{
private:
	unsigned long long m_size;
	int m_refresh_intervall;
	struct timespec m_start;
	ePtr<iDVBPESReader> m_reader;
	ePtr<eConnection> m_pes_connection;
	ePtr<eConnection> m_channel_connection;
	void dataReady(const __u8*,  int size);
	void sendData(int bitrate, int status) {dataSent(bitrate, status);}
	void stateChange(iDVBChannel *ch);
	ePtr<eTimer> m_send_data_timer;
	void sendDataTimerTimeoutCB();
public:
	eBitrateCalc(int pid, int dvbnamespace, int tsid, int onid, int refreshintervall, int buffer_size);
	PSignal2<void, int, int> dataSent;
};

#endif
