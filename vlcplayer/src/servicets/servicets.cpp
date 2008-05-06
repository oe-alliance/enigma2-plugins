

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string>
#include <sys/socket.h>
#include <netdb.h>
#include <signal.h>
#include "servicets.h"
#include <lib/base/eerror.h>
#include <lib/base/object.h>
#include <lib/base/ebase.h>
#include <servicets.h>
#include <lib/service/service.h>
#include <lib/base/init_num.h>
#include <lib/base/init.h>
#include <lib/dvb/decoder.h>

#define MAX(a,b) ((a) > (b) ? (a) : (b))

// eServiceFactoryTS

eServiceFactoryTS::eServiceFactoryTS()
{
	ePtr<eServiceCenter> sc;
	
	eServiceCenter::getPrivInstance(sc);
	if (sc)
	{
		std::list<std::string> extensions;
		sc->addServiceFactory(eServiceFactoryTS::id, this, extensions);
	}

	m_service_info = new eStaticServiceTSInfo();
}

eServiceFactoryTS::~eServiceFactoryTS()
{
	ePtr<eServiceCenter> sc;
	
	eServiceCenter::getPrivInstance(sc);
	if (sc)
		sc->removeServiceFactory(eServiceFactoryTS::id);
}

DEFINE_REF(eServiceFactoryTS)

	// iServiceHandler
RESULT eServiceFactoryTS::play(const eServiceReference &ref, ePtr<iPlayableService> &ptr)
{
		// check resources...
	ptr = new eServiceTS(ref);
	return 0;
}

