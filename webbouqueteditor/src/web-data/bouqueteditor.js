var MODE = { tv : 0, radio : 1};
var NAV_SERVICE = { provider : 0, sat : 1, all : 2 };
var currentMode = null;
var currentNav = null;
var protectionPasswordValid = false;
var protectionType = null;
var protectionConfigured = false;
var chachedPin = null;

//// index marker
var currentServicelistIndex = null;
var currentBouquetlistIndex = null;
var currentProviderServiceList = null;
var currentProviderServiceListFiltered = null;

var currentBouquetRef = null;
	

function getSelectedAttr(selectId) {

	var selectList = $(selectId);
	var selectOptions = selectList.getElementsByTagName('option');
	var idx = selectList.selectedIndex; 
	return { selectOptions: selectOptions, idx: idx};

}

function moveOptions(selectId, pos) {
	var ref = "";
	var index = -1;
	var selectList = $(selectId);
	var selectOptions = selectList.getElementsByTagName('option');
	var idx = selectList.selectedIndex; 
	if (idx >= 0){
		var opt = selectOptions[idx];
		selectList.removeChild(opt);
		if(pos < selectOptions.length){
			selectList.insertBefore(opt, selectOptions[pos]);
			ref = unescape(opt.value);
			index = pos;
		} else {
			selectList.appendChild(opt);
			ref = unescape(opt.value);
			index = selectOptions.length - 1;
		}
	}
	return { ref: ref , index: index};
}

function setProviderName(provider){
	if( currentNav != NAV_SERVICE.all){
		$("providerServiceHeader").update("All Services of '" + provider + "'");
	} else {
		$("providerServiceHeader").update("All Services");
	}
}

function setBouquetName(bouquet){
	$("bouquetServiceHeader").update("Services of Bouquet '" + bouquet + "'");
}

function setNavBackground(element, selected){
	if(selected)
		element.setStyle({background :  "#AAA"});
	else
		element.setStyle({background :  "#485052"});
}

function setMode(mode){
	currentMode = mode;
	switch(mode){
	
	case MODE.tv:
		setNavBackground($("navTv"), true);
		setNavBackground($("navRadio"), false);
		break;
		
	case MODE.radio:
		setNavBackground($("navTv"), false);
		setNavBackground($("navRadio"), true);
		break;
	}
	if (protectionPasswordValid) {
		setServiceNav(0);
		getBouquets();
	}
	else
		getProtectionData();
}

function setServiceNav(type){

	if (protectionPasswordValid) {
		currentNav = type;
		setServiceNavButtons(type);
		if(type == NAV_SERVICE.all){
			$("contentSelectionList").hide();
			setProviderName("");
		} else {
			$("contentSelectionList").show();
		}
		 
		getProviderList(type);
	}
	else
		getProtectionData();
}

function setServiceNavButtons(type){
	switch(type){
		case NAV_SERVICE.provider:
			setNavBackground($("navProv"), true);
			setNavBackground($("navSat"), false);
			setNavBackground($("navAll"), false);
			
		break;
		case NAV_SERVICE.sat:
			setNavBackground($("navProv"), false);
			setNavBackground($("navSat"), true);
			setNavBackground($("navAll"), false);
			
		break;
		case NAV_SERVICE.all:
			setNavBackground($("navProv"), false);
			setNavBackground($("navSat"), false);
			setNavBackground($("navAll"), true);
			
		break;
	}
}

function onServiceSearchFocus(event){
	if(event.element().value == "Service to search for..."){
		event.element().value = '';
	}
	event.element().setStyle({color : "#000"});
	serviceSearch(event);
}

function onServiceSearchBlur(event){
	if(event.element().value.trim() == ""){
		event.element().setStyle({color : "#AAA"});
		event.element().value = "Service to search for...";
	}
}

