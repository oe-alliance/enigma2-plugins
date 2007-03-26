
// store all objects here

//START class EPGList
function EPGList(xml){
	// parsing values from xml-element
	//debug('init EPGList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
	} catch (e) { debug("EPGList parsing Error");}
	
	this.getArray = function(sortbytime){
		debug("sort EPGList by time "+sortbytime);
		if (sortbytime = true){
			var sort1 = new Array();
			for(var i=0;i<this.xmlitems.length;i++){
				var xv = new EPGEvent(this.xmlitems.item(i));
				sort1.push(new Array(xv.startTime,xv));
			}
			sort1.sort(this.sortFunction);
			var sort2 = new Array();
			for(var i=0;i<sort1.length;i++){
				sort2.push(sort1[i][1]);
			}
			return sort2;
		}else{
			var listxy = new Array();
			for (var i=0;i<this.xmlitems.length;i++){
				var xv = new EPGEvent(this.xmlitems.item(i));
				listxy.push(xv);			
			}
			return listxy;
		}
	}
	this.sortFunction = function(a,b){
	  return a[0] - b[0];
	}
}
//END class EPGList

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
		this.fileName = xml.getElementsByTagName('e2filename').item(0).firstChild.data;
	} catch (e) {
		//debug("EPGEvent parsing Error");
	}	
	try{
		this.description = xml.getElementsByTagName('e2eventdescription').item(0).firstChild.data;
	} catch (e) {	this.description= 'N/A';	}
	
	try{
		this.descriptionE = xml.getElementsByTagName('e2eventdescriptionextended').item(0).firstChild.data;
	} catch (e) {	this.descriptionE = 'N/A';	}

	this.getFilename = function ()
	{
		return this.fileName;
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
	this.getTimeBegin = function(){
		return this.getTimeStart().getTime()/1000
	}
	this.getTimeEnd = function ()
	{
		var date = new Date((parseInt(this.startTime)+parseInt(this.duration))*1000);
		return date.getTime()/1000
	}
	this.getTimeEndString = function ()
	{
		var date = new Date((parseInt(this.startTime)+parseInt(this.duration))*1000);
		var h = date.getHours();
		var m = date.getMinutes();
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
	this.getClearServiceReference = function(){
		return this.servicereference;
	}
		
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	}
	this.setServiceReference = function(toInsert){
		this.servicereference = toInsert;
	}
		
	this.setServiceName = function(toInsert){
		this.servicename = toInsert.replace('&quot;', '"');
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

//START class MovieList
function MovieList(xml){
	// parsing values from xml-element
	debug('init MovieList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2movielist").item(0).getElementsByTagName("e2movie");
	} catch (e) {
		debug("MovieList parsing Error");
	}
	this.getArray = function(){
		var listxy = new Array();
		for(var i=0;i<this.xmlitems.length;i++){
			//debug("parsing movie "+i+" of "+this.xmlitems.length);
			var xv = new Movie(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	}
}
//END class MovieList

//START class Movie
function Movie(xml){	
	// parsing values from xml-element
	//debug('init Movie');
	try{
		this.servicereference = xml.getElementsByTagName('e2servicereference').item(0).firstChild.data;
	} catch (e) {
		this.servicereference = "N/A";
	}
	try{
		this.servicename = xml.getElementsByTagName('e2servicename').item(0).firstChild.data;
	} catch (e) {
		this.servicename = "N/A";
	}
	try{
		this.title = xml.getElementsByTagName('e2title').item(0).firstChild.data;
	} catch (e) {
		this.title = "N/A";
	}
	try{
		this.descriptionextended = xml.getElementsByTagName('e2descriptionextended').item(0).firstChild.data;
	} catch (e) {
		this.descriptionextended = "N/A";
	}
	try{
		this.description = xml.getElementsByTagName('e2description').item(0).firstChild.data;
	} catch (e) {
		this.description = "N/A";
	}
	try{
		this.tags = xml.getElementsByTagName('e2tags').item(0).firstChild.data;
	} catch (e) {
		this.tags = "no&nbsp;tags"; // no whitespaces... tags will be splittet later
	}
	try{
		this.filename = xml.getElementsByTagName('e2filename').item(0).firstChild.data;
	} catch (e) {
		this.filename = "n/a";
	}
	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	}
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	}	
	this.getTitle = function(){
		return this.title;
	}	
	this.getDescription = function(){
		return this.description;
	}	
	this.getDescriptionExtended = function(){
		return this.descriptionextended;
	}	
	this.getTags = function(){		
		return this.tags.split(" ");
	}	
	this.getFilename = function(){		
		return encodeURIComponent(this.filename);
		
	}	
}	
//END class Movie

//START class TimerList
function TimerList(xml){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName("e2timerlist").item(0).getElementsByTagName("e2timer");
	} catch (e) {
		debug("TimerList parsing Error");
	}
	this.getArray = function(){
		var listxy = new Array();
		for(var i=0;i<this.xmlitems.length;i++){
			//debug("parsing timer "+i+" of "+this.xmlitems.length);
			var xv = new Timer(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	}
}
//END class TimerList

//START class Timer
function Timer(xml){	
	// parsing values from xml-element
	//debug('init Timer');
	try{
		this.servicereference = xml.getElementsByTagName('e2servicereference').item(0).firstChild.data;
	} catch (e) {
		this.servicereference = "N/A";
	}
	try{
		this.servicename = xml.getElementsByTagName('e2servicename').item(0).firstChild.data;
	} catch (e) {
		this.servicename = "N/A";
	}
	try{
		this.eventid = xml.getElementsByTagName('e2eit').item(0).firstChild.data;
	} catch (e) {
		this.eventid = "N/A";
	}
	try{
		this.name = xml.getElementsByTagName('e2name').item(0).firstChild.data;
	} catch (e) {
		this.name = "N/A";
	}
	try{
		this.description = xml.getElementsByTagName('e2description').item(0).firstChild.data;
	} catch (e) {
		this.description = "N/A";
	}
	try{
		this.descriptionextended = xml.getElementsByTagName('e2descriptionextended').item(0).firstChild.data;
	} catch (e) {
		this.descriptionextended = "N/A";
	}
	try{
		this.disabled = xml.getElementsByTagName('e2disabled').item(0).firstChild.data;
	} catch (e) {
		this.disabled = "0";
	}
	try{
		this.timebegin = xml.getElementsByTagName('e2timebegin').item(0).firstChild.data;
	} catch (e) {
		this.timebegin = "N/A";
	}
	try{
		this.timeend = xml.getElementsByTagName('e2timeend').item(0).firstChild.data;
	} catch (e) {
		this.timeend = "N/A";
	}
	try{
		this.duration = xml.getElementsByTagName('e2duration').item(0).firstChild.data;
	} catch (e) {		
		this.duration = "0";
	}
	try{
		this.startprepare = xml.getElementsByTagName('e2startprepare').item(0).firstChild.data;
	} catch (e) {
		this.startprepare = "N/A";
	}
	try{
		this.justplay = xml.getElementsByTagName('e2justplay').item(0).firstChild.data;
	} catch (e) {
		this.justplay = "";
	}
	try{
		this.afterevent = xml.getElementsByTagName('e2afterevent').item(0).firstChild.data;
	} catch (e) {
		this.afterevent = "0";
	}
	try{
		this.logentries = xml.getElementsByTagName('e2logentries').item(0).firstChild.data;
	} catch (e) {
		this.logentries = "N/A";
	}
	try{
		this.tfilename = xml.getElementsByTagName('e2filename').item(0).firstChild.data;
	} catch (e) {
		this.tfilename = "N/A";
	}
	try{
		this.backoff = xml.getElementsByTagName('e2backoff').item(0).firstChild.data;
	} catch (e) {
		this.backoff = "N/A";
	}
	try{
		this.nextactivation = xml.getElementsByTagName('e2nextactivation').item(0).firstChild.data;
	} catch (e) {
		this.nextactivation = "N/A";
	}
	try{
		this.firsttryprepare = xml.getElementsByTagName('e2firsttryprepare').item(0).firstChild.data;
	} catch (e) {
		this.firsttryprepare = "N/A";
	}
	try{
		this.state = xml.getElementsByTagName('e2state').item(0).firstChild.data;
	} catch (e) {
		this.state = "N/A";
	}
	try{
		this.repeated = xml.getElementsByTagName('e2repeated').item(0).firstChild.data;
	} catch (e) {
		this.repeated = "0";
	}
	try{
		this.dontsave = xml.getElementsByTagName('e2dontsave').item(0).firstChild.data;
	} catch (e) {
		this.dontsave = "N/A";
	}
	try{
		this.cancled = xml.getElementsByTagName('e2cancled').item(0).firstChild.data;
	} catch (e) {
		this.cancled = "N/A";
	}

	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	}
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	}	
	this.getEventID = function(){
		return this.eventid;
	}	
	this.getName = function(){
		return this.name;
	}	
	this.getDescription = function(){
		return this.description;
	}	
	this.getDescriptionExtended = function(){
		return this.descriptionextended;
	}	
	this.getDisabled = function(){
		return this.disabled;
	}
	this.getTimeBegin = function(){
		return this.timebegin;
	}	
	this.getTimeEnd = function(){
		return this.timeend;
	}	
	this.getDuration = function(){
		return parseInt(this.duration);
	}	
	this.getStartPrepare = function(){
		return this.startprepare;
	}	
	this.getJustplay = function(){
		return this.justplay;
	}	
	this.getAfterevent = function(){
		return this.afterevent;
	}	
	this.getLogentries = function(){
		return this.logentries;
	}	
	this.getFilename = function(){
		return this.tfilename;
	}	
	this.getBackoff = function(){
		return this.backoff;
	}	
	this.getNextActivation = function(){
		return this.nextactivation;
	}	
	this.getFirsttryprepare = function(){
		return this.firsttryprepare;
	}	
	this.getState = function(){
		return this.state;
	}	
	this.getRepeated = function(){
		return this.repeated;
	}	
	this.getDontSave = function(){
		return this.dontsave;
	}	
	this.isCancled = function(){
		return this.cancled;
	}	
}
// START SimpleXMLResult ehemals TimerAddResult
function SimpleXMLResult(xml){
	// parsing values from xml-element
	debug('init SimpleXMLResult'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2simplexmlresult").item(0);
	} catch (e) {
		debug("SimpleXMLResult parsing e2simplexmlresult"+e);
	}
	try{
		this.state = this.xmlitems.getElementsByTagName("e2state").item(0).firstChild.data;
	} catch (e) {
		debug("SimpleXMLResult parsing e2state"+e);
	}
	try{
		this.statetext = this.xmlitems.getElementsByTagName("e2statetext").item(0).firstChild.data;
	} catch (e) {
		debug("SimpleXMLResult parsing e2statetext"+e);
	}
	
	this.getState = function(){
		if(this.state == 'True'){
			return true;
		}else{
			return false;
		}
	}
	this.getStateText = function(){
			return this.statetext;
	}
}
// END SimpleXMLResult

//START class Settings
function Settings(xml){
	// parsing values from xml-element
	//debug('init ServiceList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2settings").item(0).getElementsByTagName("e2setting");
		debug(this.xmlitems);
	} catch (e) {
		//debug("Service parsing Error");
	}
	this.getArray = function(){
		var listxy = new Array();
		for (var i=0;i<this.xmlitems.length;i++){
			var xv = new Setting(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	}
}
//END class Settings

//START class Setting
function Setting(xml){	
	// parsing values from xml-element
	//debug('init ServiceReference'+xml);
	try{
		this.settingvalue = xml.getElementsByTagName('e2settingvalue').item(0).firstChild.data;
		this.settingname = xml.getElementsByTagName('e2settingname').item(0).firstChild.data;
		
	} catch (e) {
		//debug("Service parsing Error "+e);
	}
	
	this.getSettingValue = function(){
		return this.settingvalue;
	}
		
	this.getSettingName = function(){
		return this.settingname;
	}
	
}
