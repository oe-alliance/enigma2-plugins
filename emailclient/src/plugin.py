from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigText, ConfigEnableDisable
from EmailConfig import EmailConfigScreen
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Tools import Notifications
from enigma import eListboxPythonMultiContent, gFont, eTimer
from twisted.mail import imap4
from zope.interface import implements
import email, time
from email.header import decode_header
from TagStrip import strip_readable
from protocol import createFactory

from . import _, initLog, debug

config.plugins.emailimap = ConfigSubsection()
config.plugins.emailimap.username = ConfigText("user", fixed_size=False)
config.plugins.emailimap.password = ConfigText("password", fixed_size=False)
config.plugins.emailimap.server = ConfigText("please.config.first", fixed_size=False)
config.plugins.emailimap.port = ConfigInteger(default=143, limits = (1, 65536))
config.plugins.emailimap.showDeleted = ConfigEnableDisable(default=False)
config.plugins.emailimap.checkForNewMails = ConfigEnableDisable(default=True)
config.plugins.emailimap.checkPeriod = ConfigInteger(default=60, limits=(0, 900)) #  in minutes
config.plugins.emailimap.timeout = ConfigInteger(default=0, limits=(0, 90)) # in seconds
# 0= fetch all header , 10= fetch only the last 10 headers/messages of a mailbox
config.plugins.emailimap.maxheadertoload = ConfigInteger(0, limits = (1, 100))
config.plugins.emailimap.debug = ConfigEnableDisable(default=False)

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
		self.factory = createFactory(self, config.plugins.emailimap.username.value, config.plugins.emailimap.server.value, config.plugins.emailimap.port.value)

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
							  ).addErrback(self.onExamineFailed, c[0], self.proto
							  )
		# self.proto.search(imap4.Query(unseen=1)).addCallback(self.cbOk).addErrback(self.cbNotOk)

	def onMessageSelected(self):
		c = self["messagelist"].getCurrent()
		if c is not None:
			self.fetchMessageSize(c[0])

	def fetchMessageSize(self, message):
		debug("[EmailScreen] fetchMessageSize: " + str(message))
		self.proto.fetchSize(message.uid
			).addCallback(self.onMessageSizeLoaded, message, self.proto
			).addErrback(self.onMessageLoadFailed, message, self.proto
			)

	def onMessageSizeLoaded(self, result, message, proto):
		debug("[EmailScreen] onMessageSizeLoaded: " + str(result) + ' ' + str(message))
		size = int(result[message.uid]['RFC822.SIZE'])
		self.MAX_MESSAGE_SIZE_TO_OPEN = 4000000
		if size >= self.MAX_MESSAGE_SIZE_TO_OPEN:
			#ask here to open message
			debug("message to large to open (size=%d" %size)
		else:
			self.loadMessage(message)

