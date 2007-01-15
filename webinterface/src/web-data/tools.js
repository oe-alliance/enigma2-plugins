var url_getvolume = '/web/vol?set=state'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?ref="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnownext = "/web/epgnownext?ref="; // plus serviceRev

var url_fetchchannels = "/web/fetchchannels?ServiceListBrowse="; // plus encoded serviceref

var url_updates= "/web/updates";

var DBG = false;

/**
*
*  UTF-8 data encode / decode
*  http://www.webtoolkit.info/
*
**/

var Utf8 = {

    // public method for url encoding
    encode : function (string) {
        string = string.replace(/\r\n/g,"\n");
        var utftext = "";

        for (var n = 0; n < string.length; n++) {

            var c = string.charCodeAt(n);

            if (c < 128) {
                utftext += String.fromCharCode(c);
            }
            else if((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            }
            else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }

        }

        return utftext;
    },

    // public method for url decoding
    decode : function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;

        while ( i < utftext.length ) {

            c = utftext.charCodeAt(i);

            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            }
            else if((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            }
            else {
                c2 = utftext.charCodeAt(i+1);
                c3 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }

        }

        return string;
    }

}

// UpdateStreamReader
var UpdateStreamReaderNextReadPos = 0;
var UpdateStreamReaderPollTimer;
UpdateStreamReaderRequest = null;
function UpdateStreamReaderStart(){
	var ua = navigator.userAgent;
	if(navigator.userAgent.indexOf("MSIE") >=0) {
		debug("UpdateStreamReader IE Fix *IE sucks*");
		$('UpdateStreamReaderIEFixPanel').innerHTML = '<iframe id="UpdateStreamReaderIEFixIFrame" src="'+url_updates+'" height="0" width="0" scrolling="none" frameborder="0">no iframe support!</iframe>';
	}else {
		debug("UpdateStreamReader Start");
		UpdateStreamReaderNextReadPos = 0;
		allMessages = "";
		UpdateStreamReaderRequest =new XMLHttpRequest();
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
			anUpdate = anUpdate.replace(/<div id="scriptzone"\/>/,'');
			anUpdate = anUpdate.replace(/<script>parent./, '');
			anUpdate = anUpdate.replace(/<\/script>\n/, '');
			anUpdate = Utf8.decode(anUpdate);

			//debug(Utf8.decode(anUpdate))
			eval(anUpdate);
			UpdateStreamReaderNextReadPos += endOfFirstMessageIndex;
		}
	} while (messageXMLEndIndex != -1);
}

