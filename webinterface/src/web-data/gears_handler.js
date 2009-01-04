var MANIFEST_FILENAME = "/webdata/manifest.json";

var localServer;
var store;

var STORE_NAME = "enigma2_web"

//	Called onload to initialize local server and store variables
function initgears() {
	if (!window.google || !google.gears) {
		debug("NOTE:  You must install Gears first.");
	} else {
		localServer = google.gears.factory.create("beta.localserver");
		store = localServer.createManagedStore(STORE_NAME);
		debug("Gears initialized.");
	}
}

//Create the managed resource store
function createStore() {
	if (!window.google || !google.gears) {
//		alert("You must install Gears first.");
		return;
	}

	store.manifestUrl = MANIFEST_FILENAME;
	store.checkForUpdate();

	var timerId = window.setInterval(function() {
		// When the currentVersion property has a value, all of the resources
		// listed in the manifest file for that version are captured. There is
		// an open bug to surface this state change as an event.
		if (store.currentVersion) {
			window.clearInterval(timerId);
			debug("Finished caputring version: " + 
					store.currentVersion);
		} else if (store.updateStatus == 3) {
			debug("Error: " + store.lastErrorMessage);
		}
	}, 500);  
}

//Remove the managed resource store.
function removeStore() {
	if (!window.google || !google.gears) {
		debug("You must install Gears first.");
		return;
	}

	localServer.removeManagedStore(STORE_NAME);
	debug("Done. The local store has been removed.");
}
