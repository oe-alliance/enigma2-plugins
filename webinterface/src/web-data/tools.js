Version = '$Header$';

var doRequestMemory = new Object();
var doRequestMemorySave = new Object();

// Get Settings
var settings = null;
var parentControlList = null;

// UpdateStreamReader
var UpdateStreamReaderNextReadPos = 0;
var UpdateStreamReaderPollTimer;
var UpdateStreamReaderPollTimerCounter = 0;
var UpdateStreamReaderPollTimerCounterTwisted = 0;
UpdateStreamReaderRequest = null;
function UpdateStreamReaderStart(){
	var ua = navigator.userAgent;
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		debug("UpdateStreamReader IE Fix");

		var namespace = { 	
					'url_updates': url_updates
		};
		$('UpdateStreamReaderIEFixPanel').innerHTML = RND(tplUpdateStreamReaderIE, namespace);
		
	}else {
		UpdateStreamReaderNextReadPos = 0;
		allMessages = "";
		UpdateStreamReaderRequest = new XMLHttpRequest();
		UpdateStreamReaderRequest.onload = UpdateStreamReaderOnLoad;
		UpdateStreamReaderRequest.onerror = UpdateStreamReaderOnError;
		UpdateStreamReaderRequest.open("GET", url_updates, true);
 		UpdateStreamReaderRequest.send(null);
		UpdateStreamReaderPollTimer = setInterval(UpdateStreamReaderLatestResponse, 10000);
	}
}
  
function UpdateStreamReaderLatestResponse() {
	UpdateStreamReaderPollTimerCounter++;
	debug(UpdateStreamReaderPollTimerCounter);
	if(UpdateStreamReaderPollTimerCounter > 6) {
		clearInterval(UpdateStreamReaderPollTimer);
		UpdateStreamReaderRequest.abort();
		UpdateStreamReaderRequest = null;
		UpdateStreamReaderPollTimerCounter = 0;
		UpdateStreamReaderStart();
		
		UpdateStreamReaderPollTimerCounterTwisted++;
		return;
	}
	var allMessages = UpdateStreamReaderRequest.responseText;
	do {
		var unprocessed = allMessages.substring(UpdateStreamReaderNextReadPos);
		var messageXMLEndIndex = unprocessed.indexOf("\n");
		
		if (messageXMLEndIndex!=-1) {
			var endOfFirstMessageIndex = messageXMLEndIndex + "\n".length;
			var anUpdate = unprocessed.substring(0, endOfFirstMessageIndex);
	
			var re = new RegExp("<script>parent\.(.*)</script>");
			anUpdate = re.exec(anUpdate);

			if(anUpdate != null){
				if (anUpdate.length == 2){
					eval(anUpdate[1]);
				}
			}
			
			UpdateStreamReaderNextReadPos += endOfFirstMessageIndex;
		}
		if(UpdateStreamReaderNextReadPos > 65000){
			UpdateStreamReaderRequest.abort();
			UpdateStreamReaderRequest = null;
			UpdateStreamReaderPollTimerCounter = 0;
			UpdateStreamReaderStart();
			messageXMLEndIndex = -1;
		}
	} while (messageXMLEndIndex != -1);
}

function UpdateStreamReaderOnLoad(){
	window.clearInterval(UpdateStreamReaderPollTimer);
	debug("UpdateStreamReaderOnLoad");
	Dialog.confirm(
		"Live Update Stream ends!<br><br>You will not receive any Update from Enigma2.<br>Should I reconnect?",
		 {windowParameters: {width:300, className: windowStyle},
			okLabel: "reconnect",
			buttonClass: "myButtonClass",
			cancel: function(win) {debug("cancel confirm panel")},
			ok: function(win) {UpdateStreamReaderStart(); return true;}
			}
		);
}
function UpdateStreamReaderOnError(){
	// TODO: change this, because it will be called on 'PageUnload' while the request is still running
	debug("UpdateStreamReaderOnError");
	window.clearInterval(UpdateStreamReaderPollTimer);
	Dialog.confirm(
		"Live Update Stream has an Error!<br><br>You will not receive any Update from Enigma2.<br>Should I try to reconnect?",
		 {windowParameters: {width:300, className: windowStyle},
			 okLabel: "reconnect",
			 buttonClass: "myButtonClass",
			 cancel: function(win) {debug("cancel confirm panel")},
			 ok: function(win) {UpdateStreamReaderStart(); return true;}
			}
		);
}
//end UpdateStreamReader

