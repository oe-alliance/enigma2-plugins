var url_getvolume = '/web/vol?set=state'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?ref="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnow = "/web/epgnow?bref="; // plus bouqetRev

var url_fetchchannels = "/web/fetchchannels?ServiceListBrowse="; // plus encoded serviceref

var url_updates= "/web/updates";

var url_movielist= "/web/movielist";

var url_timerlist= "/web/timerlist";
var url_timeradd= "/web/timeradd"; // plus serviceref,begin,end,name,description,eit,disabled,justplay,afterevent
var url_timeraddbyeventid= "/web/timeraddbyeventid"; // plus serviceref,eventid
var url_timerdelete= "/web/timerdelete"; // plus serviceref,bedin,end

var url_message = "/web/message"; // plus text,type,timeout

var bouqet_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)FROM BOUQUET "bouquets.tv" ORDER BY bouquet';
var bouqet_radio = '1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET "bouquets.radio" ORDER BY bouquet';
var bouqet_provider_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name';
var bouqet_provider_radio ='1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name';

var windowStyle = "alphacube";
var DBG = false;

// UpdateStreamReader
var UpdateStreamReaderNextReadPos = 0;
var UpdateStreamReaderPollTimer;
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
		UpdateStreamReaderPollTimer = setInterval(UpdateStreamReaderLatestResponse, 500);
	}
}
  
