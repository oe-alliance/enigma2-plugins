class EPGRefreshService(object):
	def __init__(self, sref, duration):
		self.sref = str(sref)
		self.duration = duration

	def __eq__(self, other):
		if hasattr(other, 'sref'):
			return self.sref == other.sref
		return False

	def __hash__(self):
		return self.sref.__hash__()

	def __str__(self):
		return self.sref

	def __repr__(self):
		return ''.join((
			'<EPGRefreshService (',
			', '.join((
				self.sref,
				str(self.duration or '?'),
			)),
			')>'
		))
