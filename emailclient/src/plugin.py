from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentTemplateColor
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigText, ConfigEnableDisable
from EmailConfig import EmailConfigScreen
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from enigma import eListboxPythonMultiContent, eListbox, gFont
from twisted.mail import imap4
from zope.interface import implements
import email
import email.Parser
from email.header import decode_header
from TagStrip import strip_readable
from protocol import createFactory

config.plugins.emailimap = ConfigSubsection()
config.plugins.emailimap.username = ConfigText("user", fixed_size=False)
config.plugins.emailimap.password = ConfigText("password", fixed_size=False)
config.plugins.emailimap.server = ConfigText("please.config.first", fixed_size=False)
config.plugins.emailimap.port = ConfigInteger(143, limits = (1, 65536))
config.plugins.emailimap.showDeleted = ConfigEnableDisable(default=False)

# 0= fetch all header , 10= fetch only the last 10 headers/messages of a mailbox
config.plugins.emailimap.maxheadertoload = ConfigInteger(0, limits = (1, 100))

from enigma import getDesktop
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
#
# this is pure magic.
# It returns the first value, if HD (1280x720),
# the second if SD (720x576),
# else something scaled accordingly
# if one of the parameters is -1, scale proportionally
#
def scaleH(y2, y1):
	if y2 == -1:
		y2 = y1*1280/720
	elif y1 == -1:
		y1 = y2*720/1280
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)
def scaleV(y2, y1):
	if y2 == -1:
		y2 = y1*720/576
	elif y1 == -1:
		y1 = y2*576/720
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)
def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1

def decodeHeader(text, default=''):
	if text is None:
		return _(default)
	text = text.replace('\r',' ').replace('\n',' ').replace('\t',' ')
	while text.find('  ') != -1:
		text = text.replace('  ',' ')
	textNew = ""
	for part in decode_header(text):
		(content, charset) = part
		# print("decodeHeader content/charset: %s/%s" %(repr(content),charset))
		if charset:
			textNew += content.decode(charset)
		else:
			textNew += content
	try:
		return textNew.encode('utf-8')
	except: # for faulty mail software systems
		return textNew.decode('iso-8859-1').encode('utf-8')

IS_UNSEEN = 0
IS_SEEN = 1
IS_DELETED = 2 

class EmailHandler:
	def __init__(self):
		pass
	def onConnect(self, proto):
		pass

