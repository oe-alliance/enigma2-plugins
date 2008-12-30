// $Header$

var doRequestMemory = {};
var doRequestMemorySave = {};

var templates = {};

var mediaPlayerStarted = false;

// Settings
var settings = null;
var parentControlList = null;

// Globals
var popUpBlockerHinted = false;
var requestcounter = 0;

var debugWin = '';
var signalWin = '';
var webRemoteWin = '';
var signalPanelUpdatePoller = '';
var EPGListWindow = '';
var MessageAnswerPolling = '';

var currentBouquet = bouquetsTv;

var signalPanelData = {};
var epgListData = {};
var bouquetsMemory = {};
var loadedChannellist = {};


//General Helpers
function ownLazyNumber(num) {
	if(isNaN(num)){
		return 0;
	} else {
		return Number(num);
	}
}


function d2h(nr, len){

	var hex = parseInt(nr, 10).toString(16).toUpperCase();
	if(len > 0){
		try{
			while(hex.length < len){
				hex = "0"+hex;
			}
		} 
		catch(e){}
	} 
	return hex;
}


function quotes2html(txt) {
	return txt.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}


function dateToString(date){

	var dateString = "";
	
	dateString += date.getFullYear();
	dateString += "-" + date.getMonth();
	dateString += "-" + date.getDate();
	
	var hours = date.getHours();
	if(hours < 10){
		hours = '0' + hours;
	}
	dateString += " " + hours;
	
	var minutes = date.getMinutes();
	if(minutes < 10){
		minutes = '0' + minutes;
	}
	dateString += ":" + minutes;
	
	return dateString;
}


function showhide(id){
 	var o = $(id).style;
 	o.display = (o.display!="none")? "none":"";
}


function show(id){
	try{
		$(id).style.display = "";
	} catch(e) {}
}


function hide(id){
	try{
		$(id).style.display = "none";
	} catch(e) {}
}


function set(element, value){
	if(element == "CurrentService") {
		if(value.search(/^MP3 File:/) != -1) {
			value = value.replace(/.*\//, '');
		}
	}
	element = parent.$(element);
	if(value.length > 550) {
		value = value.substr(0,550) + "[...]";
	}
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		try{
			var elementscript = $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
			if(elementscript){
				elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
			}
		}
		catch(e){}
	}
}


function setComplete(element, value){
	//debug(element+"-"+value);
	element = parent.$(element);
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >= 0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
		if(elementscript){
			elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
		}
	}
}


/*
 * Sets the Loading Notification to the given HTML Element
 * @param targetElement - The element the Ajax-Loader should be set in
 */
function setAjaxLoad(targetElement){
	$(targetElement).innerHTML = getAjaxLoad();
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
		messageBox("Please disable your Popup-Blocker for enigma2 WebControl to work flawlessly!");
		popUpBlockerHinted = true;
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
		return null;
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
		$(domElement).innerHTML = result;
	}catch(ex){
		debug("[renderTpl] exception: " + ex);
	}
}


function fetchTpl(tplName, callback){
	if(typeof(templates.tplName) == 'undefined') {
		var url = "/webdata/tpl/"+tplName+".htm";
		var options = {
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o, e){ 
								debug("[fetchTpl] exception "+ e); 
								throw(e); 
							},				
				onSuccess: function(transport){
								saveTpl(transport, tplName);
								if(typeof(callback) == 'function'){
									callback();
								}
							},
				onComplete: requestFinished 
			};
			
		var request = new Ajax.Request(url, options);
	} else {
		if(typeof(callback) != 'undefined'){
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
	var url = "/webdata/tpl/"+tplName+".htm";
		var request = new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o, e){ 
								debug("[processTpl] exception " + e);
								debug("[processTpl] exception " + typeof(o));
								throw(e); 
							},				
				onSuccess: function(transport){
								incomingProcessTpl(transport, data, domElement, callback);
							},
				onComplete: requestFinished 
			});
}

//Debugging Window


function openDebug(){
	debugWin = openPopup("Debug", templates.tplDebug, 500, 300);
}


function loadAndOpenDebug(){
	fetchTpl('tplDebug', openDebug);
}


function debug(text){
	if(DBG){
		try{
			if(!debugWin.closed && debugWin.location){
				var inner = debugWin.document.getElementById('debugContent').innerHTML;
				debugWin.document.getElementById('debugContent').innerHTML = new Date().toLocaleString() + ": "+text+"<br>" + inner;
			}
		} catch (Exception) {
			popUpBlockerHint();
		}
			
	}
}



