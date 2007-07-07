Version = '$Header$';

var doRequestMemory = new Object();
var doRequestMemorySave = new Object();

var mediaPlayerStarted = false;

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

function openWindow(title, inner, width, height, x, y, id){
			if(id == null) id = new Date().toUTCString();
			if(x == null) x = 460;
			if(y == null) y = 400;
			var win = new Window(id, {className: windowStyle, title: title, width: width, height: height});
			win.getContent().innerHTML = inner;
			win.setDestroyOnClose();
			win.showCenter();
			win.setLocation(y,x);//y=top,x=left
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
//	MP3 File: /media/hdd/13-Placebo_Song_To_Say_Goodbye-Meds.mp3
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
			elementscript= $('UpdateStreamReaderIEFixIFrame').$('scriptzone');
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

function openSignalDialog(){
	openWindow("Signal Info",tplSignalPanel, 215, 75,620,40);
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
			openWindow("Electronic Program Guide", html, 900, 500,50,60);
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
/*	debug("mediaPlayerStarted 1: " + mediaPlayerStarted);
	if(mediaPlayerStarted) {
		mediaPlayerStarted = false;
		sendMediaPlayer(5);
	}
	debug("mediaPlayerStarted 2: " + mediaPlayerStarted);*/
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
		$('BodyContent').innerHTML = listerHtml;
		setBodyMainContent('BodyContent');
		loadServiceEPGNowNext(servicereftoloadepgnow);
		debug("incomingChannellist " + typeof(loadedChannellist[servicereftoloadepgnow]));
	}
}
// Movies
function loadMovieList(tag){
	debug("loading movies by tag '"+tag+"'");
	doRequest(url_movielist+tag, incomingMovieList);	
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
				'tags': movie.getTags().join(', ') ,
				'length': movie.getLength() ,
				'time': movie.getTimeDay()+"&nbsp;"+ movie.getTimeStartString()
			};
			listerHtml += RND(tplMovieListItem, namespace);
		}
		listerHtml += tplMovieListFooter;
		$('BodyContent').innerHTML = listerHtml;
		setBodyMainContent('BodyContent');
		
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
			loadMovieList('');
		}else{
			messageBox("Deletion Error","Reason: "+delresult.getStateText());
		}
	}		
}


