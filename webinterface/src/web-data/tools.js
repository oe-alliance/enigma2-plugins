var DBG = true;
DBG = false;

var url_getvolume = '/web/vol?set=state'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?ref="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnow = "/web/epgnow?bref="; // plus bouqetRev

var url_fetchchannels = "/web/fetchchannels?ServiceListBrowse="; // plus encoded serviceref
var url_subservices = "/web/subservices"; // subservices for current service

var url_updates= "/web/updates.html";

var url_movielist= "/web/movielist";

var url_about= "/web/about";

var url_settings= "/web/settings";

var url_parentcontrol= "/web/parentcontrollist";

var url_moviefiledelete= "/web/moviefiledelete"; // plus serviceref,eventid

var url_timerlist= "/web/timerlist";
var url_recordnow= "/web/recordnow";
var url_timeradd= "/web/timeradd"; // plus serviceref,begin,end,name,description,eit,disabled,justplay,afterevent
var url_timerchange= "/web/timerchange"; // plus serviceref,begin,end,name,description,eit,disabled,justplay,afterevent
var url_timeraddbyeventid= "/web/timeraddbyeventid"; // plus serviceref,eventid
var url_timerdelete= "/web/timerdelete"; // plus serviceref,bedin,end
var url_timerlistwrite="/web/timerlistwrite?write=saveWriteNow";
var url_timertoggleOnOff= "/web/timeronoff"; // plus serviceref,bedin,end

var url_message = "/web/message"; // plus text,type,timeout

var url_powerstate = "/web/powerstate"; // plus new powerstate
var url_remotecontrol = "/web/remotecontrol"; // plus command

var bouqet_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)FROM BOUQUET "bouquets.tv" ORDER BY bouquet';
var bouqet_radio = '1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET "bouquets.radio" ORDER BY bouquet';
var bouqet_provider_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name';
var bouqet_provider_radio ='1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name';

var windowStyle = "alphacube";

// TimerEdit variables:
var addTimerEditFormObject = new Object();
addTimerEditFormObject["TVListFilled"] = 0;
addTimerEditFormObject["RadioListFilled"] = 0;
addTimerEditFormObject["deleteOldOnSave"] = 0;
addTimerEditFormObject["eventID"] = 0;

