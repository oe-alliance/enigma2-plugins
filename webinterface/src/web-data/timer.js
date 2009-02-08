// $Header$

// TimerEdit variables:
var addTimerEditFormArray = [];
addTimerEditFormArray.TVListFilled = 0;
addTimerEditFormArray.RadioListFilled = 0;
addTimerEditFormArray.deleteOldOnSave = 0;
addTimerEditFormArray.eventID = 0;
addTimerEditFormArray.locationsList = [];
addTimerEditFormArray.tagsList = [];

days = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'];


function addTimerFormChangeType() {
	selected = ($('tvradio').checked === true) ? addTimerEditFormArray.TVList: addTimerEditFormArray.RadioList;
	
	for (i = $('channel').options.length; i !== 0; i--) {
		$('channel').options[i - 1] = null;
	}
	
	i = -1;
	for(element in selected) {
		if(element != "extend") {
			i++;
			$('channel').options[i] = new Option(selected[element]);
			$('channel').options[i].value = element;
		}
	}
}

function addTimerFormChangeLocation(newloc) {
        
}

function addTimerFormPrepareTagsMenu(currtags) {
	result = {};
        resultsuff = {};
	taglist = addTimerEditFormArray.tagsList;

        if (currtags == "") {
        	i = 0;
                result[""] = "<None>";
                for (i = 0; i < taglist.length; i++) {
                	result[taglist[i]] = taglist[i];
        	}
        } else {
        	result[currtags] = currtags;
                tags = currtags.split(" ");
               	for (i = 0; i < taglist.length; i++) {
                        var res = "";
                        var found = false;
                        for (j=0; j<tags.length; j++) {
                              	if (tags[j] != taglist[i]) {
                                       	res += " "+tags[j];
				} else {
                                	found = true;
                                }
                        }
                        if (!found) {
                        	res += " "+taglist[i];
                        }
                        if (res.length > 0) {
                                res = res.substring(1,res.length);
                        }
                        if (found) {
	                	resultsuff[res] = "- "+taglist[i];
                        } else {
	                	result[res] = "+ "+taglist[i];
                        }
                }
                if (tags.length > 1) {
                	for (ele in resultsuff) {
                        	result[ele] = resultsuff[ele];
                        }
                }
                result[""] = "<None>";
        }
        return result;
}

function addTimerFormChangeTags(newtags) {
	lst = addTimerFormPrepareTagsMenu(newtags);

	for (i = $('tags').options.length; i !== 0; i--) {
		$('tags').options[i - 1] = null;
	}
	
        for(element in lst) {
               	$('tags').options[i] = new Option(lst[element]);
               	$('tags').options[i].value = element;
               	i++;
        }
}


// Timer
function addTimerByID(sRef,eventID,justplay){
	if(parentPin(sRef)) {
		debug("[addTimerByID] eventID: "+eventID);
		doRequest(url_timeraddbyeventid+"?sRef="+sRef+"&eventid="+eventID+"&justplay="+justplay, incomingTimerAddResult, false);	
	}
}


function incomingTimerAddResult(request){
	debug("[incomingTimerAddResult] called");
	if(request.readyState == 4){
		var result = new SimpleXMLResult(getXML(request));
		if(result.getState()){
			//timer has been added
			notify(result.getStateText(), result.getState());
			loadTimerList();
		}else{
			notify(result.getStateText(), result.getState());
		}
	}		
}


function loadTimerList(){
	doRequest(url_timerlist, incomingTimerList, false);	
}