function serviceSearch(event){
	var needle = event.element().value.toLowerCase();
		
	//Nur Gecko-basierte Browser k�nnen <option> elemente ausblenden
	if(Prototype.Browser.Gecko){
		var serviceElements = $$('.providerservice');
		
		for(var i = 0; i < serviceElements.length; i++){
			var option = serviceElements[i];
			var serviceName = option.readAttribute('data-servicename').toLowerCase();
			
			if(serviceName.indexOf(needle) == -1 && serviceName != ""){
				option.hide();
			} else {		
				option.show();
			}
		}
	//f�r alle anderen Anderen Browser muss die Liste komplett neu aufgebaut werden
	} else {
		currentProviderServiceListFiltered = [];
		$A(currentProviderServiceList).each(function(service){
			var serviceName = service.servicename.toLowerCase();
			if(serviceName.indexOf(needle) != -1 || serviceName == ""){
				currentProviderServiceListFiltered[currentProviderServiceListFiltered.length] = service;
			}			
		});
		
		fillProviderServiceList(currentProviderServiceListFiltered);
	}
}

function fillProviderServiceList(servicelist){
	var data = { services : servicelist };
	processTplBouquetEditor('providerservicelist', data, 'contentSelectionSubList');
}

function getCurrentSelectedBouquetlistRef() {

	var selectList = $('bouquetlist');
	var idx = selectList.selectedIndex; 
	var current = selectList.options[idx];
	return unescape(current.value);
	
}

function getAlternatives(ref){	
	doRequest('/bouqueteditor/web/getservices?sRef=' + ref, incomingAlternatives, false);
}

function incomingAlternatives(request) {
	if (request.readyState == 4) {
		var servicelist = new BouquetEditorServiceList(getXML(request)).getArray();
		var data = {
			services : servicelist
		};
		processTplBouquetEditor('alternativelist', data, 'contentAlternatives');
	}
}

function removeAlternative(selectObj) {
	var selectServicelist = $('servicelist');
	var idxServicelist = selectServicelist.selectedIndex;
	var selectList = $(selectObj);
	var selectServicelistOptions = selectList.getElementsByTagName('option');
	if (selectServicelistOptions.length > 1) {
		if (idxServicelist != -1) {
			var current_alternative_service_ref = unescape(selectServicelist.options[idxServicelist].value);
			var idx = selectList.selectedIndex; 
			if ( idx != -1) {
				var ref = unescape(selectList.options[idx].value); 
					var check = confirm("Do you really want to delete the service\n" + selectList.options[idx].text + " from current alternative list?");
				if (check == true)
					doRequest('/bouqueteditor/web/removeservice?sBouquetRef='+ current_alternative_service_ref + '&sRef=' + ref, removeAlternativeServiceCallback, false);
			}
			else
				alert("No service in alternative-list selected!");
		}
		else
			alert("No service in servicelist selected!");
	}
	else
		alert("There must be one service in the alternative-list at least!");
}

function removeAlternativeServiceCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var selectList = $('alternativelist');
			var idx = selectList.selectedIndex; 
			selectList.removeChild(selectList.options[idx]);
			var selectOptions = selectList.getElementsByTagName('option');
			if ( selectOptions.length != 0) {
				if ( idx > selectOptions.length-1)
					idx = idx - 1;
				selectOptions[idx].selected = true;
			}
		}
	}
}

function servicelistChange(element){
	var idx = element.selectedIndex; 
	var current = element.options[idx];
	var hasAlternatives = $(current).readAttribute("data-hasalt");
	
	if(hasAlternatives == "1"){

		$("removeAlternativServicesButton").show();
		$("alternativesHead").show();
		$("alternatives").show();
		
		$("contentAlternatives").update('Loading Alternatives... <img src="/bouqueteditor/ajax-loader.gif" />');
		
		var ref =  unescape(encodeURIComponent(current.value));
		getAlternatives(ref);
		
	} else {
		$("alternativesHead").hide();
		$("alternatives").hide();
		$("removeAlternativServicesButton").hide();
	}

	var hasProtection = $(current).readAttribute("data-hasprotection");
	var button = $("toggleserviceprotection");
	if (protectionConfigured) {
		if ( protectionType == "0") {
			if (hasProtection == "0"){
				button.update("Lock");
				button.show();}
			else if (hasProtection == "1"){
				button.update("Unlock");
				button.show();}
			else
				button.hide();
		} else {
			if (hasProtection == "3"){
				button.update("Unlock");
				button.show();}
			else if (hasProtection == "4"){
				button.update("Lock");
				button.show();}
			else if (hasProtection == "5")
				button.hide();
		}
			
		
	} else {
		button.hide();
	}



}

