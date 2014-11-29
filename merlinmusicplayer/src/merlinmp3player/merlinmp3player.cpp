/*
  MerlinMP3Player E2

  (c) 2010 by Dr. Best  <dr.best@dreambox-tools.info>
  Support: www.dreambox-tools.info

*/

#include <lib/base/eerror.h>
#include <lib/base/object.h>
#include <lib/base/ebase.h>
#include <string>
#include "merlinmp3player.h"
#include <lib/service/service.h>
#include <lib/base/init_num.h>
#include <lib/base/init.h>
#include <gst/gst.h>

// eServiceFactoryMerlinMP3Player

eServiceFactoryMerlinMP3Player::eServiceFactoryMerlinMP3Player()
{
	ePtr<eServiceCenter> sc;
	
	eServiceCenter::getPrivInstance(sc);
	if (sc)
	{
		std::list<std::string> extensions;
		extensions.push_back("mp3");
		sc->addServiceFactory(eServiceFactoryMerlinMP3Player::id, this, extensions);
	}
	m_service_info = new eStaticServiceMP3Info();

}

eServiceFactoryMerlinMP3Player::~eServiceFactoryMerlinMP3Player()
{
	ePtr<eServiceCenter> sc;
	
	eServiceCenter::getPrivInstance(sc);
	if (sc)
		sc->removeServiceFactory(eServiceFactoryMerlinMP3Player::id);
}

DEFINE_REF(eServiceFactoryMerlinMP3Player)

	// iServiceHandler
RESULT eServiceFactoryMerlinMP3Player::play(const eServiceReference &ref, ePtr<iPlayableService> &ptr)
{
		// check resources...
	ptr = new eServiceMerlinMP3Player(ref);
	return 0;
}

