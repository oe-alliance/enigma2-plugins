// $Header$
// store all objects here

//START class EPGList 

function getNodeContent(xml, nodename, defaultString){
	try{
		var node = xml.getElementsByTagName(nodename);
		var retVal = node.item(0).firstChild.data;

		if(retVal === "" || retVal === null){
			return 'N/A';		
		}		
		return retVal;
	} catch(e){
		if(typeof(defaultString) !== 'undefined') {
			return defaultString;
		}		
	}
	
	return 'N/A';
}

function getNamedChildren(xml, parentname, childname){
	try {
		var ret = xml.getElementsByTagName(parentname).item(0).getElementsByTagName(childname);
		return ret;
	} catch (e) {
		return {};
	}
}

//START class EPGEvent
function EPGEvent(xml){	
	this.eventID = getNodeContent(xml, 'e2eventid', '');
	this.startTime = getNodeContent(xml, 'e2eventstart', '');
	this.duration = getNodeContent(xml, 'e2eventduration', '');
	this.title = getNodeContent(xml, 'e2eventtitle', '');
	this.serviceRef = getNodeContent(xml, 'e2eventservicereference', '');
	this.serviceName = getNodeContent(xml, 'e2eventservicename', '');
	this.fileName = getNodeContent(xml, 'e2filename', '');	
	this.description = getNodeContent(xml, 'e2eventdescription');
	this.descriptionE = getNodeContent(xml, 'e2eventdescriptionextended');

	this.getFilename = function (){
		return this.fileName;
	};
	this.getEventId = function (){
		return this.eventID;
	};
	this.getTimeStart = function (){
		var date = new Date(parseInt(this.startTime, 10)*1000);
		return date;
	};
	this.getTimeStartString = function (){
		var h = this.getTimeStart().getHours();
		var m = this.getTimeStart().getMinutes();
		if (m < 10){
			m="0"+m;
		}
		return h+":"+m;
	};
	this.getTimeDay = function (){
		var weekday = ["So", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
		var wday = weekday[this.getTimeStart().getDay()];
		var day = this.getTimeStart().getDate();
		var month = this.getTimeStart().getMonth()+1;
		var year = this.getTimeStart().getFullYear();
		
		return wday+".&nbsp;"+day+"."+month+"."+year;
	};
	this.getTimeBegin = function(){
		return this.getTimeStart().getTime()/1000;
	};
	this.getTimeEnd = function (){
		var date = new Date((parseInt(this.startTime, 10)+parseInt(this.duration, 10))*1000);
		return date.getTime()/1000;
	};
	this.getTimeEndString = function (){
		var date = new Date((parseInt(this.startTime, 10)+parseInt(this.duration, 10))*1000);
		var h = date.getHours();
		var m = date.getMinutes();
		if (m < 10){
			m="0"+m;
		}
		return h+":"+m;
	};
	this.getDuration = function (){
		var date = new Date(parseInt(this.duration, 10)*1000);
		return date;
	};
	this.getTitle = function (){
		return this.title;
	};
	this.getDescription = function (){
		return this.description;
	};
	this.getDescriptionExtended = function (){
		return this.descriptionE;
	};
	this.getServiceReference = function (){
		return encodeURIComponent(this.serviceRef);
	};
	this.getServiceName = function (){
		return this.serviceName.replace(" ","&nbsp;");
	};
}
//END class EPGEvent


function EPGList(xml){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
	} catch (e) { debug("[EPGList] parsing Error");}
	
	this.getArray = function(sortbytime){
		debug("[EPGList] Sort by time "+sortbytime);
		var list = [];
		
		if (sortbytime === true){
			var sortList = [];
			for(var i=0;i<this.xmlitems.length;i++){
				var event = new EPGEvent(this.xmlitems.item(i));
				sortList.push( [event.startTime, event] );
			}
			sortList.sort(this.sortFunction);
			
			list = [];
			for(i=0;i<sortList.length;i++){
				list.push(sortList[i][1]);
			}
			
			return list;
			
		}else{
			list = [];
			for (i=0;i<this.xmlitems.length;i++){
				xv = new EPGEvent(this.xmlitems.item(i));
				list.push(xv);			
			}
			return list;
		}
	};
	
	this.sortFunction = function(a, b){
	  return a[0] - b[0];
	};
}
//END class EPGList

// START class Service
function Service(xml){	
	this.servicereference = getNodeContent(xml, 'e2servicereference', '');
	this.servicename = getNodeContent(xml, 'e2servicename');
	
	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	};
	
	this.getClearServiceReference = function(){
		return this.servicereference;
	};
		
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	};
	
	this.setServiceReference = function(sref){
		this.servicereference = sref;
	};
		
	this.setServiceName = function(sname){
		this.servicename = sname.replace('&quot;', '"');
	};
}	
//END class Service