#	def fetchBodyStructure(self, message):
#		print "fetchBodyStructure",message
#		self.proto.fetchBodyStructure(message.uid
#			).addCallback(self.onBodystructureLoaded, message, self.proto
#			).addErrback(self.onMessageLoadFailed, message, self.proto
#			)

	def loadMessage(self, message):
		debug("[EmailScreen] loadMessage: " + str(message))
		self["infolabel"].setText(_("loading message"))

		self.proto.fetchMessage(message.uid
			).addCallback(self.onMessageLoaded, message, self.proto
			).addErrback(self.onMessageLoadFailed, message, self.proto
			)

	def onMessageLoaded(self, result, message, proto):
		self["infolabel"].setText(_("parsing message"))
		debug("[EmailScreen] onMessageLoaded") #,result,message
		try:
			msgstr = result[message.uid]['RFC822']
		except KeyError:
			self.loadMessage(message)
			return
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
						debug("[EmailScreen] unkown content type= " + part.get_content_maintype() + "/", part.get_content_subtype())
				else:
					debug("[EmailScreen] found Attachment with  " + part.get_content_type() + " and name " + part.get_filename())
					msg.attachments.append(EmailAttachment(part.get_filename(), part.get_content_type(), part.get_payload()))
		else:
			msg.messagebodys.append(EmailBody(msg))
		self.session.open(ScreenMailView, msg, message.uid, proto, self.flagsList[message.uid]['FLAGS']).onHide.append(self.onBoxSelected)

	def onMessageLoadFailed(self, failure, message, proto):
		debug("[EmailScreen] onMessageLoadFailed: " + str(failure) + ' ' + str(message))
		self["infolabel"].setText(_("failed to load message") + ': ' + failure.getErrorMessage())

	def action_exit(self):
		global mailChecker
		if not mailChecker and self.proto is not None:
			self.proto.logout().addCallback(self.onLogedOut, self.proto).addErrback(self.onLogedOut, self.proto)
		else:
			self.factory.stopFactory()
			self.close()

	def onLogedOut(self, result, proto):
		debug("[EmailScreen] onLogedOut: " + str(result))
		self.factory.stopFactory()()
		self.close()

	def onConnect(self, proto):
		self["infolabel"].setText(_("connected"))
		proto.getCapabilities(
						).addCallback(self.cbCapabilities, proto
						).addErrback(self.ebCapabilities, proto
						)
		self.factory.resetDelay()

	def cbCapabilities(self,reason,proto):
		debug("[EmailScreen] \n\
####################################################################################################\n\
# If you have problems to log into your imap-server, please send me the output of the following line\n\
# cbCapabilities: " + str(reason) +"\n\
####################################################################################################\n")
		self.doLogin(proto)

	def ebCapabilities(self,reason,proto):
		debug("[EmailScreen] ebCapabilities: " + str(reason))

	def onConnectFailed(self, reason):
		debug("[EmailScreen] onConnectFailed: " + reason.getErrorMessage())
		if self.has_key('infolabel'):
			self["infolabel"].setText(_("connection to %(server)s:%(port)d failed") %{'server':config.plugins.emailimap.server.value,'port':config.plugins.emailimap.port.value}) # + ': ' + reason.getErrorMessage()) # the messages provided by twisted are crap here
		self.action_exit()

	def onAuthentication(self, result, proto):
		self.proto = proto
		self["infolabel"].setText(_("logged in"))
		# better use LSUB here to get only the subscribed to mailboxes
		proto.lsub("", "*").addCallback(self.onMailboxList, proto)

	def doLogin(self, proto):
		debug("[EmailScreen] login secure")
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
		debug("[EmailScreen] onAuthenticationFailed: " + failure.getErrorMessage())
		self["infolabel"].setText(_("encrypted login failed, trying without encryption"))
		try:
			failure.trap(imap4.NoSupportedAuthentication)
			self.doLoginInsecure(proto)
		except Exception,e:
			print e,e.message

	def doLoginInsecure(self, proto):
		debug("[EmailScreen] login INSECURE")
		proto.login(config.plugins.emailimap.username.value, config.plugins.emailimap.password.value
				).addCallback(self.onAuthentication, proto
				).addErrback(self.onInsecureAuthenticationFailed, proto
				)

	def onInsecureAuthenticationFailed(self, failure, proto):
		debug("[EmailScreen] onInsecureAuthenticationFailed: " + failure.getErrorMessage())
		self["infolabel"].setText(_("login failed") + ': ' + failure.getErrorMessage())

	def onMailboxList(self, result, proto):
		debug("[EmailScreen] onMailboxList: " + str(result) + ' ' + str(proto))
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
		debug("[EmailScreen] onExamine: " + str(result) + ' ' + mboxname)
		self.setTitle(_("Mailbox")+": "+mboxname)
		self.currentmailbox = mboxname
		numMessagesinFolder = int(result['EXISTS'])
		if numMessagesinFolder <= 0:
			self["infolabel"].setText(_("Box '%s' is empty") %(mboxname))
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
			self["infolabel"].setText(_("loading headers %(from)d-%(to)d of Box '%(name)s'") % {'from': rangeToFetch[0], 'to': rangeToFetch[1], 'name': mboxname})

			try:
