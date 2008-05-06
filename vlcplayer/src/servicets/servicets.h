#ifndef __servicets_h
#define __servicets_h

#include <lib/base/ioprio.h>
#include <lib/base/message.h>
#include <lib/service/iservice.h>
#include <lib/dvb/dvb.h>

class eStaticServiceTSInfo;

class eServiceFactoryTS: public iServiceHandler
{
DECLARE_REF(eServiceFactoryTS);
public:
	eServiceFactoryTS();
	virtual ~eServiceFactoryTS();
	enum { id = 0x1002 };

	// iServiceHandler
	RESULT play(const eServiceReference &, ePtr<iPlayableService> &ptr);
	RESULT record(const eServiceReference &, ePtr<iRecordableService> &ptr);
	RESULT list(const eServiceReference &, ePtr<iListableService> &ptr);
	RESULT info(const eServiceReference &, ePtr<iStaticServiceInformation> &ptr);
	RESULT offlineOperations(const eServiceReference &, ePtr<iServiceOfflineOperations> &ptr);
private:
	ePtr<eStaticServiceTSInfo> m_service_info;
};

class eStaticServiceTSInfo: public iStaticServiceInformation
{
	DECLARE_REF(eStaticServiceTSInfo);
	friend class eServiceFactoryTS;
	eStaticServiceTSInfo();
public:
	RESULT getName(const eServiceReference &ref, std::string &name);
	int getLength(const eServiceReference &ref);
};

class eStreamThread;

class eServiceTS: public iPlayableService, public iPauseableService, 
	public iServiceInformation, public iSeekableService, public Object
{
DECLARE_REF(eServiceTS);
public:
	virtual ~eServiceTS();

		// iPlayableService
	RESULT connectEvent(const Slot2<void,iPlayableService*,int> &event, ePtr<eConnection> &connection);
	RESULT start();
	RESULT stop();
	RESULT setTarget(int target);
	
	RESULT pause(ePtr<iPauseableService> &ptr);
	RESULT setSlowMotion(int ratio);
	RESULT setFastForward(int ratio);

	RESULT seek(ePtr<iSeekableService> &ptr);

		// not implemented (yet)
	RESULT audioChannel(ePtr<iAudioChannelSelection> &ptr) { ptr = 0; return -1; }
	RESULT audioTracks(ePtr<iAudioTrackSelection> &ptr) { ptr = 0; return -1; }
	RESULT frontendInfo(ePtr<iFrontendInformation> &ptr) { ptr = 0; return -1; }
	RESULT subServices(ePtr<iSubserviceList> &ptr) { ptr = 0; return -1; }
	RESULT timeshift(ePtr<iTimeshiftService> &ptr) { ptr = 0; return -1; }
	RESULT cueSheet(ePtr<iCueSheet> &ptr) { ptr = 0; return -1; }
	RESULT subtitle(ePtr<iSubtitleOutput> &ptr) { ptr = 0; return -1; }
	RESULT audioDelay(ePtr<iAudioDelay> &ptr) { ptr = 0; return -1; }
	RESULT rdsDecoder(ePtr<iRdsDecoder> &ptr) { ptr = 0; return -1; }
	RESULT stream(ePtr<iStreamableService> &ptr) { ptr = 0; return -1; }
	RESULT keys(ePtr<iServiceKeys> &ptr) { ptr = 0; return -1; }
		// iPausableService
	RESULT pause();
	RESULT unpause();
	
	RESULT info(ePtr<iServiceInformation>&);
	
		// iSeekableService
	RESULT getLength(pts_t &SWIG_OUTPUT);
	RESULT seekTo(pts_t to);
	RESULT seekRelative(int direction, pts_t to);
	RESULT getPlayPosition(pts_t &SWIG_OUTPUT);
	RESULT setTrickmode(int trick);
	RESULT isCurrentlySeekable();

		// iServiceInformation
	RESULT getName(std::string &name);
	int getInfo(int w);
	std::string getInfoString(int w);
private:
	friend class eServiceFactoryTS;
	std::string m_filename;
	int m_vpid, m_apid;
	int m_srcfd, m_destfd;
	ePtr<eDVBAllocatedDemux> m_decodedemux;
	ePtr<iTSMPEGDecoder> m_decoder;
	ePtr<eStreamThread> m_streamthread;
	
	eServiceTS(const eServiceReference &url);
	int openHttpConnection(std::string url);
	
	Signal2<void,iPlayableService*,int> m_event;
	enum
	{
		stIdle, stRunning, stStopped
	};
	int m_state;
	eFixedMessagePump<int> m_pump;
	void recv_event(int evt);
};

class eStreamThread: public eThread, public Object {
DECLARE_REF(eStreamThread);
public:
	eStreamThread();
	virtual ~eStreamThread();
	void start(int srcfd, int destfd);
	void stop();

	virtual void thread();
	virtual void thread_finished();

	enum { evtEOS, evtReadError, evtWriteError, evtUser };
	Signal1<void,int> m_event;
private:
	bool m_stop;
	int m_srcfd, m_destfd;
	eFixedMessagePump<int> m_messagepump;
	void recvEvent(const int &evt);
};

#endif


