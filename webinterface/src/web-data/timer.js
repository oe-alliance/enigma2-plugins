// $Header$

// TimerEdit variables:
var addTimerEditFormArray = [];
addTimerEditFormArray.TVList = [];
addTimerEditFormArray.TVListFilled = 0;
addTimerEditFormArray.RadioListFilled = 0;
addTimerEditFormArray.deleteOldOnSave = 0;
addTimerEditFormArray.eventID = 0;
addTimerEditFormArray.locationsList = [];
addTimerEditFormArray.tagsList = [];

var days = [ 'mo', 'tu', 'we', 'th', 'fr', 'sa', 'su' ];

var servicereftoloadepgnow = '';
// Channel menu consists of:
// 1. The currently selected channel, unless it is contained in 2.
// 2. The currently selected bouquet
// 3. The TV bouquets and the Radio bouquets
function addTimerFormPrepareChannelMenu() {
	var result = {};
	var tvblist = addTimerEditFormArray.TVList;
	var radioblist = addTimerEditFormArray.RadioList;
	var currbouquet = addTimerEditFormArray.currBouquetName;
	var currblist = addTimerEditFormArray.currBouquetList;

	var found = false;
	for (var i = 0; i < currblist.length; i++) {
		var service = currblist[i];
		if (addTimerEditFormArray.channel == service.servicename) {
			found = true;
			break;
		}		
	}
	if (!found) {
		result[addTimerEditFormArray.channel] = addTimerEditFormArray.channelName;
	}
	
	if (currbouquet) {
		result["<Currbouquet>"] = "-- " + currbouquet + " --";
		for (var i = 0; i < currblist.length; i++) {
			var service = currblist[i];
			result[service.servicereference] = service.servicename;
		}
	}
	result["<Bouquets>"] = "-- Bouquets --";
	for (var i = 0; i < tvblist.length; i++) {
		service = tvblist[i];
		result[service.servicereference] = service.servicename;		
	}
	for (var i = 0; i < radioblist.length; i++) {
		service = radioblist[i];
		result[service.servicereference] = service.servicename;	
	}
	return result;
}

function addTimerFormChangeChannel(newchannel) {
	var tvblist = addTimerEditFormArray.TVList;
	var radioblist = addTimerEditFormArray.RadioList;
	if (newchannel == "<Currbouquet>" || newchannel == "<Bouquets>") {
		// reset selection to last valid channel
		for ( var i = 0; i < $('channel').options.length; i++) {
			if ($('channel').options[i].value == addTimerEditFormArray.channel) {
				$('channel').options[i].selected = true;
				break;
			}
		}
		return;
	}
	var found = false;
	for (var i = 0; i < tvblist.length; i++) {
		var service = tvblist[i];
		if (service.servicereference == newchannel) {
			found = true;
			addTimerEditFormArray.currBouquetName = service.servicename;
			addTimerEditFormArray.currBouquetList = [];
			break;
		}
	}
	if (!found) {
		for (var i = 0; i < radioblist.length; i++) {
			var service = radioblist[i];
			if (service.servicereference == newchannel) {
				found = true;
				addTimerEditFormArray.currBouquetName = service.servicename;
				addTimerEditFormArray.currBouquetList = [];
				break;
			}
		}
	}
	if (found) {
		// bouquet selected, update menu
		servicereftoloadepgnow = service.servicereference;
		if (typeof (loadedChannellist[servicereftoloadepgnow]) == "undefined") {
			doRequest(URL.getservices + servicereftoloadepgnow,
					incomingAddTimerFormChangeChannel, true);
		} else {
			incomingAddTimerFormChangeChannel();
		}
	} else {
		// real channel selected, update channel and channelName
		addTimerEditFormArray.channel = newchannel;
		for (i = 0; i < $('channel').options.length; i++) {
			if ($('channel').options[i].value == newchannel) {
				addTimerEditFormArray.channelName = $('channel').options[i].text;
				break;
			}
		}
	}
}