// end requestindikator
function doRequest(url, readyFunction, save){
	requestStarted();
	doRequestMemorySave[url] = save;
//	debug("[doRequest] Requesting: "+url);
/*	
	if(save == true && typeof(doRequestMemory[url]) != "undefined") {
		readyFunction(doRequestMemory[url]);
	} else {
*/
	try{
		var request = new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o,e){ throw(e); },				
				onSuccess: function (transport, json) {
							if(typeof(doRequestMemorySave[url]) != "undefined") {
								if(doRequestMemorySave[url]) {
//									debug("[doRequest] saving request"); 
									doRequestMemory[url] = transport;
								}
							}
							readyFunction(transport);
						},
				onComplete: requestFinished 
			});
	} catch(e) {}
//	}
}

function getXML(request){
	if (document.implementation && document.implementation.createDocument){
		var xmlDoc = request.responseXML;
	}
	else if (window.ActiveXObject){
		var xmlInsert = document.createElement('xml');

		xmlInsert.setAttribute('innerHTML',request.responseText);
		xmlInsert.setAttribute('id','_MakeAUniqueID');
		document.body.appendChild(xmlInsert);
		xmlDoc = $('_MakeAUniqueID');
		document.body.removeChild($('_MakeAUniqueID'));
	} else {
		debug("[getXML] Your Browser Sucks!");
	}
	return xmlDoc;
}


//Parental Control
function incomingParentControl(request) {
	if(request.readyState == 4){
		parentControlList = new ServiceList(getXML(request)).getArray();
		debug("[incomingParentControl] Got "+parentControlList.length + " services");
	}
}

