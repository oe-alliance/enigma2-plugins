var list_tv_loaded = false;
var list_radio_loaded = false;
var list_provider_tv_loaded = false;
var list_provider_radio_loaded = false;


// Bouquetlist Template
var tplVLCBouquetListHeader = '<table id="BouquetList" width="100%" border="0" cellspacing="1" cellpadding="0" border="0">';
var tplVLCBouquetListItem  = '<tr>\n';
	tplVLCBouquetListItem += '<td><div class="navMenuItem" id="%(servicereference)" onclick="loadVLCBouquet(this.id);">%(bouquetname)</div></td>';
	tplVLCBouquetListItem += '</tr>\n';

var tplVLCBouquetListFooter = "</table>";

// Bouquetlist Template
var tplVLCServiceListHeader = '<select id="channelselect" onChange="onServiceSelected()" width="150px"><option selected>choose Service</option>';

var tplVLCServiceListItem  = '<option id="%(servicereference)" >%(servicename)</option>';

var tplVLCServiceListFooter = "</select>";

// current EPG Template
var tplVLCEPGItem = '<div class="currentServiceEPGStarttime">%(starttime)</div><div  class="currentServiceEPGTitle">%(title)</div><div class="currentServiceEPGDuration">%(duration)&nbsp;Min.</div>';

function isIE(){
	if(navigator.userAgent.indexOf("MSIE") >=0){ 
    	return true;
	}else{
		return false;
	}
	
}
function getVersion() {
	if(isIE()){
		var vstr = document.vlc.VersionInfo;
		var words = vstr.split(" ");
		return words[0];
	}else if(navigator.plugins) {
		var plug = navigator.plugins['VLC multimedia plugin'];
		if(typeof plug == 'undefined')
			var plug = navigator.plugins['VLC Multimedia Plugin'];
		var ex = /^.*[vV]ersion [\"]*([^ \"]*)[\"]*.*$/;
		var ve = ex.exec(plug.description);
		if(ve[1]){
			return ve[1];
		}else{
			return "0.0.0";
		}
	}else{
		return "0.0.0";
	}
}
function plugintype(){
		var ex = /([^\.]*)[\.]*([^\.]*)[\.]*([^\.-]*)[\.-]*([^\.]*).*$/;
		var ve = ex.exec(getVersion());
		if(ve.length >1)	version_level1 = ve[1];
		if(ve.length >2)	version_level2 = ve[2];
		if(ve.length >3 && ve[3] != "")	version_level3 = ve[3];
		if(ve.length >4 && ve[4] != "")	version_level4 = ve[4];
		if(isIE())
			return "ie1";
		else
			if(version_level1 <= "0" && version_level2 <= "8" && version_level3 <= "5")
				return "moz1";
			else
				return "moz2";
}
function onStart(){
	DBG = true;
	DBG = false;
	if(DBG) { debugWin = openWindow("DEBUG", "", 300, 300, "debugWindow"); }
	debug("startup");

var accordionOptions = {
	expandedBg : 'transparent',
	hoverBg : 'CCCCCC',
	collapsedBg : 'transparent',
	expandedTextColor : '#000000',
	expandedFontWeight : 'bold',
	hoverTextColor : '#000000',
	collapsedTextColor : '#000000',
	collapsedFontWeight : 'normal',
	borderColor : '#EEEEEE',
	border : '0',
	panelHeight : 150
}

new Rico.Accordion( $('accordionMenue'), accordionOptions );
	
	var url = url_getServices+encodeURIComponent(bouqet_tv);
	doRequest(url, incomingVLCTVBouquetList);

	var url = url_getServices+encodeURIComponent(bouqet_radio);
	doRequest(url, incomingVLCRadioBouquetList);

	var url = url_getServices+encodeURIComponent(bouqet_provider_tv);
	doRequest(url, incomingVLCProviderTVBouquetList);

	var url = url_getServices+encodeURIComponent(bouqet_provider_radio);
	doRequest(url, incomingVLCProviderRadioBouquetList);
	buildButtons();
	buildplayer(550,412);
//	buildplayer(720,576);
	debug("VLC-Version: "+getVersion()+" "+plugintype());
	
}
function onServiceSelected(){
	var index = $('channelselect').selectedIndex;
	var servicereference = $('channelselect').options[index].id;
	$('CurrentService').innerHTML = $('channelselect').options[index].text;
	loadEPG(servicereference);
	setStreamTarget(servicereference);
}
function loadEPG(servicereference){
	doRequest(url_epgservice+servicereference, incomingVLCServiceEPG);
}
 
function incomingVLCServiceEPG(request){
	if (request.readyState == 4) {
		var EPGItems = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");			
		var epg_current =new EPGEvent(EPGItems.item(0))
		var namespace = {
			 	'title': epg_current.getTitle(),
				'starttime': epg_current.getTimeStartString(),
				'duration': (parseInt(epg_current.duration)/60)				
				};
		$('CurrentEvent').innerHTML =  RND(tplVLCEPGItem, namespace);
		
	}
}
function incomingVLCTVBouquetList(request){
	if (request.readyState == 4) {
		var list_tv = new ServiceList(getXML(request)).getArray();
		list_provider_tv_loaded = true;		
		$('accordionMenueBouquetContentTV').innerHTML = renderBouquetTable(list_tv,tplVLCBouquetListHeader,tplVLCBouquetListItem,tplVLCBouquetListFooter);
		loadVLCBouquet(list_tv[0].getServiceReference());
	}
}
function incomingVLCRadioBouquetList(request){
	if (request.readyState == 4) {
		var list_radio = new ServiceList(getXML(request)).getArray();
		list_radio_loaded = true;
		$('accordionMenueBouquetContentRadio').innerHTML = renderBouquetTable(list_radio,tplVLCBouquetListHeader,tplVLCBouquetListItem,tplVLCBouquetListFooter);
	}
}
function incomingVLCProviderTVBouquetList(request){
	if (request.readyState == 4) {
		var list_provider_tv = new ServiceList(getXML(request)).getArray();
		list_provider_tv_loaded = false;
		$('accordionMenueBouquetContentProviderTV').innerHTML = renderBouquetTable(list_provider_tv,tplVLCBouquetListHeader,tplVLCBouquetListItem,tplVLCBouquetListFooter);
	}
}
function incomingVLCProviderRadioBouquetList(request){
	if (request.readyState == 4) {
		var list_provider_radio = new ServiceList(getXML(request)).getArray();
		list_provider_radio_loaded = true;
		$('accordionMenueBouquetContentProviderRadio').innerHTML = renderBouquetTable(list_provider_radio,tplVLCBouquetListHeader,tplVLCBouquetListItem,tplVLCBouquetListFooter);
	}
}
function loadVLCBouquet(servicereference){ 
	debug("loading bouquet with "+servicereference);
	servicereftoloadepgnow = servicereference;
	doRequest(url_getServices+servicereference, incomingVLCChannellist);
}
function incomingVLCChannellist(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		listerHtml 	= tplVLCServiceListHeader;		
		debug("got "+services.length+" Services");
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			var namespace = { 	'servicereference': reference.getServiceReference(),
								'servicename': reference.getServiceName() 
							};
			listerHtml += RND(tplVLCServiceListItem, namespace);
		}		
		listerHtml += tplVLCServiceListFooter;
		document.getElementById('VLCChannellist').innerHTML = listerHtml;
	}
}

