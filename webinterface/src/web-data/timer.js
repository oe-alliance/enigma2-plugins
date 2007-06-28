// Versioning
Version = '$Header$';

// TimerEdit variables:
var addTimerEditFormObject = new Object();
addTimerEditFormObject["TVListFilled"] = 0;
addTimerEditFormObject["RadioListFilled"] = 0;
addTimerEditFormObject["deleteOldOnSave"] = 0;
addTimerEditFormObject["eventID"] = 0;
days = [];
days[0] = 'mo';
days[1] = 'tu';
days[2] = 'we';
days[3] = 'th';
days[4] = 'fr';
days[5] = 'sa';
days[6] = 'su';

// Timer
function addTimerByID(sRef,eventID,justplay){
	if(parentPin(sRef)) {
		debug("addTimerByID\neventID: "+eventID);
		doRequest(url_timeraddbyeventid+"?sRef="+sRef+"&eventid="+eventID+"&justplay="+justplay, incomingTimerAddResult, false);	
	}
}
function incomingTimerAddResult(request){
	debug("onTimerAdded");
	if(request.readyState == 4){
		var addresult = new SimpleXMLResult(getXML(request));
		if(addresult.getState()){
			//timer was add
			loadTimerList();
		}else{
			messageBox("Timer Error","your Timer could not be added!\nReason: "+addresult.getStateText());
		}
	}		
}
function loadTimerList(){
	doRequest(url_timerlist, incomingTimerList, false);	
}

function incomingTimerList(request){
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		listerHtml 	= tplTimerListHeader;
		var aftereventReadable = new Array ('Nothing', 'Standby', 'Deepstandby/Shutdown');
		var justplayReadable = new Array('record', 'zap');
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];
			var beginDate = new Date(Number(timer.getTimeBegin())*1000);
			var endDate = new Date(Number(timer.getTimeEnd())*1000);
			var namespace = { 	
				'servicereference': timer.getServiceReference(),
				'servicename': quotes2html(timer.getServiceName()),
				'title': quotes2html(timer.getName()),
				'description': quotes2html(timer.getDescription()),
				'descriptionextended': quotes2html(timer.getDescriptionExtended()),
				'begin': timer.getTimeBegin(),
				'beginDate': beginDate.toLocaleString(),
				'end': timer.getTimeEnd(),
				'endDate': endDate.toLocaleString(),
				'state': timer.getState(),
				'duration': Math.ceil((timer.getDuration()/60)),
				'repeated': timer.getRepeated(),
				'repeatedReadable': repeatedReadable(timer.getRepeated()),
				'justplay': timer.getJustplay(),
				'justplayReadable': justplayReadable[Number(timer.getJustplay())],
				'afterevent': timer.getAfterevent(),
				'aftereventReadable': aftereventReadable[Number(timer.getAfterevent())],
				'disabled': timer.getDisabled(),
				'onOff': timer.getToggleDisabledIMG(),
				'color': timer.getColor()
			};
			listerHtml += RND(tplTimerListItem, namespace);
		}
		listerHtml += tplTimerListFooter;
		$('BodyContentChannellist').innerHTML = listerHtml;
		setBodyMainContent('BodyContentChannellist');
	}
}
function repeatedReadable(num) {
	num = Number(num);
	if(num == 0) {
		return "One Time";
	}
	
	var html = "";
	var Repeated = new Object();
	Repeated["Mo-Su"] =127;
	Repeated["Su"] =    64;
	Repeated["Sa"] =    32;
	Repeated["Mo-Fr"] = 31;
	Repeated["Fr"] =    16;
	Repeated["Th"] =     8;
	Repeated["We"] =     4;
	Repeated["Tu"] =     2;
	Repeated["Mo"] =     1;
	
	for(rep in Repeated) {
		if(rep.toString() != "extend") {
			var check = Number(Repeated[rep]);
			if(check <= num) {
				num -= check;
				if(html == "") {
					html += rep.toString();
				} else {
					html += "," + rep.toString();
				}
			}
		}
	}
	return html;
}