class EmailScreen(Screen, EmailHandler):
	implements(imap4.IMailboxListener)

	width = scaleH(-1,530)
	height = scaleV(-1,430)
	boxlistWidth = scaleH(-1,150)
	messagelistWidth = width-boxlistWidth
	infolabelHeight = scaleV(-1,30)
	skin = """
		<screen position="%d,%d" size="%d,%d" title="Email" >
			<widget name="boxlist" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" />
			<widget name="messagelist" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" />
			<widget name="infolabel" position="%d,%d" size="%d,%d"   foregroundColor=\"white\" font=\"Regular;%d\" />
		</screen>""" %(
					   (DESKTOP_WIDTH-width)/2, (DESKTOP_HEIGHT-height)/2, width, height,
					   boxlistWidth, height-infolabelHeight,
					   boxlistWidth, 0, messagelistWidth, height-infolabelHeight,
					   0, height-infolabelHeight, width, infolabelHeight, scaleV(20,18)
					   )

	currentmailbox = None
	proto = None

	def __init__(self, session, args = 0):
		EmailHandler.__init__(self)
		self.session = session

		self.skin = EmailScreen.skin
		Screen.__init__(self, session)
		createFactory(self, config.plugins.emailimap.username.value, config.plugins.emailimap.server.value, config.plugins.emailimap.port.value)

		self["actions"] = ActionMap(["InfobarChannelSelection", "WizardActions", "DirectionActions", "MenuActions", "ShortcutActions", "GlobalActions", "HelpActions", "NumberActions", "ChannelSelectBaseActions"],
			{
			 "ok": self.action_ok,
			 "back": self.action_exit,
			 "historyNext": self.selectMessagelist,
			 "historyBack": self.selectBoxlist,
			 "nextBouquet": self.selectMessagelist,
			 "prevBouquet": self.selectBoxlist,
			 "down":		self.down,
			 "up":		  self.up,
			 "left":		self.left,
			 "right":	   self.right,
			 "menu":		self.action_menu,
			 }, -1)
		self["boxlist"] = MenuList([])
		self["messagelist"] = MailList([])
		self["infolabel"] = Label("")
		self.onLayoutFinish.append(self.selectBoxlist)

	def action_menu(self):
		self.session.open(EmailConfigScreen).onHide.append(self.onBoxSelected)

	def selectBoxlist(self):
		self.currList = "boxlist"
		self["boxlist"].selectionEnabled(1)
		self["messagelist"].selectionEnabled(0)

	def selectMessagelist(self):
		self.currList = "messagelist"
		self["boxlist"].selectionEnabled(0)
		self["messagelist"].selectionEnabled(1)

	def up(self):
		self[self.currList].up()

	def down(self):
		self[self.currList].down()

	def left(self):
		self[self.currList].pageUp()

	def right(self):
		self[self.currList].pageDown()

	def action_ok(self):
		if self.currList == "boxlist":
			self.onBoxSelected()
		else:
			self.onMessageSelected()

	def onBoxSelected(self):
		c = self["boxlist"].getCurrent()
		if c is not None:
			self.proto.select(UTF7toUTF8(c[1][2]) # select instead of examine to get write access
							   ).addCallback(self.onExamine, c[0] , self.proto
							  ).addErrback(self.onExamineFailed, self.proto
							  )

	def onMessageSelected(self):
		c = self["messagelist"].getCurrent()
		if c is not None:
			self.fetchMessageSize(c[0])

	def fetchMessageSize(self, message):
		print "fetchMessageSize",message
		self.proto.fetchSize(message.uid
			).addCallback(self.onMessageSizeLoaded, message, self.proto
			).addErrback(self.onMessageLoadFailed, message, self.proto
			)

	def onMessageSizeLoaded(self, result, message, proto):
		print "onMessageSizeLoaded", result, message
		size = int(result[message.uid]['RFC822.SIZE'])
		self.MAX_MESSAGE_SIZE_TO_OPEN = 4000000
		if size >= self.MAX_MESSAGE_SIZE_TO_OPEN:
			#ask here to open message
			print "message to large to open (size=", size, ")"
		else:
			self.loadMessage(message)

