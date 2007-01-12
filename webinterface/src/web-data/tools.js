var url_getvolume = '/web/vol?set=info'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?ref="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnownext = "/web/epgnownext?ref="; // plus serviceRev

var DBG = false;

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
	element = document.getElementById(what);
	element.innerHTML = value;
	//$('scriptzone').innerHTML = ""; // deleting set() from page, to keep the page short and to save memory
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
	var request = getHTTPObject();
	var url = "/web/zap?ZapTo=" + escape(li.id);
	//debug("requesting "+url);
	new Ajax.Request( url,
			{
				method: 'get' 
				
			});
		
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
		new Ajax.Request( url_epgsearch+string,
			{
				method: 'get', 
				onComplete: this.incomingEPGrequest
			});
		
	},
	getByServiceReference: function(serviceRef){
		new Ajax.Request(url_epgservice+serviceRef,
			{
				method: 'get', 
				onComplete: this.incomingEPGrequest
			});
		
	},
	
	
	renderTable: function(epglist){
		debug("rendering Table with "+epglist.length+" events");
		var html='<table width="100%" border="0" cellspacing="1" cellpadding="0" border="1">';
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
		
		html +="</table>";
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
		this.eventID= element.getElementsByTagName('e2eventid').item(0).firstChild.data;
		this.startTime= element.getElementsByTagName('e2eventstart').item(0).firstChild.data;
		this.duration= element.getElementsByTagName('e2eventduration').item(0).firstChild.data;
		this.title= element.getElementsByTagName('e2eventtitle').item(0).firstChild.data;
		this.description= element.getElementsByTagName('e2eventdescription').item(0).firstChild.data;
		this.descriptionE= element.getElementsByTagName('e2eventdescriptionextended').item(0).firstChild.data;
		this.serviceRef= element.getElementsByTagName('e2eventservicereference').item(0).firstChild.data;
		this.serviceName= element.getElementsByTagName('e2eventservicename').item(0).firstChild.data;
	} catch (bullshit) {
		//debug("Bullshit is:"+bullshit);
	}
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
function doRequest(url,readyFunction){
	
	http_request =getHTTPObject();
	if(readyFunction){
		http_request.onreadystatechange = readyFunction;
	}
	http_request.open('GET', url, true);
	http_request.send(null);
	return http_request;
}
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//++++ volume functions                            ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++

function initVolumePanel(){
	document.getElementById('VolumePanel').innerHTML = tplVolumePanel;
/*	$('VolumePanel').innerHTML += "<img onclick='volumeUp()' src='/webdata/gfx/arrow_up.png'>"; 
	$('VolumePanel').innerHTML += "<img onclick='volumeDown()' src='/webdata/gfx/arrow_down.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume1' onclick='volumeSet(10)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume2' onclick='volumeSet(20)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume3' onclick='volumeSet(30)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume4' onclick='volumeSet(40)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume5' onclick='volumeSet(50)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume6' onclick='volumeSet(60)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume7' onclick='volumeSet(70)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume8' onclick='volumeSet(80)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume9' onclick='volumeSet(90)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='volume10' onclick='volumeSet(100)' src='/webdata/gfx/led_off.png'>"; 
	$('VolumePanel').innerHTML += "<img id='speaker' onclick='volumeMute()' src='/webdata/gfx/speak_on.png'>"; */
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
function handleVolumeRequest(){
	if (http_request.readyState == 4) {
		var b = getXML(http_request).getElementsByTagName("e2volume");
		debug(b.item(0).getElementsByTagName('e2current').length); 
		var newvalue = b.item(0).getElementsByTagName('e2current').item(0).firstChild.data;
		var mute = b.item(0).getElementsByTagName('e2ismuted').item(0).firstChild.data;
		//debug("volume"+newvalue+";"+mute);
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
//++++ Bouqet managing functions                   ++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
//+++++++++++++++++++++++++++++++++++++++++++++++++++++
function loadRootTVBouqet(){
	//rootB = '/web/fetchchannels?ServiceListBrowse='+escape('1:7:1:0:0:0:0:0:0:0:(type == 1) FROM BOUQUET "bouquets.tv" ORDER BY bouquet');
	rootB = '/web/fetchchannels?ServiceListBrowse='+escape('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)  FROM BOUQUET &quot;bouquets.tv&quot; ORDER BY bouquet');

	loadRootBouqet(rootB);
}
function loadRootBouqet(rootB){
	
	t = getHTTPObject();
	t.onreadystatechange = incomingResult;
	t.open('GET', rootB, true);
	t.send(null);
	
}

function incomingResult(){
	if((t.readyState == 4) && (t.status == 200)) {
	// perfekt!
		
		var b = getXML(t).getElementsByTagName("e2servicelist").item(0).getElementsByTagName("e2service");

		bouquets = new Array();
		for ( var i=0; i < b.length; i++){
			bRef = b.item(i).getElementsByTagName('e2servicereference').item(0).firstChild.data;
			bName = b.item(i).getElementsByTagName('e2servicename').item(0).firstChild.data;
			
			bu = new Array(bName,bRef);
			bouquets.push(bu)
		}
		refreshSelect(bouquets);
	} else {
	// die Anfrage enthielt Fehler;
	// die Antwort war z.B. 404 (nicht gefunden)
	// oder 500 (interner Server-Fehler)
	}
	
}

// to add the bouqetts to the list
function refreshSelect(arraybouqet){
	
	sel = document.getElementById("accordionMenueBouqetContent");
	// options neu eintragen
	html = "<table>";
		for ( var i = 0 ; i < arraybouqet.length ; i++ ){
		if(arraybouqet[i][0] && arraybouqet[i][1]){
			html+="<tr><td>";
			html+="<a  onclick=\"bouqetSelected(this); setBodyMainContent('BodyContentChannellist');\" id='";
			html+= arraybouqet[i][1];
			html+="'>";
			html+= arraybouqet[i][0];
			html+="</a>";
			html+="</td></tr>";
		}
	}
	html+="</table>";
	sel.innerHTML=html;
	refreshChannellist(arraybouqet[0][0],arraybouqet[0][1]);
}

//++++++++++++++++++++++
function bouqetSelected(element){
	refreshChannellist(element.value,element.id)
}

function refreshChannellist(bname,bref){
	urlx = '/web/fetchchannels?ServiceListBrowse='+escape(bref);
	w =getHTTPObject();
	w.onreadystatechange = incomingChannellist;
	w.open('GET', urlx, true);
	w.send(null);	
}
			
function incomingChannellist(){
	if(w.readyState == 4){

		services = getXML(w).getElementsByTagName("e2servicelist").item(0).getElementsByTagName("e2service");
		
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