RESULT eServiceFactoryMerlinMP3Player::record(const eServiceReference &ref, ePtr<iRecordableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryMerlinMP3Player::list(const eServiceReference &, ePtr<iListableService> &ptr)
{
	ptr=0;
	return -1;
}

RESULT eServiceFactoryMerlinMP3Player::info(const eServiceReference &ref, ePtr<iStaticServiceInformation> &ptr)
{
	ptr = m_service_info;
	return 0;
}

RESULT eServiceFactoryMerlinMP3Player::offlineOperations(const eServiceReference &, ePtr<iServiceOfflineOperations> &ptr)
{
	ptr = 0;
	return -1;
}

DEFINE_REF(eStaticServiceMP3Info)

eStaticServiceMP3Info::eStaticServiceMP3Info()
{
	// nothing to to here...
}

RESULT eStaticServiceMP3Info::getName(const eServiceReference &ref, std::string &name)
{
	size_t last = ref.path.rfind('/');
	if (last != std::string::npos)
		name = ref.path.substr(last+1);
	else
		name = ref.path;
	return 0;
}

int eStaticServiceMP3Info::getLength(const eServiceReference &ref)
{
	return -1;
}

// eServiceMerlinMP3Player

eServiceMerlinMP3Player::eServiceMerlinMP3Player(eServiceReference ref):  m_ref(ref), m_pump(eApp, 1)
{
	m_filename = m_ref.path.c_str();
	CONNECT(m_pump.recv_msg, eServiceMerlinMP3Player::gstPoll);
	m_state = stIdle;
	eDebug("eServiceMerlinMP3Player construct!");

	GstElement *sink;
	GstElement *source;
	GstElement *decoder;

	m_gst_pipeline = gst_pipeline_new ("audio-player");
	if (!m_gst_pipeline)
		eWarning("failed to create pipeline");

	source   = gst_element_factory_make ("filesrc", "file reader");
	decoder   = gst_element_factory_make ("mad", "MP3 decoder");
	sink     = gst_element_factory_make ("alsasink", "ALSA output");
	if (m_gst_pipeline && source && decoder && sink)
	{
		g_object_set (G_OBJECT (source), "location", m_filename.c_str(), NULL);
		gst_bin_add_many (GST_BIN (m_gst_pipeline), source, decoder, sink, NULL);
		gst_element_link_many (source, decoder, sink, NULL);
#if GST_VERSION_MAJOR < 1
		gst_bus_set_sync_handler(gst_pipeline_get_bus (GST_PIPELINE (m_gst_pipeline)), gstBusSyncHandler, this);
#else
		gst_bus_set_sync_handler(gst_pipeline_get_bus (GST_PIPELINE (m_gst_pipeline)), gstBusSyncHandler, this, NULL);
#endif
		gst_element_set_state (m_gst_pipeline, GST_STATE_PLAYING);
	}
	else
	{
		if (m_gst_pipeline)
			gst_object_unref(GST_OBJECT(m_gst_pipeline));
		if (source)
			gst_object_unref(GST_OBJECT(source));
		if (decoder)
			gst_object_unref(GST_OBJECT(decoder));
		if (sink)
			gst_object_unref(GST_OBJECT(sink));
		eDebug("no playing...!");
	}
	eDebug("eServiceMerlinMP3Player::using gstreamer with location=%s", m_filename.c_str());
}

eServiceMerlinMP3Player::~eServiceMerlinMP3Player()
{
	if (m_state == stRunning)
		stop();

	if (m_gst_pipeline)
	{
		gst_object_unref (GST_OBJECT (m_gst_pipeline));
		eDebug("eServiceMerlinMP3Player destruct!");
	}
}

DEFINE_REF(eServiceMerlinMP3Player);	

RESULT eServiceMerlinMP3Player::connectEvent(const Slot2<void,iPlayableService*,int> &event, ePtr<eConnection> &connection)
{
	connection = new eConnection((iPlayableService*)this, m_event.connect(event));
	return 0;
}

RESULT eServiceMerlinMP3Player::start()
{
	assert(m_state == stIdle);
	
	m_state = stRunning;
	if (m_gst_pipeline)
	{
		eDebug("eServiceMerlinMP3Player::starting pipeline");
		gst_element_set_state (m_gst_pipeline, GST_STATE_PLAYING);
	}
	m_event(this, evStart);
	return 0;
}

RESULT eServiceMerlinMP3Player::stop()
{
	assert(m_state != stIdle);
	if (m_state == stStopped)
		return -1;
	eDebug("eServiceMerlinMP3Player::stop %s", m_filename.c_str());
	gst_element_set_state(m_gst_pipeline, GST_STATE_NULL);
	m_state = stStopped;
	return 0;
}

RESULT eServiceMerlinMP3Player::setTarget(int target)
{
	return -1;
}

RESULT eServiceMerlinMP3Player::pause(ePtr<iPauseableService> &ptr)
{
	ptr=this;
	return 0;
}

RESULT eServiceMerlinMP3Player::setSlowMotion(int ratio)
{
	return -1;
}

RESULT eServiceMerlinMP3Player::setFastForward(int ratio)
{
	return -1;
}
  
		// iPausableService
RESULT eServiceMerlinMP3Player::pause()
{
	if (!m_gst_pipeline)
		return -1;
	gst_element_set_state(m_gst_pipeline, GST_STATE_PAUSED);
	return 0;
}

RESULT eServiceMerlinMP3Player::unpause()
{
	if (!m_gst_pipeline)
		return -1;
	gst_element_set_state(m_gst_pipeline, GST_STATE_PLAYING);
	return 0;
}

	/* iSeekableService */
RESULT eServiceMerlinMP3Player::seek(ePtr<iSeekableService> &ptr)
{
	ptr = this;
	return 0;
}

RESULT eServiceMerlinMP3Player::getLength(pts_t &pts)
{
	if (!m_gst_pipeline)
		return -1;
	if (m_state != stRunning)
		return -1;
	
	GstFormat fmt = GST_FORMAT_TIME;
	gint64 len;
	
#if GST_VERSION_MAJOR < 1
 	if (!gst_element_query_duration(m_gst_pipeline, &fmt, &len))
 		return -1;
#else
	if (!gst_element_query_duration(m_gst_pipeline, fmt, &len))
		return -1;
#endif
	
		/* len is in nanoseconds. we have 90 000 pts per second. */
	
	pts = len / 11111;
	return 0;
}

RESULT eServiceMerlinMP3Player::seekTo(pts_t to)
{
	if (!m_gst_pipeline)
		return -1;

		/* convert pts to nanoseconds */
	gint64 time_nanoseconds = to * 11111LL;
	if (!gst_element_seek (m_gst_pipeline, 1.0, GST_FORMAT_TIME, GST_SEEK_FLAG_FLUSH,
		GST_SEEK_TYPE_SET, time_nanoseconds,
		GST_SEEK_TYPE_NONE, GST_CLOCK_TIME_NONE))
	{
		eDebug("eServiceMerlinMP3Player::SEEK failed");
		return -1;
	}
	return 0;
}

RESULT eServiceMerlinMP3Player::seekRelative(int direction, pts_t to)
{
	if (!m_gst_pipeline)
		return -1;

	pause();

	pts_t ppos;
	getPlayPosition(ppos);
	ppos += to * direction;
	if (ppos < 0)
		ppos = 0;
	seekTo(ppos);
	
	unpause();

	return 0;
}

RESULT eServiceMerlinMP3Player::getPlayPosition(pts_t &pts)
{
	if (!m_gst_pipeline)
		return -1;
	if (m_state != stRunning)
		return -1;
	
	GstFormat fmt = GST_FORMAT_TIME;
	gint64 len;
	
#if GST_VERSION_MAJOR < 1
 	if (!gst_element_query_position(m_gst_pipeline, &fmt, &len))
 		return -1;
#else
	if (!gst_element_query_position(m_gst_pipeline, fmt, &len))
		return -1;
#endif
	
		/* len is in nanoseconds. we have 90 000 pts per second. */
	pts = len / 11111;
	return 0;
}

RESULT eServiceMerlinMP3Player::setTrickmode(int trick)
{
		/* trickmode currently doesn't make any sense for us. */
	return -1;
}

RESULT eServiceMerlinMP3Player::isCurrentlySeekable()
{
	return 1;
}

RESULT eServiceMerlinMP3Player::info(ePtr<iServiceInformation>&i)
{
	i = this;
	return 0;
}

RESULT eServiceMerlinMP3Player::getName(std::string &name)
{
	name = m_filename;
	size_t n = name.rfind('/');
	if (n != std::string::npos)
		name = name.substr(n + 1);
	return 0;
}

int eServiceMerlinMP3Player::getInfo(int w)
{
	return resNA;
}

std::string eServiceMerlinMP3Player::getInfoString(int w)
{
	return "";
}

void eServiceMerlinMP3Player::gstBusCall(GstBus *bus, GstMessage *msg)
{
	switch (GST_MESSAGE_TYPE (msg))
	{
		case GST_MESSAGE_EOS:
			m_event((iPlayableService*)this, evEOF);
			break;
		case GST_MESSAGE_STATE_CHANGED:
		{
			if(GST_MESSAGE_SRC(msg) != GST_OBJECT(m_gst_pipeline))
				break;
			GstState old_state, new_state;
			gst_message_parse_state_changed(msg, &old_state, &new_state, NULL);
			if(old_state == new_state)
				break;
			eDebug("eServiceMerlinMP3Player::state transition %s -> %s", gst_element_state_get_name(old_state), gst_element_state_get_name(new_state));
			break;
		}
		case GST_MESSAGE_ERROR:
		{
			gchar *debug;
			GError *err;
			gst_message_parse_error (msg, &err, &debug);
			g_free (debug);
			eWarning("Gstreamer error: %s", err->message);
			g_error_free(err);
			break;
		}
		default:
			break;
	}
}

GstBusSyncReply eServiceMerlinMP3Player::gstBusSyncHandler(GstBus *bus, GstMessage *message, gpointer user_data)
{
	eServiceMerlinMP3Player *_this = (eServiceMerlinMP3Player*)user_data;
	_this->m_pump.send(1);
		/* wake */
	return GST_BUS_PASS;
}

void eServiceMerlinMP3Player::gstPoll(const int&)
{
	usleep(1);
	GstBus *bus = gst_pipeline_get_bus (GST_PIPELINE (m_gst_pipeline));
	GstMessage *message;
	while ((message = gst_bus_pop (bus)))
	{
		gstBusCall(bus, message);
		gst_message_unref (message);
	}
}


eAutoInitPtr<eServiceFactoryMerlinMP3Player> init_eServiceFactoryMerlinMP3Player(eAutoInitNumbers::service+1, "eServiceFactoryMerlinMP3Player");

PyMODINIT_FUNC
initmerlinmp3player(void)
{
	Py_InitModule("merlinmp3player", NULL);
}