function incomingAddTimerFormChangeChannel(request) {
	var services = null;
	if (typeof (loadedChannellist[servicereftoloadepgnow]) != "undefined") {
		services = loadedChannellist[servicereftoloadepgnow];
	} else if (request.readyState == 4) {
		services = new ServiceList(getXML(request)).getArray();
		loadedChannellist[servicereftoloadepgnow] = services;
	}
	if (services !== null) {
		debug("[incomingAddTimerFormChangeChannel] Got " + services.length + " Services");
		for ( var i = 0; i < services.length; i++) {
			var service = services[i];
			addTimerEditFormArray.currBouquetList[i] = service;
		}
	}

	var lst = addTimerFormPrepareChannelMenu();

	for (i = $('channel').options.length; i !== 0; i--) {
		$('channel').options[i - 1] = null;
	}
	for (var element in lst) {
		$('channel').options[i] = new Option(lst[element]);
		$('channel').options[i].value = element;
		if (element == addTimerEditFormArray.channel) {
			$('channel').options[i].selected = true;
		}
		i++;
	}
}

function addTimerFormPrepareTagsMenu(currtags) {
	var result = {};
	var resultsuff = {};
	var taglist = addTimerEditFormArray.tagsList;

	if (currtags === "") {
		i = 0;
		result[""] = "<None>";
		for ( var i = 0; i < taglist.length; i++) {
			result[taglist[i]] = taglist[i];
		}
	} else {
		result[currtags] = currtags;
		var tags = currtags.split(" ");
		for ( var i = 0; i < taglist.length; i++) {
			var res = "";
			var found = false;
			for ( var j = 0; j < tags.length; j++) {
				if (tags[j] != taglist[i]) {
					res += " " + tags[j];
				} else {
					found = true;
				}
			}
			if (!found) {
				res += " " + taglist[i];
			}
			if (res.length > 0) {
				res = res.substring(1, res.length);
			}
			if (found) {
				resultsuff[res] = "- " + taglist[i];
			} else {
				result[res] = "+ " + taglist[i];
			}
		}
		if (tags.length > 1) {
			for (var ele in resultsuff) {
				result[ele] = resultsuff[ele];
			}
		}
		result[""] = "<None>";
	}
	return result;
}

function addTimerFormChangeTags(newtags) {
	var lst = addTimerFormPrepareTagsMenu(newtags);

	for ( var i = $('tags').options.length; i !== 0; i--) {
		$('tags').options[i - 1] = null;
	}

	for (var element in lst) {
		$('tags').options[i] = new Option(lst[element]);
		$('tags').options[i].value = element;
		i++;
	}
}

// Timer
function addTimerByID(sRef, eventID, justplay) {
	if (parentPin(sRef)) {
		debug("[addTimerByID] eventID: " + eventID);
		doRequest(URL.timeraddbyeventid + "?sRef=" + sRef + "&eventid="	+ 
				eventID + "&justplay=" + justplay, incomingTimerAddResult, false);
	}
}

function incomingTimerAddResult(request) {
	debug("[incomingTimerAddResult] called");
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		if (result.getState()) {
			//timer has been added
			loadTimerList();
		}
		simpleResultHandler(result);
	}
}

function loadTimerList() {
	doRequest(URL.timerlist, incomingTimerList, false);
}

function incomingTimerList(request) {
	if (request.readyState == 4) {
		var timerList = new TimerList(getXML(request)).getArray();
		debug("[incomingTimerList] Got " + timerList.length + " timers");

		var data = {
			timer : timerList
		};
		processTpl('tplTimerList', data, 'contentMain');
	}
}

function repeatedReadable(num) {
	num = Number(num);
	if (num === 0) {
		return "One Time";
	}

	var retVal = "";
	var Repeated = {};
	Repeated["Mo-Su"] = 127;
	Repeated["Mo-Fr"] = 31;
	Repeated["Su"] = 64;
	Repeated["Sa"] = 32;
	Repeated["Fr"] = 16;
	Repeated["Th"] = 8;
	Repeated["We"] = 4;
	Repeated["Tu"] = 2;
	Repeated["Mo"] = 1;

	for (var rep in Repeated) {
		if (rep.toString() != 'extend') {
			var check = Number(Repeated[rep]);
			if (!(~num & check)) {
				num -= check;
				if (retVal === '') {
					retVal += rep.toString();
				} else {
					retVal = rep.toString() + ',' + retVal;
				}
			}
		}
	}
	return retVal;
}