function getParentControl() {
	doRequest(url_parentcontrol, incomingParentControl, false);
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


function parentPin(servicereference) {
    debug ("parentPin: parentControlList");
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


function incomingGetDreamboxSettings(request){
	if(request.readyState == 4){
		var settings = new Settings(getXML(request)).getArray();
	}
	debug ("starte getParentControl " + getSettingByName("config.ParentalControl.configured"));
	if(String(getSettingByName("config.ParentalControl.configured")) == "true") {
		getParentControl();
	}
}


function getDreamboxSettings(){
	doRequest(url_settings, incomingGetDreamboxSettings, false);
}


//Subservices
function incomingSubServiceRequest(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		debug("[incomingSubServiceRequest] Got " + services.length + " SubServices");
		
		if(services.length > 1) {
			
			var first = services[0];

			var last = false;
			var namespace = [];
			
			//we already have the main service in our servicelist so we'll start with the second element
			for ( var i = 1; i < services.length ; i++){
				var reference = services[i];
				namespace[i] = { 	
					'servicereference': reference.getServiceReference(),
					'servicename': reference.getServiceName()
				};
			}
			var data = { subservices : namespace };
			
			
			var id = 'SUB'+first.getServiceReference();
			show('tr' + id);
			processTpl('tplSubServices', data, id);
		}
	}
}


function getSubServices() {
	doRequest(url_subservices, incomingSubServiceRequest, false);
}


function delayedGetSubservices(){
	setTimeout(getSubServices, 5000);
}

//zap zap
function zap(servicereference){
	var request = new Ajax.Request( "/web/zap?sRef=" + servicereference, 
						{
							asynchronous: true,
							method: 'get'
						}
					);
	delayedGetSubservices();
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
	doRequest(url_signal, incomingSignalPanel, false);
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
	
	if (!EPGListWindow.closed && EPGListWindow.location) {
		setWindowContent(EPGListWindow, html);
	} else {
		EPGListWindow = openPopup("EPG", html, 900, 500);
	}
}

function incomingEPGrequest(request){
	debug("[incomingEPGrequest] readyState" +request.readyState);		
	if (request.readyState == 4){
		var EPGItems = new EPGList(getXML(request)).getArray(true);
		debug("[incomingEPGrequest] got "+EPGItems.length+" e2events");
		if(EPGItems.length > 0){			
			var namespace = [];
			for (var i=0; i < EPGItems.length; i++){
				try{
					var item = EPGItems[i];				
					namespace[i] = {	
						'date': item.getTimeDay(),
						'eventid': item.getEventId(),
						'servicereference': item.getServiceReference(),
						'servicename': quotes2html(item.getServiceName()),
						'title': quotes2html(item.getTitle()),
						'titleESC': escape(item.getTitle()),
						'starttime': item.getTimeStartString(), 
						'duration': Math.ceil(item.getDuration()/60000), 
						'description': quotes2html(item.getDescription()),
						'endtime': item.getTimeEndString(), 
						'extdescription': quotes2html(item.getDescriptionExtended()),
						'number': String(i),
						'start': item.getTimeBegin(),
						'end': item.getTimeEnd()
					};
					
				} catch (Exception) { 
					debug("[incomingEPGrequest] Error rendering: " + Exception);	
				}
			}
			
			epgListData = {epg : namespace};
			fetchTpl('tplEpgList', showEpgList);
		} else {
			messageBox('No Items found!', 'Sorry but I could not find any EPG Content containing your search value');
		}
	}
}

function loadEPGBySearchString(string){
	doRequest(url_epgsearch+escape(string),incomingEPGrequest, false);
}

function loadEPGByServiceReference(servicereference){
	doRequest(url_epgservice+servicereference,incomingEPGrequest, false);
}

//function extdescriptionSmall(txt,num) {
//	if(txt.length > 410) {
//		var shortTxt = txt.substr(0,410);
//		txt = txt.replace(/\'\'/g, '&quot;');
//		txt = txt.replace(/\\/g, '\\\\');
//		txt = txt.replace(/\'/g, '\\\'');
//		txt = txt.replace(/\"/g, '&quot;');
//		var smallNamespace = { 'txt':txt,'number':num, 'shortTxt':shortTxt};
//		return RND(tplEPGListItemExtend, smallNamespace);
//	} else {
//		return txt;
//	}
//}	

function buildServiceListEPGItem(epgevent, type){
	var namespace = { 	
		'starttime': epgevent.getTimeStartString(), 
		'title': epgevent.getTitle(), 
		'length': Math.ceil(epgevent.duration/60) 
	};
	var data = {epg : namespace};
	//e.innerHTML = RND(tplServiceListEPGItem, namespace);
	
	var id = type + epgevent.getServiceReference();
	
	show('tr' + id);
	
		if(typeof(templates.tplServiceListEPGItem) == "string"){
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
				var epgEvt = new EPGEvent(epgevents.item(c));
			} catch (e){
				debug("[incomingServiceEPGNowNext]" + e);
			}
			
			if (epgEvt.getEventId() != 'None'){
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
	var url = url_epgnow+servicereference;
	
	if(typeof(next) == 'undefined'){
		doRequest(url, incomingServiceEPGNow, false);
	} else {
		url = url_epgnext+servicereference;
		doRequest(url, incomingServiceEPGNext, false);
	}
}


function getBouquetEpg(){
	loadServiceEPGNowNext(currentBouquet);
	loadServiceEPGNowNext(currentBouquet, true);
}
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ volume functions                            ++++
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
				$("volume"+i).src = "/webdata/img/led_on.png";
			}else{
				$("volume"+i).src = "/webdata/img/led_off.png";
			}
		}
		if (mute == "False"){
			$("speaker").src = "/webdata/img/speak_on.png";
		}else{
			$("speaker").src = "/webdata/img/speak_off.png";
		}
	}    	
}


function getVolume(){
	doRequest(url_getvolume, handleVolumeRequest, false);
}

function volumeSet(val){
	doRequest(url_setvolume+val, handleVolumeRequest, false);
}

function volumeUp(){
	doRequest(url_volumeup, handleVolumeRequest, false);
}

function volumeDown(){
	doRequest(url_volumedown, handleVolumeRequest, false);
}

function volumeMute(){
	doRequest(url_volumemute, handleVolumeRequest, false);
}

function initVolumePanel(){
	getVolume(); 
}

//Channels and Bouquets


function incomingChannellist(request){
	var services = null;
	if(request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		debug("[incomingChannellist] got "+services.length+" Services");
	}
	if(services !== null) {
		var namespace = {};
		var cssclass = "even";
		
		for ( var i = 0; i < services.length ; i++){
			
			cssclass = cssclass == 'even' ? 'odd' : 'even';
			
			var service = services[i];
			namespace[i] = { 	
				'servicereference' : service.getServiceReference(),
				'servicename' : service.getServiceName(),
				'cssclass' : cssclass
			};
		}
		var data = { 
			services : namespace 
		};
		
		processTpl('tplServiceList', data, 'contentMain', getBouquetEpg);
		delayedGetSubservices();
	} else {
		debug("[incomingChannellist] services is null");
	}
}


function loadBouquet(servicereference, name){ 
	debug("[loadBouquet] Loading "+servicereference);

	currentBouquet = servicereference;
		
	setContentHd(name);
	setAjaxLoad('contentMain');
	
	debug("[loadBouquet] " + typeof(loadedChannellist[servicereference]));
	if(typeof(loadedChannellist[servicereference]) == "undefined") {
		doRequest(url_getServices+servicereference, incomingChannellist, true);
	} else {
		incomingChannellist();
	}
}