// START class ServiceList
function ServiceList(xml){
	this.xmlitems = getNamedChildren(xml, "e2servicelist", "e2service");
	this.servicelist = [];
	this.getArray = function(){
		if(this.servicelist.length === 0){
			for (var i=0;i<this.xmlitems.length;i++){
				var service = new Service(this.xmlitems.item(i));
				this.servicelist.push(service);
			}
		}
		
		return this.servicelist;
	};
}
//END class ServiceList


// START class Movie
function Movie(xml){	
	this.servicereference = getNodeContent(xml, 'e2servicereference');
	this.servicename = getNodeContent(xml, 'e2servicename');
	this.title = getNodeContent(xml, 'e2title');
	this.descriptionextended = getNodeContent(xml, 'e2descriptionextended');
	this.description = getNodeContent(xml, 'e2description');
	this.tags = getNodeContent(xml, 'e2tags', '&nbsp;');
	this.filename = getNodeContent(xml, 'e2filename');
	this.filesize = getNodeContent(xml, 'e2filesize', 0);
	this.startTime = getNodeContent(xml, 'e2time', 0);
	this.length = getNodeContent(xml, 'e2length', 0);

	this.getLength = function (){
		return this.length;
	};
	
	this.getTimeStart = function (){
		var date = new Date(parseInt(this.startTime, 10)*1000);
		return date;
	};
	
	this.getTimeStartString = function (){
		var h = this.getTimeStart().getHours();
		var m = this.getTimeStart().getMinutes();
		if (m < 10){
			m="0"+m;
		}
		return h+":"+m;
	};
	
	this.getTimeDay = function (){
		var Wochentag = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
		var wday = Wochentag[this.getTimeStart().getDay()];
		var day = this.getTimeStart().getDate();
		var month = this.getTimeStart().getMonth()+1;
		var year = this.getTimeStart().getFullYear();
		
		return wday+".&nbsp;"+day+"."+month+"."+year;
	};

	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	};
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	};
	
	this.getTitle = function(){
		return this.title;
	};
	
	this.getDescription = function(){
		return this.description;
	};
	
	this.getDescriptionExtended = function(){
		return this.descriptionextended;
	};
	
	this.getTags = function(){		
		return this.tags.split(" ");
	};
	
	this.getFilename = function(){		
		return encodeURIComponent(this.filename);		
	};
	
	this.getFilesizeMB = function(){		
		return Math.round((parseInt(this.filesize, 10)/1024)/1024)+"MB";
	};	
}	
//END class Movie


// START class MovieList
function MovieList(xml){
	this.xmlitems = getNamedChildren(xml, "e2movielist", "e2movie");
	this.movielist = [];
	
	this.getArray = function(){
		if(this.movielist.length === 0){			
			for(var i=0;i<this.xmlitems.length;i++){
				//debug("parsing movie "+i+" of "+this.xmlitems.length);
				var movie = new Movie(this.xmlitems.item(i));
				this.movielist.push(movie);			
			}
		}
		
		return this.movielist;
	};
}
//END class MovieList