function delTimer(sRef, begin, end, servicename, title, description,
		readyFunction) {
	debug("[delTimer] sRef(" + sRef + "),begin(" + begin + "),end(" + 
			end	+ "),servicename(" + servicename + "),title(" + 
			title + "),description(" + description + ")");
	var result = confirm("Selected timer:\n" + "Channel: " + servicename + "\n"	+ 
			"Title: " + title + "\n" + "Description: " + description + "\n"	+ 
			"Are you sure that you want to delete the Timer?");
	if (result) {
		debug("[delTimer] ok confirm panel");
		doRequest(URL.timerdelete + "?sRef=" + sRef + "&begin=" + begin + 
				"&end=" + end, readyFunction, false);
		return true;

	} else {
		debug("[delTimer] cancel confirm panel");
	}
	return false;
}

function incomingTimerDelResult(request) {
	debug("[incomingTimerDelResult] called");
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		debug("[incomingTimerDelResult] Loading List");
		loadTimerList();
	}
}

function loadTimerFormNow() {
	var now = new Date();
	addTimerEditFormArray.year = now.getFullYear();
	addTimerEditFormArray.month = now.getMonth() + 1;
	addTimerEditFormArray.day = now.getDate();
	addTimerEditFormArray.shour = now.getHours();
	addTimerEditFormArray.smin = now.getMinutes();

	var plusTwoHours = new Date(now.getTime() + ((120 * 60) * 1000));
	addTimerEditFormArray.ehour = plusTwoHours.getHours();
	addTimerEditFormArray.emin = plusTwoHours.getMinutes();

	addTimerEditFormArray.justplay = "0";
	addTimerEditFormArray.channel = "";
	addTimerEditFormArray.channelName = "";
	addTimerEditFormArray.name = "";
	addTimerEditFormArray.description = "";
	addTimerEditFormArray.dirname = "";
	addTimerEditFormArray.tags = "";
	addTimerEditFormArray.repeated = 0;
	addTimerEditFormArray.afterEvent = "3";
	addTimerEditFormArray.deleteOldOnSave = 0;

	addTimerEditFormArray.beginOld = 0;
	addTimerEditFormArray.endOld = 0;
	addTimerEditFormArray.eventID = 0;

	debug("[loadTimerFormNow] done");
	loadTimerFormTags();
}

function loadTimerEditForm(justplay, begin, end, repeated, channel,
		channelName, name, description, dirname, tags, afterEvent,
		deleteOldOnSave, eit) {
	debug('[loadTimerEditForm] justplay: ' + justplay + ',begin: ' + begin + 
			',end: ' + end + ',repeated: ' + repeated + ',channel: ' + 
			channel + ',name: ' + name + ',description: ' + description + 
			',dirname: ' + dirname + ',tags: ' + tags + ',afterEvent: '	+ 
			afterEvent + ',deleteOldOnSave: ' + deleteOldOnSave);
	var start = new Date(Number(begin) * 1000);
	addTimerEditFormArray.year = start.getFullYear();
	addTimerEditFormArray.month = start.getMonth() + 1;
	addTimerEditFormArray.day = start.getDate();
	addTimerEditFormArray.shour = start.getHours();
	addTimerEditFormArray.smin = start.getMinutes();

	var stopp = new Date(Number(end) * 1000);
	addTimerEditFormArray.ehour = stopp.getHours();
	addTimerEditFormArray.emin = stopp.getMinutes();

	addTimerEditFormArray.justplay = String(justplay);
	addTimerEditFormArray.channel = String(channel);
	addTimerEditFormArray.channelName = String(channelName);
	addTimerEditFormArray.name = String(name);
	addTimerEditFormArray.description = String(description);
	addTimerEditFormArray.dirname = String(dirname);
	addTimerEditFormArray.tags = String(tags);
	addTimerEditFormArray.repeated = Number(repeated);
	addTimerEditFormArray.afterEvent = afterEvent;

	debug("[loadTimerEditForm]" + justplay + "|" + begin + "|" + end + "|" + 
			repeated + "|" + channel + "|" + name + "|" + description + "|"	+ 
			dirname + "|" + tags + "|" + afterEvent);

	addTimerEditFormArray.deleteOldOnSave = Number(deleteOldOnSave);
	addTimerEditFormArray.beginOld = Number(begin);
	addTimerEditFormArray.endOld = Number(end);

	addTimerEditFormArray.eventID = Number(eit);

	loadTimerFormTags();
}

