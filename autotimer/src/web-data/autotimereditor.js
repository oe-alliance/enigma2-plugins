///////////////////////////////////////////////////////////////////////////////
// Global variables
//TODO remove globals
//var currentAutoTimerListIndex = null;
//var currentAutoTimerList = [];
//TODO var currentAutoTimer = null;


///////////////////////////////////////////////////////////////////////////////
// Statics
function url() {
	this.tpl              = '';
	this.editor           = '/autotimereditor';
	this.backup           = '/autotimereditor/web/backup';
	this.restore          = '/autotimereditor/web/restore';
	this.list             = '/autotimer';
	this.get              = '/autotimer/get';
	this.set              = '/autotimer/set';
	this.edit             = '/autotimer/edit';
	this.add              = '/autotimer/edit';
	this.remove           = '/autotimer/remove';
	this.parse            = '/autotimer/parse';
	this.preview          = '/autotimer/simulate';
	this.tmp              = '/autotimereditor/tmp/';
	this.getservices      = '/web/getservices';
};
var URL = new url();

var types = {};
types['include'] = 'Include';
types['exclude'] = 'Exclude';

var wheres = {};
wheres['title'] = 'Title';
wheres['shortdescription'] = 'Short description';
wheres['description'] = 'Description';
wheres['dayofweek'] = 'Day of week';

var weekdays = {};
weekdays['0'] = 'Monday';
weekdays['1'] = 'Tuesday';
weekdays['2'] = 'Wednesday';
weekdays['3'] = 'Thursday';
weekdays['4'] = 'Friday';
weekdays['5'] = 'Saturday';
weekdays['6'] = 'Sunday';
weekdays['weekend'] = 'Weekend';
weekdays['weekday'] = 'Weekday';

///////////////////////////////////////////////////////////////////////////////
// Global functions
function compareStrings(a, b){
	a = a.toLowerCase();
	b = b.toLowerCase();
	return (b < a) - (a < b);
}

function sortAutoTimer(a,b){
	return compareStrings(a.name, b.name);
}

function in_array(a,p){
	for (i=0;i<a.length;i++)
		if (a[i] == p) return true
	return false
}

function toReadableDate(date){
	var dateString = "";
	dateString += date.getFullYear();
	dateString += "-" + addLeadingZero(date.getMonth()+1);
	dateString += "-" + addLeadingZero(date.getDate());
	return dateString;
}

function toReadableDateTime(date){
	var dateString = "";
	dateString += date.getFullYear();
	dateString += "-" + addLeadingZero(date.getMonth()+1);
	dateString += "-" + addLeadingZero(date.getDate());
	dateString += " " + addLeadingZero(date.getHours());
	dateString += ":" + addLeadingZero(date.getMinutes());
	return dateString;
}

