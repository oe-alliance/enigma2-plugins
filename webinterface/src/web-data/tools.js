//$Header$

// replace ' with \' for in-html javascript
String.prototype.esc = function(){ return this.valueOf().gsub("'", "\\'"); };

var templates = {};
var loadedChannellist = {};

var epgListData = {};
var signalPanelData = {};

var mediaPlayerStarted = false; 
var popUpBlockerHinted = false;

var settings = null;
var parentControlList = null;

var requestcounter = 0;

var debugWin = '';
var signalWin = '';
var webRemoteWin = '';
var EPGListWin = '';

var currentBouquet = bouquetsTv;

var updateBouquetItemsPoller = '';
var updateCurrentPoller = '';
var signalPanelUpdatePoller = '';

var hideNotifierTimeout = '';

var isActive = {};
isActive.getCurrent = false;

var currentLocation = "/hdd/movie";
var locationsList = [];
var tagsList = [];

var boxtype = "";

function startUpdateCurrentPoller(){
	clearInterval(updateCurrentPoller);
	updateCurrentPoller = setInterval(updateItems, userprefs.data.updateCurrentInterval);
}

function stopUpdateCurrentPoller(){
	clearInterval(updateCurrentPoller);
}

function getXML(request){
	var xmlDoc = "";

	if(window.ActiveXObject){ // we're on IE
		xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
		xmlDoc.async="false";
		xmlDoc.loadXML(request.responseText);
	} else { //we're not on IE
		if (!window.google || !google.gears){
			xmlDoc = request.responseXML;
		} else { //no responseXML on gears
			xmlDoc = (new DOMParser()).parseFromString(request.responseText, "text/xml");
		}
	}

	return xmlDoc;
}
/*
* Set boxtype Variable for being able of determining model specific stuff correctly (like WebRemote)
*/
function incomingDeviceInfoBoxtype(request){
	debug("[incomingAboutBoxtype] returned");
	boxtype = getXML(request).getElementsByTagName("e2devicename").item(0).firstChild.data;

	debug("[incomingAboutBoxtype] Boxtype: " + boxtype);
}


function getBoxtype(){
	doRequest(URL.deviceinfo, incomingDeviceInfoBoxtype, false);	
}

function toggleStandby(){
	sendPowerState(0);
}

function incomingPowerState(request){
	var standby = getXML(request).getElementsByTagName("e2instandby").item(0).firstChild.data;
	
	var signal = $('openSignalPanel');
	var signalImg = $('openSignalPanelImg');
	
	if(standby.strip() == "false"){
		signal.stopObserving('click', openSignalPanel);
		signal.observe('click', openSignalPanel);
		
		signalImg.src = "/web-data/img/signal.png";
		signalImg.title = "Show Signal Panel";
		
	} else {
		signal.stopObserving('click', openSignalPanel);		
		
		signalImg.src = "/web-data/img/signal_off.png";
		signalImg.title = "Please disable standby first";
	}
}

function getPowerState(){
	doRequest(URL.powerstate, incomingPowerState);	
}

function set(element, value){
	element = parent.$(element);
	if (element){
		element.update(value);
	}
}

function hideNotifier(){
	$('notification').fade({duration : 0.5 });
}

function notify(text, state){
	notif = $('notification');

	if(notif !== null){
		//clear possibly existing hideNotifier timeout of a previous notfication
		clearTimeout(hideNotifierTimeout);
		if(state === false){
			notif.style.background = "#C00";
		} else {
			notif.style.background = "#85C247";
		}				

		set('notification', "<div>"+text+"</div>");
		notif.appear({duration : 0.5, to: 0.9 });
		hideNotifierTimeout = setTimeout(hideNotifier, 10000);
	}
}


function simpleResultHandler(simpleResult){
	notify(simpleResult.getStateText(), simpleResult.getState());
}


function startUpdateBouquetItemsPoller(){
	debug("[startUpdateBouquetItemsPoller] called");
	clearInterval(updateBouquetItemsPoller);
	updateBouquetItemsPoller = setInterval(updateItemsLazy, userprefs.data.updateBouquetInterval);
}


function stopUpdateBouquetItemsPoller(){
	debug("[stopUpdateBouquetItemsPoller] called");
	clearInterval(updateBouquetItemsPoller);
}


//General Helpers
function parseNr(num) {
	if(isNaN(num)){
		return 0;
	} else {
		return parseInt(num);
	}
}


function dec2hex(nr, len){

	var hex = parseInt(nr, 10).toString(16).toUpperCase();
	if(len > 0){
		try{
			while(hex.length < len){
				hex = "0"+hex;
			}
		} 
		catch(e){
			//something went wrong, return -1
			hex = -1;
		}
	}
	
	hex = '0x' + hex;
	
	return hex;
}


function quotes2html(txt) {
	if(typeof(txt) != "undefined"){
		return txt.escapeHTML().replace('\n', '<br>');
	} else {
		return "";
	}
}

function addLeadingZero(nr){
	if(nr < 10){
		return '0' + nr;
	}
	return nr;
}

function dateToString(date){

	var dateString = "";

	dateString += date.getFullYear();
	dateString += "-" + addLeadingZero(date.getMonth()+1);
	dateString += "-" + addLeadingZero(date.getDate());
	dateString += " " + addLeadingZero(date.getHours());
	dateString += ":" + addLeadingZero(date.getMinutes());

	return dateString;
}


function showhide(id){
	var s = $(id).style;
	s.display = (s.display!="none")? "none":"";
}


function show(id){
	try{
		$(id).style.display = "";
	} catch(e) {
		debug("[show] Could not show element with id: " + id);
	}
}