function BouquetEditorService(xml, cssclass){	
	this.servicereference = getNodeContent(xml, 'e2servicereference', '');
	this.servicename = getNodeContent(xml, 'e2servicename');
	this.serviceisgroup = getNodeContent(xml, 'e2serviceisgroup');
	this.serviceismarker = getNodeContent(xml, 'e2serviceismarker');
	this.serviceisprotected = getNodeContent(xml, 'e2serviceisprotected');
	
	this.getServiceReference = function(){
		return encodeURIComponent(this.servicereference);
	};
	
	this.getClearServiceReference = function(){
		return this.servicereference;
	};
		
	this.getServiceName = function(){
		return this.servicename.replace('&quot;', '"');
	};

	this.getPrefix = function(){
		if (this.serviceisgroup == "1") {
			return "* ";}

		else {
			if (this.serviceismarker == "1") {
				return "<------- ";}
			else {
				return "";}}
	};

	this.getSuffix = function(){
		if (this.serviceisprotected != "0") {
			var returnvalue = '';
			switch(this.serviceisprotected){
				case "1":
					returnvalue = '(locked -S-)';
				break;
				case "2":
					returnvalue = '(locked -B-)';
				break;
				case "3":
					returnvalue = '(locked)';
				break;
				case "4":
					returnvalue = '(unlocked -S-)';
				break;
				case "5":
					returnvalue = '(unlocked -B-)';
				break;
			}
			return returnvalue;}
		else {
			if (this.serviceismarker == "1") {
				return " ------->";}
			else {
				return "";}}
		
	};

	
	this.setServiceReference = function(sref){
		this.servicereference = sref;
	};
		
	this.setServiceName = function(sname){
		this.servicename = sname.replace('&quot;', '"');
	};
	
	if( typeof( cssclass ) == undefined ){
		cssclass = 'odd';
	}
	
	this.json = { 	
			'servicereference' : this.getServiceReference(),
			'servicename' : this.getServiceName(),
			'serviceisgroup' : this.serviceisgroup,
			'prefix' : this.getPrefix(),
			'suffix' : this.getSuffix(),
			'serviceisprotected' : this.serviceisprotected

	};
	
	this.toJSON = function(){
		return this.json;
	};
}	

function BouquetEditorServiceList(xml){
	this.xmlitems = getNamedChildren(xml, "e2servicelist", "e2service");
	this.servicelist = [];
	this.getArray = function(){
		if(this.servicelist.length === 0){
			var cssclass = 'even';
			
			for (var i=0;i<this.xmlitems.length;i++){
				cssclass = cssclass == 'even' ? 'odd' : 'even';
				var service = new BouquetEditorService(this.xmlitems.item(i), cssclass).toJSON();
				this.servicelist.push(service);
			}
		}
		return this.servicelist;
	};
}

function getProviderList(type) {

	url = '';
	switch (type){
		case NAV_SERVICE.provider: 
			if (currentMode == MODE.tv) 
				url = '/bouqueteditor/web/getservices?sRef=' + providerTv;
			else
				url = '/bouqueteditor/web/getservices?sRef=' +  providerRadio;
		break;
		case NAV_SERVICE.sat:
			url = '/bouqueteditor/web/satelliteslist?mode=' + currentMode;
		break;
		case NAV_SERVICE.all:
			if (currentMode == MODE.tv) 
				url = '/bouqueteditor/web/getservices?sRef=' + allTv;
			else
				url = '/bouqueteditor/web/getservices?sRef=' +  allRadio;
		break;
	}
	if (type == NAV_SERVICE.all)
		doRequest(url, incomingProviderServiceList, false);
	else
		doRequest(url, incomingProviderList, false);
}