#	def fetchBodyStructure(self, message):
#		print "fetchBodyStructure",message
#		self.proto.fetchBodyStructure(message.uid
#			).addCallback(self.onBodystructureLoaded, message, self.proto
#			).addErrback(self.onMessageLoadFailed, message, self.proto
#			)

	def loadMessage(self, message):
		print "loadMessage",message
		self["infolabel"].setText("loading message")

		self.proto.fetchMessage(message.uid
			).addCallback(self.onMessageLoaded, message, self.proto
			).addErrback(self.onMessageLoadFailed, message, self.proto
			)

	def onMessageLoaded(self, result, message, proto):
		self["infolabel"].setText("parsing message")
		print "onMessageLoaded"#,result,message
		msgstr = result[message.uid]['RFC822']
		msg = email.Parser.Parser().parsestr(msgstr)
		msg.messagebodys = []
		msg.attachments = []

		if msg.is_multipart():
			for part in msg.walk():
				if part.get_content_maintype()=="multipart":
					continue
				if part.get_content_maintype() == 'text' and part.get_filename() is None:
					if part.get_content_subtype() == "html":
						msg.messagebodys.append(EmailBody(part))
					elif part.get_content_subtype() == "plain":
						msg.messagebodys.append(EmailBody(part))
					else:
						print "unkown content type= ", part.get_content_maintype(), "/", part.get_content_subtype()
				else:
					print "found Attachment with  ", part.get_content_type(), "and name", part.get_filename()
					msg.attachments.append(EmailAttachment(part.get_filename(), part.get_content_type(), part.get_payload()))
		else:
			msg.messagebodys.append(EmailBody(msg))
		self.session.open(ScreenMailView, msg, message.uid, proto, self.flagsList[message.uid]['FLAGS']).onHide.append(self.onBoxSelected)

	def onMessageLoadFailed(self, failure, message, proto):
		print "onMessageLoadFailed", failure, message
		self["infolabel"].setText(failure.getErrorMessage())

	def action_exit(self):
		if self.proto is not None:
			self.proto.logout().addCallback(self.onLogedOut, self.proto).addErrback(self.onLogedOut, self.proto)
		else:
			self.close()

	def onLogedOut(self, result, proto):
		print "onLogedOut", result
		self.close()

	def onConnect(self, proto):
		self["infolabel"].setText("connected")
		proto.getCapabilities(
						).addCallback(self.cbCapabilities, proto
						).addErrback(self.ebCapabilities, proto
						)

	def cbCapabilities(self,reason,proto):
		print "#"*30
		print "# If you have problems to log into your imap-server, please send me the output of the following line"
		print "# cbCapabilities",reason
		print "#"*30
		self.doLogin(proto)

	def ebCapabilities(self,reason,proto):
		print "ebCapabilities",reason

	def onConnectFailed(self, reason):
		self["infolabel"].setText(reason.getErrorMessage())

	def onAuthentication(self, result, proto):
		self.proto = proto
		self["infolabel"].setText("logged in")
		# better use LSUB here to get only the subscribed to mailboxes
		proto.lsub("", "*").addCallback(self.onMailboxList, proto)

	def doLogin(self, proto):
		print "login secure"
		useTLS = False #True
		if useTLS:
			context = proto.context.getContext()
			d = proto.startTLS(context)
			d = d.addCallback(proto.authenticate, config.plugins.emailimap.password.value)
		else:
			d = proto.authenticate(config.plugins.emailimap.password.value)
		d.addCallback(self.onAuthentication, proto)
		d.addErrback(self.onAuthenticationFailed, proto)
		return d

	def onAuthenticationFailed(self, failure, proto):
		# If it failed because no SASL mechanisms match
		print "onAuthenticationFailed", failure, proto
		self["infolabel"].setText(failure.getErrorMessage())
		try:
			failure.trap(imap4.NoSupportedAuthentication)
			self.doLoginInsecure(proto)
		except Exception,e:
			print e,e.message

	def doLoginInsecure(self, proto):
		print "login INSECURE"
		proto.login(config.plugins.emailimap.username.value, config.plugins.emailimap.password.value
				).addCallback(self.onAuthentication, proto
				).addErrback(self.onInsecureAuthenticationFailed, proto
				)

	def onInsecureAuthenticationFailed(self, failure, proto):
		print "onInsecureAuthenticationFailed", failure, proto
		self["infolabel"].setText(failure.getErrorMessage())

	def onMailboxList(self, result, proto):
		print "onMailboxList", result, proto
		list = []
		inboxPos = 0
		for i in result:
			flags, hierarchy_delimiter, name = i #@UnusedVariable
			list.append((UTF7toUTF8(name).encode('utf-8'), i))
			if name.lower() == 'inbox':
				inboxPos = len(list)
		self["boxlist"].setList(list)
		self["boxlist"].moveToIndex(inboxPos-1)

	def onExamine(self, result, mboxname, proto):
		print "onExamine", result, mboxname
		self.setTitle("Mailbox: "+mboxname)
		self.currentmailbox = mboxname
		numMessagesinFolder = int(result['EXISTS'])
		if numMessagesinFolder <= 0:
			self["infolabel"].setText("Box '"+mboxname+"' is empty")
			self["messagelist"].l.setList([])

		else:
			if config.plugins.emailimap.maxheadertoload.value > 0:
				maxMessagesToFetch = config.plugins.emailimap.maxheadertoload.value
				startmsg = numMessagesinFolder-maxMessagesToFetch+1
				if startmsg <= 0:
					startmsg = 1
				rangeToFetch = [startmsg, numMessagesinFolder]
			else:
				rangeToFetch = [1, numMessagesinFolder]
			self["infolabel"].setText("loading headers "+str(rangeToFetch[0])+"-"+str(rangeToFetch[1])+" of Box '"+mboxname+"'")

			try:
