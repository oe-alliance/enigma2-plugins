import socket

def reconnect(host='fritz.box', port=49000):
	http_body = '\r\n'.join((
		'<?xml version="1.0" encoding="utf-8"?>',
		'<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">',
		'  <s:Body>',
		'    <u:ForceTermination xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"/>',
		'  </s:Body>',
		'</s:Envelope>'))
	http_data = '\r\n'.join((
		'POST /upnp/control/WANIPConn1 HTTP/1.1',
		'Host: %s:%d' % (host, port),
		'SoapAction: urn:schemas-upnp-org:service:WANIPConnection:1#ForceTermination',
		'Content-Type: text/xml; charset="utf-8"',
		'Content-Length: %d' % len(http_body),
		'',
		http_body))
	
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		s.send(http_data)
		s.close()
		return True
	except:
		return False