function hide(id){
	try{
		$(id).style.display = "none";
	} catch(e) {
		debug("[hide] Could not hide element with id: " + id);
	}
}


/*
* Sets the Loading Notification to the given HTML Element
* @param targetElement - The element the Ajax-Loader should be set in
*/
function setAjaxLoad(targetElement){
	$(targetElement).update( getAjaxLoad() );
}


//Ajax Request Helpers
//requestindikator

function requestIndicatorUpdate(){
	/*debug(requestcounter+" open requests");
	if(requestcounter>=1){
		$('RequestIndicator').style.display = "inline";
	}else{
		$('RequestIndicator').style.display = "none";
	}*/
}

function requestStarted(){
	requestcounter +=1;
	requestIndicatorUpdate();
}

function requestFinished(){
	requestcounter -= 1;
	requestIndicatorUpdate();
}

//Popup And Messagebox Helpers
function messageBox(m){
	alert(m);
}


function popUpBlockerHint(){
	if(!popUpBlockerHinted){
		popUpBlockerHinted = true;
		messageBox("Please disable your Popup-Blocker for enigma2 WebControl to work flawlessly!");

	}
}

function setWindowContent(window, html){
	window.document.write(html);
	window.document.close();
}

function openPopup(title, html, width, height, x, y){
	try {
		var popup = window.open('about:blank',title,'scrollbars=yes, width='+width+',height='+height);		
		setWindowContent(popup, html);
		return popup;
	} catch(e){
		popUpBlockerHint();
		return "";
	}
}

function openPopupPage(title, uri, width, height, x, y){
	try {
		var popup = window.open(uri,title,'scrollbars=yes, width='+width+',height='+height);
		return popup;
	} catch(e){
		popUpBlockerHint();
		return "";
	}
}

function debug(text){
	var DBG = userprefs.data.debug || false;
	
	if(DBG){
		try{
			if(!debugWin.closed && debugWin.location){
				var inner = debugWin.document.getElementById('debugContent').innerHTML;
				debugWin.document.getElementById('debugContent').innerHTML = new Date().toLocaleString() + ": "+text+"<br>" + inner;
			} else { 			
				openDebug();
				
				setTimeout(	function(){
									var inner = debugWin.document.getElementById('debugContent').innerHTML;
									debugWin.document.getElementById('debugContent').innerHTML = new Date().toLocaleString() + ": "+text+"<br>" + inner;
								}, 
								1000
						  	);
			}
		} catch (Exception) {}
	}
}

function saveSettings(){
	userprefs.load();
	
	var debug = $('enableDebug').checked;
	var changed = false;
	if(typeof(debug) != "undefined"){
		if( userprefs.data.debug != debug ){
			userprefs.data.debug = debug;
			changed = true;
	
			if(debug){
				openDebug();
			}
		}		
	}
	
	var updateCurrentInterval = parseNr( $F('updateCurrentInterval') ) * 1000;
	if( updateCurrentInterval < 10000){
		updateCurrentInterval = 120000;
	}
	
	if( userprefs.data.updateCurrentInterval != updateCurrentInterval){
		userprefs.data.updateCurrentInterval = updateCurrentInterval;
		
		changed = true;
		startUpdateCurrentPoller();
	}
	
	var updateBouquetInterval = parseNr( $F('updateBouquetInterval') )  * 1000;
	if( updateBouquetInterval < 60000){
		updateBouquetInterval = 300000;
	}
	
	if( userprefs.data.updateBouquetInterval != updateBouquetInterval){
		userprefs.data.updateBouquetInterval = updateBouquetInterval;
		
		changed = true;
		startUpdateBouquetItemsPoller();
	}
	
	if(changed){
		userprefs.save();
	}
}

//Template Helpers
function saveTpl(request, tplName){
	debug("[saveTpl] saving template: " + tplName);
	templates[tplName] = request.responseText;
}


function renderTpl(tpl, data, domElement) {	
	var result = tpl.process(data);

	try{
		$(domElement).update( result );
	}catch(ex){
		//		debug("[renderTpl] exception: " + ex);
	}
}


function fetchTpl(tplName, callback){
	if(typeof(templates[tplName]) == "undefined") {
		var url = URL.tpl+tplName+".htm";
		
		doRequest(
				url, 
				function(transport){
					saveTpl(transport, tplName);
					if(typeof(callback) == 'function'){
						callback();
					}
				}
		);
	} else {
		if(typeof(callback) == 'function'){
			callback();
		}
	}
}

function incomingProcessTpl(request, data, domElement, callback){
	if(request.readyState == 4){
		renderTpl(request.responseText, data, domElement);
		if(typeof(callback) == 'function') {
			callback();
		}
	}
}

function processTpl(tplName, data, domElement, callback){
	var url = URL.tpl+tplName+".htm";
	
	doRequest(url, 
			function(transport){
		incomingProcessTpl(transport, data, domElement, callback);
	}
	);
}

//Debugging Window


function openDebug(){
	var uri = URL.tpl+'tplDebug.htm';
	debugWin = openPopupPage("Debug", uri, 500, 300);
}

function requestFailed(transport){
	var notifText = "Request failed for:  " + transport.request.url + "<br>Status: " + transport.status + " " + transport.statusText;
	notify(notifText, false);
}

