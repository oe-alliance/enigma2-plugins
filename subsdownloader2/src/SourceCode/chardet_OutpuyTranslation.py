def chardetOutputTranslation(recognizedCoding):
	"""Function translates recognizet codepage oputputed by getSubtitleCodepade to
	ISO nanes supported by Python.
	Modyfiecation to cooperate with chardet library
	http://chardet.feedparser.org/docs/supported-encodings.html
	and supported by Python encodings formats
	http://en.wikipedia.org/wiki/ISO/IEC_8859-1"""
	supposedEncoding = recognizedCoding['encoding'].lower()
	if supposedEncoding == "windows-1250" or supposedEncoding == "iso-8859-2":
		return "cp1250"
	elif supposedEncoding == "windows-1251" or supposedEncoding == "iso-8859-5":
		return "cp1251"
	elif supposedEncoding == "windows-1252" or supposedEncoding == "iso-8859-15":
		return "cp1252"
	elif supposedEncoding == "windows-1253" or supposedEncoding == "iso-8859-7":
		return "cp1253"
	elif supposedEncoding == "koi8-r" or supposedEncoding == "maccyrillic" or supposedEncoding == "ibm855" or supposedEncoding == "ibm866" or supposedEncoding == "windows-1251" or supposedEncoding == "iso-8859-5":
		return "cp1251"
	elif supposedEncoding == "ascii" or supposedEncoding == "iso-8859-1":
		return "ascii"
	elif supposedEncoding == "utf-8":
		return "UTF-8"
	elif supposedEncoding == "windows-1255":
		return "cp1255"
	elif supposedEncoding == "utf-16le":
		return "UTF-16LE"
	else:
		"""Encodings not supportef Yet:
		Big5, GB2312/GB18030, EUC-TW, HZ-GB-2312, and ISO-2022-CN (Traditional and Simplified Chinese)
		EUC-JP, SHIFT_JIS, and ISO-2022-JP (Japanese)
		EUC-KR and ISO-2022-KR (Korean)
		TIS-620 (Thai)
		windows-1255
		UTF-16 BE or LE (with a BOM)
		UTF-32 BE, LE, 3412-ordered, or 2143-ordered (with a BOM)"""
		#NOT SUPPORTED TET
		#self.session.open(MessageBox,_("I can't manage encodeing: %s (probability %s). So I can't convert properly subtitles to UTF-8.\nTo chcange it in future please send to developer information about unsupported CodePage (or this screenshot)." % (recognizedCoding['encoding'], recognizedCoding['confidence'])), MessageBox.TYPE_INFO, timeout = 5)
		print("I can't manage encodeing: %s (probability %s). So I can't convert properly subtitles to UTF-8.\nTo chcange it in future please send to developer information about unsupported CodePage (or this screenshot)." % (recognizedCoding['encoding'], recognizedCoding['confidence']))
		#TODO Email notyfication about error
		#self.subtitle_codepade = "None"
		return "None"
