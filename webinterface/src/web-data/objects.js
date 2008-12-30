// $Header$
// store all objects here

//START class EPGList
function EPGList(xml){
	// parsing values from xml-element
	//debug('init EPGList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2eventlist").item(0).getElementsByTagName("e2event");
	} catch (e) { debug("[EPGList] parsing Error");}
	
	this.getArray = function(sortbytime){
		debug("[EPGList] Sort by time "+sortbytime);
		if (sortbytime === true){
			var sort1 = [];
			for(var i=0;i<this.xmlitems.length;i++){
				var xv = new EPGEvent(this.xmlitems.item(i));
				sort1.push( [xv.startTime, xv] );
			}
			sort1.sort(this.sortFunction);
			var sort2 = [];
			for(i=0;i<sort1.length;i++){
				sort2.push(sort1[i][1]);
			}
			return sort2;
		}else{
			var listxy = [];
			for (i=0;i<this.xmlitems.length;i++){
				xv = new EPGEvent(this.xmlitems.item(i));
				listxy.push(xv);			
			}
			return listxy;
		}
	};
	this.sortFunction = function(a,b){
	  return a[0] - b[0];
	};
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
	}	
	try{
		this.description = xml.getElementsByTagName('e2eventdescription').item(0).firstChild.data;
	} catch (e) {	this.description= 'N/A';	}
	
	try{
		this.descriptionE = xml.getElementsByTagName('e2eventdescriptionextended').item(0).firstChild.data;
	} catch (e) {	this.descriptionE = 'N/A';	}

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
		var Wochentag = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
		var wday = Wochentag[this.getTimeStart().getDay()];
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
		return  new Date(parseInt(this.duration, 10)*1000);
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
	};
	
	this.getClearServiceReference = function(){
		return this.servicereference;
	};
		
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	};
	
	this.setServiceReference = function(toInsert){
		this.servicereference = toInsert;
	};
		
	this.setServiceName = function(toInsert){
		this.servicename = toInsert.replace('&quot;', '"');
	};
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
		var listxy = [];
		try{
			for (var i=0;i<this.xmlitems.length;i++){
				var xv = new ServiceReference(this.xmlitems.item(i));
				listxy.push(xv);
			}			
		}catch (e){}
		
		return listxy;
	};
}
//END class ServiceList