function incomingProviderList(request) {
	if (request.readyState == 4) {
		var servicelist = new BouquetEditorServiceList(getXML(request)).getArray();
		var data = {
			services : servicelist
		};
		processTplBouquetEditor('providerlist', data, 'contentSelectionList', processTplIncommingProviderListCallback);
	}
}

function processTplIncommingProviderListCallback() {

	var selectList = $('providerlist');
	var selectOptions = selectList.getElementsByTagName('option');
	if ( selectOptions.length != 0)
	{
		if(currentNav != NAV_SERVICE.all){
			selectOptions[0].selected = true;
			providerlistChange(selectList);
		}		
	}
}


function providerlistChange(selectObj) {
	
	var idx = selectObj.selectedIndex; 
	var current = selectObj.options[idx];
	var ref =  unescape(encodeURIComponent(current.value));
	setProviderName(current.innerHTML);
	doRequest('/bouqueteditor/web/getservices?sRef=' + ref, incomingProviderServiceList, false);
}

function incomingProviderServiceList(request) {
	if (request.readyState == 4) {
		var servicelist = new BouquetEditorServiceList(getXML(request)).getArray();
		currentProviderServiceList = servicelist;
		var data = {
			services : servicelist
		};
		processTplBouquetEditor('providerservicelist', data, 'contentSelectionSubList');
	}
}

function addBouquet(){
	sName=prompt("Name des Bouquets:");
	if (sName.length){
		var selectList = $('bouquetlist');
		var selectOptions = selectList.getElementsByTagName('option');
		currentBouquetlistIndex =  selectOptions.length ;
		doRequest('/bouqueteditor/web/addbouquet?name='+sName+'&mode='+currentMode, bouquetListUpdated, false);
	}
}

function bouquetListUpdated(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){			
			getBouquetServiceList();
		}
	}
}


function getBouquets() {
	currentBouquetlistIndex = null;
	getBouquetServiceList();
}


function getBouquetServiceList() {

	if (currentMode == MODE.tv) 
		url = '/bouqueteditor/web/getservices?sRef=' + bouquetsTv;
	else
		url = '/bouqueteditor/web/getservices?sRef=' +  bouquetsRadio;
	doRequest(url, incomingBouquetList, false);
}

function incomingBouquetList(request) {
	if (request.readyState == 4) {

		var bouquetlist = new BouquetEditorServiceList(getXML(request)).getArray();
		var data = {
			bouquets : bouquetlist
		};
		processTplBouquetEditor('bouquetlist', data, 'contentBouquetList', processTplBouquetListCallback);
	}
}

function processTplBouquetEditor(tplName, data, domElement, callback){
	var url = "/bouqueteditor/" +tplName+".htm";
	doRequest(url, 
			function(transport){
		incomingProcessTpl(transport, data, domElement, callback);
	}
	);
}


function processTplBouquetListCallback() {
	var selectList = $('bouquetlist');
	var selectOptions = selectList.getElementsByTagName('option');
	if ( selectOptions.length != 0){
		if (currentBouquetlistIndex != null)
			selectOptions[currentBouquetlistIndex].selected = true;
		else
			selectOptions[0].selected = true;
		bouquetlistChange(selectList);
	}
}

function showRequestResult(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
	}
}


function moveBouquet(value) {
	if ( value.ref != "" && value.index != -1)
		doRequest('/bouqueteditor/web/movebouquet?sBouquetRef='+ value.ref +'&mode='+ currentMode + '&position=' + value.index, showRequestResult, false);
}



function moveBouquetOptionsUp(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx > 0)
		moveBouquet(moveOptions(selectId,value.idx-1));
}

function moveBouquetOptionsDown(selectId) {
	var value = getSelectedAttr(selectId);
	if ( (value.idx + 1) < (value.selectOptions.length))
			moveBouquet(moveOptions(selectId,value.idx+1));
}


function removeBouquet(selectObj) {
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	var bouqueref = unescape(selectList.options[idx].value); 
	var check = confirm("Do you really want to delete the bouquet\n" + selectList.options[idx].text + " ?");
	if (check == true)
		doRequest('/bouqueteditor/web/removebouquet?sBouquetRef='+ bouqueref +'&mode=' + currentMode, removeBouquetCallback, false);
}

function removeBouquetCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var selectList = $('bouquetlist');
			var idx = selectList.selectedIndex; 
			selectList.removeChild(selectList.options[idx]);
			var selectOptions = selectList.getElementsByTagName('option');
			if ( selectOptions.length != 0) {
				if ( idx > selectOptions.length-1)
					idx = idx - 1;
				selectOptions[idx].selected = true;
				bouquetlistChange(selectList); // Update Servicelist
			}
		}
	}
}


function bouquetlistChange(selectObj) {
	var idx = selectObj.selectedIndex; 
	var current = selectObj.options[idx];
	var hasProtection = $(current).readAttribute("data-hasprotection");
	var button = $("togglebouquetprotection");
	if (protectionConfigured) {
		if ( protectionType == "0") {
			if (hasProtection == "0"){
				button.update("Lock");
				button.show();}
			else if (hasProtection == "2"){
				button.update("Unlock");
				button.show();}
			else
				button.hide();
		} else {
			if (hasProtection == "3"){
				button.update("Unlock");
				button.show();}
			else if (hasProtection == "5"){
				button.update("Lock");
				button.show();}
		}
	} else {
		button.hide();
	}
	currentServicelistIndex = null;
	var idx = selectObj.selectedIndex; 
	var current = selectObj.options[idx];
	var ref = unescape(current.value);
	setBouquetName(current.innerHTML);
	getServiceList(ref);
}

function getServiceList(ref) {
	currentBouquetRef = ref;
	doRequest('/bouqueteditor/web/getservices?sRef=' + ref, incomingServiceList);
}

function incomingServiceList(request) {
	if (request.readyState == 4) {
		var servicelist = new BouquetEditorServiceList(getXML(request)).getArray();
		var data = {
			services : servicelist
		};
		processTplBouquetEditor('servicelist', data, 'contentServicelist', processTplIncomingServiceListCallback);
	}
}

function processTplIncomingServiceListCallback() {
	var selectList = $('servicelist');
	var selectOptions = selectList.getElementsByTagName('option');
	if ( selectOptions.length != 0) {
	
		if (currentServicelistIndex != null)
			selectOptions[currentServicelistIndex].selected = true;
		else
			selectOptions[0].selected = true;
		servicelistChange(selectList);
	}
}

function moveService(value) {
	if ( value.ref != "" && value.index != -1) {
		var bouqueref = currentBouquetRef;
		doRequest('/bouqueteditor/web/moveservice?sBouquetRef='+ bouqueref + '&sRef=' + value.ref + '&mode=' + currentMode + '&position=' + value.index, showRequestResult, false);
	}
}

function moveServiceOptionsUp(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx > 0)
		moveService(moveOptions(selectId, value.idx-1));
}

function moveServiceOptionsDown(selectId) {
	var value = getSelectedAttr(selectId);
	if ( (value.idx + 1) < (value.selectOptions.length))
			moveService(moveOptions(selectId,value.idx+1));
}

function moveServiceOptionsUp5(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx > 0){
		var pos = -5;
		if (value.idx + pos < 0)
			pos = 0;
		else
			pos = value.idx + pos;
		moveService(moveOptions(selectId, pos));
	}
}

function moveServiceOptionsDown5(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx != value.selectOptions.length-1){
		var pos = 5;
		if (value.idx + pos > value.selectOptions.length-1)
			pos = value.selectOptions.length -1;
		else
			pos = value.idx + pos;
		moveService(moveOptions(selectId,pos));
	}
}

function moveServiceOptionsTop(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx > 0)
		moveService(moveOptions(selectId,0));
}

function moveServiceOptionsBottom(selectId) {
	var value = getSelectedAttr(selectId);
	if ( value.idx >= 0 && value.idx != (value.selectOptions.length-1))
		moveService(moveOptions(selectId,value.selectOptions.length-1));
}



