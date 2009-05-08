var MANIFEST_FILENAME = "/web-data/manifest.json";
var STORE_NAME = "enigma2_web";
	
var localServer;
var store;

function gearsEnabled(){
	var useGears = userprefs.data.useGears || false;
	return useGears;
}	

//	Called onload to initialize local server and store variables
function initGears() {	
	if(gearsEnabled()){
		if (!window.google || !google.gears) {
			notify("[GEARS] NOTE: You must install Gears first.", false);
		} else {
			localServer = google.gears.factory.create("beta.localserver");
			store = localServer.createManagedStore(STORE_NAME);
			createStore();
		}
	}
}

//Create the managed resource store
function createStore() {
	if (gearsEnabled()) {		
		if (!window.google || !google.gears) {
			notify("[GEARS] NOTE: You must install Gears first.", false);
			return;
		}

		store.manifestUrl = MANIFEST_FILENAME;
		store.checkForUpdate();
		store.onprogress = function(e){
								set('gearsProcess', 'Files loaded: ' + e.filesComplete + ' / ' + e.filesTotal);				
							};

		var timerId = window.setInterval( function() {
			// When the currentVersion property has a value, all of the resources
			// listed in the manifest file for that version are captured.
			// There is an open bug to surface this state change as an event.
				if (store.currentVersion) {
					window.clearInterval(timerId);
					if (typeof (debug) == "function") {
						notify("[GEARS] Finished capturing version: "
								+ store.currentVersion);
					}
				} else if (store.updateStatus == 3) {
					if (typeof (debug) == "function") {
						notify("[GEARS] Error: " + store.lastErrorMessage, false);
					}
				}
			}, 500);

	} 
}

//Remove the managed resource store.
function removeStore() {
	if (!window.google || !google.gears) {
		if(typeof(debug) == "function"){
			notify("[GEARS] NOTE: You must install Gears first.", false);
		}
		return;
	}

	localServer.removeManagedStore(STORE_NAME);
	if(typeof(debug) == "function"){
		notify("[GEARS] Done. The local GEARS-Store for enigma2 WebControl has been removed.");
	}
}

function enableGears(callback) {
	if(!gearsEnabled()){
		userprefs.data.useGears = true;
		userprefs.save();
		initGears();		
	}
	if(typeof(callback) == 'function'){
		callback();
	}
}

function disableGears(callback) {
	if(gearsEnabled()){
		userprefs.data.useGears = false;
		userprefs.save();
		removeStore();
	}
	if(typeof(callback) == 'function'){
		callback();
	}
}

initGears();