#				proto.fetchEnvelope('%i:%i'%(rangeToFetch[0], rangeToFetch[1])	#'1:*'
#						   ).addCallback(self.onnvelopeList, proto
#						   )
				self.proto = proto
				self.rangeToFetch = rangeToFetch
				proto.fetchFlags('%i:%i'%(rangeToFetch[0], rangeToFetch[1])	#'1:*'
						   ).addCallback(self.onFlagsList)

			except imap4.IllegalServerResponse, e:
				debug("[EmailScreen] onExamine exception: " + str(e))
			self.selectMessagelist()

	def onFlagsList(self, result):
		self.flagsList = result
		self.proto.fetchHeaders('%i:%i'%(self.rangeToFetch[0], self.rangeToFetch[1])	#'1:*'
				   ).addCallback(self.onHeaderList, self.proto
				   )

	def onExamineFailed(self, failure, mboxname, proto):
		debug("[EmailScreen] onExamineFailed: " + mboxname + ' ' + str(failure) + ' ' + str(proto))
		self["infolabel"].setText(_("cannot access mailbox '%(mboxname)s'") % {'mboxname':mboxname})

	def cbOk(self, result):
		debug("[EmailScreen] cbOk result: %s" %repr(result))

	def cbNotOk(self, result):
		debug("[EmailScreen] cbNotOk result: %s" %(str(result)))

	def onHeaderList(self, result, proto):
		debug("[EmailScreen] onHeaderList") #,result,proto
		self["infolabel"].setText(_("headers loaded, now parsing ..."))
		list = []
		for m in result:
			state = IS_UNSEEN
			# debug("onHeaderList :" + repr(self.flagsList[m]['FLAGS']))
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
					debug("[EmailScreen] onHeaderList error: %s (%s)" %(result[m]['RFC822.HEADER'], str(e)))
		if list:
			list.reverse()
			self["messagelist"].l.setList(list)
			self["infolabel"].setText(_("have %d messages") %(len(list)))
		else:
			self["messagelist"].l.setList([])
			self["infolabel"].setText(_("have no messages"))
			# self.onBoxSelected() # brings us into endless loop, when still deleted messages are in there...
			self.selectBoxlist()

	def buildMessageListItem(self, message, state):
		if state == IS_UNSEEN:
			font = 0
			color = 0x00FFFFFF # white
		elif state == IS_DELETED:
			font = 1 
			color = 0x00FF6666 # redish :)
		else:
			font = 2
			color = 0x00888888 # grey
		return [
			message,
			MultiContentEntryText(pos=(5, 0), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.getSenderString(), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, scaleV(20,18)+1), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.get('date', default=_('no date')), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, 2*(scaleV(20,18)+1)), size=(self.messagelistWidth, scaleV(20,18)+5), font=font, text=message.getSubject(), color=color, color_sel=color)
		]
	#
	# IMailboxListener methods
	#
	def modeChanged(self, writeable):
		debug("[EmailScreen] modeChanged: " + str(writeable))

	def flagsChanged(self, newFlags):
		debug("[EmailScreen] flagsChanged: " + str(newFlags))

	def newMessages(self, exists, recent):
		debug("[EmailScreen] newMessages: " + str(exists) + ' ' +  str(recent))