// send Messages
function showMessageSendForm(){
		$('BodyContent').innerHTML = tplMessageSendForm;
}
var MessageAnswerPolling;
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
	if(ownLazyNumber(messagetype) == 0){
		new Ajax.Request(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, { asynchronous: true, method: 'get' });
		MessageAnswerPolling = setInterval(getMessageAnswer, ownLazyNumber(messagetimeout)*1000);
	} else {
		doRequest(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult, false);
	}
}
function incomingMessageResult(request){

	if(request.readyState== 4){
		var b = getXML(request).getElementsByTagName("e2message");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
		if (result=="True"){
			messageBox('message send',resulttext);//'message send successfully! it appears on TV-Screen');
		}else{
			messageBox('message send failed',resulttext);
		}
	}		
}
function getMessageAnswer() {
	doRequest(url_messageanswer, incomingMessageResult, false);
	clearInterval(MessageAnswerPolling);
}
// RemoteControl Code
function showRemoteControllSendForm(){
	if(! $('rcWindow')){
		openWindow("Remote", tplRemoteControlForm, 220, 642, 920,0, "rcWindow");
	}
}
function sendRemoteControlRequest(command){
	doRequest(url_remotecontrol+'?command='+command, incomingRemoteControlResult, false);
	if($('getScreen').checked) {
		openGrabPicture();
	}
}
function openGrabPicture() {
	if($('BodyContent').innerHTML != tplRCGrab) {
		$('BodyContent').innerHTML = tplRCGrab;
	}
	debug("openGrabPicture");
	var buffer = new Image();
	var downloadStart;

	buffer.onload = function () { debug("image zugewiesen"); $('grabPageIMG').src = buffer.src; return true;};
	buffer.onerror = function (meldung) { debug("reload grab image failed"); return true;};

	downloadStart = new Date().getTime();
	buffer.src = '/grab?' + downloadStart;
	$('grabPageIMG').height(400);
	tplRCGrab = $('BodyContent').innerHTML;
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
		$("BodyContent").style.height = '20%';
	} else if(screenH == 1024) {
		debug("1024")
		$("BodyContent").style.height = '760px';
		
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
				debug("nims: "+nims.length);
				for(var i=0;i< nims.length;i++){
					
					name = nims.item(i).getElementsByTagName("name").item(0).firstChild.data;
					type = nims.item(i).getElementsByTagName("type").item(0).firstChild.data;
					debug(name);
					debug(type);
					var ns = { 'name' : name, 'type' : type};
					tunerinfo += RND(tplAboutTuner, ns);
					
				}
				
				var hdddata = xml.getElementsByTagName('e2hddinfo').item(0);
				
				var hddmodel 	= hdddata.getElementsByTagName("model").item(0).firstChild.data;
				var hddcapacity = hdddata.getElementsByTagName("capacity").item(0).firstChild.data;
				var hddfree		= hdddata.getElementsByTagName("free").item(0).firstChild.data;

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
					,'hddmodel': hddmodel
					,'hddcapacity': hddcapacity
					,'hddfree': hddfree
					,'serviceName': xml.getElementsByTagName('e2servicename').item(0).firstChild.data
					,'serviceProvider': xml.getElementsByTagName('e2serviceprovider').item(0).firstChild.data
					,'serviceAspect': xml.getElementsByTagName('e2serviceaspect').item(0).firstChild.data
					,'serviceNamespace': xml.getElementsByTagName('e2servicenamespace').item(0).firstChild.data
					,'vPIDh': '0x'+xml.getElementsByTagName('e2vpid').item(0).firstChild.data
					 ,'vPID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2vpid').item(0).firstChild.data),16)
					,'aPIDh': '0x'+xml.getElementsByTagName('e2apid').item(0).firstChild.data
					 ,'aPID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2apid').item(0).firstChild.data),16)
					,'pcrIDh': '0x'+xml.getElementsByTagName('e2pcrid').item(0).firstChild.data
 					 ,'pcrID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2pcrid').item(0).firstChild.data),16)
					,'pmtPIDh': '0x'+xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data
					 ,'pmtPID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2pmtpid').item(0).firstChild.data),16)
					,'txtPIDh': '0x'+xml.getElementsByTagName('e2txtpid').item(0).firstChild.data
					 ,'txtPID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2txtpid').item(0).firstChild.data),16)
					,'tsIDh': '0x'+xml.getElementsByTagName('e2tsid').item(0).firstChild.data
					 ,'tsID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2tsid').item(0).firstChild.data),16)
					,'onIDh': '0x'+xml.getElementsByTagName('e2onid').item(0).firstChild.data
					 ,'onID': parseInt(ownLazyNumber(xml.getElementsByTagName('e2onid').item(0).firstChild.data),16)
					,'sidh': '0x'+xml.getElementsByTagName('e2sid').item(0).firstChild.data
					 ,'sid': parseInt(ownLazyNumber(xml.getElementsByTagName('e2sid').item(0).firstChild.data),16)
				  };				  
				$('BodyContent').innerHTML = RND(tplAbout, namespace);
				setBodyMainContent('BodyContent');
				
			} catch (e) {
				debug("About parsing Error" + e);
			}	
		}
	}
}
function quotes2html(txt) {
	txt = txt.replace(/"/g, '&quot;');
	return txt.replace(/'/g, "\\\'");
}

// Spezial functions, mostly for testing purpose
function openHiddenFunctions(){
	openWindow("Extra Hidden Functions",tplExtraHiddenFunctions,300,100,920,0);
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
	debugWin = openWindow("DEBUG", "", 300, 300,920,140, "debugWindow");
}
function restartTwisted() {
	new Ajax.Request( "/web/restarttwisted", { asynchronous: true, method: "get" })
}
//MediaPlayer
function loadMediaPlayer(directory){
	debug("loading loadMediaPlayer");
	doRequest(url_mediaplayerlist+directory, incomingMediaPlayer);	
}
function incomingMediaPlayer(request){
	if(request.readyState == 4){
		var files = new FileList(getXML(request)).getArray();
		debug(getXML(request));
		debug("have "+files.length+" entry in filelist");
		listerHtml 	= tplMediaPlayerHeader;
		root = files[0].getRoot();
		listerHtml 	= RND(tplMediaPlayerHeader, {'root': root});
		if(root != '/') {
			re = new RegExp(/(.*)\/(.*)\/$/);
			re.exec(root);
			newroot = RegExp.$1+'/';
			if(newroot == '//') {
				newroot = '/';
			}
			listerHtml += RND(tplMediaPlayerItemBody, 
				{'root': root
				, 'servicereference': newroot
				,'exec': 'loadMediaPlayer'
				,'exec_description': 'change to directory ../'
				,'color': '000000'
				,'root': newroot
				,'filename': newroot
				,'fullpath': '..'});
		}
		for ( var i = 0; i <files.length; i++){
			var file = files[i];
			if(file.getFullPath() == 'None') {
				continue;
			}
			var exec = 'loadMediaPlayer';
			var exec_description = 'change to directory' + file.getServiceReference();
			var color = '000000';
			if (file.getIsDirectory() == "False") {
				exec = 'playFile';
				exec_description = 'play file';
				color = '00BCBC';
			}
			var namespace = {
				'servicereference': file.getServiceReference()
				,'exec': exec
				,'exec_description': exec_description
				,'color': color
				,'root': file.getRoot()
				,'filename': file.getFileName()
				,'fullpath': file.getFullPath()
			};
			listerHtml += tplMediaPlayerItemHead;
			listerHtml += RND(tplMediaPlayerItemBody, namespace);
			if (file.getIsDirectory() == "False") {
				listerHtml += RND(tplMediaPlayerItemIMG, namespace);
			}
			listerHtml += tplMediaPlayerItemFooter;
		}
		listerHtml += tplMediaPlayerFooter;
		$('BodyContent').innerHTML = listerHtml;
		var sendMediaPlayerTMP = sendMediaPlayer;
		sendMediaPlayer = false;
		setBodyMainContent('BodyContent');
		sendMediaPlayer = sendMediaPlayerTMP;
	}		
}
function playFile(file,root) {
	debug("loading playFile");
	mediaPlayerStarted = true;
	new Ajax.Request( url_mediaplayerplay+file+"&root="+root, { asynchronous: true, method: 'get' });
}
function sendMediaPlayer(command) {
	debug("loading sendMediaPlayer");
	new Ajax.Request( url_mediaplayercmd+command, { asynchronous: true, method: 'get' });
}
function showPowerStateSendForm(){
		$('BodyContent').innerHTML = tplPowerStateSendForm;
}
function sendPowerState(newState){
	new Ajax.Request( url_powerstate+'?newstate='+newState, { asynchronous: true, method: 'get' });
}