function buildplayer( width, height){
	if(isIE()){ 
    	buildPlayerIE( width, height);
	}else{
		buildPlayer( width, height);
	}
}

function buildPlayer( width, height){
 	var html  = '<embed type="application/x-vlc-plugin" ';
    	html += '    id="vlc"'; 
    	html += '    autoplay="yes" loop="yes"'; 
        html += '    width="'+width+'"';
        html += '    height="'+height+'"';
        html += '  ></embed>';
	$('vlcplayer').innerHTML =html;
}
 
function buildPlayerIE( width, height){
	var html  = '<OBJECT classid="clsid:E23FE9C6-778E-49D4-B537-38FCDE4887D8"'; 
    	html += '          codebase="cab/axvlc.cab"';
    	html += '          width="' + width + '"';
    	html += '          height="'+ height +'"'; 
    	html += '          id="vlc" ';
    	html += '          events="True" >'; 
    	html += '    <param name="Src" value="" />'; 
    	html += '    <param name="Visible" value="True" />'; 
    	html += '    <param name="AutoLoop" value="False" />';
    	html += '    <param name="AutoPlay" value="False" />'; 
    	html += '</OBJECT>';
	$('vlcplayer').innerHTML = html;
}

function buildButtons(){
	//TODO use nice GFX for buttons
	var htmlbuttons  = '<button onClick="prev()">&lt;&lt;</button>';
		htmlbuttons += '<button onClick="play()">&gt;</button>';
		htmlbuttons += '<button onClick="next()">&gt;&gt;</button>';
		htmlbuttons += '<button onClick="pause()">||</button>';
		htmlbuttons += '<button onClick="stop()">stop</button>';
		htmlbuttons += '<button onClick="fullscreen()">Fullscreen</button>';
		htmlbuttons += '<button onClick="volumeUpVLC()">Vol+</button>';
		htmlbuttons += '<button onClick="muteVLC()">Mute</button>';
		htmlbuttons += '<button onClick="volumeDownVLC()">Vol-</button>';
		htmlbuttons += '<div id="VLCChannellist"></div>';

	$('vlcbuttons').innerHTML = htmlbuttons;
}


function play(){
	if(isIE()){
		document.vlc.play();
	}else{
		document.vlc.play();
	}
}
function pause(){
	if(isIE()){
		document.vlc.playlist.togglePause()
	}else{
		document.vlc.pause();
	}
}
function stop(){
	if(isIE()){
		debug("ie stop");
		document.vlc.stop();
	}else{
		document.vlc.stop();
	}
}
function volumeUpVLC(){
	debug("volumeUpVLC");	
}
function volumeDownVLC(){
	debug("volumeUpVLC");
}
function muteVLC(){
	debug("muteVLC");
	if(isIE()) {
		document.vlc.toggleMute();
	}else{
		document.vlc.mute();
	}
}
function fullscreen(){
	try{
		if(isIE()) {
			document.vlc.fullscreen();
		}else{
			document.vlc.fullscreen();
		}
	}catch(e){debug(e);}
}
function setStreamTarget(servicereference){
	debug("setStreamTarget "+servicereference);
	url = '/web/stream.m3u?ref='+decodeURIComponent(servicereference);
	if(isIE()){
		debug("ie setStreamTarget");
		document.vlc.playlistClear();
		document.vlc.addTarget(url, null, 2,0);
		play();
				
	}else{
		document.vlc.clear_playlist();
		document.vlc.add_item(url);
		play();
	}

}