function incomingTimerList(request){
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("[incomingTimerList] Got " + timers.length + " timers");

		var aftereventReadable = ['Nothing', 'Standby', 'Deepstandby/Shutdown', 'Auto'];
		var justplayReadable = ['record', 'zap'];
		
		var namespace = [];
		var cssclass = "even";
		
		for ( var i = 0; i < timers.length; i++){
			var timer = timers[i];
			var beginDate = new Date(Number(timer.getTimeBegin())*1000);
			var endDate = new Date(Number(timer.getTimeEnd())*1000);
			
			var enDis = timer.getToggleDisabledIMG() == "on" ? "Disable Timer" : "Enable Timer";
			
			cssclass = cssclass == 'even' ? 'odd' : 'even';
			
			namespace[i] = { 	
				'servicereference': timer.getServiceReference(),
				'servicename': quotes2html(timer.getServiceName()),
				'title': quotes2html(timer.getName()),
				'description': quotes2html(timer.getDescription()),
				'descriptionextended': quotes2html(timer.getDescriptionExtended()),
				'begin': timer.getTimeBegin(),
				'beginDate': dateToString(beginDate),
				'end': timer.getTimeEnd(),
				'endDate': dateToString(endDate),
				'state': timer.getState(),
				'duration': Math.ceil((timer.getDuration()/60)),
				'repeated': timer.getRepeated(),
				'repeatedReadable': repeatedReadable(timer.getRepeated()),
				'justplay': timer.getJustplay(),
				'justplayReadable': justplayReadable[Number(timer.getJustplay())],
				'afterevent': timer.getAfterevent(),
				'aftereventReadable': aftereventReadable[Number(timer.getAfterevent())],
				'dirname' : timer.getDirname(),
				'tags' : timer.getTags(),
				'disabled': timer.getDisabled(),
				'onOff': timer.getToggleDisabledIMG(),
				'enDis': timer.getToggleDisabledText(),
				'cssclass': cssclass
			};			
		}
		data = { timer : namespace };
		processTpl('tplTimerList', data, 'contentMain');
	}
}


function repeatedReadable(num) {
	num = Number(num);
	if(num === 0) {
		return "One Time";
	}
	
	var retVal = "";
	var Repeated = [];
	Repeated["Mo-Su"] =127;
	Repeated["Mo-Fr"] = 31;
	Repeated["Su"] =    64;
	Repeated["Sa"] =    32;
	Repeated["Fr"] =    16;
	Repeated["Th"] =     8;
	Repeated["We"] =     4;
	Repeated["Tu"] =     2;
	Repeated["Mo"] =     1;
	
	for(rep in Repeated) {
		if(rep.toString() != 'extend') {
			var check = Number(Repeated[rep]);
			if(check <= num) {
				num -= check;
				if(retVal === '') {
					retVal += rep.toString();
				} else {
					retVal = rep.toString()+','+retVal;
				}
			}
		}
	}
	return retVal;
}


function delTimer(sRef, begin, end, servicename, title, description, readyFunction){
	debug("[delTimer] sRef("+sRef+"),begin("+begin+"),end("+end+"),servicename("+servicename+"),title("+title+"),description("+description+")");
	var result = confirm(
		"Selected timer:\n"	+
		"Channel: "+servicename+"\n" + 
		"Title: "+title+"\n" +
		"Description: "+description+"\n" +
		"Are you sure that you want to delete the Timer?");
	if(result){
		debug("[delTimer] ok confirm panel"); 
		doRequest(url_timerdelete+"?sRef="+sRef+"&begin="+begin+"&end="+end, readyFunction, false);
		return true;
	
	} else {
		debug("[delTimer] cancel confirm panel");
	}
	return false;
}


