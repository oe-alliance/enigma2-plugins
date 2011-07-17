/*
 * This code is inspired by http://www.phpied.com/json-javascript-cookies/
 * and modified for use with prototype
 * It's a pretty straight forward way to store and load settings in a nice to use JSON-Object
 */ 

var userprefs = {
	data : {},

	load : function() {
		var the_cookie = document.cookie.split(';');
		if (the_cookie[0]) {
			this.data = unescape(the_cookie[0]).evalJSON();
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