#				proto.fetchEnvelope('%i:%i'%(rangeToFetch[0], rangeToFetch[1])	#'1:*'
#						   ).addCallback(self.onEnvelopeList, proto
#						   )
				self.proto = proto
				self.rangeToFetch = rangeToFetch
				proto.fetchFlags('%i:%i'%(rangeToFetch[0], rangeToFetch[1])	#'1:*'
						   ).addCallback(self.onFlagsList)

			except imap4.IllegalServerResponse, e:
				print e
			self.selectMessagelist()

	def onFlagsList(self, result):
		self.flagsList = result
		self.proto.fetchHeaders('%i:%i'%(self.rangeToFetch[0], self.rangeToFetch[1])	#'1:*'
				   ).addCallback(self.onHeaderList, self.proto
				   )

	def onExamineFailed(self, failure, proto):
		print "onExamineFailed", failure, proto
		self["infolabel"].setText(failure.getErrorMessage())

	def cbOk(self, result):
		print("cbOk result: %s" %repr(result))

	def cbNotOk(self, result):
		print("cbNotOk result: %s" %(result))

	def onHeaderList(self, result, proto):
		print "onHeaderList"#,result,proto
		self["infolabel"].setText("headers loaded, now parsing ...")
		list = []
		for m in result:
			state = IS_UNSEEN
			# print("onHeaderList :" + repr(self.flagsList[m]['FLAGS']))
			if '\\Seen' in self.flagsList[m]['FLAGS']:
				state = IS_SEEN
			if '\\Deleted' in self.flagsList[m]['FLAGS']:
				if not config.plugins.emailimap.showDeleted.value:
					continue
				else:
					state = IS_DELETED
			try:
				list.append(self.buildMessageListItem(MessageHeader(m, result[m]['RFC822.HEADER']), state))
			except Exception,e:
				try:
					list.append(self.buildMessageListItem(MessageHeader(m, result[m]['RFC822.HEADER'].decode('iso8859-1', 'replace'), state)))
				except:
					# this appear to be errors in the formatting of the mail itself...
					print "onHeaderList error: %s with: %s" %(e,result[m]['RFC822.HEADER'])
		list.reverse()
		self["messagelist"].l.setList(list)
		self["infolabel"].setText("have "+str(len(list))+" messages ")

	def buildMessageListItem(self, message, state):
		if state == IS_UNSEEN:
			font = 0
			color = 0x00FFFFFF # white
		elif state == IS_DELETED:
			font = 1 
			color = 0x00FF4444 # redish :)
		else:
			font = 2
			color = 0x00CCCCCC # grey
		return [
			message,
			MultiContentEntryText(pos=(5, 0), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.getSenderString(), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, scaleV(20,18)+1), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.get('date', default='kein Datum'), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, 2*(scaleV(20,18)+1)), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.getSubject(), color=color, color_sel=color)
		]
	#
	# IMailboxListener methods
	#
	def modeChanged(self, writeable):
		print "modeChanged", writeable

	def flagsChanged(self, newFlags):
		print "flagsChanged", newFlags

	def newMessages(self, exists, recent):
		print "newMessages", exists, recent

