var url_getvolume = '/web/vol?set=info'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?ref="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnownext = "/web/epgnownext?ref="; // plus serviceRev

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


function debug(text){
//	document.getElementById('BodyContentDebugbox').innerHTML += "DEBUG: "+text+"<br>";
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

function openWindow(t, inner, w, h){
			id = new Date().toUTCString()
			
			//debug(id);
			var win = new Window(id, {className: "alphacube", title: t, width:w, height:h});
			win.getContent().innerHTML = inner;
			win.setDestroyOnClose();
			win.showCenter();
			debug("opening Window: "+t);
}

function messageBox(t, m){
	Dialog.alert(m, {windowParameters: {title: t, className: "alphacube", width:200}, okLabel: "Close"});
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
		var html='<table width="100%" border="0" cellspacing="1" cellpadding="0">';
		for (var i=0; i < epglist.length; i++){
			try{
				var item = epglist[i];
				
				html +='<tr style="background-color: #DDDDDD;">';
				html +='<td width="10%">'+item.getTimeDay()+'</td>';
				html +='<td width="30%">'+item.getServiceName()+'</td>';
				html +='<td>'+item.getTitle()+'</td>';
				html +='</tr>';
				
				html +='<tr style="background-color: #DDDDDD;">';
				html +='<td>'+item.getTimeStartString()+'</td>';
				html +='<td>'+(item.getDuration()/60000)+' min.</td>';
				html +='<td>'+item.getDescription()+'</td>';
				html +='</tr>';
				
				html +='<tr style="background-color: #DDDDDD;">';
				html +='<td valign="top">'+item.getTimeEndString()+'</td>';
				html +='<td colspan="2">'+item.getDescriptionExtended()+'</td>';
				html +='</tr>';
				
				
				html +='<tr style="background-color: #AAAAAA;">';
				html +='<td colspan="3">&nbsp;</td>';
				html +='</tr>';
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


function getVolume()
{
	doRequest(url_getvolume,handleVolumeRequest);
}
function setVolume(newvalue)
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
		var a = http_request.responseText.split("\n");
		var newvalue = a[1];
		var mute=a[2];
		set("Volume_Current",newvalue);
		for (var i = 1; i <= 10; i++)
		{
			if ( (newvalue/10)>=i){
				$("volume"+i).src = "/webdata/gfx/led_on.png";
			}else{
				$("volume"+i).src = "/webdata/gfx/led_off.png";
			}
		}
		if (mute == "notmuted"){
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
		
		listerHtml 	= '<table border="0" cellpadding="0" cellspacing="0" class="BodyContentChannellist">\n';
		listerHtml += '<thead class="fixedHeader">\n';
		listerHtml += '<tr>\n';
		listerHtml += '<th colspan="2" style="color: #FFFFFF;">ServiceList</th>\n';
		listerHtml += '<th style="text-align: right;" style="color: #FFFFFF;">'
		listerHtml += '<form onSubmit="new EPGList().getBySearchString(document.getElementById(\'searchText\').value); return false;">';
		listerHtml += '<input type="text" id="searchText" onfocus="this.value=\'\'" value="EPG suchen"/>';
		listerHtml += '</form>'
		listerHtml += '</tr>\n';
		listerHtml += '</thead>\n';
		listerHtml += '<tbody class="scrollContent">\n';
		
		debug("got "+services.length+" Services");
		
		for ( var i = 0; i < (services.length ); i++){
			sRef = services.item(i).getElementsByTagName('e2servicereference').item(0).firstChild.data;
			sName = services.item(i).getElementsByTagName('e2servicename').item(0).firstChild.data;

			listerHtml += '<tr><td onclick="zap(this)" id="';
			listerHtml += sRef;
			listerHtml += '">\n';
			listerHtml += sName;
			listerHtml += '</td>\n';
			listerHtml += '<td onclick="new EPGList().getByServiceReference(this.id);" id="';
			listerHtml += sRef;
			listerHtml += '" >EPG</td>\n';
			listerHtml += '<td><a target="blank" href="stream.m3u?ref=';
			listerHtml += sRef;
			listerHtml += '\">Stream</a></td>\n';
			listerHtml += '</tr>\n';
		}
		
		listerHtml += "</tbody></table>\n";
		document.getElementById('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
	}
}