function loadTimerFormTags() {
	doRequest(URL.gettags, incomingTimerFormTags, false);
}

function incomingTimerFormTags(request) {
	debug("[incomingTimerFormTags] called");
	if (request.readyState == 4) {
		var result = new SimpleXMLList(getXML(request), "e2tag");
		addTimerEditFormArray.tagsList = result.getList();
		loadTimerFormLocations();
	}
}

function loadTimerFormLocations() {
	doRequest(URL.getlocations, incomingTimerFormLocations, false);
}

function incomingTimerFormLocations(request) {
	debug("[incomingTimerFormLocations] called");
	if (request.readyState == 4) {
		var result = new SimpleXMLList(getXML(request), "e2location");
		addTimerEditFormArray.locationsList = result.getList();
		if (addTimerEditFormArray.locationsList.length === 0) {
			addTimerEditFormArray.locationsList = [ "/hdd/movie" ];
		}
		loadTimerFormChannels();
	}
}

// starting to load for TV
function loadTimerFormChannels() {
	if (addTimerEditFormArray.TVListFilled === 1 && 
			addTimerEditFormArray.RadioListFilled === 1) {
		loadTimerForm();
	} else if (addTimerEditFormArray.TVListFilled === 1	&& 
			addTimerEditFormArray.RadioListFilled === 0) {
		addTimerListFormatTV();
	} else {
		doRequest(URL.getservices + encodeURIComponent(bouquetsTv),
				addTimerListFormatTV, false);
	}
}

function addTimerListFormatTV(request) {
	if (addTimerEditFormArray.RadioListFilled === 0) {
		if (request.readyState == 4) {
			var serviceList = new ServiceList(getXML(request)).getArray();
			var tv = [];
			
			for ( var i = 0; i < serviceList.length; i++) {
				var service = serviceList[i];
				tv[i] = service;
			}
			
			addTimerEditFormArray.TVListFilled = 1;
			addTimerEditFormArray.TVList = tv;
		}
	}
	if (addTimerEditFormArray.RadioListFilled == 1) {
		loadTimerForm();
	} else {
		doRequest(URL.getservices + encodeURIComponent(bouquetsRadio),
				addTimerListFormatRadio, false);
	}
}

function addTimerListFormatRadio(request) {
	if (request.readyState == 4) {
		var serviceList = new ServiceList(getXML(request)).getArray();
		var radio = [];
		
		for ( var i = 0; i < serviceList.length; i++) {
			var service = serviceList[i];
			radio[i] = service;
		}
		
		addTimerEditFormArray.RadioListFilled = 1;
		addTimerEditFormArray.RadioList = radio;
	}
	addTimerEditFormArray.currBouquetName = "";
	addTimerEditFormArray.currBouquetList = {};
	loadTimerForm();
}