function incomingTimerDelResult(request){
	debug("[incomingTimerDelResult] called");
	if(request.readyState == 4){
		var result = new SimpleXMLResult(getXML(request));
		notify(result.getStateText(), result.getState());
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

	var	plusTwoHours = new Date(now.getTime() + ((120 *60)*1000) );
	addTimerEditFormArray.ehour = plusTwoHours.getHours();
	addTimerEditFormArray.emin = plusTwoHours.getMinutes();
		
	addTimerEditFormArray.justplay = "0";
	addTimerEditFormArray.channel = "";
	addTimerEditFormArray.channelName = "";
	addTimerEditFormArray.channelSort = "tv";
	addTimerEditFormArray.name = "";
	addTimerEditFormArray.description = "";
	addTimerEditFormArray.dirname = "";
	addTimerEditFormArray.tags = "";
	addTimerEditFormArray.repeated = 0;
	addTimerEditFormArray.afterEvent = "3";
	addTimerEditFormArray.deleteOldOnSave = 0;
	
	addTimerEditFormArray.beginOld = 0;
	addTimerEditFormArray.endOld = 0;
	
	
	debug("[loadTimerFormNow] done");
	loadTimerFormTags();
}


function loadTimerEditForm(justplay, begin, end, repeated, channel, channelName, name, description, dirname, tags, afterEvent, deleteOldOnSave, eit) {
	debug('[loadTimerEditForm] justplay: ' + justplay + ',begin: ' + begin + ',end: ' + end + ',repeated: ' + repeated + ',channel: ' + channel + ',name: ' + name +',description: ' + description +',dirname: ' + dirname +',tags: ' + tags + ',afterEvent: ' + afterEvent + ',deleteOldOnSave: ' + deleteOldOnSave);
	var start = new Date(Number(begin)*1000);
	addTimerEditFormArray.year = start.getFullYear();
	addTimerEditFormArray.month = start.getMonth() + 1;
	addTimerEditFormArray.day = start.getDate();
	addTimerEditFormArray.shour = start.getHours();
	addTimerEditFormArray.smin = start.getMinutes();
	
	var	stopp = new Date(Number(end)*1000);
	addTimerEditFormArray.ehour = stopp.getHours();
	addTimerEditFormArray.emin = stopp.getMinutes();
	
	addTimerEditFormArray.justplay = String(justplay);
	addTimerEditFormArray.channel = decodeURIComponent(String(channel));
	addTimerEditFormArray.channelName = String(channelName);
	addTimerEditFormArray.channelSort = "";
	addTimerEditFormArray.name = String(name);
	addTimerEditFormArray.description = String(description);
	addTimerEditFormArray.dirname = String(dirname);
	addTimerEditFormArray.tags = String(tags);
	addTimerEditFormArray.repeated = Number(repeated);
	addTimerEditFormArray.afterEvent = Number(afterEvent);
	
	debug("[loadTimerEditForm]" + justplay + "|" + begin + "|" + end + "|" + repeated + "|"+channel+"|"+name+"|"+description+"|"+dirname+"|"+tags+"|"+afterEvent);

	addTimerEditFormArray.deleteOldOnSave = Number(deleteOldOnSave);
	addTimerEditFormArray.beginOld = Number(begin);
	addTimerEditFormArray.endOld = Number(end);
	
	addTimerEditFormArray.eventID = Number(eit);
	
	loadTimerFormTags();
}

function loadTimerFormTags() {
	doRequest(url_getTags, incomingTimerFormTags, false);
}

function incomingTimerFormTags(request){
	debug("[incomingTimerFormTags] called");
	if(request.readyState == 4){
		var result = new SimpleXMLResult(getXML(request));
		addTimerEditFormArray.tagsList = (typeof(result.getStateText()) != 'undefined' ? result.getStateText().split(" ") : []);
		loadTimerFormLocations();
	}		
}

function loadTimerFormLocations() {
	doRequest(url_getLocations, incomingTimerFormLocations, false);
}

function incomingTimerFormLocations(request){
	debug("[incomingTimerFormLocations] called");
	if(request.readyState == 4){
		var result = new SimpleXMLResult(getXML(request));
		addTimerEditFormArray.locationsList = (typeof(result.getStateText()) != 'undefined' ? result.getStateText().split(" ") : ["/hdd/movie"]);
		loadTimerFormChannels();
	}		
}


// startin to load for TV
function loadTimerFormChannels() {
	if(addTimerEditFormArray.TVListFilled === 1 && addTimerEditFormArray.RadioListFilled === 1) {
		loadTimerForm();
	} else if(addTimerEditFormArray.TVListFilled === 1 && addTimerEditFormArray.RadioListFilled === 0) {
		addTimerListFormatTV();
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.tv%22%20ORDER%20BY%20bouquet';
		doRequest(url_getServices+favorites, addTimerListFormatTV, false);
	}
}


function addTimerListFormatTV(request) {
	if(addTimerEditFormArray.RadioListFilled === 0) {
		if(request.readyState == 4){
			var services = new ServiceList(getXML(request)).getArray();
			var tv = {};
			for ( var i = 0; i < services.length ; i++){
				var reference = services[i];
				tv[reference.servicereference] = reference.servicename;
			}
			addTimerEditFormArray.TVListFilled = 1;
			addTimerEditFormArray.TVList = tv;
		}
	}
	if(addTimerEditFormArray.RadioListFilled == 1) {
		loadTimerForm();
	} else {
		var favorites = '1%3A7%3A1%3A0%3A0%3A0%3A0%3A0%3A0%3A0%3AFROM%20BOUQUET%20%22userbouquet.favourites.radio%22%20ORDER%20BY%20bouquet';
		doRequest(url_getServices+favorites, addTimerListFormatRadio, false);
	}
}


function addTimerListFormatRadio(request) {
	if(request.readyState == 4){
		var services = new ServiceList(getXML(request)).getArray();
		var radio = {};
		for ( var i = 0; i < services.length ; i++){
			var reference = services[i];
			radio[reference.servicereference] = reference.servicename;
		}
		addTimerEditFormArray.RadioListFilled = 1;
		addTimerEditFormArray.RadioList = radio;
	}
	loadTimerForm();
}


function loadTimerForm(){

	var Action = {};
	Action["0"] = "Record";
	Action["1"] = "Zap";
	
	var Repeated = [];
	Repeated["1"] =  "mo";
	Repeated["2"] = "tu";
	Repeated["4"] =  "we";
	Repeated["8"] =  "th";
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
	
	addTimerEditFormArray.name = (typeof(addTimerEditFormArray.name) != 'undefined') ? addTimerEditFormArray.name : '';
	addTimerEditFormArray.name = (addTimerEditFormArray.name === '') ? ' ' : addTimerEditFormArray.name;

	addTimerEditFormArray.description = (typeof(addTimerEditFormArray.description) != 'undefined') ? addTimerEditFormArray.description : '';
	addTimerEditFormArray.description = (addTimerEditFormArray.description === '') ? ' ' : addTimerEditFormArray.description;

	var channelObject = addTimerEditFormArray.TVList;
	if(	addTimerEditFormArray.channelSort === 'tv') {
		// already set
	} else if( addTimerEditFormArray.channelSort === 'radio') {
		channelObject = addTimerEditFormArray.RadioList;
	} else {
		var found = 0;
		for( element in addTimerEditFormArray.TVList) {
			if( element == addTimerEditFormArray.channel) {
				found = 1;
				break;
			}
		}
		if(found === 0) {
			for( element in addTimerEditFormArray.RadioList) {
				if( element == addTimerEditFormArray.channel) {
					channelObject = addTimerEditFormArray.RadioList;
					found = 1;
					break;
				}
			}
		}
		if(found === 0) {
			addTimerEditFormArray.TVList[addTimerEditFormArray.channel] = addTimerEditFormArray.channelName;
		}
	}
	
	var dashString = "------";
	
	channelObject[dashString] = "- Bouquets -";
	
	var listeNeu = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouquetsTv)])).getArray();
	if(addTimerEditFormArray.channelSort == "radio") {
		listeNeu = new ServiceList(getXML(doRequestMemory[url_getServices+encodeURIComponent(bouquetsRadio)])).getArray();
	}
	
	for (i = 1; i < listeNeu.length; i++) {
		element = listeNeu[i];
		channelObject[String(dashString+i)] = "---";
		channelObject[element.getServiceReference()] = element.getServiceName();
	}

	var locationsObject = {};
	for (i = 0; i < addTimerEditFormArray.locationsList.length; i++) {
		str = addTimerEditFormArray.locationsList[i];
		locationsObject[str] = str;
        }

	var tagsObject = addTimerFormPrepareTagsMenu(addTimerEditFormArray.tags);

	var namespace = { 					
				year: createOptions(2008,2015,addTimerEditFormArray.year),
				month: createOptions(1,12,addTimerEditFormArray.month),
				day: createOptions(1,31,addTimerEditFormArray.day),
				shour: createOptions(0,23,addTimerEditFormArray.shour),
				smin: createOptions(0,59,addTimerEditFormArray.smin),
				ehour: createOptions(0,23,addTimerEditFormArray.ehour),
				emin: createOptions(0,59,addTimerEditFormArray.emin),
				action: createOptionList(Action, addTimerEditFormArray.justplay),
				channel: createOptionList(channelObject, addTimerEditFormArray.channel),
				afterEvent: createOptionList(AfterEvent, addTimerEditFormArray.afterEvent),
				repeated: createOptionListRepeated(Repeated, addTimerEditFormArray.repeated),
				dirname: createOptionList(locationsObject, addTimerEditFormArray.dirname),
				tags: createOptionList(tagsObject, addTimerEditFormArray.tags),

				timer: {
					name: addTimerEditFormArray.name,
					description: addTimerEditFormArray.description,
					deleteOldOnSave: addTimerEditFormArray.deleteOldOnSave,
					channelOld: addTimerEditFormArray.channel,
					beginOld: addTimerEditFormArray.beginOld,
					endOld: addTimerEditFormArray.endOld,					
					eventID: addTimerEditFormArray.eventID
				}
		};
	data = namespace;
	processTpl('tplTimerEdit', data, 'contentMain');
	/*
	var listerHtml = RND(tplAddTimerForm, namespace);
	$('BodyContent').innerHTML = listerHtml;
	*/
	
	// Empty some stuff, but keep others to have the performance
	var tmp1 = addTimerEditFormArray.RadioList;
	var tmp2 = addTimerEditFormArray.TVList;
	var tmp3 = addTimerEditFormArray.locationsList;
	var tmp4 = addTimerEditFormArray.tagsList;
	addTimerEditFormArray = [];
	addTimerEditFormArray.deleteOldOnSave = 0;
	addTimerEditFormArray.RadioList = tmp1;
	addTimerEditFormArray.TVList = tmp2;
	addTimerEditFormArray.locationsList = tmp3;
	addTimerEditFormArray.tagsList = tmp4;
	addTimerEditFormArray.TVListFilled = 1;
	addTimerEditFormArray.RadioListFilled = 1;
}