function toTimestamp(date){
		date = date.split('-');
		var sDate = new Date();
		sDate.setFullYear(date[0], date[1] - 1, date[2]);
		sDate.setHours( 0 );
		sDate.setMinutes( 0 );
		sDate.setSeconds( 0 );
		return Math.floor(sDate.getTime() / 1000);
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

function numericalOptionList(lowerBound, upperBound, selectedValue, offset){
	var list = [];
	var idx = 0;
	if(offset == undefined){
		offset = 0;
	}
	
	for(var i = lowerBound; i <= upperBound; i++){
		var t = i + offset;
		var txt = t < 10 ? "0" + t : t;
		var selected = "";
		if(i == selectedValue){
			selected = 'selected';
		}
		list[idx] = {value : i, txt : txt, selected : selected};
		idx++;
	}
	return list;
}

function getAttribute(xml, key, defaults){
	var value = xml.getAttribute(key);
	if (value==undefined) {
		if (key in defaults){
			value = defaults[key];
		}
	}
	return value;
}


///////////////////////////////////////////////////////////////////////////////
// AutoTimerEditorCore
var AutoTimerEditorCore = Class.create({
	initialize: function(){
		// Instantiate all elements
		this.services = new AutoTimerServiceController();
		this.settings = new AutoTimerSettingsController
		
		this.menu = new AutoTimerMenuController('contentAutoTimerMenu');
		this.list = new AutoTimerListController('contentAutoTimerList');
		this.edit = new AutoTimerEditController('contentAutoTimerContent');
		this.preview = new AutoTimerPreviewController('contentAutoTimerContent');
		
		// Display menu
		this.menu.load();
		
		// Start loading
		this.loadFirst();
	},
	
	loadFirst: function(){
		// At first load locations and tags
		core.lt.getLocationsAndTags(this.loadLocationsAndTagsCallback.bind(this));
	},
	
	loadLocationsAndTagsCallback: function(currentLocation, locations, tags){
		this.currentLocation = currentLocation;
		this.locations = locations;
		this.tags = tags;
		this.loadSecond();
	},
	
	loadSecond: function(){
		// At second load bouquet list
		this.services.loadBouquetsTv(this.loadBouquetsCallback.bind(this));
	},
	
	loadBouquetsCallback: function(bouquets){
		this.bouquets = bouquets;
		this.loadThird();
	},
	
	loadThird: function(){
		// At third load autotimer settings
		this.settings.load(this.loadSettingsCallback.bind(this));
	},
	
	loadSettingsCallback: function(settings){
		this.hasVps = settings['hasVps'];
		this.loadFourth();
	},
	
	loadFourth: function(){
		// At fourth load and display autotimer list
		this.list.load();
	},
});


///////////////////////////////////////////////////////////////////////////////
// Controller
var AutoTimerServiceController = Class.create(Controller, {
	initialize: function($super){
		$super(new AutoTimerServiceListHandler());
	},
	
	load: function(sRef, callback){
		this.handler.load( {'sRef' : sRef}, callback );
	},
	
	loadBouquetsTv: function(callback){
		this.load(bouquetsTv, callback);
	},
	
	onFinished: function(){
	},
	
	registerEvents: function(){
	}
});

var AutoTimerSettingsController = Class.create(Controller, {
	initialize: function($super){
		$super(new AutoTimerSettingsHandler());
	},
	
	load: function(callback){
		this.handler.load( callback );
	},
	
	onFinished: function(){
	},
	
	registerEvents: function(){
	}
});

var AutoTimerMenuController  = Class.create(Controller, {
	initialize: function($super, target){
		$super(new AutoTimerMenuHandler(target));
	},
	
	back: function(){
		window.location = window.location.origin;
	},
	
	load: function(){
		this.handler.load({});
	},
	
	preview: function(){
		autotimereditorcore.preview.load();
	},
	
	backup: function() {
		this.filename=prompt('Please enter filename for backup file:', 'autotimer_backup');
		if (this.filename) {
			this.handler.backup(
				{ 'Filename' : this.filename },
				this.download.bind(this));
		}
		
	},
	download: function(file){
		var url =  URL.tmp + file;
		window.open(url,'Download');
		core.notify("Downloading...");
	},
	
	restore: function(){
		this.upload();
	},
	
	upload: function(){
		//TODO move to a separate class
		var form = $('backupform');
		
		if($('file').value.trim() == ""){
			core.notify("Please select a File to restore!");
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
			var resdoc;
			
			if (iframe.contentDocument) {
					resdoc = iframe.contentDocument;
			} else if (iframe.contentWindow) {
					resdoc = iframe.contentWindow.document;
			} else if (iframe.document) {
					resdoc = iframe.document;
			}
	
			var result = new SimpleXMLResult(resdoc);
			if (result.getState()){
				autotimereditorcore.menu.handler.restore(
					{ 'Filename' : result.getStateText() },
					autotimereditorcore.menu.uploadCallback.bind(this));
			} else {
				core.notify( result.getStateText() );
			}
	
			try{
				// unregister Eventhandler
				iframe.stopObserving();
				// remove iframe
				iframe.parentNode.removeChild(iframe);
			} catch(e){alert(e);}
		}
	
		iframe.observe("load", eventHandler);
		// Set properties of form...
		form.setAttribute("target","upload_iframe");
		//form.setAttribute("action", action_url);
		form.setAttribute("action", "uploadfile");
		form.setAttribute("method","post");
		form.setAttribute("enctype","multipart/form-data");
		form.setAttribute("encoding","multipart/form-data");
	
		// Submit the form...
		form.submit();
	
		core.notify("Uploading...");
	},
	uploadCallback: function(){
		autotimereditorcore.list.reload();
	},
	
	registerEvents: function(){
		$('back').on(
			'click',
			function(event, element){
				this.back();
			}.bind(this)
		);
		$('back').title = "Back to Dreambox Webcontrol";
		$('reload').on(
			'click',
			function(event, element){
				autotimereditorcore.list.reload();
			}.bind(this)
		);
		$('reload').title = "Reload the AutoTimer list";
		$('parse').on(
			'click',
			function(event, element){
				autotimereditorcore.list.parse();
			}.bind(this)
		);
		$('parse').title = "Run AutoTimer and add timer";
		$('preview').on(
			'click',
			function(event, element){
				this.preview();
			}.bind(this)
		);
		$('preview').title = "Simulate and show the matching timer";
		$('backup').on(
			'click',
			function(event, element){
				this.backup();
			}.bind(this)
		);
		$('backup').title = "Backup the AutoTimer configuration";
		$('restore').on(
			'click',
			function(event, element){
				this.restore();
			}.bind(this)
		);
		$('restore').title = "Restore a previous backuped AutoTimer configuration";
	},
});

var AutoTimerListController = Class.create(Controller, {
	//TODO What about a clone AutoTimer function
	initialize: function($super, target){
		$super(new AutoTimerListHandler(target));
		this.select = null;
	},
	
	load: function(){
		this.handler.load({});
	},
	
	onFinished: function(){
		this.onChange();
	},
	
	onChange: function(){
		var selectList = $('list');
		var selectOptions = selectList.getElementsByTagName('option');
		if ( selectOptions.length > 0){
			if (this.select != null){
				// Select the given AutoTimer because of add/remove action
				for (idx in selectOptions){
					if ( this.select == unescape(selectOptions[idx].value) ){
						selectOptions[idx].selected = true;
						break;
					}
				}
				this.select = null;
			}
			var idx = selectList.selectedIndex;
			if (idx < 0){
				// Select at least the first element
				idx = 0;
				selectOptions[idx].selected = true;
			}

			// Update editor
			var id = unescape(selectList.options[idx].value); 
			autotimereditorcore.edit.load( id );
		} else if (selectOptions.length == 0){
			//TODO TEST we should see an empty editor page?
		}
	},
	
	reload: function(){
		this.select = $('list').value;
		this.load();
	},
	
	parse: function(){
		this.handler.parse({}, this.reload.bind(this));
	},
	
	add: function(){
		this.match = prompt("Name des AutoTimers:");
		if (this.match.length){
			var selectList = $('list');
			var selectOptions = selectList.getElementsByTagName('option');
			// Retrieve next selected entry
			this.select = selectOptions.length+1;
			// Add new AutoTimer: Use edit without an id
			this.handler.add( 
				{'match' : this.match},
				function(request){
					this.load();
				}.bind(this));
		}
	},
	
	remove: function(){
		var selectList = $('list');
		var selectOptions = selectList.getElementsByTagName('option');
		var idx = selectList.selectedIndex; 
		var id = unescape(selectOptions[idx].value);
		// Retrieve next selected entry
		if ( selectOptions.length > 0){
			if ( selectOptions.length > (idx+1)){
				this.select = unescape(selectOptions[idx+1].value);
			} else if ( (idx-1) > 0 ){
				this.select = unescape(selectOptions[idx-1].value);
			}
		}
		var check = confirm("Do you really want to delete the AutoTimer\n" + selectList.options[idx].text + " ?");
		if (check == true){
			this.handler.remove(
				{'id' : id},
				function(request){
					this.load();
				}.bind(this));
		}
	},
	
	registerEvents: function(){
		$('list').on(
			'change',
			function(event, element){
				this.onChange();
			}.bind(this)
		);
		$('add').on(
			'click',
			function(event, element){
				this.add();
			}.bind(this)
		);
		$('delete').on(
			'click',
			function(event, element){
				this.remove();
			}.bind(this)
		);
	}
});

var AutoTimerEditController = Class.create(Controller, {
	initialize: function($super, target){
		$super(new AutoTimerEditHandler(target));
	},
	
	load: function( id ){
		this.id = id;
		this.handler.load( id );
	},
	
	reload: function(){
		this.handler.load( this.id );
	},
	
	onFinished: function(){
		this.onchangeSelect( $('justplay') );
		this.onchangeCheckbox( $('timespan') );
		this.onchangeCheckbox( $('timeframe') );
		this.onchangeCheckbox( $('offset') );
		this.onchangeCheckbox( $('maxdurationavailable') );
		this.onchangeCheckbox( $('locationavailable') );
		this.onchangeSelectAfterEvent( $('afterevent') );
		this.onchangeSelect( $('counter') );
		this.onchangeCheckbox( $('usefilters') );
		var filterwheres = $$('.filterwhere');
		for (var i = 0; i < filterwheres.size(); i++) {
			this.onchangeSelectFilter(filterwheres[i]);
		}
		this.onchangeCheckbox( $('usebouquets') );
		this.onchangeCheckbox( $('useservices') );
		var services = $$('.service');
		for (var i = 0; i < services.size(); i++) {
			if (services[i].lastElementChild.className == 'add'){
				this.onchangeSelectBouquet(services[i].firstElementChild.firstElementChild);
			}
		}
		this.onchangeCheckbox( $('vps_enabled') );
		
		AnyTime.noPicker( 'from' );
		AnyTime.picker( 'from', { format: "%H:%i" } );
		AnyTime.noPicker( 'to' );
		AnyTime.picker( 'to', { format: "%H:%i" } );
		AnyTime.noPicker( 'after' );
		AnyTime.picker( 'after', { format: "%Y-%m-%d", firstDOW: 1 } );
		AnyTime.noPicker( 'before' );
	  AnyTime.picker( 'before', { format: "%Y-%m-%d", firstDOW: 1 } );
		AnyTime.noPicker( 'aftereventFrom' );
		AnyTime.picker( 'aftereventFrom', { format: "%H:%i" } );
		AnyTime.noPicker( 'aftereventTo' );
		AnyTime.picker( 'aftereventTo', { format: "%H:%i" } );
	},
	
	onchangeCheckbox: function(x) {
		if (x.checked){
			$(x.id+'content').style.display = 'block';
		} else{
			$(x.id+'content').style.display = 'none';
		}
	},
	
	onchangeSelect: function(x) {
		if (x.value > 0){
			$(x.id+'content').style.display = 'block';
		} else{
			$(x.id+'content').style.display = 'none';
		}
	},
	
	onchangeSelectAfterEvent: function(x) {
		if (x.value == 'default'){
			$('aftereventusetimespan').checked = '';
			$(x.id+'content').style.visibility = "hidden";
		} else{
			$(x.id+'content').style.visibility = 'visible';
		}
		this.onchangeCheckbox( $('aftereventusetimespan') );
	},
	
	onchangeSelectFilter: function(x) {
		if (x.value == 'dayofweek'){
			x.parentNode.nextElementSibling.children[0].style.display = 'none';
			x.parentNode.nextElementSibling.children[1].style.display = 'block';
		} else{
			x.parentNode.nextElementSibling.children[1].style.display = 'none';
			x.parentNode.nextElementSibling.children[0].style.display = 'block';
		}
	},
	
	onchangeSelectBouquet: function(x) {
		// Load services of selected bouquet
		var service = unescape(x.value);
		autotimereditorcore.services.load( service, this.loadServicesCallback.bind(this, x) );
	},
	
	loadServicesCallback: function(x, services) {
		var select = x.parentNode.nextElementSibling.firstElementChild;
		for (i = select.options.length - 1; i>=0; i--) {
			select.options.remove(i);
		}
		for ( var service in services) {
			select.options.add( new Option(String(services[service]), service ) );
		}
	},
	
	changeTag: function(x) {
		var selected = 'selected';
		var attr = 'data-selected';
		if(x.hasClassName(selected)){
			x.removeClassName(selected);
			x.writeAttribute(attr, '');
		} else {
			x.addClassName(selected);
			x.writeAttribute(attr, selected);
		}
	},
	
	addFilter: function(x) {
		var parent = x.parentNode;
		if (parent.children[1].firstElementChild.value == 'dayofweek' || parent.children[2].firstElementChild.value){
			var node = parent.cloneNode(true);
			node.children[0].firstElementChild.selectedIndex = parent.children[0].firstElementChild.selectedIndex
			node.children[1].firstElementChild.selectedIndex = parent.children[1].firstElementChild.selectedIndex
			node.children[2].firstElementChild.value = parent.children[2].firstElementChild.value
			node.children[2].lastElementChild.selectedIndex = parent.children[2].lastElementChild.selectedIndex
			node.children[3].className = 'remove';
			$('filterlist').firstElementChild.insertBefore(node, parent);
		}
	},
	
	removeFilter: function(x) {
		var parent = x.parentNode;
		var element = parent.children[0].firstElementChild;
		var text = element.options[element.selectedIndex].text;
		element = parent.children[1].firstElementChild;
		text += ' ' + element.options[element.selectedIndex].text;
		if (element.value == 'dayofweek'){
			element = parent.children[2].lastElementChild;
			text += ' ' + element.options[element.selectedIndex].text;
		} else{
			text += ' ' + parent.children[2].firstElementChild.value;
		}
		var check = confirm("Do you really want to remove the Filter\n" + text + " ?");
		if (check == true){
			$('filterlist').deleteRow(parent.rowIndex); 
		}
	},

	addBouquet: function(x) {
		var parent = x.parentNode;
		var node = parent.cloneNode(true);
		node.children[0].firstElementChild.selectedIndex = parent.children[0].firstElementChild.selectedIndex
		node.children[1].className = 'remove';
		$('bouquetlist').firstElementChild.insertBefore(node, parent);
	},
	
	removeBouquet: function(x) {
		var parent = x.parentNode;
		var element = parent.children[0].firstElementChild;
		var text = element.options[element.selectedIndex].text;
		var check = confirm("Do you really want to remove the Bouquet\n" + text + " ?");
		if (check == true){
			$('bouquetlist').deleteRow(parent.rowIndex); 
		}
	},
		
	addService: function(x) {
		var parent = x.parentNode;
		var node = parent.cloneNode(true);
		node.children[0].firstElementChild.selectedIndex = parent.children[0].firstElementChild.selectedIndex
		node.children[1].firstElementChild.selectedIndex = parent.children[1].firstElementChild.selectedIndex
		node.children[2].className = 'remove';
		$('servicelist').firstElementChild.insertBefore(node, parent);
	},
	
	removeService: function(x) {
		var parent = x.parentNode;
		var element = parent.children[1].firstElementChild;
		var text = element.options[element.selectedIndex].text;
		var check = confirm("Do you really want to remove the Service\n" + text + " ?");
		if (check == true){
			$('servicelist').deleteRow(parent.rowIndex); 
		}
	},
	
	save: function() {
		//TODO Move to a separate class similar AutoTimerListEntry
		//TODO handle defaults
		var data = {}
		var selectList = $('list');
		var idx = selectList.selectedIndex;
		data['id'] = unescape(selectList.options[idx].value);
		
		data['enabled'] = ($('enabled').checked) ? '1' : '0';
		
		options = ['match','name','encoding','searchType','searchCase','justplay','avoidDuplicateDescription'];
		for (var id = 0; id < options.length; id++) {
			if ($(options[id]).value == ''){
				notify('Error: ' + options[id] + ' is empty', false);
				return;
			}
			data[options[id]] = $(options[id]).value;
		}
		
		if ($('justplay').value > 0){
				data['setEndtime']            = ($('setEndtime').checked) ? '1' : '0';
		}
		
		data['overrideAlternatives'] = ($('overrideAlternatives').checked) ? '1' : '0';
		
		if ($('timespan').checked){
			options = ['from','to'];
			for (var id = 0; id < options.length; id++) {
				if ($(options[id]).value == ''){
					notify('Error: ' + options[id] + ' is empty', false);
					return;
				}
			}
			//WHY do we have to use timespanFrom instead of from?
			data['timespanFrom']            = $('from').value;
			data['timespanTo']              = $('to').value;
		} else{
			data['timespanFrom']            = '';
			data['timespanTo']              = '';
		}
		
		if ($('timeframe').checked){
			options = ['before','after'];
			for (var id = 0; id < options.length; id++) {
				if ($(options[id]).value == ''){
					notify('Error: ' + options[id] + ' is empty', false);
					return;
				}
			}
			data['before'] = toTimestamp($('before').value).toString();
			data['after']  = toTimestamp($('after').value).toString();
		} else{
			data['before']             = '';
			data['after']              = '';
		}
		
		if ($('offset').checked){
			if ($('offset').value == ''){
				notify('Error: offset is empty', false);
				return;
			}
			data['offset']                  = $('offsetbegin').value + ',' + $('offsetend').value;
		} else{
			data['offset']             = '';
		}
		
		if ($('maxdurationavailable').checked){
			if ($('maxduration').value == ''){
				notify('Error: maxduration is empty', false);
				return;
			}
			data['maxduration']             = $('maxduration').value;
		} else{
			data['maxduration']             = '';
		}
		
		var afterevent = $('afterevent').value;
		data['afterevent']              = afterevent;
		if ($('aftereventusetimespan').checked){
			data['aftereventFrom']        = $('aftereventFrom').value;
			data['aftereventTo']          = $('aftereventTo').value;
		}

		data['counter']                 = $('counter').value;		
		if ($('counter').value > 0){
			data['counterFormat']           = $('counterFormat').value;
			data['left']                    = $('left').value;
			var lastActivation = $('lastActivation').value;
			if (lastActivation) data['lastActivation'] = lastActivation;
			var lastBegin = $('lastBegin').value;
			if (lastBegin) data['lastBegin'] = lastBegin;
		}
		
		if ($('locationavailable').checked){
			if ($('location').value == ''){
				notify('Error: location is empty', false);
				return;
			}
			data['location']             = $('location').value;
		} else{
			data['location']             = '';
		}
		
		var tags = [];
		$$('.tags').each(function(element){
			var selected = element.readAttribute('data-selected');
			if(selected == "selected"){
				var value = element.readAttribute('data-value');
				tags.push(value);
			}
		});
		if (tags.length > 0){
			data['tag'] = tags;
		}else{
			data['tag'] = '';
		}
		
		var title = [];
		var shortdescription = [];
		var description = [];
		var dayofweek = [];
		var nottitle = [];
		var notshortdescription = [];
		var notdescription = [];
		var notdayofweek = [];
		$$('.filter').each(function(element){
			if (element.lastElementChild.className != 'add'){
				var where = element.children[1].firstElementChild.value;
				if (element.children[0].firstElementChild.value == 'include'){
					if (where == 'title' ) title.push(element.children[2].firstElementChild.value);
					if (where == 'shortdescription' ) shortdescription.push(element.children[2].firstElementChild.value);
					if (where == 'description' ) description.push(element.children[2].firstElementChild.value);
					if (where == 'dayofweek' ) dayofweek.push(element.children[2].lastElementChild.value);
				} else{
					if (where == 'title' ) nottitle.push(element.children[2].firstElementChild.value);
					if (where == 'shortdescription' ) notshortdescription.push(element.children[2].firstElementChild.value);
					if (where == 'description' ) notdescription.push(element.children[2].firstElementChild.value);
					if (where == 'dayofweek' ) notdayofweek.push(element.children[2].lastElementChild.value);
				}
			}
		});
		if (title.length > 0){
			data['title'] = title;
		}else{
			data['title'] = '';
		}
		if (shortdescription.length > 0){
			data['shortdescription'] = shortdescription;
		}else{
			data['shortdescription'] = '';
		}
		if (description.length > 0){
			data['description'] = description;
		}else{
			data['description'] = '';
		}
		if (dayofweek.length > 0){
			data['dayofweek'] = dayofweek;
		}else{
			data['dayofweek'] = '';
		}
		if (nottitle.length > 0){
			data['!title'] = nottitle;
		}else{
			data['!title'] = '';
		}
		if (notshortdescription.length > 0){
			data['!shortdescription'] = notshortdescription;
		}else{
			data['!shortdescription'] = '';
		}
		if (notdescription.length > 0){
			data['!description'] = notdescription;
		}else{
			data['!description'] = '';
		}
		if (notdayofweek.length > 0){
			data['!dayofweek'] = notdayofweek;
		}else{
			data['!dayofweek'] = '';
		}
		
		var bouquets = [];
		$$('.bouquet').each(function(element){
			if (element.lastElementChild.className != 'add'){
				var select = element.children[0].firstElementChild;
				bouquets.push( select.value );
			}
		});
		data['bouquets'] = bouquets.join(',');
		
		var services = [];
		$$('.service').each(function(element){
			if (element.lastElementChild.className != 'add'){
				var select = element.children[1].firstElementChild;
				services.push( select.value );
			}
		});
		data['services'] = services.join(',');
		
		if ($('vps_enabled').checked){
			data['vps_enabled'] = ($('vps_enabled').checked) ? '1' : '0';
			data['vps_overwrite'] = ($('vps_overwrite').checked) ? '1' : '0';
		} else{
			data['vps_enabled'] = '0';
			data['vps_overwrite'] = '0';
		}
		
		this.saveurl = [];
		for( key in data ){
			var value = data[key];
			if (typeof(value)=='string'){
				this.saveurl.push( encodeURIComponent(key) + '=' + encodeURIComponent(data[key]) );
			} else if(typeof(value)=='object'&&(value instanceof Array)){
				var len = value.length;
				for (var i=0; i<len; i++){
					this.saveurl.push( encodeURIComponent(key) + '=' + encodeURIComponent(value[i]) );
				}
			}
		}
		this.saveurl = this.saveurl.join('&');
		//alert(this.saveurl);
		
		this.handler.save( this.saveurl, this.saveCallback.bind(this) );
	},
	saveCallback: function() {
		autotimereditorcore.list.reload();
	},
	
	cancel: function() {
		this.reload();
	},
	
	registerEvents: function(){
		$('justplay').on(
			'change',
			function(event, element){
				this.onchangeSelect(element);
			}.bind(this)
		);
		$('timespan').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('timeframe').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('offset').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('maxdurationavailable').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('locationavailable').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('afterevent').on(
			'change',
			function(event, element){
				this.onchangeSelectAfterEvent(element);
			}.bind(this)
		);
		$('aftereventusetimespan').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('counter').on(
			'change',
			function(event, element){
				this.onchangeSelect(element);
			}.bind(this)
		);
		$('taglist').on(
			'click',
			function(event, element){
				this.changeTag(element);
				event.stop();
			}.bind(this)
		);
		$('usefilters').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('filterlist').on(
			'change',
			'.filterwhere', 
			function(event, element){
				this.onchangeSelectFilter(element);
			}.bind(this)
		);
		$('filterlist').on(
			'click',
			'.add', 
			function(event, element){
				this.addFilter(element);
			}.bind(this)
		);
		$('filterlist').on(
			'click',
			'.remove', 
			function(event, element){
				this.removeFilter(element);
			}.bind(this)
		);
		$('bouquetlist').on(
			'click',
			'.add', 
			function(event, element){
				this.addBouquet(element);
			}.bind(this)
		);
		$('bouquetlist').on(
			'click',
			'.remove', 
			function(event, element){
				this.removeBouquet(element);
			}.bind(this)
		);
		$('usebouquets').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('servicelist').on(
			'click',
			'.add', 
			function(event, element){
				this.addService(element);
			}.bind(this)
		);
		$('servicelist').on(
			'click',
			'.remove', 
			function(event, element){
				this.removeService(element);
			}.bind(this)
		);
		$('servicelist').on(
			'change',
			'.servicebouquet', 
			function(event, element){
				this.onchangeSelectBouquet(element);
			}.bind(this)
		);
		$('useservices').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('vps_enabled').on(
			'change',
			function(event, element){
				this.onchangeCheckbox(element);
			}.bind(this)
		);
		$('save').on(
			'click',
			function(event, element){
				this.save();
			}.bind(this)
		);
		$('cancel').on(
			'click',
			function(event, element){
				this.cancel();
			}.bind(this)
		);
	}
});

var AutoTimerPreviewController = Class.create(Controller, {
	initialize: function($super, target){
		$super(new AutoTimerPreviewHandler(target));
	},
	
	load: function(){
		this.handler.load();
	},
	
	onFinished: function(){
	},
	
	registerEvents: function(){
	}
});

///////////////////////////////////////////////////////////////////////////////
// Handler
var AutoTimerServiceListHandler = Class.create(AbstractContentHandler, {
	initialize: function($super){
		$super(null, null);
		this.provider = new SimpleServiceListProvider (this.onServicesReady.bind(this));
		this.ajaxload = false;
	},
	
	load: function( ref, callback ){
		this.callback = callback;
		this.provider.load(ref);
	},
	
	onServicesReady: function(data){
		var services = {};
		var len = data.services.length;
		for (var i=0; i<len; i++){
			services[data.services[i].servicereference] = data.services[i].servicename;
		}
		if(typeof(this.callback) == "function"){
			this.callback(services);
		}
	}
});

var AutoTimerSettingsHandler = Class.create(AbstractContentHandler, {
	initialize: function($super){
		$super(null, null);
		this.provider = new AutoTimerSettingsProvider(this.onSettingsReady.bind(this));
		this.ajaxload = false;
	},
	
	load: function( callback ){
		this.callback = callback;
		this.provider.load();
	},
	
	onSettingsReady: function(data){
		var settings = data;
		if(typeof(this.callback) == "function"){
			this.callback(settings);
		}
	}
});

var AutoTimerMenuHandler = Class.create(AbstractContentHandler,{
	initialize: function($super, target){
		$super('tplAutoTimerMenu', target);
		this.provider = new SimpleRequestProvider();
	},
	
	load: function(){
		this.show({});
	},
	
	backup: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.backup,
			parms,
			function(callback, transport){
				this.provider.simpleResultCallback(transport, this.backupCallback.bind(this, callback));
			}.bind(this, callback));
	},
	backupCallback: function(callback, result){
		var text = result.getStateText();
		this.notify(text, result.getState());
		if(typeof(callback) == "function"){
			callback(text);
		}
	},

	restore: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.restore,
			parms,
			function(callback, transport){
				this.provider.simpleResultCallback(transport, this.restoreCallback.bind(this, callback));
			}.bind(this, callback));
	},
	restoreCallback: function(callback, result){
		this.notify(result.getStateText(), result.getState());
		if(typeof(callback) == "function"){
			callback();
		}
	},
});