class ScreenMailView(Screen):
	skin=""
	def __init__(self, session, email, uid, proto, flags):
		self.session = session
		self.email = email
		# debug('ScreenMailView ' + repr(email) + ' dir: ' + repr(dir(email)))
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
		self["from"] = Label(decodeHeader(_("From") +": %s" %self.email.get('from', _('no from'))))
		self["date"] = Label(_("Date") +": %s" %self.email.get('date', 'no-date'))
		self["subject"] = Label(decodeHeader(_("Subject") +": %s" %self.email.get('subject', _('no subject'))))
		self["body"] = ScrollLabel(_(self.email.messagebodys[0].getData()))
		# TODO: show headers
		self["buttonred"] = Button("")
		self["buttongreen"] = Button("")
		self["buttonyellow"] = Button(_("leave unread"))
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
			 "yellow": self.markUnread,
			 "blue": self.delete,

			 }, -1)
		self.flags = flags
		self.proto = proto
		self.uid = uid
		proto.fetchFlags(self.uid).addCallback(self.cbOk).addErrback(self.cbNotOk)
		self.onLayoutFinish.append(self.updateButtons)

	def cbOk(self, result):
		debug("[ScreenMailView] cbOk result: %s" %repr(result))

	def cbNotOk(self, result):
		debug("[ScreenMailView] cbNotOk result: %s" %(str(result)))

	def delete(self):
		if '\\Deleted' in self.flags:
			self.session.openWithCallback(self.deleteCB, ChoiceBox, title=_("really undelete Mail?"), list=[(_("yes"), True),(_("no"), False)])
		else:
			self.session.openWithCallback(self.deleteCB, ChoiceBox, title=_("really delete Mail?"), list=[(_("yes"), True),(_("no"), False)])

	def deleteCB(self, returnValue):
		if returnValue and returnValue[1] is True:
			if '\\Deleted' in self.flags:
				self.proto.removeFlags(self.uid, ["\\Deleted"]).addCallback(self.cbOk).addErrback(self.cbNotOk)
			else:
				self.proto.addFlags(self.uid, ["\\Deleted"]).addCallback(self.cbOk).addErrback(self.cbNotOk)
			debug("[ScreenMailView] deleteCB: %s"  %repr(self.email))
			self.close()

	def markUnread(self):
		self.proto.removeFlags(self.uid, ["\\Seen"]).addCallback(self.cbOk).addErrback(self.cbNotOk)
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
			debug("[ScreenMailView] selectAttachment : " + repr(list))
			self.session.openWithCallback(self.selectAttachmentCB, ChoiceBox, _("select Attachment"), list)

	def selectAttachmentCB(self, choice):
		if choice is not None:
			debug("[ScreenMailView] Attachment selected: " + choice[1].getFilename())
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
		return "<MessageHeader uid="+str(self.uid)+", subject="+self.get("subject",_("no subject"))+">"

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
		# debug('EmailBody/getData text: ' +  text)
		#=======================================================================
		# if self.getEncoding():
		#	text = text.decode(self.getEncoding())
		#=======================================================================
		if self.getContenttype() == "text/html":
			debug("[EmailBody] stripping html")
			text = strip_readable(text)
			# debug('EmailBody/getData text: ' +  text)

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
			debug("[EmailAttachment] save %s" %str(e))
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
		session.openWithCallback(MessageCB, MessageBox, _('In order of missing standart python library files\ni have copied the nessary files now.\nBut you have to restart your Box\n to apply this!'), type = MessageBox.TYPE_INFO)
	else:
		session.open(EmailScreen)

def MessageCB(*args):
	global session2
	session2.open(EmailScreen)