function doRequest(url, readyFunction){
	requestStarted();
	var request = '';
	var parms = url.toQueryParams();
	
	// gears or not that's the question here
	if (!window.google || !google.gears){ //no gears, how sad
//		debug("NO GEARS!!");		
		try{
			request = new Ajax.Request(url,
					{
						asynchronous: true,
						method: 'POST',
						parameters: parms,
						onException: function(o,e){ throw(e); },
						onSuccess: function (transport, json) {						
							if(typeof(readyFunction) != "undefined"){
								readyFunction(transport);
							}
						},
						onFailure: function(transport){
							requestFailed(transport);
						},
						onComplete: requestFinished 
					});
		} catch(e) {}
	} else { //we're on gears!
		try{
			request = google.gears.factory.create('beta.httprequest');
			request.open('GET', url);


			request.onreadystatechange = function(){				
				if(request.readyState == 4){
					if(request.status == 200){
						if( typeof(readyFunction) != "undefined" ){
							readyFunction(request);
						}
					} else {
						requestFailed(transport);
					}
				}
			};
			request.send();
		} catch(e) {}
	}
}

//Parental Control
function incomingParentControl(request) {
	if(request.readyState == 4){
		parentControlList = new ServiceList(getXML(request)).getArray();
		debug("[incomingParentControl] Got "+parentControlList.length + " services");
	}
}

function getParentControl() {
	doRequest(URL.parentcontrol, incomingParentControl, false);
}


function getParentControlByRef(txt) {
	debug("[getParentControlByRef] ("+txt+")");
	for(var i = 0; i < parentControlList.length; i++) {
		debug( "[getParentControlByRef] "+parentControlList[i].getClearServiceReference() );
		if(String(parentControlList[i].getClearServiceReference()) == String(txt)) {
			return parentControlList[i].getClearServiceReference();
		} 
	}
	return "";
}


//Settings
function getSettingByName(txt) {
	debug("[getSettingByName] (" + txt + ")");
	for(var i = 0; i < settings.length; i++) {
		debug("("+settings[i].getSettingName()+") (" +settings[i].getSettingValue()+")");
		if(String(settings[i].getSettingName()) == String(txt)) {
			return settings[i].getSettingValue().toLowerCase();
		} 
	}
	return "";
}

function parentPin(servicereference) {
	debug("[parentPin] parentControlList");
	servicereference = decodeURIComponent(servicereference);
	if(parentControlList === null || String(getSettingByName("config.ParentalControl.configured")) != "true") {
		return true;
	}
	//debug("parentPin " + parentControlList.length);
	if(getParentControlByRef(servicereference) == servicereference) {
		if(String(getSettingByName("config.ParentalControl.type.value")) == "whitelist") {
			debug("[parentPin] Channel in whitelist");
			return true;
		}
	} else {
		debug("[parentPin] sRef differs ");
		return true;
	}
	debug("[parentPin] Asking for PIN");

	var userInput = prompt('Parental Control is enabled!<br> Please enter the Parental Control PIN','PIN');
	if (userInput !== '' && userInput !== null) {
		if(String(userInput) == String(getSettingByName("config.ParentalControl.servicepin.0")) ) {
			return true;
		} else {
			return parentPin(servicereference);
		}
	} else {
		return false;
	}
}


function incomingGetDreamboxSettings(request){
	if(request.readyState == 4){
		settings = new Settings(getXML(request)).getArray();

		debug("[incomingGetDreamboxSettings] config.ParentalControl.configured="+ getSettingByName("config.ParentalControl.configured"));

		if(String(getSettingByName("config.ParentalControl.configured")) == "true") {
			getParentControl();
		}
	}
}


function getDreamboxSettings(){
	doRequest(URL.settings, incomingGetDreamboxSettings, false);
}


//Subservices
function incomingSubServiceRequest(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		debug("[incomingSubServiceRequest] Got " + services.length + " SubServices");

		if(services.length > 1) {

			var first = services[0];

			// we already have the main service in our servicelist so we'll
			// start with the second element			
			services.shift();
			
			var data = { subservices : services };
			

			var id = 'SUB'+first.servicereference;
			show('tr' + id);
			processTpl('tplSubServices', data, id);
		}
	}
}


function getSubServices(bouquet) {
	doRequest(URL.subservices, incomingSubServiceRequest, false);
}


function delayedGetSubservices(){
	setTimeout(getSubServices, 5000);
}

//zap zap
function zap(servicereference){
	doRequest("/web/zap?sRef=" + servicereference);	
	setTimeout(updateItemsLazy, 7000); //reload epg and subservices
	setTimeout(updateItems, 3000);
}

//SignalPanel

function updateSignalPanel(){	
	var html = templates.tplSignalPanel.process(signalPanelData);

	if (!signalWin.closed && signalWin.location) {
		setWindowContent(signalWin, html);
	} else {
		clearInterval(signalPanelUpdatePoller);
		signalPanelUpdatePoller = '';
	}
}

function incomingSignalPanel(request){
	var namespace = {};

	if (request.readyState == 4){
		var xml = getXML(request).getElementsByTagName("e2frontendstatus").item(0);
		namespace = {
				snrdb : xml.getElementsByTagName('e2snrdb').item(0).firstChild.data,
				snr : xml.getElementsByTagName('e2snr').item(0).firstChild.data,
				ber : xml.getElementsByTagName('e2ber').item(0).firstChild.data,
				acg : xml.getElementsByTagName('e2acg').item(0).firstChild.data
		};
	}

	signalPanelData = { signal : namespace };
	fetchTpl('tplSignalPanel', updateSignalPanel); 	
}

function reloadSignalPanel(){
	doRequest(URL.signal, incomingSignalPanel, false);
}

function openSignalPanel(){
	if (!(!signalWin.closed && signalWin.location)){
		signalWin = openPopup('SignalPanel', '', 220, 120);
		if(signalPanelUpdatePoller === ''){
			signalPanelUpdatePoller = setInterval(reloadSignalPanel, 5000);
		}
	}
	reloadSignalPanel();
}