function loadTimerForm() {

	var Action = {};
	Action["0"] = "Record";
	Action["1"] = "Zap";

	var Repeated = {};
	Repeated["1"] = "mo";
	Repeated["2"] = "tu";
	Repeated["4"] = "we";
	Repeated["8"] = "th";
	Repeated["16"] = "fr";
	Repeated["32"] = "sa";
	Repeated["64"] = "su";
	Repeated["31"] = "mf";
	Repeated["127"] = "ms";

	var AfterEvent = {};
	AfterEvent["0"] = "Nothing";
	AfterEvent["1"] = "Standby";
	AfterEvent["2"] = "Deepstandby/Shutdown";
	AfterEvent["3"] = "Auto";

	addTimerEditFormArray.name = (typeof (addTimerEditFormArray.name) != 'undefined') ? addTimerEditFormArray.name
			: '';
	addTimerEditFormArray.name = (addTimerEditFormArray.name === '') ? ' '
			: addTimerEditFormArray.name;

	addTimerEditFormArray.description = (typeof (addTimerEditFormArray.description) != 'undefined') ? addTimerEditFormArray.description
			: '';
	addTimerEditFormArray.description = (addTimerEditFormArray.description === '') ? ' '
			: addTimerEditFormArray.description;

	var channelObject = addTimerFormPrepareChannelMenu(
			addTimerEditFormArray.TVList, addTimerEditFormArray.RadioList);

	var locationsObject = {};
	for ( var i = 0; i < addTimerEditFormArray.locationsList.length; i++) {
		str = addTimerEditFormArray.locationsList[i];
		locationsObject[str] = str;
	}

	var tagsObject = addTimerFormPrepareTagsMenu(addTimerEditFormArray.tags);

	var namespace = {
		'year' : createOptions(2009, 2015, addTimerEditFormArray.year),
		'month' : createOptions(1, 12, addTimerEditFormArray.month),
		'day' : createOptions(1, 31, addTimerEditFormArray.day),
		'shour' : createOptions(0, 23, addTimerEditFormArray.shour),
		'smin' : createOptions(0, 59, addTimerEditFormArray.smin),
		'ehour' : createOptions(0, 23, addTimerEditFormArray.ehour),
		'emin' : createOptions(0, 59, addTimerEditFormArray.emin),
		'action' : createOptionList(Action, addTimerEditFormArray.justplay),
		'channel' : createOptionList(channelObject,
				addTimerEditFormArray.channel),
		'afterEvent' : createOptionList(AfterEvent,
				addTimerEditFormArray.afterEvent),
		'repeated' : createOptionListRepeated(Repeated,
				addTimerEditFormArray.repeated),
		'dirname' : createOptionList(locationsObject,
				addTimerEditFormArray.dirname),
		'tags' : createOptionList(tagsObject, addTimerEditFormArray.tags),

		'timer' : {
			'name' : addTimerEditFormArray.name,
			'description' : addTimerEditFormArray.description,
			'deleteOldOnSave' : addTimerEditFormArray.deleteOldOnSave,
			'channelOld' : addTimerEditFormArray.channel,
			'beginOld' : addTimerEditFormArray.beginOld,
			'endOld' : addTimerEditFormArray.endOld,
			'eventID' : addTimerEditFormArray.eventID
		}
	};
	var data = namespace;
	processTpl('tplTimerEdit', data, 'contentMain');
}

function createOptions(start, end, number) {
	var namespace = [];

	for ( var i = start; i <= end; i++) {
		var txt = (String(i).length == 1) ? "0" + String(i) : String(i);
		var selected = (i == Number(number)) ? "selected" : " ";
		namespace[i] = {
			'value' : i,
			'txt' : txt,
			'selected' : selected
		};
	}
	return namespace;
}

function createOptionList(object, selected) {
	var namespace = Array();
	var i = 0;
	for ( var element in object) {
		var txt = String(object[element]);
		var sel = " ";

		if (element == selected) {
			sel = "selected";
		}

		if (element != "extend") {
			namespace[i] = {
				'value' : element,
				'txt' : txt,
				'selected' : sel
			};
			i++;
		}
	}

	return namespace;
}

function createOptionListRepeated(Repeated, repeated) {
	var num = Number(repeated);

	var list = [ 1, 2, 4, 8, 16, 32, 64, 31, 127 ];
	var namespace = [];
	var checked = [];

	for ( var i = 0; i < list.length; i++) {
		checked[i] = " ";
		if (!(~num & list[list.length - 1 - i])) {
			num -= list[list.length - 1 - i];
			checked[i] = "checked";
		}
	}
	for ( var i = 0; i < list.length; i++) {
		var txt = String(Repeated[String(list[i])]);
		if (String(Repeated[String(list[i])]) == "mf") {
			txt = "Mo-Fr";
		} else if (String(Repeated[String(list[i])]) == "ms") {
			txt = "Mo-Su";
		} else {
			txt = txt.substr(0, 1).toUpperCase() + txt.substr(1, 1);
		}
		namespace[i] = {
			'id' : Repeated[String(list[i])],
			'name' : Repeated[String(list[i])],
			'value' : list[i],
			'txt' : txt,
			'checked' : checked[list.length - 1 - i]
		};
	}
	return namespace;
}

