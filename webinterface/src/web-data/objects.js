// store all objects here

//START class EPGEvent
function EPGEvent(xml){	
	// parsing values from xml-element
	try{
		this.eventID = xml.getElementsByTagName('e2eventid').item(0).firstChild.data;
		this.startTime = xml.getElementsByTagName('e2eventstart').item(0).firstChild.data;
		this.duration = xml.getElementsByTagName('e2eventduration').item(0).firstChild.data;
		this.title = xml.getElementsByTagName('e2eventtitle').item(0).firstChild.data;
		this.serviceRef = xml.getElementsByTagName('e2eventservicereference').item(0).firstChild.data;
		this.serviceName = xml.getElementsByTagName('e2eventservicename').item(0).firstChild.data;
	} catch (e) {
		//debug("EPGEvent parsing Error");
	}	
	try{
		this.description = xml.getElementsByTagName('e2eventdescription').item(0).firstChild.data;
	} catch (e) {	this.description= 'N/A';	}
	
	try{
		this.descriptionE = xml.getElementsByTagName('e2eventdescriptionextended').item(0).firstChild.data;
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
		return encodeURIComponent(this.serviceRef);
	}
	this.getServiceName = function ()
	{
		return this.serviceName.replace(" ","&nbsp;");
	}
}
//END class EPGEvent

//START class Service
function ServiceReference(xml){	
	// parsing values from xml-element
	//debug('init ServiceReference'+xml);
	try{
		this.servicereference = xml.getElementsByTagName('e2servicereference').item(0).firstChild.data;
		this.servicename = xml.getElementsByTagName('e2servicename').item(0).firstChild.data;
		
	} catch (e) {
		//debug("Service parsing Error "+e);
	}
	
	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	}
		
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	}	
}	
//END class Service


//START class ServiceList

function ServiceList(xml){
	// parsing values from xml-element
	//debug('init ServiceList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2servicelist").item(0).getElementsByTagName("e2service");
	} catch (e) {
		//debug("Service parsing Error");
	}
	this.getArray = function(){
		var listxy = new Array();
		for (var i=0;i<this.xmlitems.length;i++){
			var xv = new ServiceReference(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	}
}
//END class ServiceList