class CheckMail:
	implements(imap4.IMailboxListener)
	_timer = None

	def __init__(self):
		debug('[CheckMail] __init__ on %s' %time.ctime())
		self.factory = createFactory(self, config.plugins.emailimap.username.value, config.plugins.emailimap.server.value, config.plugins.emailimap.port.value)
		if not self._timer:
			debug('[CheckMail] __init__ creatings timer: %s' %time.ctime())
			self._timer = eTimer()
			# self._timer.timeout.get().append(self._checkMail)
			self._timer.callback.append(self._checkMail)
			self._timer.start(config.plugins.emailimap.checkPeriod.value*60*1000) # it is minutes
		self._unseenList = None
		self._proto = None

	def exit(self):
		if self._proto:
			self._proto.logout()
			self._proto = None
		self._timer.stop()
		self.factory.stopFactory()

	def _checkMail(self):
		debug('[CheckMail] _checkMail on %s' %time.ctime())
		if self._proto:
			self._proto.search(imap4.Query(unseen=1)).addCallback(self._cbNotify).addErrback(self._ebNotify, _("cannot get list of new messages"))
		else:
			self.factory.retry()

	def _cbNotify(self, newUnseenList):
		def haveNotSeenBefore(messageNo): return messageNo not in self._unseenList

		debug("[CheckMail] _cbNotify newUnseenList: %s" %repr(newUnseenList))
		if self._unseenList is None:
			Notifications.AddNotification(MessageBox, str(len(newUnseenList)) + ' ' + _("unread messages in mailbox"), type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
		else:
			newMessages = filter(haveNotSeenBefore, newUnseenList)
			if newMessages:
				debug("[CheckMail] _cbNotify newMessages: %s" %repr(newMessages))
				newMessageSet = imap4.MessageSet()
				for messageNo in newMessages:
					newMessageSet.add(messageNo)
				self._proto.fetchHeaders(newMessageSet).addCallback(self._onHeaderList).addErrback(self._ebNotify, _("cannot get headers of new messages"))
		self._unseenList = newUnseenList

	def _onHeaderList(self, headers):
		# debug("_onHeaderList headers: %s" %repr(headers))
		message = _("New mail arrived:\n\n")
		for h in headers:
			m = MessageHeader(h, headers[h]['RFC822.HEADER'])
			message += m.getSenderString() + '\n' + m.getSubject() + '\n\n'
		Notifications.AddNotification(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)

	def _ebNotify(self, result, where, what):
		debug("[CheckMail] _ebNotify error in %s: %s: %s" %(where, what, result.getErrorMessage()))
		Notifications.AddNotification(MessageBox, "EmailClient:\n\n" + what, type=MessageBox.TYPE_ERROR, timeout=config.plugins.emailimap.timeout.value)
		# self.exit()

	def _cbOk(self, result):
		debug("[CheckMail] _cbOk result: %s" %repr(result))

	def onConnect(self, proto):
		debug('[CheckMail] onConnect ' + str(proto))
		self._proto = proto
		proto.getCapabilities().addCallback(self._cbCapabilities).addErrback(self._ebNotify, "getCapabilities", _("cannot get capabilities of mailserver"))

	def onConnectFailed(self, reason):
		debug('[CheckMail] onConnectFailed: ' + reason.getErrorMessage())
		self._ebNotify(reason, "onConnectFailed", _("connection to %(server)s:%(port)d failed:\n%(reason)s") %{'server':config.plugins.emailimap.server.value,'port':config.plugins.emailimap.port.value,'reason':reason.getErrorMessage()})
		self._proto = None

	def _cbCapabilities(self,reason):
		debug("[CheckMail] _cbCapabilities\n\
####################################################################################################\n\
# If you have problems to log into your imap-server, please send me the output of the following line\n\
# cbCapabilities: " + str(reason) +"\n\
####################################################################################################\n")
		self._doLogin()
		
	def _doLogin(self):
		useTLS = False #True
		if useTLS:
			#d = self._proto.startTLS().addCallback(self._proto.authenticate, config.plugins.emailimap.password.value)
			d = self._proto.startTLS().addCallback(self._proto.authenticate) # don't know, why authenticate wants no param...
		else:
			d = self._proto.authenticate(config.plugins.emailimap.password.value)
		d.addCallback(self._onAuthentication).addErrback(self._onAuthenticationFailed)
		
	def _onAuthentication(self, result):
		debug("[CheckMail] onAuthentication: logged in")
		self._proto.examine('inbox').addCallback(self._cbOk).addErrback(self._ebNotify, "examine", _("cannot access inbox"))
		self._checkMail()

	def _onAuthenticationFailed(self, failure):
		# If it failed because no SASL mechanisms match
		debug("[CheckMail] onAuthenticationFailed: " + failure.getErrorMessage())
		try:
			failure.trap(imap4.NoSupportedAuthentication)
			self._doLoginInsecure()
		except Exception,e:
			debug("[CheckMail] onAuthenticationFailed: %s" %str(e))

	def _doLoginInsecure(self):
		debug("[CheckMail] doLoginInsecure")
		self._proto.login(config.plugins.emailimap.username.value, config.plugins.emailimap.password.value
				).addCallback(self._onAuthentication).addErrback(self._ebNotify, "login", _("login failed"))

mailChecker = None
def autostart(reason, **kwargs):
	# ouch, this is a hack
	if kwargs.has_key("session"):
		global my_global_session
		my_global_session = kwargs["session"]
		return

	debug("[EmailClient] - Autostart")
	global mailChecker
	if config.plugins.emailimap.checkForNewMails.value and not mailChecker:
		mailChecker = CheckMail()

initLog()

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
			 PluginDescriptor(name=_("Email Client"), description=_("view Emails via IMAP4"),
			 where = PluginDescriptor.WHERE_PLUGINMENU,
			 fnc = main,
			 icon="plugin.png"
			 ),
			 PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)
		]