function sendAddTimer() {
	debug("[sendAddTimer]" + "parentChannel:" + $('channel').value);

	if (parentPin($('channel').value)) {
		var beginD = new Date(parseNr($('year').value),
				(parseNr($('month').value) - 1), parseNr($('day').value),
				parseNr($('shour').value), parseNr($('smin').value));
		var begin = beginD.getTime() / 1000;

		var endD = new Date(parseNr($('year').value),
				(parseNr($('month').value) - 1), parseNr($('day').value),
				parseNr($('ehour').value), parseNr($('emin').value));
		var end = endD.getTime() / 1000;
		if (end < begin) {
			end += 86400;
		}

		var descriptionClean = ($('descr').value == " " || $('descr').value == "N/A") ? ""
				: $('descr').value;
		var nameClean = ($('name').value == " " || $('name').value == "N/A") ? ""
				: $('name').value;

		descriptionClean = encodeURIComponent(descriptionClean);
		nameClean = encodeURIComponent(nameClean);

		var dirname = encodeURIComponent($F($('timerDir').dirname));
		var tags = encodeURIComponent($F($('timerTags').tags));

		var repeated = 0;
		if ($('ms').checked) {
			repeated = parseNr($('ms').value);
		} else if ($('mf').checked) {
			repeated = parseNr($('mf').value);
			if ($('su').checked) {
				repeated += parseNr($('su').value);
			}
			if ($('sa').checked) {
				repeated += parseNr($('sa').value);
			}
		} else {
			for ( var i = 0; i < days.length; i++) {
				if ($(days[i]).checked) {
					repeated += parseNr($(days[i]).value);
				}
			}
		}
		//addTimerByID(\'%(servicereference)\',\'%(eventid)\',\'False\');
		doRequest(URL.timerchange + "?" + "sRef=" + 
				($('channel').value).replace("&quot;", '"') + "&begin="	+ 
				begin + "&end=" + end + "&name=" + nameClean + 
				"&description=" + descriptionClean + "&dirname=" + dirname+ 
				"&tags=" + tags + "&afterevent=" + $('after_event').value + 
				"&eit=0&disabled=0" + "&justplay=" + parseNr($('justplay').value) + 
				"&repeated=" + repeated	+ "&channelOld=" + $('channelOld').value + 
				"&beginOld=" + $('beginOld').value + "&endOld=" + $('endOld').value	+ 
				"&eventID" + $('eventID').value + "&deleteOldOnSave=" + 
				parseNr($('deleteOldOnSave').value), incomingTimerAddResult, false
			);
	}
}

function cleanTimerListNow() {
	debug("[cleanTimerListNow] called");
	var result = confirm("Do you really want to cleanup the List of Timers?");
	if (result) {
		doRequest(URL.timercleanup, incomingCleanTimerListNow, false);
	}
}

function incomingCleanTimerListNow(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		loadTimerList();
	}
}

function incomingJustDoNothing(request) {
	debug("[incomingJustDoNothing] called");
}

function sendToggleTimerDisable(justplay, begin, end, repeated, channel, name,
		description, dirname, tags, afterEvent, disabled) {
	disabled = (parseNr(disabled) === 0) ? 1 : 0;

	var descriptionClean = (description == " " || description == "N/A") ? ""
			: description;
	var nameClean = (name == " " || name == "N/A") ? "" : name;

	nameClean = encodeURIComponent(nameClean);
	descriptionClean = encodeURIComponent(descriptionClean);
	tags = encodeURIComponent(tags);

	doRequest(URL.timerchange + "?" + "sRef=" + channel.replace("&quot;", '"') + 
			"&begin=" + begin + "&end=" + end + "&name=" + nameClean+ 
			"&description=" + descriptionClean + "&dirname=" + dirname + 
			"&tags=" + tags + "&afterevent=" + afterEvent + "&eit=0&disabled=" + 
			disabled + "&justplay=" + justplay + "&repeated=" + repeated +
			"&channelOld=" + channel + "&beginOld="	+ begin + "&endOld=" + end + 
			"&deleteOldOnSave=1", incomingTimerAddResult, false
		);
}

function recordNowDecision(recordNowCurrent) {
	var recordNow = "infinite";
	if (recordNowCurrent === true) {
		recordNow = "current";
	}
	doRequest(URL.recordnow + "?recordnow=" + recordNow,
			incomingTimerAddResult, false);
}

function incomingWriteTimerListNow(request) {
	var result = new SimpleXMLResult(getXML(request));
	simpleResultHandler(result);
}

function writeTimerListNow() {
	doRequest(URL.timerlistwrite, incomingWriteTimerListNow);
}