//EPG functions


function showEpgList(){
	var html = templates.tplEpgList.process(epgListData);

	if (!EPGListWin.closed && EPGListWin.location) {
		setWindowContent(EPGListWin, html);
	} else {
		EPGListWin = openPopup("EPG", html, 900, 500);
	}
}

function incomingEPGrequest(request){
	debug("[incomingEPGrequest] readyState" +request.readyState);		
	if (request.readyState == 4){
		var EPGItems = new EPGList(getXML(request)).getArray();
		debug("[incomingEPGrequest] got "+EPGItems.length+" e2events");

		if( EPGItems.length > 0){
			epgListData = {epg : EPGItems};
			fetchTpl('tplEpgList', showEpgList);
		} else {
			messageBox('No Items found!', 'Sorry but I could not find any EPG Content containing your search value');
		}
	}
}

function loadEPGBySearchString(string){
	doRequest(URL.epgsearch+escape(string),incomingEPGrequest, false);
}

function loadEPGByServiceReference(servicereference){
	doRequest(URL.epgservice+servicereference,incomingEPGrequest, false);
}

function buildServiceListEPGItem(epgevent, type){
	var data = { epg : epgevent,
				 nownext: type
				};

	var id = type + epgevent.servicereference;

	show('tr' + id);

	if(typeof(templates.tplServiceListEPGItem) != "undefined"){
		renderTpl(templates.tplServiceListEPGItem, data, id, true);
	} else {
		debug("[buildServiceListEPGItem] tplServiceListEPGItem N/A");
	}
}

function incomingServiceEPGNowNext(request, type){
	if(request.readyState == 4){
		var epgevents = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
		for (var c = 0; c < epgevents.length; c++){
			try{
				var epgEvt = new EPGEvent(epgevents.item(c), c).toJSON();
			} catch (e){
				debug("[incomingServiceEPGNowNext]" + e);
			}

			if (epgEvt.eventid != ''){
				buildServiceListEPGItem(epgEvt, type);
			}
		}
	}
}

function incomingServiceEPGNow(request){
	incomingServiceEPGNowNext(request, 'NOW');
}

function incomingServiceEPGNext(request){
	incomingServiceEPGNowNext(request, 'NEXT');
}

function loadServiceEPGNowNext(servicereference, next){
	var url = URL.epgnow+servicereference;

	if(typeof(next) == 'undefined'){
		doRequest(url, incomingServiceEPGNow, false);
	} else {
		url = URL.epgnext+servicereference;
		doRequest(url, incomingServiceEPGNext, false);
	}
}


function getBouquetEpg(){
	loadServiceEPGNowNext(currentBouquet);
	loadServiceEPGNowNext(currentBouquet, true);
}


function recordNowPopup(){
	var result = confirm(	
			"OK: Record current event\n" +
			"Cancel: Start infinite recording"
	);

	if( result === true || result === false){
		recordNowDecision(result);
	}
}


//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ volume functions ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
function handleVolumeRequest(request){
	if (request.readyState == 4) {
		var b = getXML(request).getElementsByTagName("e2volume");
		var newvalue = b.item(0).getElementsByTagName('e2current').item(0).firstChild.data;
		var mute = b.item(0).getElementsByTagName('e2ismuted').item(0).firstChild.data;
		debug("[handleVolumeRequest] Volume " + newvalue + " | Mute: " + mute);

		for (var i = 1; i <= 10; i++)		{
			if ( (newvalue/10)>=i){
				$("volume"+i).src = "/web-data/img/led_on.png";
			}else{
				$("volume"+i).src = "/web-data/img/led_off.png";
			}
		}
		if (mute == "False"){
			$("speaker").src = "/web-data/img/speak_on.png";
		}else{
			$("speaker").src = "/web-data/img/speak_off.png";
		}
	}    	
}


function getVolume(){
	doRequest(URL.getvolume, handleVolumeRequest, false);
}

function volumeSet(val){
	doRequest(URL.setvolume+val, handleVolumeRequest, false);
}

function volumeUp(){
	doRequest(URL.volumeup, handleVolumeRequest, false);
}

function volumeDown(){
	doRequest(URL.volumedown, handleVolumeRequest, false);
}

function volumeMute(){
	doRequest(URL.volumemute, handleVolumeRequest, false);
}

function initVolumePanel(){
	getVolume(); 
}



//Channels and Bouquets

function incomingChannellist(request){
	var serviceList = null;
	if(typeof(loadedChannellist[currentBouquet]) != "undefined"){
		serviceList = loadedChannellist[currentBouquet];
	} else if(request.readyState == 4) {
		serviceList = new ServiceList(getXML(request)).getArray();
		debug("[incomingChannellist] got "+serviceList.length+" Services");
	}
	if(serviceList !== null) {		
		var data = { services : serviceList };

		processTpl('tplServiceList', data, 'contentServices', getBouquetEpg);
		delayedGetSubservices();
	} else {
		debug("[incomingChannellist] services is null");
	}
}


function loadBouquet(servicereference, name){ 
	debug("[loadBouquet] called");
	setAjaxLoad('contentServices');
	
	currentBouquet = servicereference;

	setContentHd(name);
	
	var input = new Element('input');
	input.id = 'serviceSearch';
	input.value = 'Search for service';
	
	$('contentHdExt').update(input);
	
	input.observe('focus', onServiceSearchFocus);
	input.observe('keyup', serviceSearch);	

	startUpdateBouquetItemsPoller();
	doRequest(URL.getservices+servicereference, incomingChannellist, true);
}


