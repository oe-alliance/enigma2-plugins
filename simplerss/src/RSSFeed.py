from sets import Set
from TagStrip import strip, strip_readable
from Components.Scanner import ScanFile

NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
NS_RSS_09 = "{http://my.netscape.com/rdf/simple/0.9/}"
NS_RSS_10 = "{http://purl.org/rss/1.0/}"

# based on http://effbot.org/zone/element-rss-wrapper.htm
class ElementWrapper:
	def __init__(self, element, ns = ""):
		self._element = element
		self._ns = ns

	def __getattr__(self, tag):
		if tag.startswith("__"):
			raise AttributeError(tag)
		return self._element.findtext(self._ns + tag)

class RSSEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + "enclosure"):
				length = elem.get("length")
				if length:
					length = int(length) / 1048576
				myl.append({
					"href": elem.get("url"),
					"type": elem.get("type"),
					"length": length
					})
			return myl
		if tag == "id":
			possibleId = self._element.findtext(self._ns + "guid")
			if not possibleId:
				possibleId = ''.join([self.title, self.link])
			return possibleId
		if tag == "updated":
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
			return ""
		if tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + "link"):
				if elem.get("rel") == "enclosure":
					length = elem.get("length")
					if length:
						length = int(length) / 1048576
					myl.append({
						"href": elem.get("href"),
						"type": elem.get("type"),
						"length": length
						})
			return myl
		return ElementWrapper.__getattr__(self, tag)

class RSSWrapper(ElementWrapper):
	def __init__(self, channel, items, ns = ""):
		self._items = items
		ElementWrapper.__init__(self, channel, ns)

	def __iter__(self):
		return iter([self[i] for i in range(len(self))])

	def __len__(self):
		return len(self._items)

	def __getitem__(self, index):
		return RSSEntryWrapper(self._items[index], self._ns)

class RSS1Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		RSSWrapper.__init__(
			self, feed.find(ns + "channel"),
			feed.findall(ns + "item"), ns
			)

class RSS2Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		channel = feed.find("channel")
		RSSWrapper.__init__(
			self, channel, channel.findall("item")
			)

class PEAWrapper(RSSWrapper):
	def __init__(self, feed, ns):
		ns = feed.tag[:feed.tag.index("}")+1]
		RSSWrapper.__init__(
			self, feed, feed.findall(ns + "entry"), ns
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

	def __init__(self, uri, title = "", description = ""):
		# Set URI (used as Identifier)
		self.uri = uri

		# Initialize
		self.title = title or uri.encode("UTF-8")
		self.description = description
		self.history = []

	def __str__(self):
		return "<%s, \"%s\", \"%s\", %d items>" % (self.__class__, self.title, self.description, len(self.history))

class UniversalFeed(BaseFeed):
	"""Feed which can handle rdf, rss and atom feeds utilizing abstraction wrappers."""
	def __init__(self, uri, autoupdate):
		BaseFeed.__init__(self, uri)

		# Set Autoupdate
		self.autoupdate = autoupdate

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
		for item in wrapper:
			enclosures = []
			link = ""
			
			# Try to read title, continue if none found
			title = strip(item.title)
			if not title:
				continue

			# Try to read id, continue if none found (invalid feed or internal error) or to be excluded
			id = item.id
			if not id or id in self.last_ids:
				continue

			# Link
			link = item.link

			# Read out enclosures and link
			for enclosure in item.enclosures:
				enclosures.append(ScanFile(enclosure["href"], mimetype = enclosure["type"], size = enclosure["length"], autodetect = False))
			
			# Try to read summary, empty if none
			summary = strip_readable(item.summary)

			# Update Lists
			self.history.insert(idx, (
					title.encode("UTF-8"),
					link.encode("UTF-8"),
					summary.encode("UTF-8"),
					enclosures
			))
			self.last_ids.add(id)
			
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
				raise NotImplementedError, 'Unsupported Feed: %s' % feed.tag

			wrapper = self.wrapper(feed, self.ns)

			self.title = strip(wrapper.title).encode("UTF-8")
			self.description = strip_readable(wrapper.description or "").encode("UTF-8")

		return self.gotWrapper(wrapper)

