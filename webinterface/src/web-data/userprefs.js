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
		if(the_cookie[idx].startsWith("TWISTED_SESSION")){
			idx = 1;
		}
		if (the_cookie[idx]) {
			this.data = unescape(the_cookie[idx]).evalJSON();
		}
		return this.data;
	},

	save : function(expires, path) {
		var d = expires || new Date(2222, 01, 01);
		var p = path || '/';
		document.cookie = escape( Object.toJSON(this.data) ) + ';path=' + p
				+ ';expires=' + d.toUTCString();
	}
};

userprefs.load();