function removeAlternativServices(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	if ( idx != -1) {
		var ref = unescape(selectList.options[idx].value); 
		var check = confirm("Do you really want to delete all allternatives services in service\n" + selectList.options[idx].text + " ?");
		if (check == true){
			currentServicelistIndex = idx;
			var url = '/bouqueteditor/web/removealternativeservices?sBouquetRef=' + bouqueref + "&sRef=" + ref;
			doRequest(url, serviceListUpdated, false);
		}
	}
	else
		alert("No service selected!");
}


function removeService(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	if ( idx != -1) {
		var ref = unescape(selectList.options[idx].value); 
		var check = confirm("Do you really want to delete the service\n" + selectList.options[idx].text + " from current selected Bouquet?");
		if (check == true)
			doRequest('/bouqueteditor/web/removeservice?sBouquetRef='+ bouqueref + '&sRef=' + ref +'&mode=' + currentMode, removeServiceCallback, false);
	}
	else
		alert("No service selected!");
}

function removeServiceCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var selectList = $('servicelist');
			var idx = selectList.selectedIndex; 
			selectList.removeChild(selectList.options[idx]);
			var selectOptions = selectList.getElementsByTagName('option');
			if ( selectOptions.length != 0) {
				if ( idx > selectOptions.length-1)
					idx = idx - 1;
				selectOptions[idx].selected = true;
			}
			servicelistChange(selectList);
		}
	}
}


function addAlternativeService(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	if ( idx != -1){
		var ref = unescape(selectList.options[idx].value); // that service ref will be added to the current selected service from servicelist as alternative
		var selectServicelist = $('servicelist');
		var idxServicelist = selectServicelist.selectedIndex;
		if (idxServicelist != -1) {
			currentServicelistIndex = idxServicelist;
			var current_ref = unescape(selectServicelist.options[idxServicelist].value); // get current  selected ref --> this service will be the alternative
			var url = "/bouqueteditor/web/addservicetoalternative?sBouquetRef=" + bouqueref + "&sCurrentRef=" + current_ref + "&sRef=" + ref + "&mode=" + currentMode;
			doRequest(url, addAlternativeServiceCallback, false);
		}
		else
			alert ("No service in servicelist selected!");
	}
	else
		alert ("No service selected!");

}

function addAlternativeServiceCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		// always reload after adding a alertative, because it could have been created, but the result can be False however
		var ref = getCurrentSelectedBouquetlistRef();
		getServiceList(ref);
		
	}
}


function addServiceToBouquet(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex;
	var refServicelist = "";
		if ( idx != -1){
		var ref = unescape(selectList.options[idx].value);
		var selectServicelist = $('servicelist');
		var selectServicelistOptions = selectServicelist.getElementsByTagName('option');
		if (selectServicelistOptions.length > 0) {
			var idxServicelist = selectServicelist.selectedIndex;
			currentServicelistIndex = idxServicelist + 1;
			if ( idxServicelist != -1 && idxServicelist != selectServicelistOptions.length){
				if ( idxServicelist + 1 < selectServicelistOptions.length){
					refServicelist = unescape(selectServicelist.options[idxServicelist+1].value);
				}
			}
		}
		else
			currentServicelistIndex = null;
		doRequest('/bouqueteditor/web/addservicetobouquet?sBouquetRef='+ bouqueref + '&sRef=' + ref +'&sRefBefore=' + refServicelist, serviceListUpdated, false);
	}
	else
		alert ("No service selected!");

}


function serviceListUpdated(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var ref = getCurrentSelectedBouquetlistRef();
			getServiceList(ref);
		}
	}
}



function addProviderToBouquet(selectObj) {
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	if ( idx != -1){
		var ref =  unescape(encodeURIComponent(selectList.options[idx].value));
		doRequest('/bouqueteditor/web/addprovidertobouquetlist?sProviderRef='+ref+'&mode=' + currentMode, addProviderToBouquetCallback, false);
	}
	else
		alert("No provider selected!");

}

function addProviderToBouquetCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var selectList = $('bouquetlist');
			var selectOptions = selectList.getElementsByTagName('option');
			currentBouquetlistIndex =  selectOptions.length ;
			getBouquetServiceList();
		}
	}
}

