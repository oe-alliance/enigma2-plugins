var url_getvolume = '/web/vol?set=info'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eq. set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?serviceRef="; // plus serviceRev
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRev
var url_epgnownext = "/web/epgnownext?serviceRef="; // plus serviceRev

function debug(text){
	//$('debug').innerHTML += "DEBUG: "+text+"<br>";
}
function set(what, value)
{
	//debug(what+"-"+value);
	element = document.getElementById(what);
	element.innerHTML = value;
	$('scriptzone').innerHTML = ""; // deleting set() from page, to keep the page short and to save memory
}

function zap(li)
{
	var request = getHTTPObject();
	var url = "/web/zap?ZapTo=" + escape(li.id);
	//debug("requesting "+url);
	new Ajax.Request( url,
			{
				method: 'get' 
				
			});
		
}

function getHTTPObject() 
{
	var xmlhttp; 
	/*@cc_on 
	@if (@_jscript_version >= 5) 
	try 
	{ 
		xmlhttp = new ActiveXObject("Msxml2.XMLHTTP"); 
	} 
	catch (e) 
	{ 
		try 
		{ 
			xmlhttp = new ActiveXObject("Microsoft.XMLHTTP"); 
		} 
		catch (E) 
		{ 
			xmlhttp = false; 
		} 
	} 
	@else 
	xmlhttp = false; 
	@end @*/ 
	if (!xmlhttp && typeof XMLHttpRequest != 'undefined') 
	{ 
		try 
		{ 
			xmlhttp = new XMLHttpRequest(); 
		} 
		catch (e) 
		{
			xmlhttp = false; 
		}
	} 
	return xmlhttp; 
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
	getBySearchString: function(string,element){
		debug("requesting "+ url_epgsearch+string);
		targetElement = element;
		new Ajax.Request( url_epgsearch+string,
			{
				method: 'get', 
				onComplete: this.incomingEPGrequest
			});
		
	},
	getByServiceReference: function(serviceRef,element){
		targetElement = element;
		new Ajax.Request(url_epgservice+serviceRef,
			{
				method: 'get', 
				onComplete: this.incomingEPGrequest
			});
		
	},
	renderTable: function(epglist){
		debug("rendering Table with "+epglist.length+" events");
		var html="<table width='100%'>";
		for (var i=0; i<epglist.length;i++){
			var item = epglist[i];
			html +="<tr  bgcolor='gray'>";
			html +="<td>"+item.getTimeDay()+"</td>";
			html +="<td>"+item.getTimeStartString()+"</td>";
			html +="<td>"+item.getTimeEndString()+"</td>";
			html +="<td>"+item.getTitle()+"</td>";
			html +="<td>"+item.getDescription()+"</td>";
			html +="<td>"+item.getDescriptionExtended()+"</td>";
			html +="<td>"+(item.getDuration()/60000)+" min.</td>";
			html +="<td>"+item.getServiceName()+"</td>";
			html +="</tr>";
		}
		html +="</table>";
		targetElement.innerHTML = html;
		
	},
	incomingEPGrequest: function(originalRequest){
		debug("incoming request" +originalRequest.readyState);		
		if (originalRequest.readyState == 4)
		{
			if (originalRequest.responseXML!="no data")
			{
				var EPGItems = originalRequest.responseXML.getElementsByTagName("EPGList").item(0).getElementsByTagName("EPGEvent");
				debug("have "+EPGItems.length+" EPGEvents");
				epglist = new Array();
				for(var i=0;i<EPGItems.length;i++)
				{
					epglist.push(new EPGEvent(EPGItems.item(i)));
				}
					EPGList.prototype.renderTable(epglist);
				
			}				
		}
	}
	
}

function EPGEvent(element){	
	// parsing values from xml-element
	this.eventID= element.getElementsByTagName('EventID').item(0).firstChild.data;
	this.startTime= element.getElementsByTagName('TimeStart').item(0).firstChild.data;
	this.duration= element.getElementsByTagName('Duration').item(0).firstChild.data;
	this.title= element.getElementsByTagName('Title').item(0).firstChild.data;
	this.description= element.getElementsByTagName('Description').item(0).firstChild.data;
	this.descriptionE= element.getElementsByTagName('DescriptionExtended').item(0).firstChild.data;
	this.serviceRef= element.getElementsByTagName('ServiceReference').item(0).firstChild.data;
	this.serviceName= element.getElementsByTagName('ServiceName').item(0).firstChild.data;

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
	newelement.style.display = "inline";
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
  		
		t =getHTTPObject();
		t.onreadystatechange = incomingResult;
		t.open('GET', rootB, true);
		t.send(null);
		
	}
	function incomingResult(){
		if (t.readyState == 4) {
    	// perfekt!
			result = t.responseText;
			x = result.split("\n");
			bouquets = new Array();
			for ( var i = 0 ; i < x.length ; i=i+2 ){
				bu = new Array(x[i+1 ],x[i]);
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
			if (w.readyState == 4) {
    		// alles in Ordnung, Antwort wurde empfangen
				result = w.responseText;
				x = result.split("\n");
				
				
				listerHtml = "<table id=\"ChannelSelect\" >";
				for ( var i = 0 ; i < x.length ; i=i+2 ){
					if(x[i].length>=1 && x[i+1]){
						
						listerHtml += '<tr bgcolor="gray"><td><div onclick=\"zap(this)\" id="';
						listerHtml += x[i];
				  		listerHtml += '">';
						listerHtml += x[i+1];
						listerHtml += '</div></td>';
						listerHtml += '<td><a onclick=\"new EPGList().getByServiceReference(this.id,$(\'BodyEPGPanel\'));setBodyMainContent(\'BodyEPGPanel\');\" id="';
						listerHtml += x[i];
				  		listerHtml += '" >EPG</div><div><a href=\"stream.m3u?ref=';
						listerHtml += x[i];
				  		listerHtml += '\">Stream</a></div></td>';
						listerHtml += '</tr>';
					}
				}
				listerHtml += "</table>";
				document.getElementById("BodyContentChannellist").innerHTML = listerHtml;
				setBodyMainContent('BodyContentChannellist');
			} else {
    		// die Anfrage enthielt Fehler;
    		// die Antwort war z.B. 404 (nicht gefunden)
    		// oder 500 (interner Server-Fehler)
			}
			
	}