function incomingBouquetListInitial(request){
	if (request.readyState == 4) {
		var bouquetList = new ServiceList(getXML(request)).getArray();
		debug("[incomingBouquetListInitial] Got " + bouquetList.length + " TV Bouquets!");	
	
		// loading first entry of TV Favorites as default for ServiceList
		incomingBouquetList(
				request, 
				function(){
					loadBouquet(bouquetList[0].servicereference, bouquetList[0].servicename);;
				}
			);
	}
}


function incomingBouquetList(request, callback){
	if (request.readyState == 4) {
		var bouquetList = new ServiceList(getXML(request)).getArray();
		debug("[incomingBouquetList] got " + bouquetList.length + " TV Bouquets!");	
		var data = { bouquets : bouquetList };
		
		if( $('contentBouquets') != "undefined" && $('contentBouquets') != null ){
			processTpl('tplBouquetList', data, 'contentBouquets');
			if(typeof(callback) == 'function')
				callback();
		} else {
			processTpl(					
					'tplBouquetsAndServices', 
					null, 
					'contentMain',
					function(){
						processTpl('tplBouquetList', data, 'contentBouquets');
						if(typeof(callback) == 'function')
							callback();
					}
			);
		}
	}
}


function initChannelList(){
	var url = URL.getservices+encodeURIComponent(bouquetsTv);
	currentBouquet = bouquetsTv;

	doRequest(url, incomingBouquetListInitial, true);
}



//Movies
function initMovieList(){
	// get videodirs, last_videodir, and all tags
	doRequest(URL.getcurrlocation, incomingMovieListCurrentLocation, false);
}

function incomingMovieListCurrentLocation(request){
	if(request.readyState == 4){
		result  = new SimpleXMLList(getXML(request), "e2location");
		currentLocation = result.getList()[0];
		debug("[incomingMovieListCurrentLocation].currentLocation" + currentLocation);
		doRequest(URL.getlocations, incomingMovieListLocations, false);
	}
}

function incomingMovieListLocations(request){
	if(request.readyState == 4){
		result  = new SimpleXMLList(getXML(request), "e2location");
		locationsList = result.getList();

		if (locationsList.length === 0) {
			locationsList = ["/hdd/movie"];
		}
		doRequest(URL.gettags, incomingMovieListTags, false);
	}
}

function incomingMovieListTags(request){
	if(request.readyState == 4){
		result  = new SimpleXMLList(getXML(request), "e2tag");
		tagsList = result.getList();
	}
}

function createOptionListSimple(lst, selected) {
	var namespace = Array();
	var i = 0;
	var found = false;

	for (i = 0; i < lst.length; i++) {
		if (lst[i] == selected) {
			found = true;
		}
	}

	if (!found) {
		lst = [ selected ].concat(lst);
	}

	for (i = 0; i < lst.length; i++) {
		namespace[i] = {
				'value': lst[i],
				'txt': lst[i],
				'selected': (lst[i] == selected ? "selected" : " ")};
	}

	return namespace;
}

function loadMovieNav(){
	// fill in menus
	var data = {
			dirname: createOptionListSimple(locationsList, currentLocation),
			tags: createOptionListSimple(tagsList, "")
	};

	processTpl('tplNavMovies', data, 'navContent');
}

function incomingMovieList(request){
	if(request.readyState == 4){

		var movieList = new MovieList(getXML(request)).getArray();
		debug("[incomingMovieList] Got "+movieList.length+" movies");

		var data = { movies : movieList };
		processTpl('tplMovieList', data, 'contentMain');
	}		
}

function loadMovieList(loc, tag){
	if(typeof(loc) == 'undefined'){
		loc = currentLocation;
	}
	if(typeof(tag) == 'undefined'){
		tag = '';
	}
	debug("[loadMovieList] Loading movies in location '"+loc+"' with tag '"+tag+"'");
	doRequest(URL.movielist+"?dirname="+loc+"&tag="+tag, incomingMovieList, false);
}


function incomingDelMovieResult(request) {
	debug("[incomingDelMovieResult] called");
	if(request.readyState == 4){
		var result = new SimpleXMLResult(getXML(request));
		if(result.getState()){			
			loadMovieList();
		}
		simpleResultHandler(result);
	}		
}


function delMovie(sref ,servicename, title, description) {
	debug("[delMovie] File(" + unescape(sref) + "), servicename(" + servicename + ")," +
			"title(" + unescape(title) + "), description(" + description + ")");

	result = confirm( "Are you sure want to delete the Movie?\n" +
			"Servicename: " + servicename + "\n" +
			"Title: " + unescape(title) + "\n" + 
			"Description: " + description + "\n");

	if(result){
		debug("[delMovie] ok confirm panel"); 
		doRequest(URL.moviedelete+"?sRef="+unescape(sref), incomingDelMovieResult, false); 
		return true;
	}
	else{
		debug("[delMovie] cancel confirm panel");
		return false;
	}
}

//Send Messages and Receive the Answer


function incomingMessageResult(request){
	if(request.readyState== 4){
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
	}
}

function getMessageAnswer() {
	doRequest(URL.messageanswer, incomingMessageResult, false);
}

function sendMessage(messagetext, messagetype, messagetimeout){
	if(!messagetext){
		messagetext = $('MessageSendFormText').value;
	}	
	if(!messagetimeout){
		messagetimeout = $('MessageSendFormTimeout').value;
	}	
	if(!messagetype){
		var index = $('MessageSendFormType').selectedIndex;
		messagetype = $('MessageSendFormType').options[index].value;
	}	
	if(parseNr(messagetype) === 0){
		doRequest(URL.message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout);
		setTimeout(getMessageAnswer, parseNr(messagetimeout)*1000);
	} else {
		doRequest(URL.message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult, false);
	}
}


