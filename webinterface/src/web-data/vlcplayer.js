var vlc = '';
// current EPG Template
var tplVLCEPGItem = '<div class="currentServiceEPGStarttime">%(starttime)</div><div  class="currentServiceEPGTitle">%(title)</div><div class="currentServiceEPGDuration">%(duration)&nbsp;Min.</div>';


function getVersion() {
	var vstr = vlc.VersionInfo;
	var words = vstr.split(" ");
	return words[0];
}


function onServiceSelected(){
	var servicereference =$('channelSelect').options[$('channelSelect').selectedIndex].id;
//	$('currentName').innerHTML = $('channelSelect').options[$('channelSelect').selectedIndex].value;

	loadEPG(servicereference);	
	setStreamTarget(servicereference);
}

function onBouquetSelected(){	
	var servicereference =$('bouquetSelect').options[$('bouquetSelect').selectedIndex].id;	
	loadVLCBouquet(servicereference);
}

function loadEPG(servicereference){
	doRequest(url_epgservice+servicereference, incomingVLCServiceEPG);
}

function incomingVLCEpgNow(request){
	if (request.readyState == 4) {
		var events = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");			

		var namespace = [];

		for(var i = 0; i < events.length; i++){
			var event = new EPGEvent(events.item(i));
			var eventname = event.getTitle();
		
			if(eventname.length > 40){
				eventname = eventname.substring(0, 40) + '...';
			}
			
			namespace[i] = {
			 	'servicereference' : event.getServiceReference(),
			 	'servicename' : event.getServiceName(),
			 	'eventname' : eventname,
				'duration' : ( parseInt( (event.duration/60) , 10) )
			};
		}
		
		var data = { 'services' : namespace };		
		processTpl('streaminterface/tplServiceList', data, 'channelList');
	}	
}

function loadVLCEpgNow(bouquetreference){
	doRequest(url_epgnow+bouquetreference, incomingVLCEpgNow);
}


function incomingVLCServiceEPG(request){
	if (request.readyState == 4) {
		var events = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");			
		
		var event =new EPGEvent(events.item(0));
		var namespace = {
				'servicename' : event.getServiceName(),
			 	'eventname': event.getTitle(),
				'duration': ( parseInt( (event.duration/60) , 10) )				
				};
		
		var data = { 'current' : namespace };		
		processTpl('streaminterface/tplCurrent', data, 'current');		
	}
}

function incomingVLCBouquetList(request){
	if (request.readyState == 4) {
		var bouquets = new ServiceList(getXML(request)).getArray();
		
		var namespace = [];
		for(var i = 0; i < bouquets.length; i++){
			var bouquet = bouquets[i];
			
			namespace[i] = {
					"servicereference" 	: bouquet.getServiceReference(),
					"servicename"	 	: bouquet.getServiceName()
			};
		}
		data = { bouquets : namespace };
		
		processTpl('streaminterface/tplBouquetList', data, 'bouquetList');
		loadVLCBouquet(bouquets[0].getServiceReference());
	}
}


function loadVLCBouquet(servicereference){ 
	loadVLCEpgNow(servicereference);	
}

function incomingVLCChannellist(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
				
		debug("got "+services.length+" Services");
		
		namespace = [];
		
		for ( var i = 0; i < services.length ; i++){
			var service = services[i];
			namespace[i] = { 	'servicereference': service.getServiceReference(),
								'servicename': service.getServiceName() 
							};
			
			
		}
		var data = { services : namespace };
		
		processTpl('streaminterface/tplServiceList', data, 'channelList');		
	}
}

function vlcPlay(){
	try{
		onServiceSelected();
	} catch(e){
		notify("Nothing to play", false);
	}
}

function vlcPrev(){
	if(	$('channelSelect').selectedIndex > 0 ){	
		$('channelSelect').selectedIndex -= 1;
		onServiceSelected();
	}
}

function vlcNext(){
	if($('channelSelect').selectedIndex < $('channelSelect').length - 1 ){
		$('channelSelect').selectedIndex += 1;
		onServiceSelected();
	}
}

function vlcPause(){
	vlc.playlist.togglePause();
}

function vlcStop(){
	try{
		vlc.playlist.stop();
	} catch(e) {
		notify("Nothing to stop", false);
	}
}

function vlcVolumeUp(){
	if(vlc.audio.volume < 200){
		if(vlc.audio.volume + 10 > 200){
			vlc.audio.volume = 200;
		} else {
			vlc.audio.volume += 10;
		}
	}
	
	set('vlcVolume', vlc.audio.volume);
}

function vlcVolumeDown(){
	if(vlc.audio.volume > 0){
		if(vlc.audio.volume < 10){
			vlc.audio.volume = 0;
		} else {
			vlc.audio.volume -= 10;
		}
	}
	
	set('vlcVolume', vlc.audio.volume);
}

function vlcToogleMute(){
	vlc.audio.mute = !vlc.audio.mute;
	if(vlc.audio.mute){
		set('vlcVolume', 'Muted');
	} else {
		set('vlcVolume', vlc.audio.volume);
	}
}

function vlcFullscreen(){	
	if(vlc.playlist.isPlaying){
		if(vlc.input.hasVout){
			vlc.video.fullscreen = true;
			return;
		} 
	}

	notify("Cannot enable fullscreen mode when no Video is being played!", false);
}

function vlcTeletext(){
	try{
		vlc.video.teletext = 100;
	} catch(e) {
		debug("Error - Could not set teletext");
	}
	debug("Current Teletext Page:" + vlc.video.teletext);
}

function setStreamTarget(servicereference){
	host = top.location.host;
	
	url = 'http://'+host+':8001/'+decodeURIComponent(servicereference);
	debug("setStreamTarget " + url);
	
	vlc.playlist.add(url);
	
	if(vlc.playlist.isPlaying){
		vlc.playlist.next();
	} else {
		vlc.playlist.play();
	}
}

function loadBouquets(){
	url = url_getServices + bouquetsTv;
	doRequest(url, incomingVLCBouquetList);
}

function initWebTv(){
	if(DBG){
		loadAndOpenDebug();		
	}
	
	vlc = $("vlc");
	
	try{
		set('vlcVolume', vlc.audio.volume);
	} catch (e){}
//	vlc.log.verbosity = 0;
	loadBouquets();
}