function colorTimerListEntry (state) {
	if (state == 0) {
		return "000000";
	} else if(state == 1) {
		return "00BCBC";
	} else if(state == 2) {
		return "9F1919";
	} else {
		return "00BCBC";
	}
}
function delTimer(sRef,begin,end,servicename,title,description,readyFunction){
	debug("delTimer: sRef("+sRef+"),begin("+begin+"),end("+end+"),servicename("+servicename+"),title("+title+"),description("+description+")");
	Dialog.confirm(
		"Selected timer:<br>"
		+"Channel: "+servicename+"<br>"
		+"Title: "+title+"<br>"
		+"Description: "+description+"<br>"
		+"Are you sure that you want to delete the Timer?",
		 {windowParameters: {width:300, className: windowStyle},
			okLabel: "delete",
			buttonClass: "myButtonClass",
			cancel: function(win) {debug("delTimer cancel confirm panel")},
			ok: function(win) { 
							    debug("delTimer ok confirm panel"); 
							    doRequest(url_timerdelete+"?sRef="+sRef+"&begin="+begin+"&end="+end, readyFunction, false);
							    return true;
							  }
			}
	);
}

function incomingTimerDelResult(request){
	debug("onTimerDeleted");
	if(request.readyState == 4){
		var delresult = new SimpleXMLResult(getXML(request));
		debug("Lade liste");
		loadTimerList();
	}		
}
function loadTimerFormNow() {
	var now = new Date();
	addTimerEditFormObject["syear"] = now.getFullYear();
	addTimerEditFormObject["smonth"] = now.getMonth() + 1;
	addTimerEditFormObject["sday"] = now.getDate();
	addTimerEditFormObject["shour"] = now.getHours();
	addTimerEditFormObject["smin"] = now.getMinutes();

	var	plusTwoHours = new Date(now.getTime() + ((120 *60)*1000) );
	addTimerEditFormObject["eyear"] = plusTwoHours.getFullYear();
	addTimerEditFormObject["emonth"] = plusTwoHours.getMonth() + 1;
	addTimerEditFormObject["eday"] = plusTwoHours.getDate();
	addTimerEditFormObject["ehour"] = plusTwoHours.getHours();
	addTimerEditFormObject["emin"] = plusTwoHours.getMinutes();
		
	addTimerEditFormObject["justplay"] = "record";
	addTimerEditFormObject["channel"] = "";
	addTimerEditFormObject["channelName"] = "";
	addTimerEditFormObject["channelSort"] = "tv";
	addTimerEditFormObject["name"] = "";
	addTimerEditFormObject["description"] = "";
	addTimerEditFormObject["repeated"] = 0;
	addTimerEditFormObject["afterEvent"] = "0";
	addTimerEditFormObject["deleteOldOnSave"] = 0;
	
	addTimerEditFormObject["beginOld"] = 0;
	addTimerEditFormObject["endOld"] = 0;
	
	
	debug("loadTimerFormNow 2");
	loadTimerFormChannels();
}

function loadTimerFormSeconds(justplay,begin,end,repeated,channel,channelName,name,description,afterEvent,deleteOldOnSave,eit) {
	debug('justplay:'+justplay+' begin:'+begin+' end:'+end+' repeated:'+repeated+' channel:'+channel+' name:'+name+' description:'+description+' afterEvent:'+afterEvent+' deleteOldOnSave:'+deleteOldOnSave);
	var start = new Date(Number(begin)*1000);
	addTimerEditFormObject["syear"] = start.getFullYear();
	addTimerEditFormObject["smonth"] = start.getMonth() + 1;
	addTimerEditFormObject["sday"] = start.getDate();
	addTimerEditFormObject["shour"] = start.getHours();
	addTimerEditFormObject["smin"] = start.getMinutes();
	
	var	stopp = new Date(Number(end)*1000);
	addTimerEditFormObject["eyear"] = stopp.getFullYear();
	addTimerEditFormObject["emonth"] = stopp.getMonth() + 1;
	addTimerEditFormObject["eday"] = stopp.getDate();
	addTimerEditFormObject["ehour"] = stopp.getHours();
	addTimerEditFormObject["emin"] = stopp.getMinutes();
	
	addTimerEditFormObject["justplay"] = String(justplay);
	addTimerEditFormObject["channel"] = decodeURIComponent(String(channel));
	addTimerEditFormObject["channelName"] = String(channelName);
	addTimerEditFormObject["channelSort"] = "";
	addTimerEditFormObject["name"] = String(name);
	addTimerEditFormObject["description"] = String(description);
	addTimerEditFormObject["repeated"] = Number(repeated);
	addTimerEditFormObject["afterEvent"] = Number(afterEvent);
	
	debug(justplay+"|"+begin+"|"+end+"|"+repeated+"|"+channel+"|"+name+"|"+description+"|"+afterEvent);

	addTimerEditFormObject["deleteOldOnSave"] = Number(deleteOldOnSave);
	addTimerEditFormObject["beginOld"] = Number(begin);
	addTimerEditFormObject["endOld"] = Number(end);
	
	addTimerEditFormObject["eventID"] = Number(eit);
	
	loadTimerFormChannels();
}