function openWindow(title, inner, width, height, id){
			if(id == null) id = new Date().toUTCString();
			var win = new Window(id, {className: windowStyle, title: title, width: width, height: height });
			win.getContent().innerHTML = inner;
			win.setDestroyOnClose();
			win.showCenter();
			debug("opening Window: "+title);
			return win;
}
function messageBox(t, m){
	Dialog.alert(m, {windowParameters: {title: t, className: windowStyle, width:200}, okLabel: "Close"});
}

//RND Template Function (http://www.amix.dk)
function RND(tmpl, ns) {
	var fn = function(w, g) {
		g = g.split("|");
		var cnt = ns[g[0]];
		//Support for filter functions
		for(var i=1; i < g.length; i++) {
			cnt = eval(g[i])(cnt);
		}
		return cnt || w;
	};
	return tmpl.replace(/%\(([A-Za-z0-9_|.]*)\)/g, fn);
}
function debug(text){
	if(DBG){
		try{
			debugWin.getContent().innerHTML += "DEBUG: "+text+"<br>";
		} catch (windowNotPresent) {}
	}
}
function showhide(id){
 	o = $(id).style;
 	o.display = (o.display!="none")? "none":"";
}
function set(element, value){
	//debug(element+"-"+value);
	element = parent.$(element);
	if(value.length > 550) {
		value = value.substr(0,550) + "[...]";
	}
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
		if(elementscript){
			elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
		}
	}
}
function setComplete(element, value){
	//debug(element+"-"+value);
	element = parent.$(element);
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
		if(elementscript){
			elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
		}
	}
}
// requestindikator
var requestcounter = 0;
function requestIndicatorUpdate(){
	//debug(requestcounter+" open requests");
	if(requestcounter>=1){
		$('RequestIndicator').style.display = "inline";
	}else{
		$('RequestIndicator').style.display = "none";
	}
}
function requestStarted(){
	requestcounter +=1;
	requestIndicatorUpdate();
}
function requestFinished(){
	requestcounter -=1;
	requestIndicatorUpdate();
}
// end requestindikator
function doRequest(url, readyFunction, save){
	requestStarted();
	doRequestMemorySave[url] = save;
	debug("doRequest: Requesting: "+url);
	if(save == true && typeof(doRequestMemory[url]) != "undefined") {
		readyFunction(doRequestMemory[url]);
	} else {
		debug("doRequest: loading");
		new Ajax.Request(url,
			{
				asynchronous: true,
				method: 'GET',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onException: function(o,e){ throw(e); },				
				onSuccess: function (transport, json) {
							if(typeof(doRequestMemorySave[url]) != "undefined") {
								if(doRequestMemorySave[url]) {
									debug("doRequest: saving request"); 
									doRequestMemory[url] = transport;
								}
							}
							readyFunction(transport);
						},
				onComplete: requestFinished 
			});
	}
}

function getXML(request){
	if (document.implementation && document.implementation.createDocument){
		var xmlDoc = request.responseXML
	}
	else if (window.ActiveXObject){
		var xmlInsert = document.createElement('xml');

		xmlInsert.setAttribute('innerHTML',request.responseText);
		xmlInsert.setAttribute('id','_MakeAUniqueID');
		document.body.appendChild(xmlInsert);
		xmlDoc = $('_MakeAUniqueID');
		document.body.removeChild($('_MakeAUniqueID'));
	} else {
		debug("Your Browser Sucks!");
	}
	return xmlDoc;
}
function parentPin(servicereference) {
	servicereference = decodeURIComponent(servicereference);
	if(parentControlList == null || String(getSettingByName("config.ParentalControl.configured")) != "True") {
		return true;
	}
	debug("parentPin " + parentControlList.length);
	if(getParentControlByRef(servicereference) == servicereference) {
		if(String(getSettingByName("config.ParentalControl.type.value")) == "whitelist") {
			debug("leaving here 1");
			return true;
		}
	} else {
		debug("leaving here 2");
		return true;
	}
	debug("going to ask for PIN");

	var userInput = prompt('ParentControll was switch on.<br> Please enter PIN','PIN');
	if (userInput != '' && userInput != null) {
		if(String(userInput) == String(getSettingByName("config.ParentalControl.servicepin.0")) ) {
			return true;
		} else {
			return parentPin(servicereference);
		}
	} else {
		return false;
	}
}
var SubServicePoller;
var SubServicePollerCounter = 0;
var SubServicePollerRef = null;
function zap(servicereference){
	if(parentPin(servicereference)) {
		new Ajax.Request( "/web/zap?sRef=" + servicereference, 
							{
								asynchronous: true,
								method: 'get'
							}
						);
		if(SubServicePoller != 0){
			clearInterval(SubServicePoller);
			SubServicePollerCounter = 0;
		}
		SubServicePollerRef = servicereference;
		SubServicePoller = setInterval(getSubServices, 10000);
		SubServicePollerCounter = 1;
	}
}