//Screenshots
function getScreenShot(what) {
	debug("[getScreenShot] called");

	var buffer = new Image();
	var downloadStart;
	var data = {};

	buffer.onload = function () { 
		debug("[getScreenShot] image assigned");

		data = { img : { src : buffer.src } };	
		processTpl('tplGrab', data, 'contentMain');

		return true;
	};

	buffer.onerror = function (meldung) { 
		debug("[getScreenShot] Loading image failed"); 
		return true;
	};

	switch(what){
	case "o":
		what = "&o=&n=";
		break;
	case "v":
		what = "&v=";
		break;
	default:
		what = "";
	break;
	}

	downloadStart = new Date().getTime();
	buffer.src = '/grab?format=jpg&r=720&' + what + '&filename=/tmp/' + downloadStart;
}

function getVideoShot() {
	getScreenShot("v");
}

function getOsdShot(){
	getScreenShot("o");
}

//RemoteControl Code

function incomingRemoteControlResult(request){
//	if(request.readyState == 4){
//		var b = getXML(request).getElementsByTagName("e2remotecontrol");
//		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
//		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
//	}
}

function openWebRemote(){
	var template = templates.tplWebRemoteOld;

	if(boxtype == "dm8000"){
		template = templates.tplWebRemote;
	}


	if (!webRemoteWin.closed && webRemoteWin.location) {
		setWindowContent(webRemoteWin, template);
	} else {
		webRemoteWin = openPopup('WebRemote', template, 250, 620);
	}

}


function loadAndOpenWebRemote(){
	if(boxtype == "dm8000"){
		fetchTpl('tplWebRemote', openWebRemote);
		
	} else {
		fetchTpl('tplWebRemoteOld', openWebRemote);
	}
}


function sendRemoteControlRequest(command){
	var long = webRemoteWin.document.getElementById('long');
	if(long.checked){
		doRequest(URL.remotecontrol+'?command='+command+'&type=long', incomingRemoteControlResult, false);
		long.checked = undefined;
	} else {
		doRequest(URL.remotecontrol+'?command='+command, incomingRemoteControlResult, false);
	}
	
	if(webRemoteWin.document.getElementById('getScreen').checked) {
		if(webRemoteWin.document.getElementById('getVideo').checked){
			getScreenShot();
		} else {
			getScreenShot("o");
		}
	}
}


// Array.insert( index, value ) - Insert value at index, without overwriting existing keys
Array.prototype.insert = function( j, v ) {
	if( j>=0 ) {
		var a = this.slice(), b = a.splice( j );
		a[j] = v;
		return a.concat( b );
	}
};

//Array.splice() - Remove or replace several elements and return any deleted
//elements
if( typeof Array.prototype.splice==='undefined' ) {
	Array.prototype.splice = function( a, c ) {
		var e = arguments, d = this.copy(), f = a, l = this.length;

		if( !c ) { 
			c = l - a; 
		}

		for( var i = 0; i < e.length - 2; i++ ) { 
			this[a + i] = e[i + 2]; 
		}


		for( var j = a; j < l - c; j++ ) { 
			this[j + e.length - 2] = d[j - c]; 
		}
		this.length -= c - e.length + 2;

		return d.slice( f, f + c );
	};
}

function ifChecked(rObj) {
	if(rObj.checked) {
		return rObj.value;
	} else {
		return "";
	}
}

//Device Info
/*
 * Handles an incoming request for /web/deviceinfo Parses the Data, and calls
 * everything needed to render the Template using the parsed data and set the
 * result into contentMain @param request - the XHR
 */
function incomingDeviceInfo(request) {
	if(request.readyState == 4){
		debug("[incomingDeviceInfo] called");
		var deviceInfo = new DeviceInfo(getXML(request));

		processTpl('tplDeviceInfo', deviceInfo, 'contentMain');
	}
}


/*
 * Show Device Info Information in contentMain
 */
function showDeviceInfo() {
	doRequest(URL.deviceinfo, incomingDeviceInfo, false);
}

function showGears(){
	var enabled = false;
	
	if (window.google && google.gears){
		enabled = gearsEnabled();
	}
	
	data = { 'useGears' : enabled };
	processTpl('tplGears', data, 'contentMain');
}

function showSettings(){
	var debug = userprefs.data.debug;
	var debugChecked = "";
	if(debug){
		debugChecked = 'checked';
	}
	
	var updateCurrentInterval = userprefs.data.updateCurrentInterval / 1000;
	var updateBouquetInterval = userprefs.data.updateBouquetInterval / 1000;
	

	data = {'debug' : debugChecked,
			'updateCurrentInterval' : updateCurrentInterval,
			'updateBouquetInterval' : updateBouquetInterval
	};
	processTpl('tplSettings', data, 'contentMain');
}

 
// Spezial functions, mostly for testing purpose
function openHiddenFunctions(){
	openPopup("Extra Hidden Functions",tplExtraHiddenFunctions,300,100,920,0);
}


function startDebugWindow() {
	DBG = true;
	debugWin = openPopup("DEBUG", "", 300, 300,920,140, "debugWindow");
}


function restartTwisted() {
	doRequest( "/web/restarttwisted" );
}


//MediaPlayer
function sendMediaPlayer(command) {
	debug("[sendMediaPlayer] called");
	doRequest( URL.mediaplayercmd+command );
}