function createOptions(start, end, number) {
	var namespace =[];
	
	for(i = start; i <= end; i++) {
		var txt = (String(i).length == 1) ? "0" + String(i) : String(i);
		var selected = 	(i == Number(number)) ? "selected" : " ";
		namespace[i] = {
			'value': i,
			'txt': txt,
			'selected': selected };
	}
	return namespace;
}


function createOptionList(object, selected) {
	var namespace = Array();
	var i = 0;
	
	for(var element in object) {		
		var txt = String(object[element]);
		var sel = " ";
		
		if(element == selected) {
			sel = "selected";
		}
		
		if(element != "extend") {
			namespace[i] = {
				'value': element,
				'txt': txt,
				'selected': sel };
			i++;
		}
	}

	return namespace;
}


function createOptionListRepeated(Repeated, repeated) {
	num = Number(repeated);
		
	list = [1, 2, 4, 8, 16, 32, 64, 31, 127];
	namespace = [];
	
	for(var i = 0; i < list.length; i++) {
		txt = String(Repeated[String(list[i])]);
		if( String(Repeated[String(list[i])]) == "mf") {
			txt = "Mo-Fr";
		} else if( String(Repeated[String(list[i])]) == "ms") {
			txt = "Mo-Su";
		} else {
			txt = txt.substr(0,1).toUpperCase() + txt.substr(1,1);
		}
		checked = " ";
		if (!(~num & list[i])) {
			checked = "checked";
		}
		namespace[i] = { 'id': Repeated[String(list[i])],
			'name': Repeated[String(list[i])],
			'value': list[i],
			'txt': txt,
			'checked': checked
		};
	}
	return namespace;
}


