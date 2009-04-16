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
	$('currentName').innerHTML = $('channelSelect').options[$('channelSelect').selectedIndex].value;

	//	loadEPG(servicereference);	
	setStreamTarget(servicereference);
}

function onBouquetSelected(){	
	var servicereference =$('bouquetSelect').options[$('bouquetSelect').selectedIndex].id;	
	loadVLCBouquet(servicereference);
}

function loadEPG(servicereference){
	doRequest(url_epgservice+servicereference, incomingVLCServiceEPG);
}
 
function incomingVLCServiceEPG(request){
	if (request.readyState == 4) {
		var EPGItems = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");			
		var epg_current =new EPGEvent(EPGItems.item(0));
		var namespace = {
			 	'title': epg_current.getTitle(),
				'starttime': epg_current.getTimeStartString(),
				'duration': (parseInt(epg_current.duration)/60)				
				};
//		$('CurrentEvent').innerHTML =  RND(tplVLCEPGItem, namespace);
		
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
	servicereftoloadepgnow = servicereference;
	doRequest(url_getServices+servicereference, incomingVLCChannellist);
}

function incomingVLCChannellist(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
				
		debug("got "+services.length+" Services");
		
		namespace = [];
		
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			namespace[i] = { 	'servicereference': reference.getServiceReference(),
								'servicename': reference.getServiceName() 
							};
			
			
		}
		var data = { services : namespace };
		
		processTpl('streaminterface/tplServiceList', data, 'channelList');		
	}
}

function vlcPlay(){
	onServiceSelected();
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
	vlc.playlist.stop();
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
	try{
		vlc.video.fullscreen = true;
	}catch(e){
		debug(e);
	}
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
	set('vlcVolume', vlc.audio.volume);
//	vlc.log.verbosity = 0;
	loadBouquets();
}