// startin to load for TV
function loadTimerFormChannels() {
	if(addTimerEditFormObject["TVListFilled"] == 1 && addTimerEditFormObject["RadioListFilled"] == 1) {
		loadTimerForm();
	} else if(addTimerEditFormObject["TVListFilled"] == 1 && addTimerEditFormObject["RadioListFilled"] == 0) {
		addTimerListFormatTV();
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.tv%22%20ORDER%20BY%20bouquet'
		doRequest(url_getServices+favorites, addTimerListFormatTV, false);
	}
}

function addTimerListFormatTV(request) {
	if(addTimerEditFormObject["RadioListFilled"] == 0) {
		if(request.readyState == 4){
			var services = new ServiceList(getXML(request)).getArray();
			var tv = new Object();
			for ( var i = 0; i < services.length ; i++){
				var reference = services[i];
				tv[reference.servicereference] = reference.servicename;
			}
			addTimerEditFormObject["TVListFilled"] = 1;
			addTimerEditFormObject["TVList"] = tv;
		}
	}
	if(addTimerEditFormObject["RadioListFilled"] == 1) {
		loadTimerForm()
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.radio%22%20ORDER%20BY%20bouquet';
		doRequest(url_getServices+favorites, addTimerListFormatRadio, false);
	}
}
function addTimerListFormatRadio(request) {
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		var radio = new Object();
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			radio[reference.servicereference] = reference.servicename;
		}
		addTimerEditFormObject["RadioListFilled"] = 1;
		addTimerEditFormObject["RadioList"] = radio;
	}
	loadTimerForm();
}