function ProtectionXMLResult(xml){		
	try{
		this.xmlitems = xml.getElementsByTagName("e2serviceprotection").item(0);
	} catch (e) {
		notify("Error parsing e2serviceprotection: " + e, false);
	}
	this.configured = getNodeContent(this.xmlitems, 'e2serviceprotectionconfigured', 'False');
	this.setupepin = getNodeContent(this.xmlitems, 'e2serviceprotectionsetuppin', '');
	this.type = getNodeContent(this.xmlitems, 'e2serviceprotectiontype', '');
	this.servicepinactive = getNodeContent(this.xmlitems, 'e2serviceprotectionsetuppinactive', 'False');

	this.getConfigured = function(){
		if(this.configured == 'True'){
			return true;
		}else{
			return false;
		}
	};
	
	this.getSetupPin = function(){
			return this.setupepin;
	};
	
	this.getProtectionType = function(){
			return this.type;
	};
	
	this.getSetupPinActive = function(){
		if(this.servicepinactive == 'True'){
			return true;
		}else{
			return false;
		}
	};
	
}

function incommingProtectionData(request) {
	if (request.readyState == 4) {
		var result = new ProtectionXMLResult(getXML(request));
		if(result.getConfigured()){
			protectionConfigured = true;
			protectionType = result.getProtectionType();
			
			if (result.getSetupPinActive()){
				chachedPin=prompt('Please enter your setup pin:', '');
				if (result.getSetupPin() == chachedPin) {
					protectionPasswordValid = true;
				}
				else
					alert("Password is wrong!");
			}
			else
				protectionPasswordValid = true;
		}
		else
			protectionPasswordValid = true;
			
		if (protectionPasswordValid) {
			setServiceNav(0);
			getBouquets();
		}
	}
}

function getProtectionData() {
	url = '/bouqueteditor/web/getprotectionsettings';
	doRequest(url, incommingProtectionData, false);
}


function toggleBouquetProtection(selectObj) {
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	var bouqueref = unescape(selectList.options[idx].value);
	currentBouquetlistIndex =  idx;
	doRequest('/bouqueteditor/web/togglelock?sRef='+ bouqueref +'&password=' + chachedPin, toggleBouquetProtectionCallback, false);
}

function toggleBouquetProtectionCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			getBouquetServiceList();
		}
	}
}

function toggleServiceProtection(selectObj) {
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	var serviceref = unescape(selectList.options[idx].value);
	currentServicelistIndex =  idx;
	doRequest('/bouqueteditor/web/togglelock?sRef='+ serviceref +'&password=' + chachedPin, toggleServiceProtectionCallback, false);
}

function toggleServiceProtectionCallback(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			var ref = getCurrentSelectedBouquetlistRef();
			getServiceList(ref);
		}
	}
}

function createBackup() {
	var filename=prompt('Please enter filename for backup file:', 'webbouqueteditor_backup');
	if (filename) {
		url = '/bouqueteditor/web/backup?Filename='+filename;
		doRequest(url, incommingBackupResult, false);
	}
}

function incommingBackupResult(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		if(result.getState()){
			startDownloadBackupFile(result.getStateText());
		}
		else
			simpleResultHandler(result);
	}
}

function startDownloadBackupFile(file) {
	var url =  "/bouqueteditor/tmp/" + file;
	window.open(url,'Download');
}


function incommingRestoreResult(request) {
	if (request.readyState == 4) {
		var result = new SimpleXMLResult(getXML(request));
		simpleResultHandler(result);
		if(result.getState()){
			setMode(MODE.tv);
		}
		else
			simpleResultHandler(result);
	}
}