function UpdateStreamReaderOnLoad(){
	window.clearInterval(UpdateStreamReaderPollTimer);
	debug("UpdateStreamReaderOnLoad");
	Dialog.confirm(
		"Live Update Stream ends!<br><br>You will not receive any Update from Enigma2.<br>Should I reconnect?",
		 {windowParameters: {width:300, className: "alphacube"},
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
		 {windowParameters: {width:300, className: "alphacube"},
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
			var win = new Window(id, {className: "alphacube", title: title, width: width, height: height});
			win.getContent().innerHTML = inner;
			win.setDestroyOnClose();
			win.showCenter();
			debug("opening Window: "+title);
			return win;
}

function messageBox(t, m){
	Dialog.alert(m, {windowParameters: {title: t, className: "alphacube", width:200}, okLabel: "Close"});
}

function getHTTPObject( ){
    var xmlHttp = false;
            
    // try to create a new instance of the xmlhttprequest object        
    try{
        // Internet Explorer
        if( window.ActiveXObject ){
            for( var i = 5; i; i-- ){
                try{
                    // loading of a newer version of msxml dll (msxml3 - msxml5) failed
                    // use fallback solution
                    // old style msxml version independent, deprecated
                    if( i == 2 ){
                        xmlHttp = new ActiveXObject( "Microsoft.XMLHTTP" );    
                    }
                    // try to use the latest msxml dll
                    else{
                        
                        xmlHttp = new ActiveXObject( "Msxml2.XMLHTTP." + i + ".0" );
                    }
                    break;
                }
                catch( excNotLoadable ){                        
                    xmlHttp = false;
                }
            }
        }
        // Mozilla, Opera und Safari
        else if( window.XMLHttpRequest ){
            xmlHttp = new XMLHttpRequest();
        }
    }
    // loading of xmlhttp object failed
    catch( excNotLoadable ){
        xmlHttp = false;
    }
    return xmlHttp ;
}

//RND Template Function
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
	//debug("requesting "+url);
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
		debug("using responseXML");
		var xmlDoc = request.responseXML
	}
	else if (window.ActiveXObject){
		debug("Creating XML for IE");
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

function zap(li){
	var url = "/web/zap?ZapTo=" + escape(li.id);
	//debug("requesting "+url);
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
var EPGList = Class.create();
EPGList.prototype = {
	//contructor
	initialize: function(){
		debug("init class EPGList");
	},
	getBySearchString: function(string){
		debug("requesting "+ url_epgsearch+string);
		doRequest(url_epgsearch+string,this.incomingEPGrequest);
		
	},
	getByServiceReference: function(serviceRef){
		doRequest(url_epgservice+serviceRef,this.incomingEPGrequest);
	},
	
	
	renderTable: function(epglist){
		debug("rendering Table with "+epglist.length+" events");
		var html = tplEPGListHeader;
		for (var i=0; i < epglist.length; i++){
			try{
				var item = epglist[i];
				
				//Create JSON Object for Template
				var namespace = { 	'date': item.getTimeDay(), 
									'servicename': item.getServiceName(), 
									'title': item.getTitle(),
									'titleESC': escape(item.getTitle()),
									'starttime': item.getTimeStartString(), 
									'duration': (item.getDuration()/60000), 
									'description': item.getDescription(), 
									'endtime': item.getTimeEndString(), 
									'extdescription': item.getDescriptionExtended()
								};
				//Fill template with data and add id to our result
				html += RND(tplEPGListItem, namespace);
			} catch (blubb) {
				//debug("Error rendering: "+blubb);
			}
		}
		
		html += tplEPGListFooter;
		//element.innerHTML = html;
		openWindow("Electronic Program Guide", html, 900, 500);
		
	},
	incomingEPGrequest: function(request){
		debug("incoming request" +request.readyState);		
		if (request.readyState == 4)
		{
			var EPGItems = getXML(request).getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
			
			debug("have "+EPGItems.length+" e2events");
			if(EPGItems.length > 0){
			
				epglist = new Array();
				for(var i=0; i < EPGItems.length; i++){		
					epglist.push(new EPGEvent(EPGItems.item(i)));
				}
				debug("Calling prototype.renderTable(epglist)");
				EPGList.prototype.renderTable(epglist);
				
			} else {
				messageBox('No Items found!', 'Sorry but i could not find any EPG Content containing your search value');
			}
			
		}
	}
	
}

function EPGEvent(element){	
	// parsing values from xml-element
	try{
		this.eventID = element.getElementsByTagName('e2eventid').item(0).firstChild.data;
		this.startTime = element.getElementsByTagName('e2eventstart').item(0).firstChild.data;
		this.duration = element.getElementsByTagName('e2eventduration').item(0).firstChild.data;
		this.title = element.getElementsByTagName('e2eventtitle').item(0).firstChild.data;
		this.serviceRef = element.getElementsByTagName('e2eventservicereference').item(0).firstChild.data;
		this.serviceName = element.getElementsByTagName('e2eventservicename').item(0).firstChild.data;
	} catch (e) {
		debug("EPGEvent parsing Error");
	}	
	try{
		this.description = element.getElementsByTagName('e2eventdescription').item(0).firstChild.data;
	} catch (e) {	this.description= 'N/A';	}
	
	try{
		this.descriptionE = element.getElementsByTagName('e2eventdescriptionextended').item(0).firstChild.data;
	} catch (e) {	this.descriptionE = 'N/A';	}

	
	this.getEventId = function ()
	{
		return this.eventID;
	}
	this.getTimeStart = function ()
	{
		var date = new Date(parseInt(this.startTime)*1000);
		return date;
	}
	this.getTimeStartString = function ()
	{
		var h = this.getTimeStart().getHours();
		var m = this.getTimeStart().getMinutes();
		if (m < 10){
			m="0"+m;
		}
		return h+":"+m;
	}
	this.getTimeDay = function ()
	{
		var Wochentag = new Array("So", "Mo", "Di", "Mi", "Do", "Fr", "Sa");
		var wday = Wochentag[this.getTimeStart().getDay()];
		var day = this.getTimeStart().getDate();
		var month = this.getTimeStart().getMonth()+1;
		var year = this.getTimeStart().getFullYear();
		
		return wday+".&nbsp;"+day+"."+month+"."+year;
	}
	this.getTimeEnd = function ()
	{
		var date = new Date((parseInt(this.startTime)+parseInt(this.duration))*1000);
		return date;
	}
	this.getTimeEndString = function ()
	{
		var h = this.getTimeEnd().getHours();
		var m = this.getTimeEnd().getMinutes();
		if (m < 10){
			m="0"+m;
		}
		return h+":"+m;
	}
	this.getDuration = function ()
	{
		return  new Date(parseInt(this.duration)*1000);
	}
	this.getTitle = function ()
	{
		return this.title;
	}
	this.getDescription = function ()
	{
		return this.description;
	}
	this.getDescriptionExtended = function ()
	{
		return this.descriptionE;
	}
	this.getServiceReference = function ()
	{
		return this.serviceRef;
	}
	this.getServiceName = function ()
	{
		return this.serviceName.replace(" ","&nbsp;");
	}
}//END class EPGEvent

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
	debug("init ChannelList");	

	//refreshChannellist('Favourites (TV)', '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet');
	var url = url_fetchchannels+encodeURIComponent('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)FROM BOUQUET "bouquets.tv" ORDER BY bouquet');
	doRequest(url, incomingTVBouquetList);

	var url = url_fetchchannels+encodeURIComponent('1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET "bouquets.radio" ORDER BY bouquet');
	doRequest(url, incomingRadioBouquetList);

	var url = url_fetchchannels+encodeURIComponent('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name');
	doRequest(url, incomingProviderTVBouquetList);

	var url = url_fetchchannels+encodeURIComponent('1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name');
	doRequest(url, incomingProviderRadioBouquetList);
}

function loadBouquet(servicereference){ 
	debug("loading bouquet with "+servicereference);	
	doRequest(url_fetchchannels+servicereference, incomingChannellist);
}

function incomingTVBouquetList(request){
	if (request.readyState == 4) {
		var list0 = e2servicelistToArray(getXML(request));
		debug("have "+list0.length+" TV Bouquet ");	
		$('accordionMenueBouquetContentTV').innerHTML = renderBouquetTable(list0,tplBouquetListItem);
		
		//loading first entry of TV Favorites as default for ServiceList
		loadBouquet(list0[0][1]);
	}
}
function incomingRadioBouquetList(request){
	if (request.readyState == 4) {
		var list1 = e2servicelistToArray(getXML(request));
		debug("have "+list1.length+" Radio Bouquet ");	
		$('accordionMenueBouquetContentRadio').innerHTML = renderBouquetTable(list1,tplBouquetListItem);
	}	
}
function incomingProviderTVBouquetList(request){
	if (request.readyState == 4) {
		var list2 = e2servicelistToArray(getXML(request));
		debug("have "+list2.length+" TV Provider Bouquet ");	
		$('accordionMenueBouquetContentProviderTV').innerHTML = renderBouquetTable(list2,tplBouquetListItem);
	}	
}
function incomingProviderRadioBouquetList(request){
	if (request.readyState == 4) {
		var list2 = e2servicelistToArray(getXML(request));
		debug("have "+list2.length+" Radio Provider Bouquet ");	
		$('accordionMenueBouquetContentProviderRadio').innerHTML = renderBouquetTable(list2,tplBouquetListItem);
	}	
}

function e2servicelistToArray(xml){
	var b = xml.getElementsByTagName("e2servicelist").item(0).getElementsByTagName("e2service");
	var list = new Array();
	for ( var i=0; i < b.length; i++){
		var bRef = escape(b.item(i).getElementsByTagName('e2servicereference').item(0).firstChild.data.replace('&quot;', '"'));
		var bName = b.item(i).getElementsByTagName('e2servicename').item(0).firstChild.data;
		var listitem = new Array(bName,bRef);
		list.push(listitem)
	}
	return list
}

function renderBouquetTable(bouquet,template){
	var html = tplBouquetListHeader;
	for (var i=0; i < bouquet.length; i++){
		try{
			var item = bouquet[i];
			
			//Create JSON Object for Template
			var namespace = {
				'bouquetname': item[0], 
				'servicereference': item[1] 
				};
			
			html += RND(template, namespace);
		} catch (blubb) {}
	}
	html += tplBouquetListFooter;
	return html;
}	

function incomingChannellist(request){
	if(request.readyState == 4){

		services = getXML(request).getElementsByTagName("e2servicelist").item(0).getElementsByTagName("e2service");
		
		listerHtml 	= tplServiceListHeader;
		
		debug("got "+services.length+" Services");
		
		for ( var i = 0; i < (services.length ); i++){
			sRef = services.item(i).getElementsByTagName('e2servicereference').item(0).firstChild.data;
			sName = services.item(i).getElementsByTagName('e2servicename').item(0).firstChild.data;
				
			var namespace = { 	'serviceref': sRef,
								'servicerefESC': escape(sRef), 
								'servicename': sName 
							};
							
			listerHtml += RND(tplServiceListItem, namespace);
			
		}
		
		listerHtml += tplServiceListFooter;
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
	}
}




