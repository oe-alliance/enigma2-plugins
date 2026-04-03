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

#include "bitratecalc.h"
#include <fcntl.h>

eBitrateCalc::eBitrateCalc(int pid, int dvbnamespace, int tsid, int onid, int refreshintervall, int buffer_size)
	: m_size(0), m_refresh_intervall(refreshintervall)
{
	m_send_data_timer = eTimer::create(eApp);
	CONNECT(m_send_data_timer->timeout, eBitrateCalc::sendDataTimerTimeoutCB);

	eDVBChannelID chid;
	chid.dvbnamespace = eDVBNamespace(dvbnamespace);
	chid.transport_stream_id = eTransportStreamID(tsid);
	chid.original_network_id = eOriginalNetworkID(onid);

	ePtr<eDVBResourceManager> res_mgr;
	eDVBResourceManager::getInstance(res_mgr);

	eUsePtr<iDVBChannel> channel;
	int success = 0;
	m_reader = NULL;

	if (!res_mgr->allocateChannel(chid, channel, false))
	{
		ePtr<iDVBDemux> demux;
		if (!channel->getDemux(demux))
		{
			if (!demux->createPESReader(eApp, m_reader))
			{
				if (!m_reader->connectRead(sigc::mem_fun(*this, &eBitrateCalc::dataReady), m_pes_connection))
				{
					channel->connectStateChange(sigc::mem_fun(*this, &eBitrateCalc::stateChange), m_channel_connection);
					success = 1;
				}
				else
					eDebug("[eBitrateCalc] connect pes reader failed...");
			}
			else
				eDebug("[eBitrateCalc] create PES reader failed...");
		}
		else
			eDebug("[eBitrateCalc] getDemux failed...");
	}
	else
	{
		eDebug("[eBitrateCalc] allocate channel failed...trying pvr_allocate_demux");
		ePtr<eDVBAllocatedDemux> pvr_allocated_demux;
		int i = 0;
		if (!res_mgr->allocateDemux(NULL, pvr_allocated_demux, i))
		{
			eDVBDemux &demux = pvr_allocated_demux->get();
			if (!demux.createPESReader(eApp, m_reader))
			{
				if (!m_reader->connectRead(sigc::mem_fun(*this, &eBitrateCalc::dataReady), m_pes_connection))
					success = 1;
				else
					eDebug("[eBitrateCalc] connect pes reader failed...");
			}
			else
				eDebug("[eBitrateCalc] create PES reader failed...");
		}
		else
			eDebug("[eBitrateCalc] allocate pvr_allocated_demux failed...");
	}

	if (m_reader && success)
	{
		clock_gettime(CLOCK_MONOTONIC, &m_start);
		m_reader->setBufferSize(buffer_size);
		m_reader->start(pid);
		m_send_data_timer->start(m_refresh_intervall, true);
	}
	else
		sendData(-1, 0);
}

void eBitrateCalc::dataReady(const __u8*, int size)
{
	m_size += size;
}

void eBitrateCalc::sendDataTimerTimeoutCB()
{
	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);
	timespec delta = now - m_start;
	unsigned int delta_ms = delta.tv_nsec / 1000000 + delta.tv_sec * 1000;

	if (delta_ms)
	{
		int bitrate = int(m_size / delta_ms) * 8;
		sendData(bitrate, 1);
	}

	m_send_data_timer->start(m_refresh_intervall, true);
}

void eBitrateCalc::stateChange(iDVBChannel *ch)
{
	int state;
	if (ch->getState(state))
		return;

	if (state == iDVBChannel::state_release)
	{
		m_send_data_timer = NULL;
		m_reader = NULL;
		m_pes_connection = NULL;
		m_channel_connection = NULL;
		sendData(-1, 0);
	}
}

extern "C" {

struct eBitrateCalculatorPy
{
	PyObject_HEAD
	eBitrateCalc *bc;
};

static void
eBitrateCalculatorPy_dealloc(eBitrateCalculatorPy *self)
{
	if (self->bc)
	{
		delete self->bc;
		self->bc = NULL;
	}
	Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
eBitrateCalculatorPy_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	static const char *kwlist[] = {
		"pid", "dvbnamespace", "tsid", "onid", "refreshinterval", "buffer_size", NULL
	};

	eBitrateCalculatorPy *self = (eBitrateCalculatorPy *)type->tp_alloc(type, 0);
	if (!self)
		return NULL;

	self->bc = NULL;

	int pid, dvbnamespace, tsid, onid, refreshinterval, buffer_size;
	if (!PyArg_ParseTupleAndKeywords(
			args, kwds, "iiiiii", (char **)kwlist,
			&pid, &dvbnamespace, &tsid, &onid, &refreshinterval, &buffer_size))
	{
		Org_Py_DECREF((PyObject *)self);
		return NULL;
	}

	self->bc = new eBitrateCalc(pid, dvbnamespace, tsid, onid, refreshinterval, buffer_size);
	if (!self->bc)
	{
		Org_Py_DECREF((PyObject *)self);
		PyErr_SetString(PyExc_MemoryError, "failed to allocate eBitrateCalc");
		return NULL;
	}

	return (PyObject *)self;
}

static PyObject *
eBitrateCalculatorPy_get_cb_list(eBitrateCalculatorPy *self, void *closure)
{
	if (!self->bc)
		Py_RETURN_NONE;
	return self->bc->dataSent.get();
}

static PyGetSetDef eBitrateCalculatorPy_getseters[] = {
	{
		(char *)"callback",
		(getter)eBitrateCalculatorPy_get_cb_list,
		(setter)0,
		(char *)"returns the callback python list",
		NULL
	},
	{NULL, NULL, NULL, NULL, NULL}
};

static PyTypeObject eBitrateCalculatorPyType = {
	PyVarObject_HEAD_INIT(NULL, 0)
};

static PyMethodDef module_methods[] = {
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef bitratecalcmodule = {
	PyModuleDef_HEAD_INIT,
	"bitratecalc",
	"Module that implements bitrate calculations.",
	-1,
	module_methods,
	NULL,
	NULL,
	NULL,
	NULL
};

PyMODINIT_FUNC
PyInit_bitratecalc(void)
{
	eBitrateCalculatorPyType.tp_name = "eBitrateImpl.eBitrateCalculator";
	eBitrateCalculatorPyType.tp_basicsize = sizeof(eBitrateCalculatorPy);
	eBitrateCalculatorPyType.tp_itemsize = 0;
	eBitrateCalculatorPyType.tp_dealloc = (destructor)eBitrateCalculatorPy_dealloc;
	eBitrateCalculatorPyType.tp_flags = Py_TPFLAGS_DEFAULT;
	eBitrateCalculatorPyType.tp_doc = "eBitrateCalculator objects";
	eBitrateCalculatorPyType.tp_getset = eBitrateCalculatorPy_getseters;
	eBitrateCalculatorPyType.tp_new = eBitrateCalculatorPy_new;

	if (PyType_Ready(&eBitrateCalculatorPyType) < 0)
		return NULL;

	PyObject *m = PyModule_Create(&bitratecalcmodule);
	if (m == NULL)
		return NULL;

	Org_Py_INCREF((PyObject *)&eBitrateCalculatorPyType);
	if (PyModule_AddObject(m, "eBitrateCalculator", (PyObject *)&eBitrateCalculatorPyType) < 0)
	{
		Org_Py_DECREF((PyObject *)&eBitrateCalculatorPyType);
		Org_Py_DECREF(m);
		return NULL;
	}

	return m;
}

} // extern "C"