function incomingMediaPlayer(request){
	if(request.readyState == 4){
		var files = new FileList(getXML(request)).getArray();

		debug("[loadMediaPlayer] Got "+files.length+" entries in mediaplayer filelist");
		// listerHtml = tplMediaPlayerHeader;

		var namespace = {};

		var root = files[0].getRoot();
		if (root != "playlist") {
			namespace = {'root': root};
			if(root != '/') {
				var re = new RegExp(/(.*)\/(.*)\/$/);
				re.exec(root);
				var newroot = RegExp.$1+'/';
				if(newroot == '//') {
					newroot = '/';
				}
				namespace = {
						'root': root,
						'servicereference': newroot,
						'exec': 'loadMediaPlayer',
						'exec_description': 'Change to directory ../',
						'color': '000000',
						'newroot': newroot,
						'name': '..'
				};	
			}
		}

		var itemnamespace = Array();
		for ( var i = 0; i <files.length; i++){
			var file = files[i];
			if(file.getNameOnly() == '') {
				continue;
			}
			var exec = 'loadMediaPlayer';
			var exec_description = 'Change to directory' + file.getServiceReference();
			var color = '000000';			
			var isdir = 'true';

			if (file.getIsDirectory() == "False") {
				exec = 'playFile';
				exec_description = 'play file';
				color = '00BCBC';
				isdir = 'false';
			}

			itemnamespace[i] = {
					'isdir' : isdir,
					'servicereference': file.getServiceReference(),
					'exec': exec,
					'exec_description': exec_description,
					'color': color,							
					'root': file.getRoot(),
					'name': file.getNameOnly()
			};

		}
		/*
		if (root == "playlist") {
			listerHtml += tplMediaPlayerFooterPlaylist;
		}
		 */

		var data = { mp : namespace,
				items: itemnamespace
		};

		processTpl('tplMediaPlayer', data, 'contentMain');
		var sendMediaPlayerTMP = sendMediaPlayer;
		sendMediaPlayer = false;
		// setBodyMainContent('BodyContent');
		sendMediaPlayer = sendMediaPlayerTMP;
	}		
}


function loadMediaPlayer(directory){
	debug("[loadMediaPlayer] called");
	if(typeof(directory) == 'undefined') directory = 'Filesystems';
	doRequest(URL.mediaplayerlist+directory, incomingMediaPlayer, false);
}


function playFile(file,root) {
	debug("[playFile] called");
	mediaPlayerStarted = true;
	doRequest( URL.mediaplayerplay+file+"&root="+root );
}


function deleteFile(sref) {
	debug("[deleteFile] called");
	mediaPlayerStarted = true;
	doRequest( URL.mediaplayerremove+sref );
}


function openMediaPlayerPlaylist() {
	debug("[openMediaPlayerPlaylist] called");
	doRequest(URL.mediaplayerlist+"playlist", incomingMediaPlayer, false);
}


function writePlaylist() {
	debug("[writePlaylist] called");
	var filename = '';
	filename = prompt("Please enter a name for the playlist", "");

	if(filename !== "") {
		doRequest( URL.mediaplayerwrite+filename );
	}
}

//Powerstate
/*
 * Sets the Powerstate @param newState - the new Powerstate Possible Values
 * (also see WebComponents/Sources/PowerState.py) #-1: get current state # 0:
 * toggle standby # 1: poweroff/deepstandby # 2: rebootdreambox # 3:
 * rebootenigma
 */
function sendPowerState(newState){
	doRequest( URL.powerstate+'?newstate='+newState, incomingPowerState);
}


//Currently Running Service
function incomingCurrent(request){
	//	debug("[incomingCurrent called]");
	if(request.readyState == 4){
		try{
			var xml = getXML(request);
			var epg = new EPGList(xml).getArray();
			epg = epg[0];
			
			var service = new Service(xml).toJSON(); 
			
			var data = { 
						'current' : epg,
						'service' : service
					};

			if(typeof(templates.tplCurrent) != "undefined"){
				var display = 'none';
				try{
					var display = $('trExtCurrent').style.display;
				} catch(e){}
				
				renderTpl(templates.tplCurrent, data, "currentContent");
				$('trExtCurrent').style.display = display;
			} else {
				debug("[incomingCurrent] tplCurrent N/A");
			}

		} catch (e){}
		
		isActive.getCurrent = false;
	}
}


function getCurrent(){
	if(!isActive.getCurrent){
		isActive.getCurrent = true;
		doRequest(URL.getcurrent, incomingCurrent, false);
	}
}


//Navigation and Content Helper Functions

/*
 * Loads all Bouquets for the given enigma2 servicereference and sets the
 * according contentHeader @param sRef - the Servicereference for the bouquet to
 * load
 */
function getBouquets(sRef){	
	var url = URL.getservices+encodeURIComponent(sRef);
	
	doRequest(url, incomingBouquetList, true);		
}

/*
 * Loads another navigation template and sets the navigation header
 * @param template - The name of the template
 * @param title - The title to set for the navigation
 */
function reloadNav(template, title){
	setAjaxLoad('navContent');
	processTpl(template, null, 'navContent');
	setNavHd(title);
}

function reloadNavDynamic(fnc, title){
	setAjaxLoad('navContent');
	setNavHd(title);
	fnc();
}

function getBouquetsTv(){
	getBouquets(bouquetsTv);
}

function getProviderTv(){
	getBouquets(providerTv);
}

function getSatellitesTv(){
	getBouquets(satellitesTv);
}

function getAllTv(){
	loadBouquet(allTv, "All (TV)");
}


function getBouquetsRadio(){
	getBouquets(bouquetsRadio);
}

function getProviderRadio(){
	getBouquets(providerRadio);
}

function getSatellitesRadio(){
	getBouquets(satellitesRadio);
}

function getAllRadio(){
	loadBouquet(allRadio, "All (Radio)");
}

