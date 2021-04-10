from enigma import eTPM

from Components.Sources.Source import Source

from base64 import b64encode, b64decode

tpm = eTPM()

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

		if cmd == self.CERTIFICATES:
			l2cert = tpm.getData(eTPM.DT_LEVEL2_CERT)
			l3cert = tpm.getData(eTPM.DT_LEVEL3_CERT)

			return (b64encode(l2cert), b64encode(l3cert), None, True, _('LEVEL2 and LEVEL3 Certifcates (Base64-encoded)'))

		elif cmd == self.CHALLENGE:
			random = self.cmd.get('random', None)

			if random != None:

				value = b64encode(tpm.computeSignature(b64decode(random)))
				return (None, None, value, True, _('Challenge executed, please verify the result!'))
			else:
				return (None, None, None, False, _('Obligatory parameter "random" for cmd="%s" missing') %self.CHALLENGE)

		return (None, None, None, False, _('Unknown for parameter "cmd" [%s|%s]') %(self.CERTIFICATES, self.CHALLENGE))

	tpm_result = property(do_tpm)
