/*
 * This code is inspired by http://www.phpied.com/json-javascript-cookies/
 * and modified for use with prototype
 * It's a pretty straight forward way to store and load settings in a nice to use JSON-Object
 */

var userprefs = {
	data : {},

	load : function() {
		var the_cookie = document.cookie.split(';');

		var idx = 0;
		while(idx < the_cookie.length) {
			if (!the_cookie[idx].trim().startsWith("dmweb=")) {
				idx++;
				continue;
			}
			var data = the_cookie[idx].split("=")[1]
			this.data = JSON.parse(unescape(data));
			break;
		}
		return this.data;
	},

	save : function(expires, path) {
		var d = expires || new Date(2222, 01, 01);
		var p = path || '/';
		document.cookie = "dmweb=" + escape( JSON.stringify(this.data) ) + ';path=' + p
				+ ';expires=' + d.toUTCString();
	}
};

userprefs.load();