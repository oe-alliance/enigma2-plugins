var vlc = '';
var currentServiceRef = '';
var bouquetUpdatePoller = '';
var currentBouquetRef = '';
/*
 * incoming request-data for Current Service Epg
 */
function incomingVLCServiceEPG(request) {
	if (request.readyState == 4) {
		var events = getXML(request).getElementsByTagName("e2eventlist")
				.item(0).getElementsByTagName("e2event");

		var event = new EPGEvent(events.item(0)).toJSON();

		var data = {
			'current' : event
		};
		processTpl('streaminterface/tplCurrent', data, 'current');
	}
}

/*
 * Load Now information for Service
 */
function loadVLCEPGServiceNow(servicereference) {
	doRequest(URL.epgservicenow + servicereference, incomingVLCServiceEPG);
}

function onServiceSelected() {
	currentServiceRef = $('channelSelect').options[$('channelSelect').selectedIndex].id;
	
	if(currentServiceRef !== "vlcemptyservice"){
		loadVLCEPGServiceNow(currentServiceRef);
		setStreamTarget(currentServiceRef);
		
		if($('vlcZap').checked){			
			doRequest("/web/zap?sRef=" + currentServiceRef);			
		}
		delayedLoadVlcSubservices();
	} else {
		vlcStop();
	}
}

function incomingVLCBouquetList(request) {
	if (request.readyState == 4) {
		var services = new ServiceList(getXML(request)).getArray();

		data = {
			bouquets : services
		};

		processTpl('streaminterface/tplBouquetList', data, 'bouquetList');
		loadVLCBouquet(services[0].servicereference);
	}
}
function reloadVLCBouquet(){
	loadVLCBouquet(currentBouquetRef);
}


function loadVLCBouquet(servicereference) {
//	clearInterval(bouquetUpdatePoller);	
	currentBouquetRef = servicereference;
	
	loadVLCChannelList(servicereference);
	
//	bouquetUpdatePoller = setInterval(reloadVLCBouquet, 30000);
}

function incomingVLCSubservices(request){
	if (request.readyState == 4) {
		var services = new ServiceList(getXML(request)).getArray();
		debug("[incomincVLCSubservices] Got " + services.length + " SubServices");
		
		if(services.length > 1) {

			var first = services[0];
			
			var lastoption = $(services[0].servicereference);
			
			if(lastoption !== null){
				// we already have the main service in our servicelist so we'll
				// start with the second element
				for ( var i = 1; i < services.length ; i++){
					var service = services[i];
					
					//TODO: FIX THIS UGLY CODE
					var option = $(service.servicereference);
					if(option !== null){
						option.remove();
					}
					option = new Option(' |- ' + service.servicename);
					option.id =  service.servicereference;
					
					lastoption.insert( { after : option } );
					
					lastoption = option;
				}
			}
		}
	}
}

function loadVlcSubservices(){
	var url = URL.streamsubservices + currentServiceRef;
	doRequest(url, incomingVLCSubservices);
}

function delayedLoadVlcSubservices(){
	setTimeout(loadVlcSubservices, 7500);
}

/*
 * Incoming request-data for EPG Now information
 * Builds the Channellist
 */
function incomingVLCChannelList(request) {
	if (request.readyState == 4) {
		var events = new EPGList(getXML(request)).getArray();

		var data = {
			'events' : events
		};
		processTpl('streaminterface/tplServiceList', data, 'channelList');
	}
}

/*
 * Load List of all Channels with epg now where available
 */
function loadVLCChannelList(bouquetreference) {
	doRequest(URL.epgnow + bouquetreference, incomingVLCChannelList);
}

function vlcPlay() {
	try {
		onServiceSelected();
	} catch (e) {
		notify("Nothing to play", false);
	}
}

function vlcPrev() {
	if ($('channelSelect').selectedIndex > 0) {
		$('channelSelect').selectedIndex -= 1;
		onServiceSelected();
	}
}

function vlcNext() {
	if ($('channelSelect').selectedIndex < $('channelSelect').length - 1) {
		$('channelSelect').selectedIndex += 1;
		onServiceSelected();
	}
}

function vlcPause() {
	vlc.playlist.togglePause();
}

function vlcStop() {
	try {
		vlc.playlist.stop();
	} catch (e) {
		notify("Nothing to stop", false);
	}
}

function vlcVolumeUp() {
	if (vlc.audio.volume < 200) {
		if (vlc.audio.volume + 10 > 200) {
			vlc.audio.volume = 200;
		} else {
			vlc.audio.volume += 10;
		}
	}

	set('vlcVolume', vlc.audio.volume);
}

function vlcVolumeDown() {
	if (vlc.audio.volume > 0) {
		if (vlc.audio.volume < 10) {
			vlc.audio.volume = 0;
		} else {
			vlc.audio.volume -= 10;
		}
	}

	set('vlcVolume', vlc.audio.volume);
}

function vlcToogleMute() {
	vlc.audio.mute = !vlc.audio.mute;
	if (vlc.audio.mute) {
		set('vlcVolume', 'Muted');
	} else {
		set('vlcVolume', vlc.audio.volume);
	}
}

function vlcFullscreen() {
	if (vlc.playlist.isPlaying) {
		if (vlc.input.hasVout) {
			vlc.video.fullscreen = true;
			return;
		}
	}

	notify("Cannot enable fullscreen mode when no Video is being played!",
			false);
}

function vlcTeletext() {
	try {
		vlc.video.teletext = 100;
	} catch (e) {
		debug("Error - Could not set teletext");
	}
	debug("Current Teletext Page:" + vlc.video.teletext);
}

function playUrl(url) {
	current = vlc.playlist.add(url);
	vlc.playlist.playItem(current);
}

function setStreamTarget(servicereference) {
	host = top.location.host;
	url = 'http://' + host + ':8001/' + decodeURIComponent(servicereference);

	debug("setStreamTarget " + url);
	vlc.playlist.clear();
	playUrl(url);
}

function loadVLCBouquets() {
	url = URL.getservices + bouquetsTv;
	doRequest(url, incomingVLCBouquetList);
	
}

/*
 * Event when the user selected a Bouquet in the bouquets <select>
 */
function onBouquetSelected() {
	var servicereference = $('bouquetSelect').options[$('bouquetSelect').selectedIndex].id;
	loadVLCBouquet(servicereference);
}

function initWebTv() {
	var DBG = userprefs.data.debug || false;
	if (DBG) {
		openDebug();
	}

	vlc = $('vlc');

	try {
		set('vlcVolume', vlc.audio.volume);
	} catch (e) {
		debug('[initWebTv] Error on initializing WebTv');
	}

	loadVLCBouquets();
}
