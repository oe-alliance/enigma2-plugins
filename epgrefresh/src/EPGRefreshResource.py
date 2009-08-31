from twisted.web import http, resource
from EPGRefresh import epgrefresh
from EPGRefreshService import EPGRefreshService
from enigma import eServiceReference

# pretty basic resource which is just present to have a way to start a
# forced refresh through the webif
class EPGRefreshResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		do_add = req.args.has_key("add")
		do_del = req.args.has_key("del")
		state = False

		if req.args.has_key("refresh"):
			# forced refresh
			if epgrefresh.forceRefresh():
				output = "initiated refresh"
				state = True
			else:
				output = "could not initiate refresh"
		elif do_add or do_del:
			# add/remove service/bouquet
			if do_add:
				sref = req.args["add"][0]
				# strip all after last : (custom name)
				pos = sref.rfind(':')
				if pos != -1:
					sref = sref[:pos+1]
			else:
				sref = req.args["del"][0]

			duration = req.args.get("duration", None)
			duration = duration and int(duration)
			epgservice = EPGRefreshService(sref, duration)

			if sref:
				ref = eServiceReference(str(sref))
				if not ref.valid():
					output = "invalid argument"
				elif (ref.flags & 7) == 7:
					# bouquet
					if epgservice in epgrefresh.services[1]:
						if do_add:
							output = "bouquet already in list"
						else:
							epgrefresh.services[1].remove(epgservice)
							output = "bouquet removed from list"
							state = True
					else:
						if do_del:
							output = "bouquet not in list"
						else:
							epgrefresh.services[1].add(epgservice)
							output = "bouquet added to list"
							state = True
				else:
					# assume service
					if epgservice in epgrefresh.services[0]:
						if do_add:
							output = "service already in list"
						else:
							epgrefresh.services[0].remove(epgservice)
							output = "service removed from list"
							state = True
					else:
						if do_del:
							output = "service not in list"
						else:
							epgrefresh.services[0].add(epgservice)
							output = "service added to list"
							state = True

				# save if list changed
				if state:
					epgrefresh.saveConfiguration()
			else:
				output = "invalid argument"
		elif req.args.has_key("list"):
			# show xml
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'application; xhtml+xml')
			req.setHeader('charset', 'UTF-8')
			return ''.join(epgrefresh.buildConfiguration())
		else:
			output = "unknown command"

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if state else 'false', output)

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return result
