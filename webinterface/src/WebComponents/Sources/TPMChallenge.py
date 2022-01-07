from Components.Sources.Source import Source

from base64 import b64encode, b64decode
from six import ensure_binary, ensure_str

try:
	from enigma import eTPM
	tpm = eTPM()
except ImportError:
	tpm = None


class TPMChallenge(Source):
	CERTIFICATES = "certificates"
	CHALLENGE = "challenge"

	def __init__(self):
		Source.__init__(self)
		self.cmd = None

	def handleCommand(self, cmd):
		self.cmd = cmd

	def do_tpm(self):
		l2cert = None
		l3cert = None
		cmd = self.cmd.get('cmd', self.CERTIFICATES)

		if cmd == self.CERTIFICATES and tpm != None:
			l2cert = tpm.getData(eTPM.DT_LEVEL2_CERT)
			l3cert = tpm.getData(eTPM.DT_LEVEL3_CERT)

			return (b64encode(ensure_binary(l2cert)), b64encode(ensure_binary(l3cert)), None, True, _('LEVEL2 and LEVEL3 Certifcates (Base64-encoded)'))

		elif cmd == self.CHALLENGE and tpm != None:
			random = self.cmd.get('random', None)

			if random != None:

				value = b64encode(ensure_binary(tpm.computeSignature(ensure_str(b64decode(random)))))
				return (None, None, value, True, _('Challenge executed, please verify the result!'))
			else:
				return (None, None, None, False, _('Obligatory parameter "random" for cmd="%s" missing') % self.CHALLENGE)

		return (None, None, None, False, _('Unknown for parameter "cmd" [%s|%s]') % (self.CERTIFICATES, self.CHALLENGE))

	tpm_result = property(do_tpm)