class ScreenMailView(Screen):
	skin=""
	def __init__(self, session, email, uid, proto, flags):
		self.session = session
		self.email = email
		# print('ScreenMailView ' + repr(email) + ' dir: ' + repr(dir(email)))
		width = max(4*140,scaleH(-1,550))
		height = scaleV(-1,476)
		fontSize = scaleV(24,20)
		lineHeight = fontSize+5
		buttonsGap = (width-4*140)/5
		self.skin = """
		<screen position="%d,%d" size="%d,%d" title="view Email" >
			<widget name="from" position="%d,%d" size="%d,%d"  font="Regular;%d" />
			<widget name="date" position="%d,%d" size="%d,%d"  font="Regular;%d" />
			<widget name="subject" position="%d,%d" size="%d,%d"  font="Regular;%d" />
			<eLabel position="%d,%d" size="%d,2" backgroundColor="#aaaaaa" />
			<widget name="body" position="%d,%d" size="%d,%d"  font="Regular;%d" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="buttonred" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="buttongreen" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="buttonyellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="buttonblue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" %(
					   (DESKTOP_WIDTH-width)/2, (DESKTOP_HEIGHT-height)/2, width, height,
					   0, 0, width, lineHeight, fontSize-1, # from
					   0, lineHeight, width, lineHeight, fontSize-1, # date
					   0, 2*lineHeight, width, lineHeight, fontSize-1, # subject 
					   0, 3*lineHeight+1, width, # line 
					   0, 3*lineHeight+5, width, height-3*lineHeight-5-5-30-5, fontSize, # body
					   buttonsGap, height-30-5,
                       2*buttonsGap+140, height-30-5,
                       3*buttonsGap+2*140, height-30-5,
                       4*buttonsGap+3*140, height-30-5,
                       buttonsGap, height-30-5, scaleV(18,16),
                       2*buttonsGap+140, height-30-5, scaleV(18,16),
                       3*buttonsGap+2*140, height-30-5, scaleV(18,16),
                       4*buttonsGap+3*140, height-30-5, scaleV(18,16),
					   )
		Screen.__init__(self, session)
		self["from"] = Label(decodeHeader(_("From") +": %s" %self.email.get('from', 'no-from')))
		self["date"] = Label(_("Date") +": %s" %self.email.get('date', 'no-date'))
		self["subject"] = Label(decodeHeader(_("Subject") +": %s" %self.email.get('subject', 'no-subject')))
		self["body"] = ScrollLabel(_(self.email.messagebodys[0].getData()))
		self["buttonred"] = Button(_(""))
		self["buttongreen"] = Button("")
		# TODO: show headers
		self["buttonyellow"] = Button("")
		if '\\Deleted' in flags:
			self["buttonblue"] = Button(_("undelete"))
		else:
			self["buttonblue"] = Button(_("delete"))
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions", "ShortcutActions"],
			{
			 "back": self.close,
			 "up": self["body"].pageUp,
			 "down": self["body"].pageDown,
			 # TODO: perhaps better use left/right for previous/next message
			 "left": self["body"].pageUp,
			 "right": self["body"].pageDown,
			 "red": self.selectBody,
			 "green": self.selectAttachment,
			 "yellow": self.openMessagesHeaders,
			 "blue": self.delete,

			 }, -1)
		self.flags = flags
		self.proto = proto
		self.uid = uid
		proto.fetchFlags(self.uid).addCallback(self.cbOk).addErrback(self.cbNotOk)
		self.onLayoutFinish.append(self.updateButtons)

	def cbOk(self, result):
		print("cbOk result: %s" %repr(result))

	def cbNotOk(self, result):
		print("cbNotOk result: %s" %(result))

	def delete(self):
		if '\\Deleted' in self.flags:
			self.session.openWithCallback(self.deleteCB, ChoiceBox, title=_("really undelete Mail?"), list=[(_("yes"), True),(_("no"), False)])
		else:
			self.session.openWithCallback(self.deleteCB, ChoiceBox, title=_("really delete Mail?"), list=[(_("yes"), True),(_("no"), False)])

	def deleteCB(self, returnValue):
		if returnValue[1] is True:
			if '\\Deleted' in self.flags:
				self.proto.removeFlags(self.uid, ["\\Deleted"]).addCallback(self.cbOk).addErrback(self.cbNotOk)
			else:
				self.proto.addFlags(self.uid, ["\\Deleted"]).addCallback(self.cbOk).addErrback(self.cbNotOk)
			print("deleteCB: %s"  %repr(self.email))
			self.close()

	def openMessagesHeaders(self):
		pass #self.session.open(ScreenMailViewHeader,self.profil,self.email)

	def updateButtons(self):
		self["buttonred"].setText(_("Bodys"))
		if len(self.email.attachments):
			self["buttongreen"].setText(_("Attachments"))
		else:
			self["buttongreen"].setText("")

	def selectBody(self):
		if len(self.email.messagebodys):
			list = []
			for a in self.email.messagebodys:
				list.append((a.getContenttype(), a))
			self.session.openWithCallback(self.selectBodyCB, ChoiceBox, _("select Body"), list)

	def selectBodyCB(self, choice):
		if choice is not None:
			self["body"].setText(choice[1].getData())

	def selectAttachment(self):
		if len(self.email.attachments):
			list = []
			for a in self.email.attachments:
				name = a.getFilename()
				if name:
					list.append((a.getFilename(), a))
				else:
					list.append((_("no filename"), a))
			print("selectAttachment : " + repr(list))
			self.session.openWithCallback(self.selectAttachmentCB, ChoiceBox, _("select Attachment"), list)

	def selectAttachmentCB(self, choice):
		if choice is not None:
			print "Attachment selected", choice[1].getFilename()
			#showMessageBox(self.session)

class MailList(MenuList):
	def __init__(self, list, enableWrapAround = False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", scaleV(20,18))) # new
		self.l.setFont(1, gFont("Regular", scaleV(18,16))) # deleted
		self.l.setFont(2, gFont("Regular", scaleV(18,16))) # seen

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(scaleV(70,60))

class MessageHeader(object):
	def __init__(self, uid, message):
		self.uid = uid #must be int
		self.message = email.Parser.Parser().parsestr(message)

	def getSenderString(self):
		return decodeHeader(self.get("from"), _("no sender"))

	def getSubject(self):
		return decodeHeader(self.get("subject"), _("no subject"))

	def get(self, key, default=None):
		return self.message.get(key,failobj=default)

	def __str__(self):
		return "<MessageHeader uid="+str(self.uid)+", subject="+self.get("subject","no-subject")+">"

############
class EmailBody:
	def __init__(self,data):
		self.data = data

	def getEncoding(self):
		return self.data.get_content_charset()

	def getData(self):
		text = self.data.get_payload(decode=True)
		if self.getEncoding():
			try:
				text = text.decode(self.getEncoding())
			except UnicodeDecodeError:
				pass	
		# print('EmailBody/getData text: ' +  text)
		#=======================================================================
		# if self.getEncoding():
		#	text = text.decode(self.getEncoding())
		#=======================================================================
		if self.getContenttype() == "text/html":
			print "stripping html"
			text = strip_readable(text)
			# print('EmailBody/getData text: ' +  text)

		try:
			return text.encode('utf-8')
		except UnicodeDecodeError:
			return text
		

	def getContenttype(self):
		return self.data.get_content_type()

############
class EmailAttachment:
	def __init__(self, filename, contenttype, data):
		self.filename = filename
		self.contenttype = contenttype
		self.data = data

	def save(self,folder):
		try:
			fp = open(folder+"/"+self.getFilename(),"wb")
			fp.write(self.data)
			fp.close()
		except Exception,e:
			print e
			return False
		return True

	def getFilename(self):
		return self.filename

	def getContenttype(self):
		return self.contenttype

	def getData(self):
		return self.data

def UTF7toUTF8(str):
	return imap4.decoder(str)[0]

def UTF8toUTF7(str):
	return imap4.encoder(str.decode('utf-8'))[0]

def main(session, **kwargs):
	import os,shutil
	if os.path.isfile('/usr/lib/python2.5/uu.py') is not True:
		shutil.copy('/usr/lib/enigma2/python/Plugins/Extensions/EmailClient/uu.py', '/usr/lib/python2.5/uu.py')
		global session2
		session2 = session
		session.openWithCallback(MessageCB, MessageBox, 'In order of missing standart python library files\ni have copied the nessary files now.\nBut you have to restart your Box\n to apply this!', type = MessageBox.TYPE_INFO)
	else:
		session.open(EmailScreen)

def MessageCB(*args):
	global session2
	session2.open(EmailScreen)

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
			 PluginDescriptor(name="Email Client", description="view Emails via IMAP4",
			 where = PluginDescriptor.WHERE_PLUGINMENU,
			 fnc = main,
			 icon="plugin.png"
			 ),
		]
