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
#include <lib/base/etpm.h>
#include <openssl/bn.h>
#include <openssl/sha.h>

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
				if (!m_reader->connectRead(slot(*this, &eBitrateCalc::dataReady), m_pes_connection))
				{
					channel->connectStateChange(slot(*this, &eBitrateCalc::stateChange), m_channel_connection);
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
				if (!m_reader->connectRead(slot(*this, &eBitrateCalc::dataReady), m_pes_connection))
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

static void rsa_pub1024(unsigned char dest[128],
			const unsigned char src[128],
			const unsigned char mod[128])
{
	BIGNUM bbuf, bexp, bmod;
	BN_CTX *ctx;

	ctx = BN_CTX_new();
	BN_init(&bbuf);
	BN_init(&bexp);
	BN_init(&bmod);

	BN_bin2bn(src, 128, &bbuf);
	BN_bin2bn(mod, 128, &bmod);
	BN_bin2bn((const unsigned char *)"\x01\x00\x01", 3, &bexp);

	BN_mod_exp(&bbuf, &bbuf, &bexp, &bmod, ctx);

	BN_bn2bin(&bbuf, dest);

	BN_clear_free(&bexp);
	BN_clear_free(&bmod);
	BN_clear_free(&bbuf);
	BN_CTX_free(ctx);
}

static bool decrypt_block(unsigned char dest[128],
			  const unsigned char *src,
			  unsigned int len,
			  const unsigned char mod[128])
{
	unsigned char hash[20];
	SHA_CTX ctx;

	if ((len != 128) &&
	    (len != 202))
		return false;

	rsa_pub1024(dest, src, mod);

	SHA1_Init(&ctx);
	SHA1_Update(&ctx, &dest[1], 106);
	if (len == 202)
		SHA1_Update(&ctx, &src[131], 61);
	SHA1_Final(hash, &ctx);

	return (memcmp(hash, &dest[107], 20) == 0);
}

static bool read_random(unsigned char *buf, size_t len)
{
	ssize_t ret;
	int fd;

	fd = open("/dev/urandom", O_RDONLY);
	if (fd < 0) {
		perror("/dev/urandom");
		return false;
	}

	ret = read(fd, buf, len);

	close(fd);

	if (ret != (ssize_t)len) {
		fprintf(stderr, "could not read random data\n");
		return false;
	}

	return true;
}

static bool validate_cert(unsigned char dest[128],
			  const unsigned char *src,
			  const unsigned char mod[128])
{
	unsigned char buf[128];

	if (!decrypt_block(buf, &src[8], 210 - 8, mod))
		return false;

	memcpy(&dest[0], &buf[36], 71);
	memcpy(&dest[71], &src[131 + 8], 57);
	return true;
}

static const unsigned char tpm_root_mod[128] = {
	0x9F,0x7C,0xE4,0x47,0xC9,0xB4,0xF4,0x23,0x26,0xCE,0xB3,0xFE,0xDA,0xC9,0x55,0x60,
	0xD8,0x8C,0x73,0x6F,0x90,0x9B,0x5C,0x62,0xC0,0x89,0xD1,0x8C,0x9E,0x4A,0x54,0xC5,
	0x58,0xA1,0xB8,0x13,0x35,0x45,0x02,0xC9,0xB2,0xE6,0x74,0x89,0xDE,0xCD,0x9D,0x11,
	0xDD,0xC7,0xF4,0xE4,0xE4,0xBC,0xDB,0x9C,0xEA,0x7D,0xAD,0xDA,0x74,0x72,0x9B,0xDC,
	0xBC,0x18,0x33,0xE7,0xAF,0x7C,0xAE,0x0C,0xE3,0xB5,0x84,0x8D,0x0D,0x8D,0x9D,0x32,
	0xD0,0xCE,0xD5,0x71,0x09,0x84,0x63,0xA8,0x29,0x99,0xDC,0x3C,0x22,0x78,0xE8,0x87,
	0x8F,0x02,0x3B,0x53,0x6D,0xD5,0xF0,0xA3,0x5F,0xB7,0x54,0x09,0xDE,0xA7,0xF1,0xC9,
	0xAE,0x8A,0xD7,0xD2,0xCF,0xB2,0x2E,0x13,0xFB,0xAC,0x6A,0xDF,0xB1,0x1D,0x3A,0x3F,
};

#define CLEN 8

static bool signature()
{
	int chk = 1;
	FILE *fp; 
	fp = fopen ("/proc/stb/info/model", "r");
	if (fp)
	{
		char line[256];
		int n;
		fgets(line, sizeof(line), fp);
 		if ((n = strlen(line)) && line[n - 1] == '\n')
		         line[n - 1] = '\0';
		fclose(fp);
		if (strstr(line,"dm7025"))
			chk = 0;
	}
	if (chk)
	{
	  	eTPM tpm;
		unsigned char rnd[CLEN];
		/* read random bytes */
		if (!read_random(rnd, CLEN))
			return 1;
		unsigned char level2_mod[128];
		unsigned char level3_mod[128];
		unsigned char buf[128];
		std::string challenge((char*)rnd, CLEN);
		std::string response = tpm.computeSignature(challenge);
		unsigned int len = response.size();
		unsigned char val[len];
		if ( len != 128 )
			return false;
		memcpy(val, response.c_str(), len);
		std::string cert = tpm.getData(eTPM::DT_LEVEL2_CERT);
		if ( cert.size() != 210 || !validate_cert(level2_mod, (const unsigned char*) cert.c_str(), tpm_root_mod))
			return false;
		cert = tpm.getData(eTPM::DT_LEVEL3_CERT);
		if ( cert.size() != 210 || !validate_cert(level3_mod, (const unsigned char*) cert.c_str(), level2_mod))
			return false;
		if (!decrypt_block(buf, val, 128, level3_mod))
			return false;
		if (memcmp(&buf[80], rnd, CLEN))
			return false;
		return true;
	}
	else
		return true;
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
	bool init = signature();
	PyObject* m = Py_InitModule3("bitratecalc", module_methods,
		"Module that implements bitrate calculations.");
	if (m == NULL)
		return;
	if (!init)
	{
		PyErr_SetString(PyExc_TypeError, "TPM challenge failed");
		return; 
	}
	if (!PyType_Ready(&eBitrateCalculatorPyType))
	{
		Org_Py_INCREF((PyObject*)&eBitrateCalculatorPyType);
		PyModule_AddObject(m, "eBitrateCalculator", (PyObject*)&eBitrateCalculatorPyType);
	}
}
};