var doRequestMemory = new Object();

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
/*
// Quickhack jjbig start
// Its not great, but the best I could come up with to solve the 
// problem with the memory leak

 		if(UpdateStreamReaderPollTimerCounterTwisted > 5) {
			UpdateStreamReaderPollTimerCounterTwisted = 0;
			debug("restarting twisted");
			debug(new Ajax.Request( "/web/restarttwisted", { method: 'get' }));
			debug("...twisted restart");
		}
		* // Quickhack jjbig end
*/
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
			var win = new Window(id, {className: windowStyle, title: title, width: width, height: height});
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
 	o = document.getElementById(id).style;
 	o.display = (o.display!="none")? "none":"";
}
function set(what, value){
	//debug(what+"-"+value);
	element = parent.document.getElementById(what);
	if(value.length > 550) {
		value = value.substr(0,550) + "[...]";
	}
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').document.getElementById('scriptzone');
		if(elementscript){
			elementscript.innerHTML = ""; // deleting set() from page, to keep the page short and to save memory			
		}
	}
}
function setComplete(what, value){
	//debug(what+"-"+value);
	element = parent.document.getElementById(what);
	if (element){
		element.innerHTML = value;
	}
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		elementscript= $('UpdateStreamReaderIEFixIFrame').document.getElementById('scriptzone');
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
	//var password = "";
	//var username = "";
	debug(url);
	if(save == true && typeof(doRequestMemory[url]) != "undefined") {
		debug("not loading");
		readyFunction(doRequestMemory[url]);
	} else {
		debug("loading");
		new Ajax.Request(url,
			{
				method: 'get',
				requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
				onSuccess: function (transport, json) { if(save == true) { doRequestMemory[url] = transport; }
															 readyFunction(transport);},
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
		xmlDoc = document.getElementById('_MakeAUniqueID');
		document.body.removeChild(document.getElementById('_MakeAUniqueID'));
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
/*
 * The Ajax Dialog didn't work, because auf the asycnonity :(
	Dialog.confirm(
		"ParentControll was switch on.<br> Please enter PIN?<br>"+
			'<input type="text" id="pin" name="pin" value="">',
		 {windowParameters: {width:300, className: windowStyle},
			okLabel: "OK",
			buttonClass: "myButtonClass",
			cancel: function(win) { return false; },
			ok: function(win) {
				   if(String($('pin').value) == String(getSettingByName("config.ParentalControl.servicepin.0")) ) {
				      return true;
				   } else {
				   	  return parentPin(servicereference);
				   }
      			}
			}
		);
		*/
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
		new Ajax.Request( "/web/zap?ZapTo=" + servicereference, 
							{
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
	newelement =document.getElementById(newelementname);
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
	document.getElementById('VolumePanel').innerHTML = tplVolumePanel;
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
	var url = url_fetchchannels+encodeURIComponent(bouqet_tv);
	doRequest(url, incomingTVBouquetList, true);

	var url = url_fetchchannels+encodeURIComponent(bouqet_radio);
	doRequest(url, incomingRadioBouquetList, true);

	var url = url_fetchchannels+encodeURIComponent(bouqet_provider_tv);
	doRequest(url, incomingProviderTVBouquetList, true);

	var url = url_fetchchannels+encodeURIComponent(bouqet_provider_radio);
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
		doRequest(url_fetchchannels+servicereference, incomingChannellist, true);
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
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
		loadServiceEPGNowNext(servicereftoloadepgnow);
/*		alert(document.getElementById('scrollContent').style.height);
		document.getElementById('scrollContent').style.height = '14.5%';
				alert(document.getElementById('scrollContent').style.height);*/
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
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
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
// Timer
function addTimerByID(serviceRef,eventID,justplay){
	if(parentPin(serviceRef)) {
		doRequest(url_timeraddbyeventid+"?serviceref="+serviceRef+"&eventid="+eventID+"&justplay="+justplay, incomingTimerAddResult, false);	
	}
}
function incomingTimerAddResult(request){
	debug("onTimerAdded");
	if(request.readyState == 4){
		var addresult = new SimpleXMLResult(getXML(request));
		if(addresult.getState()){
			//timer was add
			loadTimerList();
		}else{
			messageBox("Timer Error","your Timer could not be added!\nReason: "+addresult.getStateText());
		}
	}		
}
function loadTimerList(){
	doRequest(url_timerlist, incomingTimerList, false);	
}

function incomingTimerList(request){
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		listerHtml 	= tplTimerListHeader;
		var aftereventReadable = new Array ('Nothing', 'Standby', 'Deepstandby/Shutdown');
		var justplayReadable = new Array('record', 'zap');
		var OnOff = new Array('on', 'off');
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];
			var beginDate = new Date(Number(timer.getTimeBegin())*1000);
			var endDate = new Date(Number(timer.getTimeEnd())*1000);
			var namespace = { 	
				'servicereference': timer.getServiceReference(),
				'servicename': quotes2html(timer.getServiceName()),
				'title': quotes2html(timer.getName()),
				'description': quotes2html(timer.getDescription()),
				'descriptionextended': quotes2html(timer.getDescriptionExtended()),
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
		listerHtml += tplTimerListFooter;
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
	}
}
function repeatedReadable(num) {
	num = Number(num);
	if(num == 0) {
		return "One Time";
	}
	
	var html = "";
	var Repeated = new Object();
	Repeated["Mo-Su"] =127;
	Repeated["Su"] =    64;
	Repeated["Sa"] =    32;
	Repeated["Mo-Fr"] = 31;
	Repeated["Fr"] =    16;
	Repeated["Th"] =     8;
	Repeated["We"] =     4;
	Repeated["Tu"] =     2;
	Repeated["Mo"] =     1;
	
	for(rep in Repeated) {
		if(rep.toString() != "extend") {
			var check = Number(Repeated[rep]);
			if(check <= num) {
				num -= check;
				if(html == "") {
					html += rep.toString();
				} else {
					html += "," + rep.toString();
				}
			}
		}
	}
	return html;
}

function colorTimerListEntry (state) {
	if (state == 0) {
		return "000000";
	} else if(state == 1) {
		return "00BCBC";
	} else if(state == 2) {
		return "9F1919";
	} else {
		return "00BCBC";
	}
}
function delTimer(serviceRef,begin,end,servicename,title,description){
	debug("delTimer: serviceRef("+serviceRef+"),begin("+begin+"),end("+end+"),servicename("+servicename+"),title("+title+"),description("+description+")");
	Dialog.confirm(
		"Selected timer:<br>"
		+"Channel: "+servicename+"<br>"
		+"Title: "+title+"<br>"
		+"Description: "+description+"<br>"
		+"Are you sure that you want to delete the Timer?",
		 {windowParameters: {width:300, className: windowStyle},
			okLabel: "delete",
			buttonClass: "myButtonClass",
			cancel: function(win) {debug("delTimer cancel confirm panel")},
			ok: function(win) { debug("delTimer ok confirm panel"); doRequest(url_timerdelete+"?serviceref="+serviceRef+"&begin="+begin+"&end="+end, incomingTimerDelResult, false); return true; }
			}
	);
}
function incomingTimerDelResult(request){
	debug("onTimerDeleted");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		debug("Lade liste");
		loadTimerList();
	}		
}

// send Messages
function showMessageSendForm(){
		document.getElementById('BodyContentChannellist').innerHTML = tplMessageSendForm;
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
		document.getElementById('BodyContentChannellist').innerHTML = tplPowerStateSendForm;
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
		document.getElementById('BodyContentChannellist').innerHTML = tplPowerStateSendForm2;
	} else {
		document.getElementById('BodyContentChannellist').innerHTML = "<h1>some unknown error</h1>" + tplPasswordSendForm;
	}
}

// RemoteControl Code
function showRemoteControllSendForm(){
		document.getElementById('BodyContentChannellist').innerHTML = tplRemoteControlForm;
}
function sendRemoteControlRequest(command){
	doRequest(url_remotecontrol+'?command='+command, incomingRemoteControlResult, false);
}
function incomingRemoteControlResult(request){
	if(request.readyState == 4){
		var b = getXML(request).getElementsByTagName("e2remotecontrol");
		var result = b.item(0).getElementsByTagName('e2result').item(0).firstChild.data;
		var resulttext = b.item(0).getElementsByTagName('e2resulttext').item(0).firstChild.data;
		showRemoteControllSendForm();
	} else {
		document.getElementById('BodyContentChannellist').innerHTML = "<h1>some unknown error</h1>" + tplRemoteControlForm;
	}
}

function loadTimerFormNow() {
	var now = new Date();
	addTimerEditFormObject["syear"] = now.getFullYear();
	addTimerEditFormObject["smonth"] = now.getMonth() + 1;
	addTimerEditFormObject["sday"] = now.getDate();
	addTimerEditFormObject["shour"] = now.getHours();
	addTimerEditFormObject["smin"] = now.getMinutes();

	var	plusTwoHours = new Date(now.getTime() + ((120 *60)*1000) );
	addTimerEditFormObject["eyear"] = plusTwoHours.getFullYear();
	addTimerEditFormObject["emonth"] = plusTwoHours.getMonth() + 1;
	addTimerEditFormObject["eday"] = plusTwoHours.getDate();
	addTimerEditFormObject["ehour"] = plusTwoHours.getHours();
	addTimerEditFormObject["emin"] = plusTwoHours.getMinutes();
		
	addTimerEditFormObject["justplay"] = "record";
	addTimerEditFormObject["channel"] = "";
	addTimerEditFormObject["channelName"] = "";
	addTimerEditFormObject["channelSort"] = "tv";
	addTimerEditFormObject["name"] = "";
	addTimerEditFormObject["description"] = "";
	addTimerEditFormObject["repeated"] = 0;
	addTimerEditFormObject["afterEvent"] = "0";
	addTimerEditFormObject["deleteOldOnSave"] = 0;
	
	addTimerEditFormObject["beginOld"] = 0;
	addTimerEditFormObject["endOld"] = 0;
	
	
	debug("loadTimerFormNow 2");
	loadTimerFormChannels();
}

function loadTimerFormSeconds(justplay,begin,end,repeated,channel,channelName,name,description,afterEvent,deleteOldOnSave,eit) {
	debug('justplay:'+justplay+' begin:'+begin+' end:'+end+' repeated:'+repeated+' channel:'+channel+' name:'+name+' description:'+description+' afterEvent:'+afterEvent+' deleteOldOnSave:'+deleteOldOnSave);
	var start = new Date(Number(begin)*1000);
	addTimerEditFormObject["syear"] = start.getFullYear();
	addTimerEditFormObject["smonth"] = start.getMonth() + 1;
	addTimerEditFormObject["sday"] = start.getDate();
	addTimerEditFormObject["shour"] = start.getHours();
	addTimerEditFormObject["smin"] = start.getMinutes();
	
	var	stopp = new Date(Number(end)*1000);
	addTimerEditFormObject["eyear"] = stopp.getFullYear();
	addTimerEditFormObject["emonth"] = stopp.getMonth() + 1;
	addTimerEditFormObject["eday"] = stopp.getDate();
	addTimerEditFormObject["ehour"] = stopp.getHours();
	addTimerEditFormObject["emin"] = stopp.getMinutes();
	
	addTimerEditFormObject["justplay"] = String(justplay);
	addTimerEditFormObject["channel"] = decodeURIComponent(String(channel));
	addTimerEditFormObject["channelName"] = String(channelName);
	addTimerEditFormObject["channelSort"] = "";
	addTimerEditFormObject["name"] = String(name);
	addTimerEditFormObject["description"] = String(description);
	addTimerEditFormObject["repeated"] = Number(repeated);
	addTimerEditFormObject["afterEvent"] = Number(afterEvent);
	
	debug(justplay+"|"+begin+"|"+end+"|"+repeated+"|"+channel+"|"+name+"|"+description+"|"+afterEvent);

	addTimerEditFormObject["deleteOldOnSave"] = Number(deleteOldOnSave);
	addTimerEditFormObject["beginOld"] = Number(begin);
	addTimerEditFormObject["endOld"] = Number(end);
	
	addTimerEditFormObject["eventID"] = Number(eit);
	
	loadTimerFormChannels();
}

// startin to load for TV
function loadTimerFormChannels() {
	if(addTimerEditFormObject["TVListFilled"] == 1 && addTimerEditFormObject["RadioListFilled"] == 1) {
		loadTimerForm();
	} else if(addTimerEditFormObject["TVListFilled"] == 1 && addTimerEditFormObject["RadioListFilled"] == 0) {
		addTimerListFormatTV();
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.tv%22%20ORDER%20BY%20bouquet'
		doRequest(url_fetchchannels+favorites, addTimerListFormatTV, false);
	}
}

function addTimerListFormatTV(request) {
	if(addTimerEditFormObject["RadioListFilled"] == 0) {
		if(request.readyState == 4){
			var services = new ServiceList(getXML(request)).getArray();
			var tv = new Object();
			for ( var i = 0; i < services.length ; i++){
				var reference = services[i];
				tv[reference.servicereference] = reference.servicename;
			}
			addTimerEditFormObject["TVListFilled"] = 1;
			addTimerEditFormObject["TVList"] = tv;
		}
	}
	if(addTimerEditFormObject["RadioListFilled"] == 1) {
		loadTimerForm()
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.radio%22%20ORDER%20BY%20bouquet';
		doRequest(url_fetchchannels+favorites, addTimerListFormatRadio, false);
	}
}
function addTimerListFormatRadio(request) {
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		var radio = new Object();
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			radio[reference.servicereference] = reference.servicename;
		}
		addTimerEditFormObject["RadioListFilled"] = 1;
		addTimerEditFormObject["RadioList"] = radio;
	}
	loadTimerForm();
}

function loadTimerForm(){

	var Action = new Object();
	Action["0"] = "Record";
	Action["1"] = "Zap";
	
	var Repeated = new Object();
	Repeated["1"] =  "mo";
	Repeated["2"] = "tu";
	Repeated["4"] =  "we";
	Repeated["8"] =  "th";
	Repeated["16"] = "fr";
	Repeated["32"] = "sa";
	Repeated["64"] = "su";
	Repeated["31"] = "mf";
	Repeated["127"] ="ms";
	
	var AfterEvent = new Object();
	AfterEvent["0"] = "Nothing";
	AfterEvent["1"] = "Standby";
	AfterEvent["2"] = "Deepstandby/Shutdown";
	
	addTimerEditFormObject["name"] = (typeof(addTimerEditFormObject["name"]) != "undefined") ? addTimerEditFormObject["name"] : "";
	addTimerEditFormObject["name"] = (addTimerEditFormObject["name"] == "") ? " " : addTimerEditFormObject["name"];

	addTimerEditFormObject["description"] = (typeof(addTimerEditFormObject["description"]) != "undefined") ? addTimerEditFormObject["description"] : "";
	addTimerEditFormObject["description"] = (addTimerEditFormObject["description"] == "") ? " " : addTimerEditFormObject["description"];

	var channelObject = addTimerEditFormObject["TVList"];
	if(	addTimerEditFormObject["channelSort"] == "tv") {
		// already set
	} else if( addTimerEditFormObject["channelSort"] == "radio") {
		channelObject = addTimerEditFormObject["RadioList"];
	} else {
		var found = 0;
		for( element in addTimerEditFormObject["TVList"]) {
			if( element == addTimerEditFormObject["channel"]) {
				found = 1;
				break;
			}
		}
		if(found == 0) {
			for( element in addTimerEditFormObject["RadioList"]) {
				if( element == addTimerEditFormObject["channel"]) {
					channelObject = addTimerEditFormObject["RadioList"];
					found = 1;
					break;
				}
			}
		}
		if(found == 0) {
			addTimerEditFormObject["TVList"][addTimerEditFormObject["channel"]] = addTimerEditFormObject["channelName"];
		}
	}
	var dashString = "------";
	channelObject[dashString] = "- Bouquets -";
	var listeNeu = new ServiceList(getXML(doRequestMemory[url_fetchchannels+encodeURIComponent(bouqet_tv)])).getArray();
	if(addTimerEditFormObject["channelSort"] == "radio") {
		debug("weiter");
		listeNeu = new ServiceList(getXML(doRequestMemory[url_fetchchannels+encodeURIComponent(bouqet_radio)])).getArray();
	}
	debug("hier" + listeNeu.length);
	for (i = 1; i < listeNeu.length; i++) {
		var element = listeNeu[i];
		channelObject[String(dashString+i)] = "---";
		channelObject[element.getServiceReference()] = element.getServiceName();
	}
	debug("geklappt" + channelObject.length);
	var namespace = { 	
				'justplay': addTimerFormCreateOptionList(Action, addTimerEditFormObject["justplay"]),
				'syear': addTimerFormCreateOptions(2007,2010,addTimerEditFormObject["syear"]),
				'smonth': addTimerFormCreateOptions(1,12,addTimerEditFormObject["smonth"]),
				'sday': addTimerFormCreateOptions(1,31,addTimerEditFormObject["sday"]),
				'shour': addTimerFormCreateOptions(0,23,addTimerEditFormObject["shour"]),
				'smin': addTimerFormCreateOptions(0,59,addTimerEditFormObject["smin"]),
				'eyear': addTimerFormCreateOptions(2007,2010,addTimerEditFormObject["eyear"]),
				'emonth': addTimerFormCreateOptions(1,12,addTimerEditFormObject["emonth"]),
				'eday': addTimerFormCreateOptions(1,31,addTimerEditFormObject["eday"]),
				'ehour': addTimerFormCreateOptions(0,23,addTimerEditFormObject["ehour"]),
				'emin': addTimerFormCreateOptions(0,59,addTimerEditFormObject["emin"]),
				'channel': addTimerFormCreateOptionList(channelObject, addTimerEditFormObject["channel"]),
				'name': addTimerEditFormObject["name"],
				'description': addTimerEditFormObject["description"],
				'repeated': addTimerFormCreateOptionListRepeated(Repeated, addTimerEditFormObject["repeated"]),
				'deleteOldOnSave': addTimerEditFormObject["deleteOldOnSave"],
				'channelOld': addTimerEditFormObject["channel"],
				'beginOld': addTimerEditFormObject["beginOld"],
				'endOld': addTimerEditFormObject["endOld"],
				'afterEvent': addTimerFormCreateOptionList(AfterEvent, addTimerEditFormObject["afterEvent"]),
				'eventID': addTimerEditFormObject["eventID"]
		};
	var listerHtml = RND(tplAddTimerForm, namespace);
	document.getElementById('BodyContentChannellist').innerHTML = listerHtml;

	// Empty some stuff, but keep others to have the performance
	var tmp1 = addTimerEditFormObject["RadioList"];
	var tmp2 = addTimerEditFormObject["TVList"];
	addTimerEditFormObject = new Object();
	addTimerEditFormObject["deleteOldOnSave"] = 0;
	addTimerEditFormObject["RadioList"] = tmp1;
	addTimerEditFormObject["TVList"] = tmp2;
	addTimerEditFormObject["TVListFilled"] = 1;
	addTimerEditFormObject["RadioListFilled"] = 1;
}

function addTimerFormCreateOptions(start,end,number) {
	var html = '';
	for(i = start; i <= end; i++) {
		var txt = (String(i).length == 1) ? "0" + String(i) : String(i);
		var selected = 	(i == Number(number)) ? "selected" : " ";
		var namespace = {
			'value': i,
			'txt': txt,
			'selected': selected };
		html += RND(tplAddTimerFormOptions, namespace);
	}
	return html;
}
function addTimerFormCreateOptionList(object,selected) {
	html = '';
	var found = 0;
	for(var element in object) {
		var txt = String(object[element]);
		var sel = " ";
		if(element == selected) {
			found = 1;
			sel = "selected";
		}
		var namespace = {
			'value': element,
			'txt': txt,
			'selected': sel };
		if(element != "extend") {
			html += RND(tplAddTimerFormOptions, namespace);
		}
	}
	if(found == 0) {
		var namespace = {
			'value': element,
			'txt': txt,
			'selected': sel };
	}
	return html;
}

function timerFormExtendChannellist(bouqet) {
	var listeTV = new ServiceList(getXML(doRequestMemory[url_fetchchannels+encodeURIComponent(bouqet_tv)])).getArray();
	var listeRadio = new ServiceList(getXML(doRequestMemory[url_fetchchannels+encodeURIComponent(bouqet_radio)])).getArray();
	found = 0;
	for(i = 0; i < listeTV.length; i++) {
		var element = listeTV[i];
		if(String(element.getServiceReference()) == bouqet) {
			found = 1;
			break;
		}
	}
	if(found == 0) {
		for(i = 0; i < listeRadio.length; i++) {
			var element = listeTV[i];
			if(String(element.getServiceReference()) == bouqet) {
				found = 1;
				break;
			}
		}
	}
	if(found == 1) {
		servicereftoloadepgnow = bouqet;
		if(typeof(loadedChannellist[servicereftoloadepgnow]) == "undefined") {	
			doRequest(url_fetchchannels+servicereftoloadepgnow, incomingTimerFormExtendChannellist, true);
		} else {
			incomingTimerFormExtendChannellist();
		}
	}
}
function incomingTimerFormExtendChannellist(request) {
	var services = null;
	if(typeof(loadedChannellist[servicereftoloadepgnow]) != "undefined"){
		services = loadedChannellist[servicereftoloadepgnow];
	} else if(request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		loadedChannellist[servicereftoloadepgnow] = services;
		debug("got "+services.length+" Services");
	}
	var attachLater = new Object();
	if(services != null) {
		debug("incomingTimerFormExtendChannellist " + services.length);
		var selected = $('channel').selectedIndex;
		for(j = selected; j < $('channel').options.length; j++) {
			if($('channel').options[j].value == servicereftoloadepgnow) {
				j++;
				for(var i = 0; i < services.length ; i++) {
					var reference = services[i];
					var newEntry = new Option(reference.getServiceName(), reference.getServiceReference(), false, true);
					if(typeof($('channel').options[j]) != "undefined") {
						attachLater[String($('channel').options[j].value)] = $('channel').options[j].text;
					}
					$('channel').options[j] = newEntry;
					j++;
				}
			}
			break;
		}
		for(x in attachLater) {
			var newEntry = new Option(attachLater[x], x, false, true);
			if(x != "extend") {
				$('channel').options[$('channel').options.length] = newEntry;
			}
		}
		$('channel').options[selected].selected = true;
		
	}
}
//doRequest(url_fetchchannels+servicereference, incomingChannellist, true);

function addTimerFormChangeTime(which) {
	var start = new Date( $('syear').value, ($('smonth').value -1), $('sday').value, $('shour').value, $('smin').value, 0);
	var end = new Date($('eyear').value, ($('emonth').value -1), $('eday').value, $('ehour').value, $('emin').value, 0);
//	debug("("+start+")(" + end+")");

	if(start.getTime() > end.getTime()) {
		opponent = (which.substr(0,1) == 's') ? 'e' +  which.substr(1, which.length -1) : 's' +  which.substr(1, which.length -1) ;
		$(opponent).value = $(which).value;
	}
	var all = new Array('year','month','day','hour','min');
	for(i=0; i < all.length; i++) {
		if(which.substr(1, which.length -1) == all[i]) {
			addTimerFormChangeTime(which.substr(0,1) + all[i+1] );
			break;
		}
	}
}
function addTimerFormChangeType() {
	var selected = ($('tvradio').checked == true) ? addTimerEditFormObject["TVList"]: addTimerEditFormObject["RadioList"];
	for (i = $('channel').options.length; i != 0; i--) {
		$('channel').options[i - 1] = null;
	}
	var i = -1;
	for(element in selected) {
		if(element != "extend") {
			i++;
			$('channel').options[i] = new Option(selected[element]);
			$('channel').options[i].value = element;
		}
	}
}
function addTimerFormCreateOptionListRepeated(Repeated,repeated) {
	var num = Number(repeated);
	var html = "";
	var html2 = "";
	var list = new Array(127, 64, 32, 31, 16, 8, 4, 2, 1);
	for(i = 0; i < list.length; i++) {
		var txt = String(Repeated[String(list[i])]);
		if( String(Repeated[String(list[i])]) == "mf") {
			txt = "Mo-Fr";
		} else if( String(Repeated[String(list[i])]) == "ms") {
			txt = "Mo-Su";
		} else {
			txt = txt.substr(0,1).toUpperCase() + txt.substr(1,1);
		}
		var checked = " ";
		if(num >=  list[i]) {
			num -= list[i];
			checked = "checked";
		}
		var namespace = {
			'id': Repeated[String(list[i])],
			'name': Repeated[String(list[i])],
			'value': list[i],
			'txt': txt,
			'checked': checked };
		if(String(Repeated[String(list[i])]) == "mf" || String(Repeated[String(list[i])]) == "ms") {
			html2 = RND(tplAddTimerFormCheckbox, namespace) + html2;
		} else {
			html = RND(tplAddTimerFormCheckbox, namespace) + html;
		}
	}
	return html + html2;
}
function sendAddTimer() {
	debug("sendAddTimer" + "parentChannel:" +$('channel').value);
	
	if(parentPin($('channel').value)) {
		var beginD = new Date(ownLazyNumber($('syear').value), (ownLazyNumber($('smonth').value) - 1), ownLazyNumber($('sday').value), ownLazyNumber($('shour').value), ownLazyNumber($('smin').value));
		var begin = beginD.getTime()/1000;
		
		var endD = new Date(ownLazyNumber($('eyear').value), (ownLazyNumber($('emonth').value) - 1), ownLazyNumber($('eday').value), ownLazyNumber($('ehour').value), ownLazyNumber($('emin').value));
		var end = endD.getTime()/1000;

		var repeated = 0;
		if( $('ms').checked ) {
			repeated = 127;
		} else if($('mf').checked) {
			repeated = 31;
			if($('sa').checked) {
				repeated += ownLazyNumber($('sa').value);
			}
			if($('su').checked) {
				repeated += ownLazyNumber($('su').value);
			}
		} else {
			var check = new Array('mo', 'tu', 'we', 'th', 'fr');
			for(i = 0; i < check.length; i++) {
				if($(check[i]).cheked) {
					repeated += Number($(check[i]).value);
				}
			}
		}
	
		var descriptionClean = ($('descr').value == " " || $('descr').value == "N/A") ? "" : $('descr').value;
		var nameClean = ($('name').value == " " || $('name').value == "N/A") ? "" : $('name').value;
	
		var repeated = 0;
		if($('ms').checked) {
			repeated = ownLazyNumber($('ms').value);
		} else if($('mf').checked) {
			repeated = ownLazyNumber($('mf').value);
			if($('su').checked) {
				repeated += ownLazyNumber($('su').value);
			}
			if($('sa').checked) {
				repeated += ownLazyNumber($('sa').value);
			}
		} else {
			if($('mo').checked) {
				repeated += ownLazyNumber($('mo').value);
			}
			if($('tu').checked) {
				repeated += ownLazyNumber($('tu').value);
			}
			if($('we').checked) {
				repeated += ownLazyNumber($('we').value);
			}
			if($('th').checked) {
				repeated += ownLazyNumber($('th').value);
			}
			if($('fr').checked) {
				repeated += ownLazyNumber($('fr').value);
			}
			if($('sa').checked) {
				repeated += ownLazyNumber($('sa').value);
			}
			if($('su').checked) {
				repeated += ownLazyNumber($('su').value);
			}
		}
		//addTimerByID(\'%(servicereference)\',\'%(eventid)\',\'False\');
		doRequest(url_timerchange+"?"+"serviceref="+($('channel').value).replace("&quot;", '"')+"&begin="+begin
		  +"&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean)
		  +"&afterevent="+$('after_event').value+"&eit=0&disabled=0"
		  +"&justplay="+ownLazyNumber($('justplay').value)+"&repeated="+repeated
		  +"&channelOld="+$('channelOld').value
		  +"&beginOld="+$('beginOld').value+"&endOld="+$('endOld').value
		  +"&eventID"+$('eventID').value
		  +"&deleteOldOnSave="+ownLazyNumber($('deleteOldOnSave').value), incomingTimerAddResult, false);
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

	doRequest(url_timerchange+"?"+"serviceref="+channel.replace("&quot;", '"')+"&begin="+begin
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
					document.getElementById(reference.getServiceReference()+'extend').innerHTML = "";
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
			document.getElementById(first.getServiceReference()+'extend').innerHTML = listerHtml;
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
	new Ajax.Request( url_timerlistwrite, { method: 'get' });
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
		document.getElementById("BodyContentChannellist").style.height = '20%';
	} else if(screenH == 1024) {
		debug("1024")
		document.getElementById("BodyContentChannellist").style.height = '760px';
		
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
				var namespace = {
					'enigmaVersion': xml.getElementsByTagName('e2enigmaversion').item(0).firstChild.data
					,'lanDHCP': xml.getElementsByTagName('e2landhcp').item(0).firstChild.data
					,'lanIP': xml.getElementsByTagName('e2lanip').item(0).firstChild.data
					,'lanMask': xml.getElementsByTagName('e2lanmask').item(0).firstChild.data
					,'lanGW': xml.getElementsByTagName('e2langw').item(0).firstChild.data
					,'lanDNS': xml.getElementsByTagName('e2landns').item(0).firstChild.data
					,'fpVersion': xml.getElementsByTagName('e2fpversion').item(0).firstChild.data
					,'tunerInfo': xml.getElementsByTagName('e2tunerinfo').item(0).firstChild.data
					,'hddInfo': xml.getElementsByTagName('e2hddinfo').item(0).firstChild.data
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
				document.getElementById('BodyContentChannellist').innerHTML = RND(tplAbout, namespace);;
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