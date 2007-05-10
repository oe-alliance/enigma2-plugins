Version = '$Header$';

var DBG = true;
//DBG = false;

var url_getvolume = '/web/vol?set=state'; 
var url_setvolume = '/web/vol?set=set'; // plus new value eg: set=set15
var url_volumeup = '/web/vol?set=up';
var url_volumedown = '/web/vol?set=down';
var url_volumemute = '/web/vol?set=mute';

var url_epgservice = "/web/epgservice?sRef="; // plus serviceRef
var url_epgsearch = "/web/epgsearch?search="; // plus serviceRef
var url_epgnow = "/web/epgnow?bRef="; // plus bouqetRev

var url_getServices = "/web/getservices?sRef="; // plus serviceref
var url_subservices = "/web/subservices"; // subservices for current service

var url_updates= "/web/updates.html";

var url_movielist= "/web/movielist";

var url_about= "/web/about";

var url_settings= "/web/settings";

var url_parentcontrol= "/web/parentcontrollist";

var url_moviefiledelete= "/web/moviefiledelete"; // plus serviceref,eventid

var url_timerlist= "/web/timerlist";
var url_recordnow= "/web/recordnow";
var url_timeradd= "/web/timeradd"; // plus serviceref,begin,end,name,description,eit,disabled,justplay,afterevent
var url_timerchange= "/web/timerchange"; // plus serviceref,begin,end,name,description,eit,disabled,justplay,afterevent
var url_timeraddbyeventid= "/web/timeraddbyeventid"; // plus serviceref,eventid
var url_timerdelete= "/web/timerdelete"; // plus serviceref,bedin,end
var url_timerlistwrite="/web/timerlistwrite?write=saveWriteNow";
var url_timertoggleOnOff= "/web/timeronoff"; // plus serviceref,bedin,end

var url_message = "/web/message"; // plus text,type,timeout

var url_powerstate = "/web/powerstate"; // plus new powerstate
var url_remotecontrol = "/web/remotecontrol"; // plus command

var bouqet_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25)FROM BOUQUET "bouquets.tv" ORDER BY bouquet';
var bouqet_radio = '1:7:2:0:0:0:0:0:0:0:(type == 2)FROM BOUQUET "bouquets.radio" ORDER BY bouquet';
var bouqet_provider_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM PROVIDERS ORDER BY name';
var bouqet_provider_radio ='1:7:2:0:0:0:0:0:0:0:(type == 2) FROM PROVIDERS ORDER BY name';

var windowStyle = 'alphacube';