function incomingBouquetListInitial(request){
	if (request.readyState == 4) {
		var bouquetList = new ServiceList(getXML(request)).getArray();
		debug("[loadBouquet] Got " + bouquetList.length + " TV Bouquets!");	

		//loading first entry of TV Favorites as default for ServiceList
		loadBouquet(bouquetList[0].getServiceReference(), bouquetList[0].getServiceName());

		bouquetsMemory.bouquetsTv = bouquetList;
	}
}


function renderBouquetTable(list, target){
	debug("[renderBouquetTable] Rendering " + list.length + " Bouquets");	
	
	var namespace = [];
	if (list.length < 1){
		alert("NO BOUQUETS!");
	}
	for (var i=0; i < list.length; i++){
		try{
			var bouquet = list[i];
			namespace[i] = {
				'servicereference': bouquet.getServiceReference(), 
				'bouquetname': bouquet.getServiceName()
			};
		} catch (e) { 
			//TODO error handling 
		}
	}
	var data = { 
		services : namespace 
	};
	
	processTpl('tplBouquetList', data, 'contentMain');
}	



function incomingBouquetList(request){
	if (request.readyState == 4) {
		var bouquetList = new ServiceList(getXML(request)).getArray();
		debug("[incomingBouquetList] got " + bouquetList.length + " TV Bouquets!");	
		renderBouquetTable(bouquetList, 'contentMain');		
	}
}


function initChannelList(){
	//debug("init ChannelList");	
	var url = url_getServices+encodeURIComponent(bouquetsTv);
	currentBouquet = bouquetsTv;
	doRequest(url, incomingBouquetListInitial, true);
}



// Movies
function incomingMovieList(request){
	if(request.readyState == 4){
		
		var movies = new MovieList(getXML(request)).getArray();
		debug("[incomingMovieList] Got "+movies.length+" movies");
		namespace = [];	
		
		var cssclass = "even";
		
		for ( var i = 0; i < movies.length; i++){
			cssclass = cssclass == 'even' ? 'odd' : 'even';
			
			var movie = movies[i];
			namespace[i] = { 	
				'servicereference': movie.getServiceReference(),
				'servicename': movie.getServiceName() ,
				'title': movie.getTitle(), 
				'description': movie.getDescription(), 
				'descriptionextended': movie.getDescriptionExtended(),
				'filelink': String(movie.getFilename()).substr(17,movie.getFilename().length),
				'filename': String(movie.getFilename()),
				'filesize': movie.getFilesizeMB(),
				'tags': movie.getTags().join(', ') ,
				'length': movie.getLength() ,
				'time': movie.getTimeDay()+"&nbsp;"+ movie.getTimeStartString(),
				'cssclass' : cssclass
			};
		}
		var data = { movies : namespace };
		processTpl('tplMovieList', data, 'contentMain');
	}		
}


function loadMovieList(tag){
	if(typeof(tag) == 'undefined'){
		tag = '';
	}
	debug("[loadMovieList] Loading movies with tag '"+tag+"'");
	doRequest(url_movielist+tag, incomingMovieList, false);
}


function incomingDelMovieFileResult(request) {
	debug("[incomingDelMovieFileResult] called");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		if(delresult.getState()){
			loadMovieList('');
		}else{
			messageBox("Deletion Error","Reason: "+delresult.getStateText());
		}
	}		
}


function delMovieFile(file ,servicename, title, description) {
	debug("[delMovieFile] File(" + file + "), servicename(" + servicename + ")," +
			"title(" + title + "), description(" + description + ")");
	
	result = confirm( "Are you sure want to delete the Movie?\n" +
		"Servicename: "+servicename+"\n" +
		"Title: "+title+"\n" + 
		"Description: "+description+"\n");

	if(result){
		debug("[delMovieFile] ok confirm panel"); 
		doRequest(url_moviefiledelete+"?filename="+file, incomingDelMovieFileResult, false); 
		return true;
	}
	else{
		debug("[delMovieFile] cancel confirm panel");
		return false;
	}
}

//Send Messages and Receive the Answer


function incomingMessageResult(request){
	if(request.readyState== 4){
		var result = getXML(request).getElementsByTagName("e2message").item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		
		if (result=="True"){
			messageBox('Message sent successfully!');
			return;
		}
	}	
	messageBox('Message NOT sent!');
}

