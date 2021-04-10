from Plugins.SystemPlugins.Toolkit.TagStrip import strip, strip_readable
from Components.Scanner import ScanFile

NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
NS_RSS_09 = "{http://my.netscape.com/rdf/simple/0.9/}"
NS_RSS_10 = "{http://purl.org/rss/1.0/}"

# based on http://effbot.org/zone/element-rss-wrapper.htm
class ElementWrapper:
	def __init__(self, element, ns=""):
		self._element = element
		self._ns = ns

	def __getattr__(self, tag):
		if tag.startswith('__'):
			raise AttributeError(tag)
		return self._element.findtext(self._ns + tag)

class RSSEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + 'enclosure'):
				length = elem.get("length")
				if length:
					length = int(length) / 1048576
				myl.append(ScanFile(
					elem.get("url"),
					mimetype=elem.get("type"),
					size=length,
					autodetect=False)
				)
			return myl
		elif tag == "id":
			return self._element.findtext(self._ns + 'guid', self.title + self.link)
		elif tag == "updated":
			tag = "lastBuildDate"
		elif tag == "summary":
			tag = "description"
		return ElementWrapper.__getattr__(self, tag)

class PEAEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "link":
			for elem in self._element.findall(self._ns + tag):
				if not elem.get("rel") == "enclosure":
					return elem.get("href")
			return ''
		elif tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + 'link'):
				if elem.get("rel") == "enclosure":
					length = elem.get("length")
					if length:
						length = int(length) / 1048576
					myl.append(ScanFile(
						elem.get("href"),
						mimetype=elem.get("type"),
						size=length,
						autodetect=False
					))
			return myl
		elif tag == "summary":
			text = self._element.findtext(self._ns + 'summary')
			if not text:
				# NOTE: if we don't have a summary we use the full content instead
				elem = self._element.find(self._ns + 'content')
				if elem is not None and elem.get('type') == "html":
					text = elem.text
			return text

		return ElementWrapper.__getattr__(self, tag)

class RSSWrapper(ElementWrapper):
	def __init__(self, channel, items, ns=""):
		self._items = items
		ElementWrapper.__init__(self, channel, ns)

	def __iter__(self):
		self.idx = 0
		self.len = len(self)-1
		return self

	def __next__(self):
		return next(self)

	def next(self):
		idx = self.idx
		if idx > self.len:
			raise StopIteration
		self.idx = idx+1
		return self[idx]

	def __len__(self):
		return len(self._items)

	def __getitem__(self, index):
		return RSSEntryWrapper(self._items[index], self._ns)

class RSS1Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		RSSWrapper.__init__(
			self, feed.find(ns + 'channel'),
			feed.findall(ns + 'item'), ns
		)

	def __getattr__(self, tag):
		if tag == 'logo': # XXX: afaik not officially part of older rss, but can't hurt
			tag = 'image'
		return ElementWrapper.__getattr__(self, tag)

class RSS2Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		channel = feed.find("channel")
		RSSWrapper.__init__(
			self, channel, channel.findall("item")
		)

	def __getattr__(self, tag):
		if tag == 'logo':
			tag = 'image'
		return ElementWrapper.__getattr__(self, tag)

class PEAWrapper(RSSWrapper):
	def __init__(self, feed, ns):
		ns = feed.tag[:feed.tag.index("}")+1]
		RSSWrapper.__init__(
			self, feed, feed.findall(ns + 'entry'), ns
		)

	def __getitem__(self, index):
		return PEAEntryWrapper(self._items[index], self._ns)

	def __getattr__(self, tag):
		if tag == "description":
			tag = "subtitle"
		return ElementWrapper.__getattr__(self, tag)

class BaseFeed:
	"""Base-class for all Feeds. Initializes needed Elements."""
	MAX_HISTORY_ELEMENTS = 100

	def __init__(self, uri, title="", description=""):
		# Set URI (used as Identifier)
		self.uri = uri

		# Initialize
		self.title = title or uri.encode("UTF-8")
		self.description = description
		self.logoUrl = ''
		self.history = []

	def __str__(self):
		return "<%s, \"%s\", \"%s\", %d items>" % (self.__class__, self.title, self.description, len(self.history))

class UniversalFeed(BaseFeed):
	"""Feed which can handle rdf, rss and atom feeds utilizing abstraction wrappers."""
	def __init__(self, uri, autoupdate, sync=False):
		BaseFeed.__init__(self, uri)

		# Set Autoupdate
		self.autoupdate = autoupdate
		
		# Is this a synced feed?
		self.sync = sync

		# Initialize
		self.last_update = None
		self.last_ids = set()
		self.wrapper = None
		self.ns = ""

	def gotWrapper(self, wrapper):
		updated = wrapper.updated
		if updated and self.last_update == updated:
			return []

		idx = 0
		ids = self.last_ids
		for item in wrapper:
			# Try to read title, continue if none found
			title = strip(item.title)
			if not title:
				continue

			# Try to read id, continue if none found (invalid feed or internal error) or to be excluded
			id = item.id
			if not id or id in ids:
				continue

			# Link
			link = item.link

			# Try to read summary, empty if none
			summary = strip_readable(item.summary or "")

			# Update Lists
			self.history.insert(idx, (
					title.encode("UTF-8"),
					link.encode("UTF-8"),
					summary.encode("UTF-8"),
					item.enclosures
			))
			ids.add(id)

			idx += 1

		# Eventually cut history
		del self.history[self.MAX_HISTORY_ELEMENTS:]

		return self.history[:idx]

	def gotFeed(self, feed):
		if self.wrapper is not None:
			wrapper = self.wrapper(feed, self.ns)
		else:
			if feed.tag == "rss":
				self.wrapper = RSS2Wrapper
			elif feed.tag.startswith(NS_RDF):
				self.ns = NS_RDF
				self.wrapper = RSS1Wrapper
			elif feed.tag.startswith(NS_RSS_09):
				self.ns = NS_RSS_09
				self.wrapper = RSS1Wrapper
			elif feed.tag.startswith(NS_RSS_10):
				self.ns = NS_RSS_10
				self.wrapper = RSS1Wrapper
			elif feed.tag.endswith("feed"):
				self.wrapper = PEAWrapper
			else:
				raise NotImplementedError('Unsupported Feed: %s' % feed.tag)

			wrapper = self.wrapper(feed, self.ns)

			self.title = strip(wrapper.title).encode("UTF-8")
			self.description = strip_readable(wrapper.description or "").encode("UTF-8")
			self.logoUrl = wrapper.logo

		return self.gotWrapper(wrapper)

