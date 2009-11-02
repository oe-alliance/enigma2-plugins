// $Header$

function url() {
	this.tpl = '/web-data/tpl/default/';
	
	this.getcurrent = '/web/getcurrent';
	
	this.getvolume = '/web/vol'; 
	this.setvolume = '/web/vol?set=set'; // plus new value eg: set=set15
	this.volumeup = '/web/vol?set=up';
	this.volumedown = '/web/vol?set=down';
	this.volumemute = '/web/vol?set=mute';
	
	this.epgservice = "/web/epgservice?sRef="; // plus serviceRef
	this.epgsearch = "/web/epgsearch?search="; // plus serviceRef
	this.epgservicenow = "/web/epgservicenow?sRef="; // plus serviceRef
	this.epgservicenext = "/web/epgservicenext?sRef="; // plus serviceRef
	this.epgnow = "/web/epgnow?bRef="; // plus bouquetRev
	this.epgnext = "/web/epgnext?bRef="; // plus bouquetRev
	
	this.getservices = "/web/getservices?sRef="; // plus serviceref
	this.subservices = "/web/subservices"; // subservices for current service
	this.streamsubservices = "/web/streamsubservices?sRef="; // subservices for streaming service
	
	this.movielist= "/web/movielist"; // plus dirname,tag
	this.moviedelete= "/web/moviedelete"; // plus serviceref
	
	this.about= "/web/about";	
	this.settings= "/web/settings";	
	this.parentcontrol= "/web/parentcontrollist";
	this.signal = "/web/signal";
	this.deviceinfo = "/web/deviceinfo";
	
	this.mediaplayerlist= "/web/mediaplayerlist?types=audio&path="; // plus full qualified path
	this.mediaplayerplay= "/web/mediaplayerplay?file="; // plus file-serviceref
	this.mediaplayerremove= "/web/mediaplayerremove?file="; // plus file-serviceref
	this.mediaplayercmd= "/web/mediaplayercmd?command="; // plus command
	this.mediaplayerwrite= "/web/mediaplayerwrite?filename="; // plus filename
	
	this.filelist = "/web/mediaplayerlist?path="; // plus full qualified path
	
	this.timerlist= "/web/timerlist";
	this.recordnow= "/web/recordnow";
	this.timeradd= "/web/timeradd"; // plus serviceref,begin,end,name,description,dirname,tags,eit,disabled,justplay,afterevent
	this.timerchange= "/web/timerchange"; // plus serviceref,begin,end,name,description,dirname,tags,eit,disabled,justplay,afterevent
	this.timeraddbyeventid= "/web/timeraddbyeventid"; // plus serviceref,eventid
	this.timerdelete= "/web/timerdelete"; // plus serviceref,begin,end
	this.timerlistwrite="/web/timerlistwrite?write=saveWriteNow";
	this.timercleanup="/web/timercleanup?cleanup=true";
	
	this.getcurrlocation="/web/getcurrlocation";
	this.getlocations="/web/getlocations";
	this.gettags="/web/gettags";
	
	this.message = "/web/message"; // plus text,type,timeout
	this.messageanswer = "/web/messageanswer?getanswer=now"; 
	
	this.powerstate = "/web/powerstate"; // plus new powerstate
	this.remotecontrol = "/web/remotecontrol"; // plus command
};

var URL = new url();

var bouquetsTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet';
var bouquetsRadio = '1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET "bouquets.radio" ORDER BY bouquet';
var providerTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name';
var providerRadio ='1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name';
var satellitesTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM SATELLITES ORDER BY name';
var satellitesRadio ='1:7:2:0:0:0:0:0:0:0:(type == 2) FROM SATELLITES ORDER BY name';
var allTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) ORDER BY name';
var allRadio = '1:7:2:0:0:0:0:0:0:0:(type == 2) ORDER BY name';