function getMessageAnswer() {
	doRequest(url_messageanswer, incomingMessageResult, false);
	clearInterval(MessageAnswerPolling);
}

function sendMessage(messagetext,messagetype,messagetimeout){
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
	if(ownLazyNumber(messagetype) === 0){
		var request = new Ajax.Request(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, { asynchronous: true, method: 'get' });
		
		MessageAnswerPolling = setInterval(getMessageAnswer, ownLazyNumber(messagetimeout)*1000);
	} else {
		doRequest(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult, false);
	}
}


//Screenshots
function getScreenShot(what) {
	debug("[getScreenShot] called");
	
	setAjaxLoad('contentMain');
	setContentHd('Screenshot');
	
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
			what = "&o";
			break;
		case "v":
			what = "&v";
			break;
		default:
			what = "";
			break;
	}
	
	downloadStart = new Date().getTime();
	buffer.src = '/grab?format=jpg&n=&r=720&' + what + '&' + downloadStart;
}


// RemoteControl Code

function incomingRemoteControlResult(request){
	if(request.readyState == 4){
		var b = getXML(request).getElementsByTagName("e2remotecontrol");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
	} //else {
		//TODO Some Error Handling
//	}
}

function openWebRemote(){
	
	if (!webRemoteWin.closed && webRemoteWin.location) {
		setWindowContent(webRemoteWin, templates.tplWebRemote);
	} else {
		webRemoteWin = openPopup('WebRemote', templates.tplWebRemote, 250, 670);
	}
	
}


function loadAndOpenWebRemote(){
	fetchTpl('tplWebRemote', openWebRemote);
}


function sendRemoteControlRequest(command){
	doRequest(url_remotecontrol+'?command='+command, incomingRemoteControlResult, false);
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

// Array.splice() - Remove or replace several elements and return any deleted elements
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

function writeTimerListNow() {
	var request = new Ajax.Request( url_timerlistwrite, { asynchronous: true, method: 'get' });
}

//Recording
function incomingRecordingPushed(request) {
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("[incomingRecordingPushed] Got " + timers.length + " timers");
		
		var aftereventReadable = ['Nothing', 'Standby', 'Deepstandby/Shutdown'];
		var justplayReadable = ['record', 'zap'];
		var OnOff = ['on', 'off'];
		
		var namespace = [];
		
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];

			if(ownLazyNumber(timer.getDontSave()) == 1) {
				var beginDate = new Date(Number(timer.getTimeBegin())*1000);
				var endDate = new Date(Number(timer.getTimeEnd())*1000);
				namespace[i] = {
				'servicereference': timer.getServiceReference(),
				'servicename': timer.getServiceName() ,
				'title': timer.getName(), 
				'description': timer.getDescription(), 
				'descriptionextended': timer.getDescriptionExtended(), 
				'begin': timer.getTimeBegin(),
				'beginDate': beginDate.toLocaleString(),
				'end': timer.getTimeEnd(),
				'endDate': endDate.toLocaleString(),
				'state': timer.getState(),
				'duration': Math.ceil((timer.getDuration()/60)),
				'repeated': timer.getRepeated(),
				'repeatedReadable': repeatedReadable(timer.getRepeated()),
				'justplay': timer.getJustplay(),
				'justplayReadable': justplayReadable[Number(timer.getJustplay())],
				'afterevent': timer.getAfterevent(),
				'aftereventReadable': aftereventReadable[Number(timer.getAfterevent())],
				'disabled': timer.getDisabled(),
				'onOff': OnOff[Number(timer.getDisabled())]
				};
			}
		}
		var data = { recordings : namespace };
		openPopup("Record Now", 'tplTimerListItem', data, 900, 500, "Record now window");
	}
}


function recordingPushed() {
	doRequest(url_timerlist, incomingRecordingPushed, false);
}


function recordingPushedDecision(recordNowNothing,recordNowUndefinitely,recordNowCurrent) {
	var recordNow = recordNowNothing;
	recordNow = (recordNow === "") ? recordNowUndefinitely: recordNow;
	recordNow = (recordNow === "") ? recordNowCurrent: recordNow;
	if(recordNow !== "nothing" && recordNow !== "") {
		doRequest(url_recordnow+"?recordnow="+recordNow, incomingTimerAddResult, false);
	}
}

function ifChecked(rObj) {
	if(rObj.checked) {
		return rObj.value;
	} else {
		return "";
	}
}