// START class Timer
function Timer(xml){	
	this.servicereference = getNodeContent(xml, 'e2servicereference');
	this.servicename = getNodeContent(xml, 'e2servicename');
	this.eventid = getNodeContent(xml, 'e2eit');
	this.name = getNodeContent(xml, 'e2name');
	this.description = getNodeContent(xml, 'e2description', '');
	this.descriptionextended = getNodeContent(xml, 'e2descriptionextended', '');
	this.disabled = getNodeContent(xml, 'e2disabled', '0');
	this.timebegin = getNodeContent(xml, 'e2timebegin');
	this.timeend = getNodeContent(xml, 'e2timeend');
	this.duration = getNodeContent(xml, 'e2duration', '0');
	this.startprepare = getNodeContent(xml, 'e2startprepare');
	this.justplay = getNodeContent(xml, 'e2justplay', '');
	this.afterevent = getNodeContent(xml, 'e2afterevent', '0');
	this.dirname = getNodeContent(xml, 'e2dirname', '/hdd/movie/');
	this.tags = getNodeContent(xml, 'e2tags', '');
	this.logentries = getNodeContent(xml, 'e2logentries');
	this.tfilename = getNodeContent(xml, 'e2filename');
	this.backoff = getNodeContent(xml, 'e2backoff');
	this.nextactivation = getNodeContent(xml, 'e2nextactivation');
	this.firsttryprepare = getNodeContent(xml, 'e2firsttryprepare');
	this.state = getNodeContent(xml, 'e2state');
	this.repeated = getNodeContent(xml, 'e2repeated', '0');
	this.dontsave = getNodeContent(xml, 'e2dontsave');
	this.cancled = getNodeContent(xml, 'e2cancled');
	this.color = getNodeContent(xml, 'e2color');
	this.toggledisabled = getNodeContent(xml, 'e2toggledisabled');
	this.toggledisabledimg = getNodeContent(xml, 'e2toggledisabledimg');

	this.getColor = function(){
		return this.color;
	};
	
	this.getToggleDisabled = function(){
		return this.toggledisabled;
	};
	
	this.getToggleDisabledIMG = function(){
		return this.toggledisabledimg;
	};
	
	this.getToggleDisabledText = function(){
		var retVal = this.toggledisabled == "0" ? "Enable timer" : "Disable timer";
		return retVal;
	};
	
	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	};
	
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	};
	
	this.getEventID = function(){
		return this.eventid;
	};
	
	this.getName = function(){
		return this.name;
	};
	
	this.getDescription = function(){
		return this.description;
	};
	
	this.getDescriptionExtended = function(){
		return this.descriptionextended;
	};
	
	this.getDisabled = function(){
		return this.disabled;
	};
	
	this.getTimeBegin = function(){
		return this.timebegin;
	};
	
	this.getTimeEnd = function(){
		return this.timeend;
	};
	
	this.getDuration = function(){
		return parseInt(this.duration, 10);
	};
	
	this.getStartPrepare = function(){
		return this.startprepare;
	};
	
	this.getJustplay = function(){
		return this.justplay;
	};
	
	this.getAfterevent = function(){
		return this.afterevent;
	};
	
	this.getDirname = function(){
		return this.dirname;
	};

	this.getTags = function(){
		return this.tags;
	};

	this.getLogentries = function(){
		return this.logentries;
	};
	
	this.getFilename = function(){
		return this.tfilename;
	};
	
	this.getBackoff = function(){
		return this.backoff;
	};
	
	this.getNextActivation = function(){
		return this.nextactivation;
	};
	
	this.getFirsttryprepare = function(){
		return this.firsttryprepare;
	};
	
	this.getState = function(){
		return this.state;
	};
	
	this.getRepeated = function(){
		return this.repeated;
	};
	
	this.getDontSave = function(){
		return this.dontsave;
	};
	
	this.isCancled = function(){
		return this.cancled;
	};	
}


// START class TimerList
function TimerList(xml){
	this.xmlitems = getNamedChildren(xml, "e2timerlist", "e2timer");
	this.timerlist = [];
	
	this.getArray = function(){
		if(this.timerlist.length === 0){
			for(var i=0;i<this.xmlitems.length;i++){
				var timer = new Timer(this.xmlitems.item(i));
				this.timerlist.push(timer);			
			}
		}
		
		return this.timerlist;
	};
}
//END class TimerList


function SimpleXMLResult(xml){		
	try{
		this.xmlitems = xml.getElementsByTagName("e2simplexmlresult").item(0);
	} catch (e) {
		debug("[SimpleXMLResult] parsing e2simplexmlresult" + e);
	}

	this.state = getNodeContent(this.xmlitems, 'e2state', 'False');
	this.statetext = getNodeContent(this.xmlitems, 'e2statetext', 'Error Parsing XML');

	this.getState = function(){
		if(this.state == 'True'){
			return true;
		}else{
			return false;
		}
	};
	
	this.getStateText = function(){
			return this.statetext;
	};
}
// END SimpleXMLResult

// START SimpleXMLList
function SimpleXMLList(xml, tagname){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName(tagname);
	} catch (e) {
		debug("[SimpleXMLList] parsing e2simplexmllist"+e);
	}
	this.xmllist = [];
	
	this.getList = function(){
		if(this.xmllist.length === 0){
			for(var i=0;i<this.xmlitems.length;i++){
				this.xmllist.push(this.xmlitems.item(i).firstChild.data);			
			}
		}
		
		return this.xmllist;
	};
}
// END SimpleXMLList


// START class Setting
function Setting(xml){	
	this.settingvalue = getNodeContent(xml, 'e2settingvalue');
	this.settingname = getNodeContent(xml, 'e2settingname');
	
	this.getSettingValue = function(){
		return this.settingvalue;
	};
		
	this.getSettingName = function(){
		return this.settingname;
	};
	
}


// START class Settings
function Settings(xml){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName("e2settings").item(0).getElementsByTagName("e2setting");
		debug("[Settings] Number of items: " + this.xmlitems);
	} catch (e) {
		debug("[Settings] parsing Error");
	}	
	this.settings = [];
	
	this.getArray = function(){
		if(this.settings.length === 0){
			for (var i=0;i<this.xmlitems.length;i++){
				var setting = new Setting(this.xmlitems.item(i));
				this.settings.push(setting);			
			}
		}
		
		return this.settings;		
	};
}
//END class Settings