var AutoTimerListHandler  = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplAutoTimerList', target);
		this.provider = new AutoTimerListProvider(this.show.bind(this));
		this.ajaxload = true;
	},
	
	parse: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.parse,
			parms,
			function(callback, transport){
				this.simpleResultCallback(transport, callback);
				if(typeof(callback) == "function"){
					callback();
				}
			}.bind(this, callback));
	},
	
	add: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.add, 
			parms, 
			function(callback, transport){
				this.simpleResultCallback(transport, callback);
				if(typeof(callback) == "function"){
					callback();
				}
			}.bind(this, callback));
	},
	
	remove: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.remove, 
			parms, 
			function(callback, transport){
				this.simpleResultCallback(transport, callback);
				if(typeof(callback) == "function"){
					callback();
				}
			}.bind(this, callback));
	},
});

var AutoTimerEditHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplAutoTimerEdit', target);
		this.provider = new AutoTimerEditProvider(this.show.bind(this));
		this.ajaxload = true;
	},
	
	load: function( id ){
		this.provider.load( id );
	},
	
	save: function(parms, callback){
		this.provider.simpleResultQuery(
			URL.edit, 
			parms, 
			function(callback, transport){
				this.simpleResultCallback(transport, callback);
				if(typeof(callback) == "function"){
					callback();
				}
			}.bind(this, callback));
	},
});