//About
/*
 * Handles an incoming request for /web/about
 * Parses the Data, and calls everything needed to render the 
 * Template using the parsed data and set the result into contentMain
 * @param request - the XHR
 */
function incomingAbout(request) {
	if(request.readyState == 4){
		debug("[incomingAbout] returned");
		var xml = getXML(request).getElementsByTagName("e2abouts").item(0).getElementsByTagName("e2about");

		xml = xml.item(0);
		
		var namespace = {};
		var ns = [];
		
		try{
			var fptext = "V"+xml.getElementsByTagName('e2fpversion').item(0).firstChild.data;
			
			
			var nims = xml.getElementsByTagName('e2tunerinfo').item(0).getElementsByTagName("e2nim");
			debug("[incomingAbout] nims: "+nims.length);
			for(var i = 0; i < nims.length; i++){
				
				var name = nims.item(i).getElementsByTagName("name").item(0).firstChild.data;
				var type = nims.item(i).getElementsByTagName("type").item(0).firstChild.data;
				debug("[incomingAbout]" + name);
				debug("[incomingAbout]" + type);
				ns[i] = { 'name' : name, 'type' : type};
				
			}
			
			
			var hdddata = xml.getElementsByTagName('e2hddinfo').item(0);
			
			var hddmodel 	= hdddata.getElementsByTagName("model").item(0).firstChild.data;
			var hddcapacity = hdddata.getElementsByTagName("capacity").item(0).firstChild.data;
			var hddfree		= hdddata.getElementsByTagName("free").item(0).firstChild.data;

			namespace = {
				'model' : xml.getElementsByTagName('e2model').item(0).firstChild.data,	
				'enigmaVersion': xml.getElementsByTagName('e2enigmaversion').item(0).firstChild.data,
				'fpVersion': fptext,
				'webifversion': xml.getElementsByTagName('e2webifversion').item(0).firstChild.data,	
				'lanMac' : xml.getElementsByTagName('e2lanmac').item(0).firstChild.data,
				'lanDHCP': xml.getElementsByTagName('e2landhcp').item(0).firstChild.data,
				'lanIP': xml.getElementsByTagName('e2lanip').item(0).firstChild.data,
				'lanNetmask': xml.getElementsByTagName('e2lanmask').item(0).firstChild.data,
				'lanGateway': xml.getElementsByTagName('e2langw').item(0).firstChild.data,

				'hddmodel': hddmodel,
				'hddcapacity': hddcapacity,
				'hddfree': hddfree,
				
				'serviceName': xml.getElementsByTagName('e2servicename').item(0).firstChild.data,
				'serviceProvider': xml.getElementsByTagName('e2serviceprovider').item(0).firstChild.data,
				'serviceAspect': xml.getElementsByTagName('e2serviceaspect').item(0).firstChild.data,
				'serviceVideosize': xml.getElementsByTagName('e2servicevideosize').item(0).firstChild.data,
				'serviceNamespace': xml.getElementsByTagName('e2servicenamespace').item(0).firstChild.data,
				
				'vPidh': '0x'+d2h(xml.getElementsByTagName('e2vpid').item(0).firstChild.data, 4),
				'vPid': ownLazyNumber(xml.getElementsByTagName('e2vpid').item(0).firstChild.data),
				'aPidh': '0x'+d2h(xml.getElementsByTagName('e2apid').item(0).firstChild.data, 4),
				'aPid': ownLazyNumber(xml.getElementsByTagName('e2apid').item(0).firstChild.data),
				'pcrPidh': '0x'+d2h(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data, 4),
				'pcrPid': ownLazyNumber(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data),
				'pmtPidh': '0x'+d2h(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data, 4),
				'pmtPid': ownLazyNumber(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data),
				'txtPidh': '0x'+d2h(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data, 4),
				'txtPid': ownLazyNumber(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data),
				'tsidh': '0x'+d2h(xml.getElementsByTagName('e2tsid').item(0).firstChild.data, 4),
				'tsid': ownLazyNumber(xml.getElementsByTagName('e2tsid').item(0).firstChild.data),
				'onidh': '0x'+d2h(xml.getElementsByTagName('e2onid').item(0).firstChild.data, 4),
				'onid': ownLazyNumber(xml.getElementsByTagName('e2onid').item(0).firstChild.data),
				'sidh': '0x'+d2h(xml.getElementsByTagName('e2sid').item(0).firstChild.data, 4),
				'sid': ownLazyNumber(xml.getElementsByTagName('e2sid').item(0).firstChild.data)
			};				  
		} catch (e) {
			debug("[incomingAbout] About parsing Error" + e);
		}

		var data = { about : namespace,
				 tuner : ns};
		processTpl('tplAbout', data, 'contentMain');
	}
}