function sendAddTimer() {
	debug("[sendAddTimer]" + "parentChannel:" +$('channel').value);
	
	if(parentPin($('channel').value)) {
		beginD = new Date(ownLazyNumber($('year').value), (ownLazyNumber($('month').value) - 1), ownLazyNumber($('day').value), ownLazyNumber($('shour').value), ownLazyNumber($('smin').value));
		begin = beginD.getTime()/1000;
		
		endD = new Date(ownLazyNumber($('year').value), (ownLazyNumber($('month').value) - 1), ownLazyNumber($('day').value), ownLazyNumber($('ehour').value), ownLazyNumber($('emin').value));
		end = endD.getTime()/1000;
		if(end<begin) {
			end += 86400;
		}

		repeated = 0;
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
			check = ['mo', 'tu', 'we', 'th', 'fr'];
			for(i = 0; i < check.length; i++) {
				if($(check[i]).checked) {
					repeated += Number($(check[i]).value);
				}
			}
		}
	
		descriptionClean = ($('descr').value == " " || $('descr').value == "N/A") ? "" : $('descr').value;
		nameClean = ($('name').value == " " || $('name').value == "N/A") ? "" : $('name').value;
		
		neverString = "[0-9a-zA-Z\\-_\\.\\!\\(\\)&=\\+$,;\\?/:\\\\ ]*";
		if(descriptionClean != descriptionClean.match(neverString) ||
			nameClean != nameClean.match(neverString)) {
			alert("Please only use "+neverString+" in the name and the description field");
			return;
		}

		dirname = $('dirname').value;
		tags = $('tags').value;
		repeated = 0;
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
		doRequest(url_timerchange+"?"+"sRef="+($('channel').value).replace("&quot;", '"')+"&begin="+ begin +
		  "&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean) +
		  "&dirname="+dirname+"&tags="+escape(tags) +
		  "&afterevent="+$('after_event').value+"&eit=0&disabled=0" +
		  "&justplay="+ownLazyNumber($('justplay').value)+"&repeated="+repeated +
		  "&channelOld="+$('channelOld').value +
		  "&beginOld="+$('beginOld').value+"&endOld="+$('endOld').value +
		  "&eventID"+$('eventID').value +
		  "&deleteOldOnSave="+ownLazyNumber($('deleteOldOnSave').value), incomingTimerAddResult, false);
	}
}


