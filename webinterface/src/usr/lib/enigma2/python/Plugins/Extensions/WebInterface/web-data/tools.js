function getHTTPObject() 
{
	var xmlhttp; 
	/*@cc_on 
	@if (@_jscript_version >= 5) 
	try 
	{ 
		xmlhttp = new ActiveXObject("Msxml2.XMLHTTP"); 
	} 
	catch (e) 
	{ 
		try 
		{ 
			xmlhttp = new ActiveXObject("Microsoft.XMLHTTP"); 
		} 
		catch (E) 
		{ 
			xmlhttp = false; 
		} 
	} 
	@else 
	xmlhttp = false; 
	@end @*/ 
	if (!xmlhttp && typeof XMLHttpRequest != 'undefined') 
	{ 
		try 
		{ 
			xmlhttp = new XMLHttpRequest(); 
		} 
		catch (e) 
		{
			xmlhttp = false; 
		}
	} 
	return xmlhttp; 
}