function loadTimerForm(){

	var Action = new Object();
	Action["0"] = "Record";
	Action["1"] = "Zap";
	
	var Repeated = new Object();
	Repeated["1"] =  "mo";
	Repeated["2"] = "tu";
	Repeated["4"] =  "we";
	Repeated["8"] =  "th";
	Repeated["16"] = "fr";
	Repeated["32"] = "sa";
	Repeated["64"] = "su";
	Repeated["31"] = "mf";
	Repeated["127"] ="ms";
	
	var AfterEvent = new Object();
	AfterEvent["0"] = "Nothing";
	AfterEvent["1"] = "Standby";
	AfterEvent["2"] = "Deepstandby/Shutdown";
	
	addTimerEditFormObject["name"] = (typeof(addTimerEditFormObject["name"]) != "undefined") ? addTimerEditFormObject["name"] : "";
	addTimerEditFormObject["name"] = (addTimerEditFormObject["name"] == "") ? " " : addTimerEditFormObject["name"];

	addTimerEditFormObject["description"] = (typeof(addTimerEditFormObject["description"]) != "undefined") ? addTimerEditFormObject["description"] : "";
	addTimerEditFormObject["description"] = (addTimerEditFormObject["description"] == "") ? " " : addTimerEditFormObject["description"];

	var channelObject = addTimerEditFormObject["TVList"];
	if(	addTimerEditFormObject["channelSort"] == "tv") {
		// already set
	} else if( addTimerEditFormObject["channelSort"] == "radio") {
		channelObject = addTimerEditFormObject["RadioList"];
	} else {
		var found = 0;
		for( element in addTimerEditFormObject["TVList"]) {
			if( element == addTimerEditFormObject["channel"]) {
				found = 1;
				break;
			}
		}
		if(found == 0) {
			for( element in addTimerEditFormObject["RadioList"]) {
				if( element == addTimerEditFormObject["channel"]) {
					channelObject = addTimerEditFormObject["RadioList"];
					found = 1;
					break;
				}
			}
		}
		if(found == 0) {
			addTimerEditFormObject["TVList"][addTimerEditFormObject["channel"]] = addTimerEditFormObject["channelName"];
		}
	}
	var dashString = "------";
	channelObject[dashString] = "- Bouquets -";
	var listeNeu = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouqet_tv)])).getArray();
	if(addTimerEditFormObject["channelSort"] == "radio") {
		debug("weiter");
		listeNeu = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouqet_radio)])).getArray();
	}
	debug("hier" + listeNeu.length);
	for (i = 1; i < listeNeu.length; i++) {
		var element = listeNeu[i];
		channelObject[String(dashString+i)] = "---";
		channelObject[element.getServiceReference()] = element.getServiceName();
	}
	var namespace = { 	
				'justplay': addTimerFormCreateOptionList(Action, addTimerEditFormObject["justplay"]),
				'syear': addTimerFormCreateOptions(2007,2010,addTimerEditFormObject["syear"]),
				'smonth': addTimerFormCreateOptions(1,12,addTimerEditFormObject["smonth"]),
				'sday': addTimerFormCreateOptions(1,31,addTimerEditFormObject["sday"]),
				'shour': addTimerFormCreateOptions(0,23,addTimerEditFormObject["shour"]),
				'smin': addTimerFormCreateOptions(0,59,addTimerEditFormObject["smin"]),
				'eyear': addTimerFormCreateOptions(2007,2010,addTimerEditFormObject["eyear"]),
				'emonth': addTimerFormCreateOptions(1,12,addTimerEditFormObject["emonth"]),
				'eday': addTimerFormCreateOptions(1,31,addTimerEditFormObject["eday"]),
				'ehour': addTimerFormCreateOptions(0,23,addTimerEditFormObject["ehour"]),
				'emin': addTimerFormCreateOptions(0,59,addTimerEditFormObject["emin"]),
				'channel': addTimerFormCreateOptionList(channelObject, addTimerEditFormObject["channel"]),
				'name': addTimerEditFormObject["name"],
				'description': addTimerEditFormObject["description"],
				'repeated': addTimerFormCreateOptionListRepeated(Repeated, addTimerEditFormObject["repeated"]),
				'deleteOldOnSave': addTimerEditFormObject["deleteOldOnSave"],
				'channelOld': addTimerEditFormObject["channel"],
				'beginOld': addTimerEditFormObject["beginOld"],
				'endOld': addTimerEditFormObject["endOld"],
				'afterEvent': addTimerFormCreateOptionList(AfterEvent, addTimerEditFormObject["afterEvent"]),
				'eventID': addTimerEditFormObject["eventID"]
		};
	var listerHtml = RND(tplAddTimerForm, namespace);
	$('BodyContentChannellist').innerHTML = listerHtml;

	// Empty some stuff, but keep others to have the performance
	var tmp1 = addTimerEditFormObject["RadioList"];
	var tmp2 = addTimerEditFormObject["TVList"];
	addTimerEditFormObject = new Object();
	addTimerEditFormObject["deleteOldOnSave"] = 0;
	addTimerEditFormObject["RadioList"] = tmp1;
	addTimerEditFormObject["TVList"] = tmp2;
	addTimerEditFormObject["TVListFilled"] = 1;
	addTimerEditFormObject["RadioListFilled"] = 1;
}

function addTimerFormCreateOptions(start,end,number) {
	var html = '';
	for(i = start; i <= end; i++) {
		var txt = (String(i).length == 1) ? "0" + String(i) : String(i);
		var selected = 	(i == Number(number)) ? "selected" : " ";
		var namespace = {
			'value': i,
			'txt': txt,
			'selected': selected };
		html += RND(tplAddTimerFormOptions, namespace);
	}
	return html;
}
function addTimerFormCreateOptionList(object,selected) {
	html = '';
	var found = 0;
	for(var element in object) {
		var txt = String(object[element]);
		var sel = " ";
		if(element == selected) {
			found = 1;
			sel = "selected";
		}
		var namespace = {
			'value': element,
			'txt': txt,
			'selected': sel };
		if(element != "extend") {
			html += RND(tplAddTimerFormOptions, namespace);
		}
	}
	if(found == 0) {
		var namespace = {
			'value': element,
			'txt': txt,
			'selected': sel };
	}
	return html;
}