function renameService(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex;
	var refServicelist = "";
	if ( idx != -1) {
		var ref = unescape(selectList.options[idx].value); 
	
		var newServicename=prompt('Please enter new servicename for selected service:', selectList.options[idx].text);
		if (newServicename){
			var selectServicelistOptions = selectList.getElementsByTagName('option');
			if (selectServicelistOptions.length > 0) {
				var idxServicelist = selectList.selectedIndex;
				currentServicelistIndex = idxServicelist;
				if ( idxServicelist != -1 && idxServicelist != selectServicelistOptions.length){
					if ( idxServicelist + 1 < selectServicelistOptions.length){
						refServicelist = unescape(selectList.options[idxServicelist+1].value);
					}
				}
			}
			else
				currentServicelistIndex = null;
			doRequest('/bouqueteditor/web/renameservice?sBouquetRef='+ bouqueref + '&sRef=' + ref +'&sRefBefore=' + refServicelist + '&newName=' + encodeURIComponent(newServicename), serviceListUpdated, false);
		}
	}
	else
		alert ("No service selected!");
}

function renameBouquet(selectObj) {
	var selectList = $(selectObj);
	var idx = selectList.selectedIndex; 
	var bouqueref = unescape(selectList.options[idx].value); 
	var newServicename=prompt('Please enter new servicename for selected bouquet:', selectList.options[idx].text);
	if (newServicename){
		currentBouquetlistIndex =  idx;
		doRequest('/bouqueteditor/web/renameservice?sRef=' + bouqueref +'&mode=' + currentMode + '&newName=' + encodeURIComponent(newServicename), bouquetListUpdated,false);
	}
}


function addMarkerToBouquet(selectObj) {
	var bouqueref = currentBouquetRef;
	var selectList = $(selectObj);
	var markername=prompt('Please enter a marker name:', '');
	var refServicelist = "";
	if (markername) {
		var selectServicelistOptions = selectList.getElementsByTagName('option');
		if (selectServicelistOptions.length > 0) {
			var idxServicelist = selectList.selectedIndex;
			currentServicelistIndex = idxServicelist + 1;
			if ( idxServicelist != -1 && idxServicelist != selectServicelistOptions.length){
				if ( idxServicelist + 1 < selectServicelistOptions.length){
					refServicelist = unescape(selectList.options[idxServicelist+1].value);
				}
			}
		}
		else
			currentServicelistIndex = null;
		doRequest('/bouqueteditor/web/addmarkertobouquet?sBouquetRef='+ bouqueref + '&Name=' + encodeURIComponent(markername) +'&sRefBefore=' + refServicelist, serviceListUpdated, false);
	}
}

function fileUpload(form, action_url)
{
	if($('file').value.trim() == ""){
		notify("Please select a File to restore!");
		return;
	}
	// Create the iframe...
	var iframe = document.createElement("iframe");
	iframe.setAttribute("id","upload_iframe");
	iframe.setAttribute("name","upload_iframe");
	iframe.setAttribute("width","0");
	iframe.setAttribute("height","0");
	iframe.setAttribute("border","0");
	iframe.setAttribute("style","width: 0; height: 0; border: none;");

	// Add to document...
	form.parentNode.appendChild(iframe);
	window.frames['upload_iframe'].name="upload_iframe";
	iframe = $(iframe);


	// Add event...
	var eventHandler = function(){
		// Message from server...
		var resdoc = "";

		if (iframe.contentDocument) {
				resdoc = iframe.contentDocument;
		} else if (iframe.contentWindow) {
				resdoc = iframe.contentWindow.document;
		} else if (iframe.document) {
				resdoc = iframe.document;
		}

		var result = new SimpleXMLResult(resdoc);

		if (result.getState()){
			doRequest('/bouqueteditor/web/restore?Filename=' + result.getStateText() , incommingRestoreResult, false);
		} else {
			simpleResultHandler(result);
		}
		
        try{
			// unregister Eventhandler
			iframe.stopObserving();
			// remove iframe
			iframe.parentNode.removeChild(iframe);
		} catch(e){return;}
    };
	
	iframe.observe("load", eventHandler);
	// Set properties of form...
	form.setAttribute("target","upload_iframe");
	form.setAttribute("action", action_url);
	form.setAttribute("method","post");
	form.setAttribute("enctype","multipart/form-data");
	form.setAttribute("encoding","multipart/form-data");

	// Submit the form...
	form.submit();

	notify("Uploading...");
}