//START class MovieList
function MovieList(xml){
	// parsing values from xml-element
	debug('[MovieList] init: ' + xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2movielist").item(0).getElementsByTagName("e2movie");
	} catch (e) {
		debug("[MovieList] parsing Error");
	}
	this.getArray = function(){
		var listxy = [];
		for(var i=0;i<this.xmlitems.length;i++){
			//debug("parsing movie "+i+" of "+this.xmlitems.length);
			var xv = new Movie(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	};
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
	try{
		this.filesize = xml.getElementsByTagName('e2filesize').item(0).firstChild.data;
	} catch (e) {
		this.filesize = 0;
	}
	try{
		this.startTime = xml.getElementsByTagName('e2time').item(0).firstChild.data;
	} catch (e) {
		this.startTime = "0";
	}
	try{
		this.length = xml.getElementsByTagName('e2length').item(0).firstChild.data;
	} catch (e) {
		this.length = "0";
	}
	
		
	

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

//START class TimerList
function TimerList(xml){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName("e2timerlist").item(0).getElementsByTagName("e2timer");
	} catch (e) {
		debug("[TimerList] parsing Error");
	}
	this.getArray = function(){
		var listxy = [];
		for(var i=0;i<this.xmlitems.length;i++){
			//debug("parsing timer "+i+" of "+this.xmlitems.length);
			var xv = new Timer(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	};
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
	try{
		this.color = xml.getElementsByTagName('e2color').item(0).firstChild.data;
	} catch (e) {
		this.color = "N/A";
	}
	try{
		this.toggledisabled = xml.getElementsByTagName('e2toggledisabled').item(0).firstChild.data;
	} catch (e) {
		this.toggledisabled = "N/A";
	}
	try{
		this.toggledisabledimg = xml.getElementsByTagName('e2toggledisabledimg').item(0).firstChild.data;
	} catch (e) {
		this.toggledisabledimg = "N/A";
	}

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
// START SimpleXMLResult ehemals TimerAddResult
function SimpleXMLResult(xml){
	// parsing values from xml-element
	debug('[SimpleXMLResult] init: '+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2simplexmlresult").item(0);
		debug("[SimpleXMLResult] count: " + xml.getElementsByTagName("e2simplexmlresult").length);
	} catch (e) {
		debug("[SimpleXMLResult] parsing e2simplexmlresult"+e);
	}
	try{
		this.state = this.xmlitems.getElementsByTagName("e2state").item(0).firstChild.data;
	} catch (e) {
		debug("[SimpleXMLResult] parsing e2state"+e);
	}
	try{
		this.statetext = this.xmlitems.getElementsByTagName("e2statetext").item(0).firstChild.data;
	} catch (e) {
		debug("[SimpleXMLResult] parsing e2statetext"+e);
	}
	
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

//START class Settings
function Settings(xml){
	// parsing values from xml-element
	//debug('init ServiceList'+xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2settings").item(0).getElementsByTagName("e2setting");
		debug("[Settings] Number of items: " + this.xmlitems);
	} catch (e) {
		//debug("Service parsing Error");
	}
	this.getArray = function(){
		var listxy = [];
		for (var i=0;i<this.xmlitems.length;i++){
			var xv = new Setting(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	};
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
	};
		
	this.getSettingName = function(){
		return this.settingname;
	};
	
}
//START class FileList
function FileList(xml){
	// parsing values from xml-element
	debug('[FileList] init: ' + xml);
	try{
		this.xmlitems = xml.getElementsByTagName("e2filelist").item(0).getElementsByTagName("e2file");
	} catch (e) {
		debug("[FileList] parsing Error");
	}
	this.getArray = function(){
		var listxy = [];
		for(var i=0;i<this.xmlitems.length;i++){
			//debug("parsing File "+i+" of "+this.xmlitems.length);
			var xv = new File(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	};
}
//END class FileList

//START class File
function File(xml){	
	// parsing values from xml-element
	//debug('init Movie');
	try{
		this.servicereference = xml.getElementsByTagName('e2servicereference').item(0).firstChild.data;
	} catch (e) {
		this.servicereference = "N/A";
	}
	this.getServiceReference = function(){
		return this.servicereference;
	};
	
	this.getNameOnly = function(){
		if(this.root == '/') {
			return this.servicereference;
		} else {
			return this.servicereference.replace(new RegExp('.*'+this.root, "i"), '');
		}
	};
	
	try{
		this.isdirectory = xml.getElementsByTagName('e2isdirectory').item(0).firstChild.data;
	} catch (e) {
		this.isdirectory = "N/A";
	}
	
	this.getIsDirectory = function(){
		return this.isdirectory;
	};
	
	try{
		this.root = xml.getElementsByTagName('e2root').item(0).firstChild.data;
	} catch (e) {
		this.root = "N/A";
	}
	
	this.getRoot = function(){
		return this.root;
	};
}	
//END class File



//START class NoteList
function NoteList(xml){
	// parsing values from xml-element
	try{
		this.xmlitems = xml.getElementsByTagName("e2noteslist").item(0).getElementsByTagName("e2note");
	} catch (e) {
		debug("[NoteList] parsing Error");
	}
	this.getArray = function(){
		var listxy = [];
		for(var i=0;i<this.xmlitems.length;i++){
			var xv = new Note(this.xmlitems.item(i));
			listxy.push(xv);			
		}
		return listxy;
	};
}
//END class NoteList

//START class Note
function Note(xml){	
	try{
		this.filename = xml.getElementsByTagName('e2notename').item(0).firstChild.data;
	} catch (e) {
		this.filename = "N/A";
	}
	try{
		this.saved = xml.getElementsByTagName('e2notesaved').item(0).firstChild.data;
	} catch (e) {
		this.saved = "N/A";
	}
	try{
		this.nameold = xml.getElementsByTagName('e2notenameold').item(0).firstChild.data;
	} catch (e) {
		this.nameold = "False";
	}
	try{
		this.content = xml.getElementsByTagName('e2notecontent').item(0).firstChild.data;
	} catch (e) {
		this.content = " ";
	}
	try{
		this.size = xml.getElementsByTagName('e2notesize').item(0).firstChild.data;
	} catch (e) {
		this.size = "N/A";
	}
	try{
		this.mtime = new Date(parseInt(xml.getElementsByTagName('e2notemtime').item(0).firstChild.data, 10)*1000);
	} catch (e) {
		this.mtime = "N/A";
	}
	try{
		this.ctime = new Date(parseInt(xml.getElementsByTagName('e2notectime').item(0).firstChild.data, 10)*1000);
	} catch (e) {
		this.ctime = "N/A";
	}

	this.getMTime = function(){
		var Wochentag = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
		var wday = Wochentag[this.mtime.getDay()];
		var day = this.mtime.getDate();
		var month = this.mtime.getMonth()+1;
		var year = this.mtime.getFullYear();
		return wday+".&nbsp;"+day+"."+month+"."+year+" "+this.mtime.getHours()+":"+this.mtime.getMinutes();
	};
	
	this.getCTime = function(){
		var Wochentag = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
		var wday = Wochentag[this.ctime.getDay()];
		var day = this.ctime.getDate();
		var month = this.ctime.getMonth()+1;
		var year = this.ctime.getFullYear();
		return wday+".&nbsp;"+day+"."+month+"."+year+" "+this.ctime.getHours()+":"+this.ctime.getMinutes();
	};
}
//END class NoteList