/*
 * Show About Information in contentMain
 */
function showAbout() {
	doRequest(url_about, incomingAbout, false);
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
	var request = new Ajax.Request( "/web/restarttwisted", { asynchronous: true, method: "get" });
}


//MediaPlayer
function sendMediaPlayer(command) {
	debug("[playFile] loading sendMediaPlayer");
	var request = new Ajax.Request( url_mediaplayercmd+command, { asynchronous: true, method: 'get' });
}


function incomingMediaPlayer(request){
	if(request.readyState == 4){
		var files = new FileList(getXML(request)).getArray();
		
		debug("[loadMediaPlayer] Got "+files.length+" entries in mediaplayer filelist");
		//listerHtml 	= tplMediaPlayerHeader;
		
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
			if(file.getNameOnly() == 'None') {
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
		//setBodyMainContent('BodyContent');
		sendMediaPlayer = sendMediaPlayerTMP;
	}		
}


function loadMediaPlayer(directory){
	debug("[loadMediaPlayer] called");
	doRequest(url_mediaplayerlist+directory, incomingMediaPlayer, false);
}


function playFile(file,root) {
	debug("[playFile] called");
	mediaPlayerStarted = true;
	var request = new Ajax.Request( url_mediaplayerplay+file+"&root="+root, { asynchronous: true, method: 'get' });
}


function openMediaPlayerPlaylist() {
	debug("[playFile] loading openMediaPlayerPlaylist");
	doRequest(url_mediaplayerlist+"playlist", incomingMediaPlayer, false);
}


function writePlaylist() {
	debug("[playFile] loading writePlaylist");
	var filename = prompt("Please enter a name for the playlist", "");
	if(filename !== "") {
		var request = new Ajax.Request( url_mediaplayerwrite+filename, { asynchronous: true, method: 'get' });
	}
}


//Powerstate
/*
 * Sets the Powerstate
 * @param newState - the new Powerstate
 * Possible Values (also see WebComponents/Sources/PowerState.py)
 * #-1: get current state
 * # 0: toggle standby
 * # 1: poweroff/deepstandby
 * # 2: rebootdreambox
 * # 3: rebootenigma
 */
function sendPowerState(newState){
	var request = new Ajax.Request( url_powerstate+'?newstate='+newState, { asynchronous: true, method: 'get' });
}


//FileBrowser
//function incomingFileBrowser(request){
//	if(request.readyState == 4){
//		var files = new FileList(getXML(request)).getArray();
//
//		debug("[incomingFileBrowser] Got " + files.length + " entry in filelist");
//		listerHtml 	= tplFileBrowserHeader;
//		root = files[0].getRoot();
//		listerHtml 	= RND(tplFileBrowserHeader, {'root': root});
//		if(root != '/') {
//			re = new RegExp(/(.*)\/(.*)\/$/);
//			re.exec(root);
//			newroot = RegExp.$1+'/';
//			if(newroot == '//') {
//				newroot = '/';
//			}
//			listerHtml += RND(tplFileBrowserItemBody, 
//				{'root': root,
//				'servicereference': newroot,
//				'exec': 'loadFileBrowser',
//				'exec_description': 'change to directory ../',
//				'color': '000000',
//				'newroot': newroot,
//				'name': '..'});
//		}
//		for ( var i = 0; i <files.length; i++){
//			var file = files[i];
//			if(file.getNameOnly() == 'None') {
//				continue;
//			}
//			var exec = 'loadFileBrowser';
//			var exec_description = 'change to directory' + file.getServiceReference();
//			var color = '000000';
//			if (file.getIsDirectory() == "False") {
//				exec = '';
//				exec_description = 'do Nothing';
//				color = '00BCBC';
//			}
//			var namespace = {
//				'servicereference': file.getServiceReference(),
//				'exec': exec,
//				'exec_description': exec_description,
//				'color': color,
//				'root': file.getRoot(),
//				'name': file.getNameOnly()
//			};
//			listerHtml += tplFileBrowserItemHead;
//			listerHtml += RND(tplFileBrowserItemBody, namespace);
//			if (file.getIsDirectory() == "False") {
//				listerHtml += RND(tplFileBrowserItemIMG, namespace);
//			}
//			listerHtml += tplFileBrowserItemFooter;
//		}
//		listerHtml += RND(tplFileBrowserFooter, {'root': root});
//		$('BodyContent').innerHTML = listerHtml;
////		setBodyMainContent('BodyContent');
//	}		
//}
//
//
//function loadFileBrowser(directory,types){
//	debug("[loadFileBrowser] loading loadFileBrowser");
//	doRequest(url_filelist+directory+"&types="+types, incomingFileBrowser, false);	
//}
//
//
//function incomingDelFileResult(request) {
//	debug("[incomingDelFileResult called]");
//	if(request.readyState == 4){
//		var delresult = new SimpleXMLResult(getXML(request));
//		if(delresult.getState()){
//			loadFileBrowser($('path').value);
//		}else{
//			messageBox("Deletion Error","Reason: "+delresult.getStateText());
//		}
//	}		
//}


function delFile(file,root) {
	debug("[delFile] called");
	doRequest(url_delfile+root+file, incomingDelFileResult, false);
}


//Currently Running Service
function incomingCurrent(request){
//	debug("[incomingCurrent called]");
	if(request.readyState == 4){
		try{
			var xml = getXML(request).getElementsByTagName("e2currentserviceinformation").item(0);
			
			var servicereference = xml.getElementsByTagName('e2servicereference').item(0).firstChild.data;
			var servicename = xml.getElementsByTagName('e2servicename').item(0).firstChild.data;
			var currentname = xml.getElementsByTagName('e2eventname').item(0).firstChild.data;
			var currentduration	= xml.getElementsByTagName('e2eventduration').item(0).firstChild.data;
			
			if(servicereference.length > 0){
				set('currentName', servicename + ' - ' + currentname );
				set('currentDuration', currentduration);
			} else {
				set('currentName', 'N/A');
				set('currentDuration', 'N/A');
			}
		} catch (e){}
		
	}
}


function getCurrent(){
	doRequest(url_getcurrent, incomingCurrent, false);
}


//Navigation and Content Helper Functions
/*
 * Loads all Bouquets for the given enigma2 servicereference and sets the according contentHeader
 * @param sRef - the Servicereference for the bouquet to load
 */
function getBouquets(sRef){
	setAjaxLoad('contentMain');

	var contentHeader = "";
	switch(sRef){
		case bouquetsTv:
			contentHeader = "Bouquets (TV)";
			break;
		
		case providerTv:
			contentHeader = "Provider (TV)";
			break;
		
		case bouquetsRadio:
			contentHeader = "Bouquets (Radio)";
			break;
		
		case providerRadio:
			contentHeader = "Provider (Radio)";
			break;
		
		default:
			break;
	}
	setContentHd(contentHeader);
	
	var url = url_getServices+encodeURIComponent(sRef);
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

/*
 * Loads dynamic content to $(contentMain) by calling a execution function
 * @param fnc - The function used to load the content
 * @param title - The Title to set on the contentpanel
 */
function loadContentDynamic(fnc, title){
	setAjaxLoad('contentMain');
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
	processTpl(template, null, 'contentMain');
}


/*
 * Opens the given Extra
 * @param extra - Extra Page as String
 * Possible Values: power, about, message
 */
function openExtra(extra){
	switch(extra){
		case "power":
			loadContentStatic('tplPower', 'PowerControl');
			break;
	
		case "about":
			loadContentDynamic(showAbout, 'About');
			break;
		
		case "message":
			loadContentStatic('tplSendMessage', 'Send a Message');
			break;
		
		default:
			break;
	}
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
			loadContentDynamic(loadMovieList, 'Movies');
			break;
			
		case "Timer":
			//The Navigation
			reloadNav('tplNavTimer', 'Timer');
			
			//The Timerlist
			loadContentDynamic(loadTimerList, 'Timer');
			break;
		
		case "MediaPlayer":
			loadContentDynamic(loadMediaPlayer, 'MediaPlayer');
			break;
			
		case "Extras":
			reloadNav('tplNavExtras', 'Extras');
			break;
		default:
			break;
	}
}




function updateItems(){
	getCurrent();
}

function updateItemsLazy(){
	getSubServices();
	getBouquetEpg();
}

var updateItemsPoller = setInterval(updateItems, 7500);
var updateItemsLazyPoller = setInterval(updateItemsLazy, 60000);
/*
 * Does the everything required on initial pageload
 */

function init(){
	if(DBG){
		loadAndOpenDebug();
	}
	
	setAjaxLoad('navContent');
	setAjaxLoad('contentMain');
	
	fetchTpl('tplServiceListEPGItem');
	reloadNav('tplNavTv', 'TeleVision');
	
	initChannelList();
	initVolumePanel();
	
	updateItems();
}
