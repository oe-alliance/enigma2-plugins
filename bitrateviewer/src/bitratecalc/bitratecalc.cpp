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

eBitrateCalc::eBitrateCalc(int pid, int dvbnamespace, int tsid, int onid, int refreshintervall, int buffer_size): m_size(0), m_refresh_intervall(refreshintervall)
{
	m_send_data_timer = eTimer::create(eApp);
	CONNECT(m_send_data_timer->timeout, eBitrateCalc::sendDataTimerTimeoutCB);
	eDVBChannelID chid; //(eDVBNamespace(dvbnamespace), eTransportStreamID(tsid), eOriginalNetworkID(onid));  <-- weird, that does not work
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
		if (!res_mgr->allocateDemux(NULL,pvr_allocated_demux,i))
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
		sendData(-1,0);
}

void eBitrateCalc::dataReady(const __u8*,  int size)
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
		int bitrate =  int(m_size / delta_ms)*8;
		sendData(bitrate,1);
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
		sendData(-1,0);
	}
}

// eBitrateCalculator replacement
extern "C" {

struct eBitrateCalculatorPy
{
	PyObject_HEAD
	eBitrateCalc *bc;
};

static int
eBitrateCalculatorPy_traverse(eBitrateCalculatorPy *self, visitproc visit, void *arg)
{
	PyObject *obj = self->bc->dataSent.getSteal();
	if (obj)
		Py_VISIT(obj);
	return 0;
}

static int
eBitrateCalculatorPy_clear(eBitrateCalculatorPy *self)
{
	PyObject *obj = self->bc->dataSent.getSteal(true);
	if (obj)
		Py_CLEAR(obj);
	delete self->bc;
	return 0;
}

static void
eBitrateCalculatorPy_dealloc(eBitrateCalculatorPy* self)
{
	eBitrateCalculatorPy_clear(self);
	self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
eBitrateCalculatorPy_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	eBitrateCalculatorPy *self = (eBitrateCalculatorPy *)type->tp_alloc(type, 0);
	int size = PyTuple_Size(args);
	int pid, dvbnamespace, tsid, onid, refreshinterval, buffer_size;
	if (size < 6 || !PyArg_ParseTuple(args, "iiiiii", &pid, &dvbnamespace, &tsid, &onid, &refreshinterval, &buffer_size))
		return NULL;
	self->bc = new eBitrateCalc(pid, dvbnamespace, tsid, onid, refreshinterval, buffer_size);
	return (PyObject *)self;
}

static PyObject *
eBitrateCalculatorPy_get_cb_list(eBitrateCalculatorPy *self, void *closure)
{
	return self->bc->dataSent.get();
}

static PyGetSetDef eBitrateCalculatorPy_getseters[] = {
	{"callback",
	 (getter)eBitrateCalculatorPy_get_cb_list, (setter)0,
	 "returns the callback python list",
	 NULL},
	{NULL} /* Sentinel */
};

static PyTypeObject eBitrateCalculatorPyType = {
	PyObject_HEAD_INIT(NULL)
	0, /*ob_size*/
	"eBitrateImpl.eBitrateCalculator", /*tp_name*/
	sizeof(eBitrateCalculatorPy), /*tp_basicsize*/
	0, /*tp_itemsize*/
	(destructor)eBitrateCalculatorPy_dealloc, /*tp_dealloc*/
	0, /*tp_print*/
	0, /*tp_getattr*/
	0, /*tp_setattr*/
	0, /*tp_compare*/
	0, /*tp_repr*/
	0, /*tp_as_number*/
	0, /*tp_as_sequence*/
	0, /*tp_as_mapping*/
	0, /*tp_hash */
	0, /*tp_call*/
	0, /*tp_str*/
	0, /*tp_getattro*/
	0, /*tp_setattro*/
	0, /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /*tp_flags*/
	"eBitrateCalculator objects", /* tp_doc */
	(traverseproc)eBitrateCalculatorPy_traverse, /* tp_traverse */
	(inquiry)eBitrateCalculatorPy_clear, /* tp_clear */
	0, /* tp_richcompare */
	0, /* tp_weaklistoffset */
	0, /* tp_iter */
	0, /* tp_iternext */
	0, /* tp_methods */
	0, /* tp_members */
	eBitrateCalculatorPy_getseters, /* tp_getset */
	0, /* tp_base */
	0, /* tp_dict */
	0, /* tp_descr_get */
	0, /* tp_descr_set */
	0, /* tp_dictoffset */
	0, /* tp_init */
	0, /* tp_alloc */
	eBitrateCalculatorPy_new, /* tp_new */
};

static PyMethodDef module_methods[] = {
	{NULL}  /* Sentinel */
};

PyMODINIT_FUNC
initbitratecalc(void)
{
	PyObject* m = Py_InitModule3("bitratecalc", module_methods,
		"Module that implements bitrate calculations.");
	if (m == NULL)
		return;
	if (!PyType_Ready(&eBitrateCalculatorPyType))
	{
		Org_Py_INCREF((PyObject*)&eBitrateCalculatorPyType);
		PyModule_AddObject(m, "eBitrateCalculator", (PyObject*)&eBitrateCalculatorPyType);
	}
}
};
