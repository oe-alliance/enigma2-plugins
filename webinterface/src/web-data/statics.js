// $Header$

function url() {
	this.tpl = '/web-data/tpl/default/';

	this.zap = '/web/zap';
	this.getcurrent = '/web/getcurrent';
	this.volume = '/web/vol';
	this.epgservice = "/web/epgservice"; // plus serviceRef
	this.epgsearch = "/web/epgsearch"; // plus needle
	this.epgservicenow = "/web/epgservicenow?sRef="; // plus serviceRef
	this.epgservicenext = "/web/epgservicenext?sRef="; // plus serviceRef
	this.epgnow = "/web/epgnow"; // plus bouquetRev
	this.epgnext = "/web/epgnext"; // plus bouquetRev
	this.epgnownext = "/web/epgnownext";
	this.epgmulti = "/web/epgmulti";

	this.getservices = "/web/getservices"; // plus serviceref
	this.subservices = "/web/subservices"; // subservices for current service
	this.streamsubservices = "/web/streamsubservices?sRef="; // subservices for streaming service

	this.movielist= "/web/movielist"; // plus dirname,tag
	this.moviedelete= "/web/moviedelete"; // plus serviceref

	this.about= "/web/about";
	this.settings= "/web/settings";
	this.parentcontrol= "/web/parentcontrollist";
	this.signal = "/web/signal";
	this.deviceinfo = "/web/deviceinfo";
	this.external = "/web/external";

	this.mediaplayeradd= "/web/mediaplayeradd"; // plus file-serviceref
	this.mediaplayerlist= "/web/mediaplayerlist"; // plus full qualified path
	this.mediaplayerplay= "/web/mediaplayerplay"; // plus file-serviceref
	this.mediaplayerremove= "/web/mediaplayerremove"; // plus file-serviceref
	this.mediaplayercmd= "/web/mediaplayercmd"; // plus command
	this.mediaplayerwrite= "/web/mediaplayerwrite"; // plus filename

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
	this.grab = "/grab";
	this.session = "/web/session";
};

var URL = new url();

var bouquetsTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195) FROM BOUQUET "bouquets.tv" ORDER BY bouquet';
var bouquetsRadio = '1:7:2:0:0:0:0:0:0:0:(type == 2) || (type == 10) FROM BOUQUET "bouquets.radio" ORDER BY bouquet';
var providerTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195) FROM PROVIDERS ORDER BY name';
var providerRadio ='1:7:2:0:0:0:0:0:0:0:(type == 2) || (type == 10) FROM PROVIDERS ORDER BY name';
var satellitesTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195) FROM SATELLITES ORDER BY name';
var satellitesRadio ='1:7:2:0:0:0:0:0:0:0:(type == 2) || (type == 10) FROM SATELLITES ORDER BY name';
var allTv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195) ORDER BY name';
var allRadio = '1:7:2:0:0:0:0:0:0:0:(type == 2) || (type == 10) ORDER BY name';