var AutoTimerPreviewHandler = Class.create(AbstractContentHandler, {
	initialize: function($super, target){
		$super('tplAutoTimerPreview', target);
		this.provider = new AutoTimerPreviewProvider(this.show.bind(this));
		this.ajaxload = true;
	},
	
	load: function(){
		this.provider.load();
	},
});

///////////////////////////////////////////////////////////////////////////////
// Provider
var AutoTimerSettingsProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.get, showFnc);
	},
	
	load: function( ){
		this.getUrl(this.url, null, this.loadCallback.bind(this), this.errorback.bind(this));
	},
	
	loadCallback: function(transport){
		var data = this.renderXML(this.getXML(transport));
		this.show(data);
	},
	
	renderXML: function(xml){
		this.settings = new AutoTimerSettings(xml).toJSON();
		return this.settings;
	},
});

var AutoTimerListProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.list, showFnc);
	},
	
	renderXML: function(xml){
		this.list = new AutoTimerList(xml).getList();
		return {list : this.list};
	},
	
	getAutoTimer: function(id){
		var autotimer = null;
		for (idx in this.list) {
			if (this.list[idx].id == id){
				autotimer = this.list[idx];
				break;
			}
		}
		return autotimer;
	},
	
	getAutoTimerIndex: function(id){
		var idx = null;
		for (i in this.list) {
			if (this.list[i].id == id){
				idx = i;
				break;
			}
		}
		return idx;
	}
});

var AutoTimerEditProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.list, showFnc);
	},
	
	load: function( id ){
		callback = this.callback.bind(this, id);
		this.getUrl(this.url, null, callback, this.errorback.bind(this));
	},
	
	callback: function(id, transport){
		var data = this.renderXML(this.getXML(transport), id);
		this.show(data);
	},
	
	renderXML: function(xml, id){
		this.edit = new AutoTimerEdit(xml, id).getItem();
		return this.edit;
	},
});

var AutoTimerPreviewProvider = Class.create(AbstractContentProvider, {
	initialize: function($super, showFnc){
		$super(URL.preview, showFnc);
	},
	
	callback: function(transport){
		var data = this.renderXML(this.getXML(transport));
		this.show(data);
	},
	
	renderXML: function(xml){
		this.list = new AutoTimerPreview(xml).getList();
		return {list : this.list};
	},
});

///////////////////////////////////////////////////////////////////////////////
// Objects
function AutoTimerSettings(xml){
	this.xmlitems = getNamedChildren(xml, "e2settings", "e2setting");
	this.json = new Array();
	var len = this.xmlitems.length;
	for (var i=0; i<len; i++){
		var element = this.xmlitems[i].getElementsByTagName('e2settingname');
		var name = element[0].firstChild.nodeValue;
		var element = this.xmlitems[i].getElementsByTagName('e2settingvalue');
		var value = element[0].firstChild.nodeValue;
		this.json[name] = value;
	}
	this.toJSON = function(){
		return this.json;
	};
}