/*
 * Loads dynamic content to $(contentMain) by calling a execution function
 * @param fnc - The function used to load the content
 * @param title - The Title to set on the contentpanel
 */
function loadContentDynamic(fnc, title, domid){
	if(typeof(domid) != "undefined" && $(domid) != null){
		setAjaxLoad(domid);
	} else {
		setAjaxLoad('contentMain');
	}
	setContentHd(title);
	stopUpdateBouquetItemsPoller();

	fnc();
}

/*
 * like loadContentDynamic but without the AjaxLoaderAnimation being shown
 */
function reloadContentDynamic(fnc, title){
	setContentHd(title);
	fnc();
}

/*
 * Loads a static template to $(contentMain)
 * @param template - Name of the Template
 * @param title - The Title to set on the Content-Panel
 */
function loadContentStatic(template, title){
	setAjaxLoad('contentMain');
	setContentHd(title);
	stopUpdateBouquetItemsPoller();
	processTpl(template, null, 'contentMain');
}


/*
 * Opens the given Control
 * @param control - Control Page as String
 * Possible Values: power, extras, message, screenshot, videoshot, osdshot
 */
function loadControl(control){
	switch(control){
	case "power":
		loadContentStatic('tplPower', 'PowerControl');
		break;

	case "message":
		loadContentStatic('tplSendMessage', 'Send a Message');
		break;

	case "remote":
		loadAndOpenWebRemote();
		break;

	case "screenshot":
		loadContentDynamic(getScreenShot, 'Screenshot');
		break;

	case "videoshot":
		loadContentDynamic(getVideoShot, 'Videoshot');
		break;

	case "osdshot":
		loadContentDynamic(getOsdShot, 'OSDshot');
		break;

	default:
		break;
	}
}


function loadDeviceInfo(){
	loadContentDynamic(showDeviceInfo, 'Device Information');
}

function loadTools(){
	loadContentStatic('tplTools', 'Tools');
}

function loadAbout(){
	loadContentStatic('tplAbout', 'About');
}

function loadSettings(){
	loadContentDynamic(showSettings, 'Settings');
}

function loadGearsInfo(){
	loadContentDynamic(showGears, 'Google Gears');
}

function reloadGearsInfo(){
	loadContentDynamic(showGears, 'Google Gears');
}

var cachedServiceElements = null;

function onServiceSearchFocus(event){
	event.element().value = '';
	cachedServiceElements = null;
	serviceSearch(event);
}

function serviceSearch(event){
	var needle = event.element().value.toLowerCase();
	
	if(cachedServiceElements == null){
		cachedServiceElements = $$('.sListRow');
	}
	
	for(var i = 0; i < cachedServiceElements.length; i++){
		var row = cachedServiceElements[i];
		var serviceName = row.readAttribute('data-servicename').toLowerCase();
		
		if(serviceName.match(needle) != needle && serviceName != ""){
			row.hide();
		} else {		
			row.show();
		}
	}
	
	debug('serviceNames');
}

/*
 * Switches Navigation Modes
 * @param mode - The Navigation Mode you want to switch to
 * Possible Values: TV, Radio, Movies, Timer, Extras
 */
function switchMode(mode){
	switch(mode){
	case "TV":
		reloadNav('tplNavTv', 'TeleVision');
		break;

	case "Radio":
		reloadNav('tplNavRadio', 'Radio');
		break;

	case "Movies":
		//The Navigation
		reloadNavDynamic(loadMovieNav, 'Movies');

		// The Movie list
		loadContentDynamic(loadMovieList, 'Movies');
		break;

	case "Timer":
		//The Navigation
		reloadNav('tplNavTimer', 'Timer');

		// The Timerlist
		loadContentDynamic(loadTimerList, 'Timer');
		break;

	case "MediaPlayer":
		loadContentDynamic(loadMediaPlayer, 'MediaPlayer');
		break;

	case "BoxControl":
		reloadNav('tplNavBoxControl', 'BoxControl');
		break;

	case "Extras":
		reloadNav('tplNavExtras', 'Extras');
		break;
		
	default:
		break;
	}
}

function openWebTV(){
	window.open('/web-data/streaminterface.html', 'WebTV', 'scrollbars=no, width=800, height=740');
}

function clearSearch(){
	$('epgSearch').value = "";
	$('epgSearch').focus();
}

function updateItems(){
	getCurrent();
	getPowerState();
}

function updateItemsLazy(bouquet){
	getSubServices();
	getBouquetEpg();
}

/*
 * Does the everything required on initial pageload
 */

function init(){
	var DBG = userprefs.data.debug || false;
	
	if(DBG){
		openDebug();
	}

	if( parseNr(userprefs.data.updateCurrentInterval) < 10000){
		userprefs.data.updateCurrentInterval = 120000;
		userprefs.save();
	}
	
	if( parseNr(userprefs.data.updateBouquetInterval) < 60000 ){
		userprefs.data.updateBouquetInterval = 300000;
		userprefs.save();
	}
	
	if (typeof document.body.style.maxHeight == "undefined") {
		alert("Due to the tremendous amount of work needed to get everthing to " +
		"work properly, there is (for now) no support for Internet Explorer Versions below 7");
	}
	
	getBoxtype();

	setAjaxLoad('navContent');
	setAjaxLoad('contentMain');

	fetchTpl('tplServiceListEPGItem');
	fetchTpl('tplBouquetsAndServices');
	fetchTpl('tplCurrent');	
	reloadNav('tplNavTv', 'TeleVision');

	initChannelList();
	initVolumePanel();
	initMovieList();

	updateItems();
	startUpdateCurrentPoller();
}