//++++       SignalPanel                           ++++
function initSignalPanel(){
	$('SignalPanel').innerHTML = tplSignalPanelButton;
}
function openSignalDialog(){
	openWindow("Signal Info",tplSignalPanel, 215, 75);
}


//++++ EPG functions                               ++++
function loadEPGBySearchString(string){
		doRequest(url_epgsearch+escape(string),incomingEPGrequest, false);
}
function loadEPGByServiceReference(servicereference){
		doRequest(url_epgservice+servicereference,incomingEPGrequest, false);
}
function incomingEPGrequest(request){
	debug("incoming request" +request.readyState);		
	if (request.readyState == 4){
		var EPGItems = new EPGList(getXML(request)).getArray(true);
		debug("have "+EPGItems.length+" e2events");
		if(EPGItems.length > 0){			
			var html = tplEPGListHeader;
			for (var i=0; i < EPGItems.length; i++){
				try{
					var item = EPGItems[i];				
					var namespace = {	
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
							'extdescriptionSmall': extdescriptionSmall(item.getDescriptionExtended(),String(i)),
							'start': item.getTimeBegin(),
							'end': item.getTimeEnd()
						};
					//Fill template with data and add id to our result
					html += RND(tplEPGListItem, namespace);
				} catch (blubb) { debug("Error rendering: "+blubb);	}
			}
			html += tplEPGListFooter;
			openWindow("Electronic Program Guide", html, 900, 500);
		} else {
			messageBox('No Items found!', 'Sorry but i could not find any EPG Content containing your search value');
		}
	}
}
function extdescriptionSmall(txt,num) {
	if(txt.length > 410) {
		var shortTxt = txt.substr(0,410);
		txt = txt.replace(/\'\'/g, '&quot;');
		txt = txt.replace(/\\/g, '\\\\');
		txt = txt.replace(/\'/g, '\\\'');
		txt = txt.replace(/\"/g, '&quot;');
		var smallNamespace = { 'txt':txt,'number':num, 'shortTxt':shortTxt};
		return RND(tplEPGListItemExtend, smallNamespace);
	} else {
		return txt;
	}
}	

/////////////////////////

function loadServiceEPGNowNext(servicereference){
	var url = url_epgnow+servicereference;
	doRequest(url, incomingServiceEPGNowNext, false);	
}

function incomingServiceEPGNowNext(request){
	if(request.readyState == 4){
		var epgevents = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
		for (var c =0; c < epgevents.length;c++){
			var eventnow = new EPGEvent(epgevents.item(c));
			
			if (eventnow.getEventId() != 'None'){
				buildServiceListEPGItem(eventnow,"NOW");
			}
		}
	}
}
function buildServiceListEPGItem(epgevent,nownext){
	var e = $(epgevent.getServiceReference()+'EPG'+nownext);
		try{
			var namespace = { 	
				'starttime': epgevent.getTimeStartString(), 
				'title': epgevent.getTitle(), 
				'length': Math.ceil(epgevent.duration/60) 
			};
			e.innerHTML = RND(tplServiceListEPGItem, namespace);
		} catch (blubb) {
			debug("Error rendering: "+blubb);
		}	
}
///////////////////


//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ GUI functions                               ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

var currentBodyMainElement = null

function setBodyMainContent(newelementname){
	newelement =$(newelementname);
	if(currentBodyMainElement != null){
		currentBodyMainElement.style.display = "none";
		
	}
	newelement.style.display = "";
	currentBodyMainElement = newelement;
}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ volume functions                            ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

function initVolumePanel(){
	$('VolumePanel').innerHTML = tplVolumePanel;
	getVolume(); 
}
function getVolume(){
	doRequest(url_getvolume,handleVolumeRequest, false);
}
function volumeSet(newvalue){
	doRequest(url_setvolume+newvalue,handleVolumeRequest, false);
}
function volumeUp(){
	doRequest(url_volumeup,handleVolumeRequest, false);
}
function volumeDown(){
	doRequest(url_volumedown,handleVolumeRequest, false);	
}
function volumeMute(){
	doRequest(url_volumemute,handleVolumeRequest, false);
}
function handleVolumeRequest(request){
	if (request.readyState == 4) {
		var b = getXML(request).getElementsByTagName("e2volume");
		var newvalue = b.item(0).getElementsByTagName('e2current').item(0).firstChild.data;
		var mute = b.item(0).getElementsByTagName('e2ismuted').item(0).firstChild.data;
		debug("volume"+newvalue+";"+mute);
		
		for (var i = 1; i <= 10; i++)		{
			if ( (newvalue/10)>=i){
				$("volume"+i).src = "/webdata/gfx/led_on.png";
			}else{
				$("volume"+i).src = "/webdata/gfx/led_off.png";
			}
		}
		if (mute == "False"){
			$("speaker").src = "/webdata/gfx/speak_on.png";
		}else{
			$("speaker").src = "/webdata/gfx/speak_off.png";
		}
	}    	
}

var bouqetsMemory = new Object();

function initChannelList(){
	//debug("init ChannelList");	
	var url = url_getServices+encodeURIComponent(bouqet_tv);
	doRequest(url, incomingTVBouquetList, true);

	var url = url_getServices+encodeURIComponent(bouqet_radio);
	doRequest(url, incomingRadioBouquetList, true);

	var url = url_getServices+encodeURIComponent(bouqet_provider_tv);
	doRequest(url, incomingProviderTVBouquetList, true);

	var url = url_getServices+encodeURIComponent(bouqet_provider_radio);
	doRequest(url, incomingProviderRadioBouquetList, true);
	
	getSettings();
}

var servicereftoloadepgnow = "";
var loadedChannellist = new Object();
function loadBouquet(servicereference){ 
	debug("loading bouquet with "+servicereference);
	servicereftoloadepgnow = servicereference;
	debug("loadBouquet " + typeof(loadedChannellist[servicereftoloadepgnow]));
	if(typeof(loadedChannellist[servicereftoloadepgnow]) == "undefined") {
		doRequest(url_getServices+servicereference, incomingChannellist, true);
	} else {
		incomingChannellist();
	}
}

function incomingTVBouquetList(request){
	if (request.readyState == 4) {
		var list0 = new ServiceList(getXML(request)).getArray();
		debug("have "+list0.length+" TV Bouquet ");	
		$('accordionMenueBouquetContentTV').innerHTML = renderBouquetTable(list0,tplBouquetListHeader,tplBouquetListItem,tplBouquetListFooter);
		//loading first entry of TV Favorites as default for ServiceList
		loadBouquet(list0[0].getServiceReference());
		bouqetsMemory["bouqet_tv"] = list0;
	}
}
function incomingRadioBouquetList(request){
	if (request.readyState == 4) {
		var list1 = new ServiceList(getXML(request)).getArray();
		debug("have "+list1.length+" Radio Bouquet ");	
		$('accordionMenueBouquetContentRadio').innerHTML = renderBouquetTable(list1,tplBouquetListHeader,tplBouquetListItem,tplBouquetListFooter);
	}	
}
function incomingProviderTVBouquetList(request){
	if (request.readyState == 4) {
		var list2 = new ServiceList(getXML(request)).getArray();
		debug("have "+list2.length+" TV Provider Bouquet ");	
		$('accordionMenueBouquetContentProviderTV').innerHTML = renderBouquetTable(list2,tplBouquetListHeader,tplBouquetListItem,tplBouquetListFooter);
	}	
}
function incomingProviderRadioBouquetList(request){
	if (request.readyState == 4) {
		var list2 = new ServiceList(getXML(request)).getArray();
		debug("have "+list2.length+" Radio Provider Bouquet ");	
		$('accordionMenueBouquetContentProviderRadio').innerHTML = renderBouquetTable(list2,tplBouquetListHeader,tplBouquetListItem,tplBouquetListFooter);
	}	
}

function renderBouquetTable(bouquet,templateHeader,templateItem,templateFooter){
	debug("renderBouquetTable with "+bouquet.length+" Bouqet");	
	var html = templateHeader;
	for (var i=0; i < bouquet.length; i++){
		try{
			var namespace = {
				'servicereference': bouquet[i].getServiceReference(), 
				'bouquetname': bouquet[i].getServiceName()
			};
			html += RND(templateItem, namespace);
		} catch (blubb) {}
	}
	html += templateFooter;
	return html;
}	

function incomingChannellist(request){
	var services = null;
	if(typeof(loadedChannellist[servicereftoloadepgnow]) != "undefined"){
		services = loadedChannellist[servicereftoloadepgnow];
	} else if(request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		loadedChannellist[servicereftoloadepgnow] = services;
		debug("got "+services.length+" Services");
	}
	if(services != null) {
		var smallNamespace = {'mainServiceRef': servicereftoloadepgnow };
		listerHtml = RND(tplServiceListHeader, smallNamespace);
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			var namespace = { 	
				'servicereference': reference.getServiceReference(),
				'servicename': reference.getServiceName()
			};
			listerHtml += RND(tplServiceListItem, namespace);
		}		
		listerHtml += tplServiceListFooter;
		$('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
		loadServiceEPGNowNext(servicereftoloadepgnow);
		debug("incomingChannellist " + typeof(loadedChannellist[servicereftoloadepgnow]));
	}
}
// Movies
function loadMovieList(){
	debug("loading movies");
	doRequest(url_movielist, incomingMovieList);	
}

function incomingMovieList(request){
	if(request.readyState == 4){
		var movies = new MovieList(getXML(request)).getArray();
		debug("have "+movies.length+" movies");
		listerHtml 	= tplMovieListHeader;		
		for ( var i = 0; i <movies.length; i++){
			var movie = movies[i];
			var namespace = { 	
				'servicereference': movie.getServiceReference(),
				'servicename': movie.getServiceName() ,
				'title': movie.getTitle(), 
				'description': movie.getDescription(), 
				'descriptionextended': movie.getDescriptionExtended(),
				'filelink': String(movie.getFilename()).substr(17,movie.getFilename().length),
				'filename': String(movie.getFilename()),
				'tags': movie.getTags().join(', ') 
			};
			listerHtml += RND(tplMovieListItem, namespace);
		}
		listerHtml += tplMovieListFooter;
		$('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
		
	}		
}
function delMovieFile(file,servicename,title,description) {
	debug("delMovieFile: file("+file+"),servicename("+servicename+"),title("+title+"),description("+description+")");
	Dialog.confirm(
		"Selected timer:<br>"
		+"Servicename: "+servicename+"<br>"
		+"Title: "+title+"<br>"
		+"Description: "+description+"<br>"
		+"Are you sure that you want to delete the Timer?",
		 {windowParameters: {width:300, className: windowStyle},
			okLabel: "delete",
			buttonClass: "myButtonClass",
			cancel: function(win) {debug("delMovieFile cancel confirm panel")},
			ok: function(win) { debug("delMovieFile ok confirm panel"); doRequest(url_moviefiledelete+"?filename="+file, incomingDelMovieFileResult, false); return true; }
			}
	);
	
}
function incomingDelMovieFileResult(request) {
	debug("incomingDelMovieFileResult");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		if(delresult.getState()){
			loadMovieList();
		}else{
			messageBox("Deletion Error","Reason: "+delresult.getStateText());
		}
	}		
}


// send Messages
function showMessageSendForm(){
		$('BodyContentChannellist').innerHTML = tplMessageSendForm;
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
	doRequest(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult, false);
}
function incomingMessageResult(request){

	if(request.readyState== 4){
		var b = getXML(request).getElementsByTagName("e2message");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
		if (result=="True"){
			messageBox('message send','message send successfully! it appears on TV-Screen');
		}else{
			messageBox('message send failed',resulttext);
		}
	}		
}

// PowerState Code
function showPowerStateSendForm(){
		$('BodyContentChannellist').innerHTML = tplPowerStateSendForm;
}
function sendPowerState(newState){
	doRequest(url_powerstate+'?newstate='+newState, incomingPowerStateResult, false);
}
function incomingPowerStateResult(request){
	debug(request.readyState);
	if(request.readyState == 4){
		var b = getXML(request).getElementsByTagName("e2powerstate");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
		var tplPowerStateSendForm2 = '<h1>PowerState is changing to:'+resulttext+ '</h1>' + tplPowerStateSendForm;
		$('BodyContentChannellist').innerHTML = tplPowerStateSendForm2;
	} else {
		$('BodyContentChannellist').innerHTML = "<h1>some unknown error</h1>" + tplPasswordSendForm;
	}
}

// RemoteControl Code
function showRemoteControllSendForm(){
	if(! $('rcWindow')){
		openWindow("Remote", tplRemoteControlForm, 220, 615, "rcWindow");
	}
}
function sendRemoteControlRequest(command){
	doRequest(url_remotecontrol+'?command='+command, incomingRemoteControlResult, false);
}
function incomingRemoteControlResult(request){
	if(request.readyState == 4){
		var b = getXML(request).getElementsByTagName("e2remotecontrol");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
	} else {
		$('rcWindow').innerHTML = "<h1>some unknown error</h1>" + tplRemoteControlForm;
	}
}

function getSettings(){
	doRequest(url_settings, incomingGetSettings, false);
}

function incomingGetSettings(request){
	if(request.readyState == 4){
		settings = new Settings(getXML(request)).getArray();
	}
	if(String(getSettingByName("config.ParentalControl.configured")) == "True") {
		getParentControl();
	}
}
function getSettingByName(txt) {
	debug("getSettingByName ("+txt+")");
	for(i = 0; i < settings.length; i++) {
		debug("("+settings[i].getSettingName()+") (" +settings[i].getSettingValue()+")");
		if(String(settings[i].getSettingName()) == String(txt)) {
			return settings[i].getSettingValue();
		} 
	}
	return "";
}
function getParentControl() {
	doRequest(url_parentcontrol, incomingParentControl, false);
}
function incomingParentControl(request) {
	if(request.readyState == 4){
		parentControlList = new ServiceList(getXML(request)).getArray();
		debug("parentControlList got "+parentControlList.length + " services");
	}
}
function getParentControlByRef(txt) {
	debug("getParentControlByRef ("+txt+")");
	for(i = 0; i < parentControlList.length; i++) {
		debug("("+parentControlList[i].getClearServiceReference()+")");
		if(String(parentControlList[i].getClearServiceReference()) == String(txt)) {
			return parentControlList[i].getClearServiceReference();
		} 
	}
	return "";
}
function sendToggleTimerDisable(justplay,begin,end,repeated,channel,name,description,afterEvent,disabled){
	disabled = (ownLazyNumber(disabled) == 0) ? 1 : 0;
	
	var descriptionClean = (description == " " || description == "N/A") ? "" : description;
	var nameClean = (name == " " || name == "N/A") ? "" : name;

	doRequest(url_timerchange+"?"+"sRef="+channel.replace("&quot;", '"')+"&begin="+begin
	 +"&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean)
	 +"&afterevent="+afterEvent+"&eit=0&disabled="+disabled
	 +"&justplay="+justplay+"&repeated="+repeated
	 +"&channelOld="+channel
	 +"&beginOld="+begin+"&endOld="+end
	 +"&deleteOldOnSave=1", incomingTimerAddResult, false);
}
function ownLazyNumber(num) {
	if(isNaN(num)){
		return 0;
	} else {
		return Number(num);
	}
}

var subServicesInsertedList = new Object();

function getSubServices(servicereference) {
	clearInterval(SubServicePoller);
	SubServicePollerCounter = 0;
	doRequest(url_subservices,incomingSubServiceRequest, false);
}
function incomingSubServiceRequest(request){
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		listerHtml 	= '';		
		debug("got "+services.length+" SubServices");
		if(services.length > 1) {
			
			first = services[0];
			var mainChannellist = loadedChannellist[String($('mainServiceRef').value)];
			
			var oldEntryPosition = -1;
			for(i = 0; i < mainChannellist.length; i++) {
				var service = mainChannellist[i];
				if(String(service.getServiceReference()) == String(first.getServiceReference())) {
					oldEntryPosition = i + 1;
					break;
				}
			}
			if(typeof(subServicesInsertedList[String(first.getServiceReference())]) != "undefined") {
				for ( var i = 1; i < subServicesInsertedList[String(first.getServiceReference())].length ; i++){
					var reference = subServicesInsertedList[String(first.getServiceReference())][i];
					$(reference.getServiceReference()+'extend').innerHTML = "";
				}
				for(i = oldEntryPosition; i < oldEntryPosition + subServicesInsertedList[String(first.getServiceReference())].length; i++) {
					mainChannellist.splice(i);
				}
			}
			for ( var i = 0; i < services.length ; i++){
				var reference = services[i];
				var namespace = { 	
					'servicereference': reference.getServiceReference(),
					'servicename': reference.getServiceName()
				};
				listerHtml += RND(tplServiceListItem, namespace);
				if(oldEntryPosition > -1) {
					mainChannellist = mainChannellist.insert(oldEntryPosition++, reference);
				}
			}
			$(first.getServiceReference()+'extend').innerHTML = listerHtml;
			subServicesInsertedList[String(first.getServiceReference())] = services;
			loadedChannellist[$('mainServiceRef').value] = mainChannellist;
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
}
// Array.splice() - Remove or replace several elements and return any deleted elements
if( typeof Array.prototype.splice==='undefined' ) {
 Array.prototype.splice = function( a, c ) {
  var i = 0, e = arguments, d = this.copy(), f = a, l = this.length;
  if( !c ) { c = l - a; }
  for( i; i < e.length - 2; i++ ) { this[a + i] = e[i + 2]; }
  for( a; a < l - c; a++ ) { this[a + e.length - 2] = d[a - c]; }
  this.length -= c - e.length + 2;
  return d.slice( f, f + c );
 };
}
function writeTimerListNow() {
	new Ajax.Request( url_timerlistwrite, { asynchronous: true, method: 'get' });
}
function recordingPushed() {
	doRequest(url_timerlist, incomingRecordingPushed, false);
}
function incomingRecordingPushed(request) {
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		
		var aftereventReadable = new Array ('Nothing', 'Standby', 'Deepstandby/Shutdown');
		var justplayReadable = new Array('record', 'zap');
		var OnOff = new Array('on', 'off');
		
		listerHtml = '';
		
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];

			if(ownLazyNumber(timer.getDontSave()) == 1) {
				var beginDate = new Date(Number(timer.getTimeBegin())*1000);
				var endDate = new Date(Number(timer.getTimeEnd())*1000);
				var namespace = {
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
				'onOff': OnOff[Number(timer.getDisabled())],
				'color': colorTimerListEntry( timer.getState() )
				};
				listerHtml += RND(tplTimerListItem, namespace);
			}
		}
		openWindow("Record Now", listerHtml+tplRecordingFooter, 900, 500, "Record now window");
	}
}
function inserteSizes() {
/*	var screenW = 640, screenH = 480;
	if (parseInt(navigator.appVersion)>3) {	
		screenW = screen.width;
		screenH = screen.height;
	} else if (navigator.appName == "Netscape"
	   && parseInt(navigator.appVersion)==3
	   && navigator.javaEnabled() ) {
		var jToolkit = java.awt.Toolkit.getDefaultToolkit();
		var jScreenSize = jToolkit.getScreenSize();
		screenW = jScreenSize.width;
		screenH = jScreenSize.height;
	}
	debug("screenW:"+screenW+" screenH:"+screenH);
	/* 640x480
	 * 800x600
	 * 1024x768
	 * 1280x1024
	 * 1600x1280
	if(screenH == 800) {
		debug("size 1");
		$("BodyContentChannellist").style.height = '20%';
	} else if(screenH == 1024) {
		debug("1024")
		$("BodyContentChannellist").style.height = '760px';
		
	} else {
		alert("unsupported screensize");
	}*/
	
}
function recordingPushedDecision(recordNowNothing,recordNowUndefinitely,recordNowCurrent) {
	var recordNow = recordNowNothing;
	recordNow = (recordNow == "") ? recordNowUndefinitely: recordNow;
	recordNow = (recordNow == "") ? recordNowCurrent: recordNow;
	if(recordNow != "nothing" && recordNow != "") {
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
function showAbout() {
	doRequest(url_about, incomingAbout, false);
}
function incomingAbout(request) {
	if(request.readyState == 4){
		debug("incomingAbout returned");
		var aboutEntries = getXML(request).getElementsByTagName("e2abouts").item(0).getElementsByTagName("e2about");
		for (var c =0; c < aboutEntries.length;c++){
			var xml = aboutEntries.item(c);
			try{
				var fptext = "V"+xml.getElementsByTagName('e2fpversion').item(0).firstChild.data;
				var tunerinfo = "";
				
				var nims = xml.getElementsByTagName('e2tunerinfo').item(0).getElementsByTagName("e2nim");
				for(var i=0;i< nims.length;i++){
					tunerinfo += nims.item(i).firstChild.data+"<br>";
				}
				
				var hdddata = xml.getElementsByTagName('e2hddinfo').item(0);
				var hddinfo = "";
				if(hdddata.firstChild.data != "None"){
					hddinfo += "Model: "+hdddata.getElementsByTagName("model").item(0).firstChild.data;
					hddinfo += "<br>Capacity: "+hdddata.getElementsByTagName("capacity").item(0).firstChild.data;
					hddinfo += "<br>Free: "+hdddata.getElementsByTagName("free").item(0).firstChild.data;
				}else{
					hddinfo +="no Harddisc";
				}

				var namespace = {
					'enigmaVersion': xml.getElementsByTagName('e2enigmaversion').item(0).firstChild.data
/*
					,'lanDHCP': xml.getElementsByTagName('e2landhcp').item(0).firstChild.data
					,'lanIP': xml.getElementsByTagName('e2lanip').item(0).firstChild.data
					,'lanMask': xml.getElementsByTagName('e2lanmask').item(0).firstChild.data
					,'lanGW': xml.getElementsByTagName('e2langw').item(0).firstChild.data
					,'lanDNS': xml.getElementsByTagName('e2landns').item(0).firstChild.data
*/
					,'fpVersion': fptext
					,'webifversion': xml.getElementsByTagName('e2webifversion').item(0).firstChild.data
					,'tunerInfo': tunerinfo
					,'hddInfo': hddinfo
					,'serviceName': xml.getElementsByTagName('e2servicename').item(0).firstChild.data
					,'serviceProvider': xml.getElementsByTagName('e2serviceprovider').item(0).firstChild.data
					,'serviceAspect': xml.getElementsByTagName('e2serviceaspect').item(0).firstChild.data
					,'serviceNamespace': xml.getElementsByTagName('e2servicenamespace').item(0).firstChild.data
					,'vPID': xml.getElementsByTagName('e2vpid').item(0).firstChild.data
					 ,'vPIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2vpid').item(0).firstChild.data),16)+" "
					,'aPID': xml.getElementsByTagName('e2apid').item(0).firstChild.data+" "
					 ,'aPIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2apid').item(0).firstChild.data),16)+" "
					,'pcrID': xml.getElementsByTagName('e2pcrid').item(0).firstChild.data
 					 ,'pcrIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data),16)+" "
					,'pmtPID': xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data
					 ,'pmtPIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data),16)+" "
					,'txtPID': xml.getElementsByTagName('e2txtpid').item(0).firstChild.data
					 ,'txtPIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data),16)+" "
					,'tsID': xml.getElementsByTagName('e2tsid').item(0).firstChild.data
					 ,'tsIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2tsid').item(0).firstChild.data),16)+" "
					,'onID': xml.getElementsByTagName('e2onid').item(0).firstChild.data
					 ,'onIDh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2onid').item(0).firstChild.data),16)+" "
					,'sid': xml.getElementsByTagName('e2sid').item(0).firstChild.data
					 ,'sidh': parseInt(ownLazyNumber(xml.getElementsByTagName('e2sid').item(0).firstChild.data),16)+" "
				  };
				$('BodyContentChannellist').innerHTML = RND(tplAbout, namespace);;
				setBodyMainContent('BodyContentChannellist');
				
			} catch (e) {
				debug("About parsing Error" + e);
			}	
		}
	}
}
function quotes2html(txt) {
	txt = txt.replace(/"/g, '&quot;');
	return txt.replace(/'/g, '&#39;');
}

// Spezial functions, mostly for testing purpose
function openHiddenFunctions(){
	openWindow("Extra Hidden Functions",tplExtraHiddenFunctions,300,100);
}
function restartUpdateStream() {
	clearInterval(UpdateStreamReaderPollTimer);
	UpdateStreamReaderRequest.abort();
	UpdateStreamReaderRequest = null;
	UpdateStreamReaderPollTimerCounter = 0;
	UpdateStreamReaderStart();
}
function startDebugWindow() {
	DBG = true;
	debugWin = openWindow("DEBUG", "", 300, 300, "debugWindow");
}
function restartTwisted() {
	new Ajax.Request( "/web/restarttwisted", { asynchronous: true, method: "get" })
}