function AutoTimerPreview(xml){
	this.xmlitems = getNamedChildren(xml, "e2autotimersimulate", "e2simulatedtimer");
	this.list = [];
	this.getList = function(){
		if(this.list.length === 0){
			var len = this.xmlitems.length;
			for (var i=0; i<len; i++){
				var xmlitem = this.xmlitems[i];
				var timer = {
					'name' :           getNodeContent(xmlitem, 'e2name'),
					'begin' :          toReadableDateTime( new Date( getNodeContent(xmlitem, 'e2timebegin') * 1000 ) ),
					'end' :            toReadableDateTime( new Date( getNodeContent(xmlitem, 'e2timeend') * 1000 ) ),
					'servicename' :    getNodeContent(xmlitem, 'e2servicename'),
					'autotimer' :      getNodeContent(xmlitem, 'e2autotimername'),
				};
				this.list.push(timer);
			}
			this.list.sort(sortAutoTimer);
			return this.list;
		}
	};
}

function AutoTimerList(xml){
	this.xmlitems = getNamedChildren(xml, "autotimer", "timer");
	this.list = [];
	this.getList = function(){
		if(this.list.length === 0){
			var len = this.xmlitems.length;
			for (var i=0; i<len; i++){
				var autotimer = new AutoTimerListEntry(this.xmlitems.item(i)).toJSON();
				this.list.push(autotimer);
			}
		}
		this.list.sort(sortAutoTimer);
		return this.list;
	};
}

function AutoTimerListEntry(xml){
	// Extract only list relevant parts
	this.id = xml.getAttribute('id');
	this.enabled = xml.getAttribute('enabled');
	this.css = (this.enabled == 'yes') ? 'enabled' : 'disabled';
	this.name = xml.getAttribute('name');
	if ( (this.name == undefined) || (this.name == '') ){
		this.name = xml.getAttribute('match');
	}
	this.json = {
		'id' :                this.id,
		'enabled' :           this.enabled,
		'css' :               this.css,
		'name' :              this.name,
	};
	this.toJSON = function(){
		return this.json;
	};
}

function AutoTimerEdit(xml, id){
	this.xmldefaults = getNamedChildren(xml, "autotimer", "defaults");
	this.defaults = AutoTimerDefaults(this.xmldefaults.item(0));
	this.xmlitems = getNamedChildren(xml, "autotimer", "timer");
	this.autotimer = null;
	this.getItem = function(){
		var len = this.xmlitems.length;
		for (var i=0; i<len; i++){
			if (this.xmlitems.item(i).getAttribute('id') == id){
				this.autotimer = new AutoTimer(this.xmlitems.item(i), this.defaults).toJSON();
				break;
			}
		}
		return this.autotimer;
	};
}

