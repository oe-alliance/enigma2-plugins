var MANIFEST_FILENAME = "/web-data/manifest.json";
var STORE_NAME = "enigma2_web";
	
var localServer;
var store;

function gearsAvailable(){
	if(!window.google || !google.gears){
		return false;
	} else {
		return true;
	}
		
}

function gearsEnabled(){
	var useGears = userprefs.data.useGears || false;
	return useGears;
}	

//	Called onload to initialize local server and store variables
function initGears() {	
	if( gearsAvailable() && gearsEnabled() ){
		localServer = google.gears.factory.create("beta.localserver");
		store = localServer.createManagedStore(STORE_NAME);
		if(createStore() ){
			return true;
		} else {
			return false;
		}
	}
	
	return false;
}

//Create the managed resource store
function createStore() {
	if (gearsEnabled()) {		
		if (!window.google || !google.gears) {
			notify("[GEARS] NOTE: You must install Gears first.", false);
			return false;
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
		return true;
	} else {
		return false;
	}
}

//Remove the managed resource store.
function removeStore() {
	if (!window.google || !google.gears) {
		if(typeof(debug) == "function"){
			notify("[GEARS] NOTE: You must install Gears first.", false);			
		}
		return false;
	}

	localServer.removeManagedStore(STORE_NAME);
	if(typeof(debug) == "function"){
		notify("[GEARS] Done. The local GEARS-Store for enigma2 WebControl has been removed.");
	}
	return true;
}

function enableGears(callback) {
	if(!gearsAvailable()){
		notify("You must install GEARS first.", false);
		return;
	}
	if(!gearsEnabled()){
		userprefs.data.useGears = true;
		userprefs.save();
		
		if(initGears()){			
			if(typeof(callback) == 'function'){
				callback();
			}
		} else { //could not enable Gears
			userprefs.data.useGears = false;
			userprefs.save();
		}
	}
}

function disableGears(callback) {
	if(gearsEnabled()){
		if(removeStore()){
			userprefs.data.useGears = false;
			userprefs.save();
			if(typeof(callback) == 'function'){
				callback();
			}
		}
	}
}

initGears();