RESULT eServiceFactoryTS::record(const eServiceReference &ref, ePtr<iRecordableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryTS::list(const eServiceReference &, ePtr<iListableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryTS::info(const eServiceReference &ref, ePtr<iStaticServiceInformation> &ptr)
{
	ptr = m_service_info;
	return 0;
}

RESULT eServiceFactoryTS::offlineOperations(const eServiceReference &, ePtr<iServiceOfflineOperations> &ptr)
{
	ptr = 0;
	return -1;
}


// eStaticServiceTSInfo
DEFINE_REF(eStaticServiceTSInfo)

eStaticServiceTSInfo::eStaticServiceTSInfo()
{
}

RESULT eStaticServiceTSInfo::getName(const eServiceReference &ref, std::string &name)
{
	size_t last = ref.path.rfind('/');
	if (last != std::string::npos)
		name = ref.path.substr(last+1);
	else
		name = ref.path;
	return 0;
}

int eStaticServiceTSInfo::getLength(const eServiceReference &ref)
{
	return -1;
}

// eServiceTS

eServiceTS::eServiceTS(const eServiceReference &url): m_pump(eApp, 1)
{
	eDebug("ServiceTS construct!");
	m_filename = url.path.c_str();
	m_vpid = url.getData(0) == 0 ? 0x44 : url.getData(0);
	m_apid = url.getData(1) == 0 ? 0x45 : url.getData(1);
	m_state = stIdle;
}

eServiceTS::~eServiceTS()
{
	eDebug("ServiceTS destruct!");
	if (m_state == stRunning)
		stop();
}

DEFINE_REF(eServiceTS);	

size_t crop(char *buf)
{
	size_t len = strlen(buf) - 1;
	while (len > 0 && (buf[len] == '\r' || buf[len] == '\n')) {
		buf[len--] = '\0';
	}
	return len;
}

static int getline(char** pbuffer, size_t* pbufsize, int fd) 
{
	size_t i = 0;
	int rc;
	while (true) {
		if (i >= *pbufsize) {
			char *newbuf = (char*)realloc(*pbuffer, (*pbufsize)+1024);
			if (newbuf == NULL)
				return -ENOMEM;
			*pbuffer = newbuf;
			*pbufsize = (*pbufsize)+1024;
		}
		rc = ::read(fd, (*pbuffer)+i, 1);
		if (rc <= 0 || (*pbuffer)[i] == '\n')
		{
			(*pbuffer)[i] = '\0';
			return rc <= 0 ? -1 : i;
		}
		if ((*pbuffer)[i] != '\r') i++;
	}
}

int eServiceTS::openHttpConnection(std::string url)
{
	std::string host;
	int port = 80;
	std::string uri;

	int slash = url.find("/", 7);
	if (slash > 0) {
		host = url.substr(7, slash-7);
		uri = url.substr(slash, url.length()-slash);
	} else {
		host = url.substr(7, url.length()-7);
		uri = "";
	}
	int dp = host.find(":");
	if (dp == 0) {
		port = atoi(host.substr(1, host.length()-1).c_str());
		host = "localhost";
	} else if (dp > 0) {
		port = atoi(host.substr(dp+1, host.length()-dp-1).c_str());
		host = host.substr(0, dp);
	}

	struct hostent* h = gethostbyname(host.c_str());
	if (h == NULL || h->h_addr_list == NULL)
		return -1;
	int fd = socket(PF_INET, SOCK_STREAM, 0);
	if (fd == -1)
		return -1;

	struct sockaddr_in addr;
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = *((in_addr_t*)h->h_addr_list[0]);
	addr.sin_port = htons(port);

	eDebug("connecting to %s", url.c_str());

	if (connect(fd, (sockaddr*)&addr, sizeof(addr)) == -1) {
		std::string msg = "connect failed for: " + url;
		eDebug(msg.c_str());
		return -1;
	}

	std::string request = "GET ";
	request.append(uri).append(" HTTP/1.1\n");
	request.append("Host: ").append(host).append("\n");
	request.append("Accept: */*\n");
	request.append("Connection: close\n");
	request.append("\n");
	//eDebug(request.c_str());
	write(fd, request.c_str(), request.length());

	int rc;
	size_t buflen = 1000;
	char* linebuf = (char*)malloc(1000);

	rc = getline(&linebuf, &buflen, fd);
	//eDebug("RECV(%d): %s", rc, linebuf);
	if (rc <= 0)
	{
		close(fd);
		free(linebuf);
		return -1;
	}

	char proto[100];
	int statuscode = 0;
	char statusmsg[100];
	rc = sscanf(linebuf, "%99s %d %99s", proto, &statuscode, statusmsg);
	if (rc != 3 || statuscode != 200) {
		eDebug("wrong response: \"200 OK\" expected.");
		free(linebuf);
		close(fd);
		return -1;
	}
	eDebug("proto=%s, code=%d, msg=%s", proto, statuscode, statusmsg);
	while (rc > 0)
	{
		rc = getline(&linebuf, &buflen, fd);
		//eDebug("RECV(%d): %s", rc, linebuf);
	}
	free(linebuf);

	return fd;
}

RESULT eServiceTS::connectEvent(const Slot2<void,iPlayableService*,int> &event, ePtr<eConnection> &connection)
{
	connection = new eConnection((iPlayableService*)this, m_event.connect(event));
	return 0;
}

RESULT eServiceTS::start()
{
	ePtr<eDVBResourceManager> rmgr;
	eDVBResourceManager::getInstance(rmgr);
	if (rmgr->allocateDemux(NULL, m_decodedemux, iDVBChannel::capDecode) != 0) {
		eDebug("Cannot allocate decode-demux");
		return 1;
	}
	if (m_decodedemux->get().getMPEGDecoder(m_decoder, 1) != 0) {
		eDebug("Cannot allocate MPEGDecoder");
		return 1;
	}
	m_decodedemux->get().setSourcePVR(0);
	m_decoder->setVideoPID(m_vpid, eDVBVideo::MPEG2);
	m_decoder->setAudioPID(m_apid, eDVBAudio::aMPEG);
	m_streamthread = new eStreamThread();
	CONNECT(m_streamthread->m_event, eServiceTS::recv_event);
	m_decoder->freeze(0);
	m_decoder->preroll();
	if (unpause() != 0) return -1;
	m_state = stRunning;
	m_event(this, evStart);
	return 0;
}

RESULT eServiceTS::stop()
{
	if (m_state != stRunning)
		return -1;
	printf("TS: %s stop\n", m_filename.c_str());
	m_streamthread->stop();
	m_decodedemux->get().flush();
	m_state = stStopped;
	return 0;
}

void eServiceTS::recv_event(int evt)
{
	eDebug("eServiceTS::recv_event: %d", evt);
	switch (evt) {
	case eStreamThread::evtEOS:
		m_decodedemux->get().flush();
		m_state = stStopped;
		m_event((iPlayableService*)this, evEOF);
		break;
	case eStreamThread::evtReadError:
	case eStreamThread::evtWriteError:
		m_decoder->freeze(0);
		m_state = stStopped;
		m_event((iPlayableService*)this, evEOF);
	}
}

RESULT eServiceTS::setTarget(int target)
{
	return -1;
}

RESULT eServiceTS::pause(ePtr<iPauseableService> &ptr)
{
	ptr=this;
	return 0;
}

RESULT eServiceTS::setSlowMotion(int ratio)
{
	return -1;
}

RESULT eServiceTS::setFastForward(int ratio)
{
	return -1;
}
  
		// iPausableService
RESULT eServiceTS::pause()
{
	m_streamthread->stop();
	m_decoder->freeze(0);
	return 0;
}

RESULT eServiceTS::unpause()
{
	int is_streaming = !strncmp(m_filename.c_str(), "http://", 7);
	int srcfd = -1;
	if (is_streaming) {
		srcfd = openHttpConnection(m_filename);
	} else {
		srcfd = ::open(m_filename.c_str(), O_RDONLY);
	}
	if (srcfd < 0) {
		eDebug("Cannot open source stream: %s", m_filename.c_str());
		return 1;
	}
	
	int destfd = ::open("/dev/misc/pvr", O_WRONLY);
	if (destfd < 0) {
		eDebug("Cannot open source stream: %s", m_filename.c_str());
		::close(srcfd);
		return 1;
	}
	m_decodedemux->get().flush();
	m_streamthread->start(srcfd, destfd);
	// let the video buffer fill up a bit
	usleep(200*1000);
	m_decoder->unfreeze();
	return 0;
}

	/* iSeekableService */
RESULT eServiceTS::seek(ePtr<iSeekableService> &ptr)
{
	ptr = this;
	return 0;
}

RESULT eServiceTS::getLength(pts_t &pts)
{
	return 0;
}

RESULT eServiceTS::seekTo(pts_t to)
{
	return 0;
}

RESULT eServiceTS::seekRelative(int direction, pts_t to)
{
	return 0;
}

RESULT eServiceTS::getPlayPosition(pts_t &pts)
{
	return 0;
}

RESULT eServiceTS::setTrickmode(int trick)
{
	return -1;
}


RESULT eServiceTS::isCurrentlySeekable()
{
	return 1;
}

RESULT eServiceTS::info(ePtr<iServiceInformation>&i)
{
	i = this;
	return 0;
}

RESULT eServiceTS::getName(std::string &name)
{
	name = m_filename;
	size_t n = name.rfind('/');
	if (n != std::string::npos)
		name = name.substr(n + 1);
	return 0;
}

int eServiceTS::getInfo(int w)
{
	return resNA;
}

std::string eServiceTS::getInfoString(int w)
{
	return "";
}

DEFINE_REF(eStreamThread)

eStreamThread::eStreamThread(): m_messagepump(eApp, 0) {
	CONNECT(m_messagepump.recv_msg, eStreamThread::recvEvent);
}
eStreamThread::~eStreamThread() {
}

void eStreamThread::start(int srcfd, int destfd) {
	m_srcfd = srcfd;
	m_destfd = destfd;
	m_stop = false;
	run(IOPRIO_CLASS_RT);
}
void eStreamThread::stop() {
	m_stop = true;
	kill();
}

void eStreamThread::recvEvent(const int &evt)
{
	m_event(evt);
}

void eStreamThread::thread() {
	const int bufsize = 60000;
	unsigned char buf[bufsize];
	bool eof = false;
	fd_set rfds;
	fd_set wfds;
	struct timeval timeout;
	int rc,r,w,maxfd;
	
	r = w = 0;
	hasStarted();
	eDebug("eStreamThread started");
	while (!m_stop) {
		pthread_testcancel();
		FD_ZERO(&rfds);
		FD_ZERO(&wfds);
		maxfd = 0;
		timeout.tv_sec = 1;
		timeout.tv_usec = 0;
		if (r < bufsize) {
			FD_SET(m_srcfd, &rfds);
			maxfd = MAX(maxfd, m_srcfd);
		}
		if (w < r) {
			FD_SET(m_destfd, &wfds);
			maxfd = MAX(maxfd, m_destfd);
		}
		rc = select(maxfd+1, &rfds, &wfds, NULL, &timeout);
		if (rc == 0) {
			eDebug("eStreamThread::thread: timeout!");
			continue;
		}
		if (rc < 0) {
			eDebug("eStreamThread::thread: error in select (%d)", errno);
			break;
		}
		if (FD_ISSET(m_srcfd, &rfds)) {
			rc = ::read(m_srcfd, buf+r, bufsize - r);
			if (rc < 0) {
				eDebug("eStreamThread::thread: error in read (%d)", errno);
				m_messagepump.send(evtReadError);
				break;
			} else if (rc == 0) {
				eof = true;
			} else {
				r += rc;
				if (r == bufsize) eDebug("eStreamThread::thread: buffer full");
			}
		}
		if (FD_ISSET(m_destfd, &wfds) && (w < r)) {
			rc = ::write(m_destfd, buf+w, r-w);
			if (rc < 0) {
				eDebug("eStreamThread::thread: error in write (%d)", errno);
				m_messagepump.send(evtWriteError);
				break;
			}
			w += rc;
			//eDebug("eStreamThread::thread: buffer r=%d w=%d",r,w);
			if (w == r) w = r = 0;
		}
		if (eof && (r==w)) {
			::close(m_destfd);
			m_destfd = -1;
			::close(m_srcfd);
			m_srcfd = -1;
			m_messagepump.send(evtEOS);
			break;
		}
	}
	eDebug("eStreamThread end");
}

void eStreamThread::thread_finished() {
	if (m_srcfd >= 0) ::close(m_srcfd);
	if (m_destfd >= 0) ::close(m_destfd);
	eDebug("eStreamThread closed");
}

eAutoInitPtr<eServiceFactoryTS> init_eServiceFactoryTS(eAutoInitNumbers::service+1, "eServiceFactoryTS");

PyMODINIT_FUNC
initservicets(void)
{
	Py_InitModule("servicets", NULL);
}