function AutoTimerDefaults(xml){	
	this.defaults = {}
	// Extract default values
	for (var i=0;i<xml.attributes.length;i++){
		this.defaults[xml.attributes[i].name] = xml.attributes[i].value;
	}
	return this.defaults;
}

function AutoTimer(xml, defaults){	
	// Items that must exist
	this.id = xml.getAttribute('id');
	this.enabled = (xml.getAttribute('enabled')=='yes') ? 'checked' : '';
	
	var name = xml.getAttribute('name');
	this.match = xml.getAttribute('match');
	this.name = (this.name == undefined) ? name : this.match;
	
	var encoding = getAttribute(xml, 'encoding', defaults);
	if (encoding==undefined) encoding = 'ISO8859-15';
	var options = ['ISO8859-15', 'UTF-8'];
	this.encoding = toOptionList(options, encoding);
	this.encoding.shift();

	// Items which only exists if they differ from the default value
	var searchType = getAttribute(xml, 'searchType', defaults);
	if (searchType==undefined) searchType = 'partial';
	var options = {};
	options['partial'] = 'partial match';
	options['exact'] = 'exact match';
	options['description'] = 'description match';
	this.searchType = createOptionList(options, searchType);

	var searchCase = getAttribute(xml, 'searchCase', defaults);
	if (searchCase==undefined) searchCase = 'insensitive';
	var options = {};
	options['sensitive'] = 'case-sensitive search';
	options['insensitive'] = 'case-insensitive search';
	this.searchCase = createOptionList(options, searchCase);

	var justplay = getAttribute(xml, 'justplay', defaults);
	if (justplay==undefined) justplay = 'record';
	var options = {};
	options['0'] = 'record';
	options['1'] = 'zap';
	this.justplay = createOptionList(options, justplay);
	
	var setEndtime = getAttribute(xml, 'setEndtime', defaults);
	if (setEndtime==undefined || setEndtime=='1'){
		setEndtime = 'checked';
	}else{
		setEndtime = '';
	}
	this.setEndtime = setEndtime;
	
	this.overrideAlternatives = (getAttribute(xml, 'overrideAlternatives', defaults)) ? 'checked' : '';
	
	var from = getAttribute(xml, 'from', defaults);
	var to = getAttribute(xml, 'to', defaults);
	var usetimespan = (from || to) ? 'checked' : '';
	if (to == undefined) to = '23:15';
	if (from == undefined) from = '20:15';
	this.timespan = {
		'usetimespan' : usetimespan,
		'from' : from,
		'to' : to,
	}	
	
	var after = getAttribute(xml, 'after', defaults);
	var before = getAttribute(xml, 'before', defaults);
	var usetimeframe = (before || after) ? 'checked' : '';
	if (after == undefined) {
		after = new Date();
		after = new Date( after.getUTCFullYear(), after.getUTCMonth(), after.getUTCDate() + 7 );
	} else {
		after = new Date( after * 1000 )
	}
	if (this.before == undefined) {
		before = new Date();
	} else {
		before = new Date( this.before * 1000 )
	}
	this.timeframe = {
		'usetimeframe' : usetimeframe,
		'after' : toReadableDate( after ),
		'before' : toReadableDate( before ),
	}	
	
	var offset = getAttribute(xml, 'offset', defaults);
	var useoffset = (offset) ? 'checked' : '';
	if (offset != undefined) {
		offset = offset.split(',');
		if (offset.length!=2){
			offset = [offset, offset];
		}
	} else {
		offset = ['5','5'];
	}
	var begin = parseInt(offset[0]);
	var end = parseInt(offset[1]);
	this.offset = {
		'useoffset' : useoffset,
		'begin' : numericalOptionList(0, 100, begin),
		'end' : numericalOptionList(0, 100, end),
	}	
	
	var maxduration = getAttribute(xml, 'maxduration', defaults);
	var usemaxduration = (maxduration) ? 'checked' : '';
	if (maxduration == undefined) maxduration = 70;
	this.maxduration = {
		'usemaxduration' : usemaxduration,
		'maxduration' : numericalOptionList(0, 999, maxduration),
	}	
	
	var xmlafterevents = xml.getElementsByTagName('afterevent');
	var afterevent = '';
	var aftereventFrom = '';
	var aftereventTo = '';
	if (xmlafterevents.length > 0){
		var xmlafterevent = xmlafterevents.item(0);
		afterevent = xmlafterevent.firstChild.nodeValue;
		aftereventFrom = xmlafterevent.getAttribute('from');
		aftereventTo = xmlafterevent.getAttribute('to');
	}
	var useaftereventtimespan = (aftereventFrom || aftereventTo) ? 'checked' : '';
	if (aftereventFrom == undefined || aftereventFrom == '') aftereventFrom = '23:15';
	if (aftereventTo == undefined || aftereventTo =='') aftereventTo = '07:00';
	if (afterevent == '') afterevent = 'default';
	//TODO AutoTimer is a bit inconsistent: sometimes it is none or nothing
	if (afterevent == 'shutdown') afterevent = 'deepstandby';
	if (afterevent == 'none') afterevent = 'nothing';
	//ENDTODO
	var options = {};
	options['default'] = 'Standard';
	options['nothing'] = 'Do nothing';
	options['standby'] = 'Go to Standby';
	options['deepstandby'] = 'Go to Deep Standby';
	options['auto'] = 'auto';
	this.afterevent = {
		'options' : createOptionList(options, afterevent),
		'usetimespan' : useaftereventtimespan,
		'from' : aftereventFrom,
		'to' : aftereventTo,
	}
	
	//TODO TEST lastactivation lastbegin
	var counter = getAttribute(xml, 'counter', defaults);
	var left = getAttribute(xml, 'left', defaults);
	var counterFormat = getAttribute(xml, 'counterFormat', defaults);
	var lastActivation = getAttribute(xml, 'lastActivation', defaults);
	var lastBegin = getAttribute(xml, 'lastBegin', defaults);
	if (counter==undefined) counter = 0;
	if (left == undefined) left = 0;
	if (counterFormat==undefined) counterFormat = '';
	var counterFormatOptions = {};
	counterFormatOptions[''] = 'Never';
	counterFormatOptions['%m'] = 'Monthly';
	counterFormatOptions['%U'] = 'Weekly (Sunday)';
	counterFormatOptions['%W'] = 'Weekly (Monday)';
	if (lastActivation == undefined  || lastActivation == '') {
		lastActivation = '';
	}else if (lastActivation == '0') {
		lastBegin = '0';
	} else{
		lastActivation = toReadableDate(lastActivation);
	}
	if (lastBegin == undefined || lastBegin == '') {
		lastBegin = '';
	}else if (lastBegin == '0') {
		lastBegin = '0';
	} else{
		lastBegin = toReadableDate(lastBegin);
	}
	this.counter = {
		'options' : numericalOptionList(0, 100, counter),
		'left' : numericalOptionList(0, 100, left),
		'counterFormat' : createOptionList(counterFormatOptions, counterFormat),
		'lastActivation' : lastActivation,
		'lastBegin' : lastBegin,
	}

	avoidDuplicateDescription = getAttribute(xml, 'avoidDuplicateDescription', defaults);
	if (avoidDuplicateDescription==undefined) avoidDuplicateDescription = '0';
	var options = {};
	options['0'] = 'No';
	options['1'] = 'On same service';
	options['2'] = 'On any service';
	options['3'] = 'Any service/recording';
	this.avoidDuplicateDescription = createOptionList(options, avoidDuplicateDescription);

	var location = getAttribute(xml, 'location', defaults);
	var uselocation = (location) ? 'checked' : '';
	if (location == undefined) {
		location = '';
	}
	var l = toOptionList(autotimereditorcore.locations, this.location);
	l.shift();
	this.location = {
		'uselocation' : uselocation,
		'locations' : l,
	}
	
	var xmltags = xml.getElementsByTagName('e2tags');
	var tags = '';
	if (xmltags.length > 0){
		tags = xmltags.item(0).firstChild.nodeValue;
	}
	this.tags = toOptionList(autotimereditorcore.tags, tags, " ");
	this.tags.shift();
	
	var filters = [];
	var filtertags = ['include', 'exclude'];
	var tlen = filtertags.length;
	for (var t=0; t<tlen; t++){
		var xmlfilters = xml.getElementsByTagName(filtertags[t]);
		var len = xmlfilters.length;
		for (var i=0; i<len; i++){
			var text = xmlfilters.item(i).firstChild.nodeValue;
			var weekday = text;
			if (text in weekdays ){
				text = '';
			} else{
				weekday = '0';
			}
			
			filters.push({ 
				'type' : createOptionList(types, xmlfilters.item(i).nodeName),
				'where' : createOptionList(wheres, xmlfilters.item(i).getAttribute('where')),
				'text' : text,
				'weekdays' : createOptionList(weekdays, weekday),
				'class' : 'remove',
			});
		}
	}
	var usefilters = (filters.length > 0) ? 'checked' : '';
	filters.push({ 
		'type' : createOptionList(types, 'include'),
		'where' : createOptionList(wheres, 'title'),
		'text' : '',
		'weekdays' : createOptionList(weekdays, '0'),
		'class' : 'add',
	});
	this.filters = {
		'usefilters' : usefilters,
		'filters' : filters,
	}
	
	var bouquetoptions = createOptionList(autotimereditorcore.bouquets);
	var bouquets = [];
	var services = [];
	var xmlservices = xml.getElementsByTagName('e2service');
	var len = xmlservices.length;
	for (var i=0; i<len; i++){
		var name = xmlservices.item(i).getElementsByTagName('e2servicename');
		name = name.item(0).firstChild.nodeValue;
		var reference = xmlservices.item(i).getElementsByTagName('e2servicereference');
		reference = escape(reference.item(0).firstChild.nodeValue);
		// Check if service is a bouquet
		// Service reference flags == isDirectory | mustDescent | canDescent (== 7)
		if (unescape(reference).slice(2,3) == "7"){
			bouquets.push({
				'bouquet' : createOptionList(autotimereditorcore.bouquets, reference),
				'class' : 'remove',
			});
		}else{
			var service = [];
			var bouquet = bouquetoptions.slice(0);
			service.push({
					'value' : reference,
					'txt' : name,
					'selected' : 'selected'
				});
			bouquet.push({
					'value' : '',
					'txt' : '---',
					'selected' : 'selected'
				});
			services.push({ 
				'bouquet' : bouquet,
				'service' : service,
				'class' : 'remove',
			});
		}
	}
	
	var usebouquets = (bouquets.length > 0) ? 'checked' : '';
	bouquets.push({ 
		'bouquet' : bouquetoptions,
		'class' : 'add',
	});
	this.bouquets = {
		'usebouquets' : usebouquets,
		'bouquets' : bouquets,
	}
	
	var useservices = (services.length > 0) ? 'checked' : '';
	services.push({ 
		'bouquet' : bouquetoptions,
		'service' : bouquetoptions,
		'class' : 'add',
	});
	this.services = {
		'useservices' : useservices,
		'services' : services,
	}
	
	var hasVps = (autotimereditorcore.hasVps == "True") ? '' : 'invisible';
	var vps_enabled = (getAttribute(xml, 'vps_enabled', defaults)) ? 'checked' : '';
	var vps_overwrite = (getAttribute(xml, 'vps_overwrite', defaults)) ? 'checked' : '';
	this.vps = {
		'hasVPS' : hasVps,
		'vps_enabled' : vps_enabled,
		'vps_overwrite' : vps_overwrite,
	}
	
	this.json = { 	
			'id' :                    this.id,
			'enabled' :               this.enabled,
			'name' :                  this.name,
			'match' :                 this.match,
			'encoding' :              this.encoding,
			
			'searchType' :            this.searchType,
			'searchCase' :            this.searchCase,
			
			'justplay' :              this.justplay,
			'setEndtime' :            this.setEndtime,
			
			'overrideAlternatives' :  this.overrideAlternatives,
			'timespan' :              this.timespan,
			'timeframe' :             this.timeframe,
			'offset' :                this.offset,
			'maxduration' :           this.maxduration,
						
			'afterevent' :            this.afterevent,
			'counter' :               this.counter,
			
			'avoidDuplicateDescription' :  this.avoidDuplicateDescription,
			'location' :                   this.location,
			'tags' :                       this.tags,
			'filters' :                    this.filters,
			'bouquets' :                   this.bouquets,
			'services' :                   this.services,
			
			'vps' :                   this.vps,
	};

	this.toJSON = function(){
		return this.json;
	};
}