function timerFormExtendChannellist(bouqet) {
	var listeTV = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouqet_tv)])).getArray();
	var listeRadio = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouqet_radio)])).getArray();
	found = 0;
	for(i = 0; i < listeTV.length; i++) {
		var element = listeTV[i];
		if(String(element.getServiceReference()) == bouqet) {
			found = 1;
			break;
		}
	}
	if(found == 0) {
		for(i = 0; i < listeRadio.length; i++) {
			var element = listeTV[i];
			if(String(element.getServiceReference()) == bouqet) {
				found = 1;
				break;
			}
		}
	}
	if(found == 1) {
		servicereftoloadepgnow = bouqet;
		if(typeof(loadedChannellist[servicereftoloadepgnow]) == "undefined") {	
			doRequest(url_getServices+servicereftoloadepgnow, incomingTimerFormExtendChannellist, true);
		} else {
			incomingTimerFormExtendChannellist();
		}
	}
}
function incomingTimerFormExtendChannellist(request) {
	var services = null;
	if(typeof(loadedChannellist[servicereftoloadepgnow]) != "undefined"){
		services = loadedChannellist[servicereftoloadepgnow];
	} else if(request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		loadedChannellist[servicereftoloadepgnow] = services;
		debug("got "+services.length+" Services");
	}
	var attachLater = new Object();
	if(services != null) {
		debug("incomingTimerFormExtendChannellist " + services.length);
		var selected = $('channel').selectedIndex;
		for(j = selected; j < $('channel').options.length; j++) {
			if($('channel').options[j].value == servicereftoloadepgnow) {
				j++;
				for(var i = 0; i < services.length ; i++) {
					var reference = services[i];
					var newEntry = new Option(reference.getServiceName(), reference.getServiceReference(), false, true);
					if(typeof($('channel').options[j]) != "undefined") {
						attachLater[String($('channel').options[j].value)] = $('channel').options[j].text;
					}
					$('channel').options[j] = newEntry;
					j++;
				}
			}
			break;
		}
		for(x in attachLater) {
			var newEntry = new Option(attachLater[x], x, false, true);
			if(x != "extend") {
				$('channel').options[$('channel').options.length] = newEntry;
			}
		}
		$('channel').options[selected].selected = true;
		
	}
}