function cleanTimerListNow(){
	debug("[cleanTimerListNow] called");
	doRequest(url_timerlist, incomingCleanTimerListNow, false);	
}


function incomingCleanTimerListNow(request) {
	if(request.readyState == 4){
		var timers = new TimerList(getXML(request)).getArray();
		debug("[cleanTimerListNow] Got "+timers.length+" timer");
		for ( var i = 0; i <timers.length; i++){
			var timer = timers[i];
			debug("[cleanTimerListNow]" + timer.getState() + " " + quotes2html(timer.getName()));
			if(timer.getState() != "0" && timer.getState() != "2") {
				delTimer(timer.getServiceReference(),timer.getTimeBegin(),timer.getTimeEnd(),
					quotes2html(timer.getServiceName()),quotes2html(timer.getName()),quotes2html(timer.getDescription()),incomingJustDoNothing);
			}
		}
		loadTimerList();
	}
}


function incomingJustDoNothing(request){
	debug("[incomingJustDoNothing] called");
}


function sendToggleTimerDisable(justplay,begin,end,repeated,channel,name,description,dirname,tags,afterEvent,disabled){
	disabled = (ownLazyNumber(disabled) === 0) ? 1 : 0;
	
	var descriptionClean = (description == " " || description == "N/A") ? "" : description;
	var nameClean = (name == " " || name == "N/A") ? "" : name;

	doRequest(url_timerchange+"?"+"sRef="+channel.replace("&quot;", '"')+"&begin="+begin +
	 "&end="+end+"&name="+escape(nameClean)+"&description="+escape(descriptionClean) +
	 "&dirname="+dirname+"&tags="+escape(tags) +
	 "&afterevent="+afterEvent+"&eit=0&disabled="+disabled +
	 "&justplay="+justplay+"&repeated="+repeated +
	 "&channelOld="+channel +
	 "&beginOld="+begin+"&endOld="+end +
	 "&deleteOldOnSave=1", incomingTimerAddResult, false);
}

function incomingWriteTimerListNow(request){
	var result = new SimpleXMLResult(getXML(request));
	notify(result.getStateText(), result.getState());
}

function writeTimerListNow() {
	var request = doRequest(url_timerlistwrite, incomingWriteTimerListNow);
}
