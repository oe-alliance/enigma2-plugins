from Components.Sources.Source import Source


class VariableProgressSource(Source):
	"""Source to feed Progress Renderer from HTTPProgressDownloader"""

	def __init__(self):
		# Initialize and invalidate
		Source.__init__(self)
		self.invalidate()

	def invalidate(self):
		# Invalidate
		self.range = None
		self.value = 0
		self.factor = 1
		self.changed((self.CHANGED_CLEAR, ))

	def writeValues(self, pos, max):
		# Increase Factor as long as range is too big
		if self.range > 5000000:
			self.factor *= 500
			self.range /= 500

		# Only save range if not None
		if max is not None:
			self.range = max / self.factor

		# Save pos
		self.value = pos / self.factor

		# Trigger change
		self.changed((self.CHANGED_ALL, ))