function addTimerFormChangeTime(which) {
	var start = new Date( $('syear').value, ($('smonth').value -1), $('sday').value, $('shour').value, $('smin').value, 0);
	var end = new Date($('eyear').value, ($('emonth').value -1), $('eday').value, $('ehour').value, $('emin').value, 0);
//	debug("("+start+")(" + end+")");

	if(start.getTime() > end.getTime()) {
		opponent = (which.substr(0,1) == 's') ? 'e' +  which.substr(1, which.length -1) : 's' +  which.substr(1, which.length -1) ;
		$(opponent).value = $(which).value;
	}
	var all = new Array('year','month','day','hour','min');
	for(i=0; i < all.length; i++) {
		if(which.substr(1, which.length -1) == all[i]) {
			addTimerFormChangeTime(which.substr(0,1) + all[i+1] );
			break;
		}
	}
}
function addTimerFormChangeType() {
	var selected = ($('tvradio').checked == true) ? addTimerEditFormObject["TVList"]: addTimerEditFormObject["RadioList"];
	for (i = $('channel').options.length; i != 0; i--) {
		$('channel').options[i - 1] = null;
	}
	var i = -1;
	for(element in selected) {
		if(element != "extend") {
			i++;
			$('channel').options[i] = new Option(selected[element]);
			$('channel').options[i].value = element;
		}
	}
}
function addTimerFormCreateOptionListRepeated(Repeated,repeated) {
	var num = Number(repeated);
	var html = "";
	var html2 = "";
	var list = new Array(127, 64, 32, 31, 16, 8, 4, 2, 1);
	for(i = 0; i < list.length; i++) {
		var txt = String(Repeated[String(list[i])]);
		if( String(Repeated[String(list[i])]) == "mf") {
			txt = "Mo-Fr";
		} else if( String(Repeated[String(list[i])]) == "ms") {
			txt = "Mo-Su";
		} else {
			txt = txt.substr(0,1).toUpperCase() + txt.substr(1,1);
		}
		var checked = " ";
		if(num >=  list[i]) {
			num -= list[i];
			checked = "checked";
		}
		var namespace = {
			'id': Repeated[String(list[i])],
			'name': Repeated[String(list[i])],
			'value': list[i],
			'txt': txt,
			'checked': checked };
		if(String(Repeated[String(list[i])]) == "mf" || String(Repeated[String(list[i])]) == "ms") {
			html2 = RND(tplAddTimerFormCheckbox, namespace) + html2;
		} else {
			html = RND(tplAddTimerFormCheckbox, namespace) + html;
		}
	}
	return html + html2;
}
function sendAddTimer() {
	debug("sendAddTimer" + "parentChannel:" +$('channel').value);
	
	if(parentPin($('channel').value)) {
		var beginD = new Date(ownLazyNumber($('syear').value), (ownLazyNumber($('smonth').value) - 1), ownLazyNumber($('sday').value), ownLazyNumber($('shour').value), ownLazyNumber($('smin').value));
		var begin = beginD.getTime()/1000;
		
		var endD = new Date(ownLazyNumber($('eyear').value), (ownLazyNumber($('emonth').value) - 1), ownLazyNumber($('eday').value), ownLazyNumber($('ehour').value), ownLazyNumber($('emin').value));
		var end = endD.getTime()/1000;

		var repeated = 0;
		if( $('ms').checked ) {
			repeated = 127;
		} else if($('mf').checked) {
			repeated = 31;
			if($('sa').checked) {
				repeated += ownLazyNumber($('sa').value);
			}
			if($('su').checked) {
				repeated += ownLazyNumber($('su').value);
			}
		} else {
			var check = new Array('mo', 'tu', 'we', 'th', 'fr');
			for(i = 0; i < check.length; i++) {
				if($(check[i]).checked) {
					repeated += Number($(check[i]).value);
				}
			}
		}
	
		var descriptionClean = ($('descr').value == " " || $('descr').value == "N/A") ? "" : $('descr').value;
		var nameClean = ($('name').value == " " || $('name').value == "N/A") ? "" : $('name').value;
		
		var neverString = "[0-9a-zA-Z\-_\.\!\(\)&=\+$,;\?/:\\\ ]*";
		if(descriptionClean != descriptionClean.match(neverString) ||
			nameClean != nameClean.match(neverString)) {
			alert("Please only use "+neverString+" in the name and the description field");
			return;
		}

		var repeated = 0;
		if($('ms').checked) {
			repeated = ownLazyNumber($('ms').value);
		} else if($('mf').checked) {
			repeated = ownLazyNumber($('mf').value);
			if($('su').checked) {
				repeated += ownLazyNumber($('su').value);
			}
			if($('sa').checked) {
				repeated += ownLazyNumber($('sa').value);
			}
		} else {
			for(i = 0; i < days.length; i++){
				if($(days[i]).checked) {
					repeated += ownLazyNumber($(days[i]).value);
				}
			}
		}
		//addTimerByID(\'%(servicereference)\',\'%(eventid)\',\'False\');
		doRequest(url_timerchange+"?"+"sRef="+($('channel').value).replace("&quot;", '"')+"&begin="+begin
		  +"&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean)
		  +"&afterevent="+$('after_event').value+"&eit=0&disabled=0"
		  +"&justplay="+ownLazyNumber($('justplay').value)+"&repeated="+repeated
		  +"&channelOld="+$('channelOld').value
		  +"&beginOld="+$('beginOld').value+"&endOld="+$('endOld').value
		  +"&eventID"+$('eventID').value
		  +"&deleteOldOnSave="+ownLazyNumber($('deleteOldOnSave').value), incomingTimerAddResult, false);
	}
}

function cleanTimerListNow(){
	debug("cleanTimerListNow pushed");
	doRequest(url_timerlist, incomingCleanTimerListNow, false);	
}
function incomingCleanTimerListNow(request) {
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("have "+timers.length+" timer");
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];
			debug(timer.getState() + " " + quotes2html(timer.getName()));
			if(timer.getState() != 0 && timer.getState() != 2) {
				delTimer(timer.getServiceReference(),timer.getTimeBegin(),timer.getTimeEnd()
					,quotes2html(timer.getServiceName()),quotes2html(timer.getName()),quotes2html(timer.getDescription()),incomingJustDoNothing);
			}
		}
	}
}
function incomingJustDoNothing(request){
	debug("just do nothing");
}
function sendToggleTimerDisable(justplay,begin,end,repeated,channel,name,description,afterEvent,disabled){
	disabled = (ownLazyNumber(disabled) == 0) ? 1 : 0;
	
	var descriptionClean = (description == " " || description == "N/A") ? "" : description;
	var nameClean = (name == " " || name == "N/A") ? "" : name;

	doRequest(url_timerchange+"?"+"sRef="+channel.replace("&quot;", '"')+"&begin="+begin
	 +"&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean)
	 +"&afterevent="+afterEvent+"&eit=0&disabled="+disabled
	 +"&justplay="+justplay+"&repeated="+repeated
	 +"&channelOld="+channel
	 +"&beginOld="+begin+"&endOld="+end
	 +"&deleteOldOnSave=1", incomingTimerAddResult, false);
}