function UpdateStreamReaderLatestResponse() {
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
			
			//debug(id);
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

function doRequest(url, readyFunction){
	requestStarted();
	new Ajax.Request(url,
		{
			method: 'get',
			requestHeaders: ['Pragma', 'no-cache', 'Cache-Control', 'must-revalidate', 'If-Modified-Since', 'Sat, 1 Jan 2000 00:00:00 GMT'],
			onSuccess: readyFunction,
			onComplete: requestFinished 
		});
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

function zap(servicereference){
	var url = "/web/zap?ZapTo=" + servicereference;
	new Ajax.Request( url,
		{
			method: 'get' 				
		});
}
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++       SignalPanel                           ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

function initSignalPanel(){
	$('SignalPanel').innerHTML = tplSignalPanelButton;
}
function openSignalDialog(){
	openWindow("Signal Info",tplSignalPanel, 215, 75);
}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ EPG functions                               ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
function loadEPGBySearchString(string){
		doRequest(url_epgsearch+string,incomingEPGrequest);
}
function loadEPGByServiceReference(servicereference){
		doRequest(url_epgservice+servicereference,incomingEPGrequest);
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
					//Create JSON Object for Template
					var namespace = { 	
							'date': item.getTimeDay(), 
							'eventid': item.getEventId(), 
							'servicereference': item.getServiceReference(), 
							'servicename': item.getServiceName(), 
							'title': item.getTitle(),
							'titleESC': escape(item.getTitle()),
							'starttime': item.getTimeStartString(), 
							'duration': Math.ceil(item.getDuration()/60000), 
							'description': item.getDescription(), 
							'endtime': item.getTimeEndString(), 
							'extdescription': item.getDescriptionExtended()
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
	

/////////////////////////

function loadServiceEPGNowNext(servicereference){
	var url = url_epgnow+servicereference;
	doRequest(url, incomingServiceEPGNowNext);	
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
function getVolume()
{
	doRequest(url_getvolume,handleVolumeRequest);
}
function volumeSet(newvalue)
{
	doRequest(url_setvolume+newvalue,handleVolumeRequest);
}
function volumeUp()
{
	doRequest(url_volumeup,handleVolumeRequest);
}
function volumeDown()
{
	doRequest(url_volumedown,handleVolumeRequest);	
}
function volumeMute()
{
	doRequest(url_volumemute,handleVolumeRequest);
}
function handleVolumeRequest(request){
	if (request.readyState == 4) {
		var b = getXML(request).getElementsByTagName("e2volume");
		var newvalue = b.item(0).getElementsByTagName('e2current').item(0).firstChild.data;
		var mute = b.item(0).getElementsByTagName('e2ismuted').item(0).firstChild.data;
		debug("volume"+newvalue+";"+mute);
		
		for (var i = 1; i <= 10; i++)
		{
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
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ bouquet managing functions                  ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
function initChannelList(){
	//debug("init ChannelList");	
	var url = url_fetchchannels+encodeURIComponent(bouqet_tv);
	doRequest(url, incomingTVBouquetList);

	var url = url_fetchchannels+encodeURIComponent(bouqet_radio);
	doRequest(url, incomingRadioBouquetList);

	var url = url_fetchchannels+encodeURIComponent(bouqet_provider_tv);
	doRequest(url, incomingProviderTVBouquetList);

	var url = url_fetchchannels+encodeURIComponent(bouqet_provider_radio);
	doRequest(url, incomingProviderRadioBouquetList);
}
var servicereftoloadepgnow="";
function loadBouquet(servicereference){ 
	debug("loading bouquet with "+servicereference);
	servicereftoloadepgnow = servicereference;
	doRequest(url_fetchchannels+servicereference, incomingChannellist);
}

function incomingTVBouquetList(request){
	if (request.readyState == 4) {
		var list0 = new ServiceList(getXML(request)).getArray();
		debug("have "+list0.length+" TV Bouquet ");	
		$('accordionMenueBouquetContentTV').innerHTML = renderBouquetTable(list0,tplBouquetListHeader,tplBouquetListItem,tplBouquetListFooter);
		//loading first entry of TV Favorites as default for ServiceList
		loadBouquet(list0[0].getServiceReference());
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
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		listerHtml 	= tplServiceListHeader;		
		debug("got "+services.length+" Services");
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
				'tags': movie.getTags().join(', ') 
			};
			debug(movie.getServiceReference());
			listerHtml += RND(tplMovieListItem, namespace);
		}
		listerHtml += tplMovieListFooter;
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
		
	}		
}

// Timer
function addTimerByID(serviceRef,eventID){
	debug("adding timer by eventid="+eventID+" for "+serviceRef);
	doRequest(url_timeraddbyeventid+"?serviceref="+serviceRef+"&eventid="+eventID, incomingTimerAddResult);	
}
function incomingTimerAddResult(request){
	debug("onTimerAdded");
	if(request.readyState == 4){
		var addresult = new TimerAddResult(getXML(request));
		if(addresult.getState()){
			//timer was add
			loadTimerList();
		}else{
			messageBox("Timer Error","your Timer could not be added!\nReason: "+addresult.getStateText());
		}
	}		
}
function loadTimerList(){
	debug("loading timers");
	doRequest(url_timerlist, incomingTimerList);	
}

function incomingTimerList(request){
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		listerHtml 	= tplTimerListHeader;		
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];
			var namespace = { 	
				'servicereference': timer.getServiceReference(),
				'servicename': timer.getServiceName() ,
				'title': timer.getName(), 
				'description': timer.getDescription(), 
				'descriptionextended': timer.getDescriptionExtended(), 
				'begin': timer.getTimeBegin(), 
				'end': timer.getTimeEnd(), 
				'state': timer.getState(),
				'duration': Math.ceil((timer.getDuration()/60))
			};
			listerHtml += RND(tplTimerListItem, namespace);
		}
		listerHtml += tplTimerListFooter;
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
		
	}
}
function delTimer(serviceRef,begin,end){
	debug("deleting timer with serviceRef="+serviceRef+" and start="+begin+"end="+end );
	debug(url_timerdelete+"?serviceref="+serviceRef+"&begin="+begin+"&end="+end);
	doRequest(url_timerdelete+"?serviceref="+serviceRef+"&begin="+begin+"&end="+end, incomingTimerDelResult);	
}

function incomingTimerDelResult(request){
	debug("onTimerDeleted");
	debug(request.readyState);
	if(request.readyState == 4){
		var delresult = new TimerAddResult(getXML(request));
		debug("Lade liste");
		loadTimerList();
	}		
}
function loadTimerForm() {
	debug("timers form");
	debug("there is still work to do here");
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
	doRequest(url_message+'?text='+messagetext+'&type='+messagetype+'&timeout='+messagetimeout, incomingMessageResult);
}
function incomingMessageResult(request){
	if(request.readyState == 4){
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