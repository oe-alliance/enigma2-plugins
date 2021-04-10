# -*- coding: utf-8 -*-
'''
$Author$
$Revision$
$Date$
$Id$
'''
from __future__ import print_function
from __future__ import absolute_import
from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigEnableDisable
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Tools import Notifications
from enigma import eListboxPythonMultiContent, gFont, eTimer #@UnresolvedImport # pylint: disable-msg=E0611
from twisted.mail import imap4 #@UnresolvedImport
from zope.interface import implementer
import email
import re
import os
from email.header import decode_header
import time
from .TagStrip import strip_readable
from .protocol import createFactory

from . import _, initLog, debug, scaleH, scaleV, DESKTOP_WIDTH, DESKTOP_HEIGHT #@UnresolvedImport # pylint: disable-msg=F0401
mailAccounts = [] # contains all EmailAccount objects
from .EmailConfig import EmailConfigOptions, EmailConfigAccount

from functools import reduce

config.plugins.emailimap = ConfigSubsection()
config.plugins.emailimap.showDeleted = ConfigEnableDisable(default=False)
config.plugins.emailimap.timeout = ConfigInteger(default=0, limits=(0, 90)) # in seconds
config.plugins.emailimap.verbose = ConfigEnableDisable(default=True)
config.plugins.emailimap.debug = ConfigEnableDisable(default=False)

def decodeHeader(text, default=''):
	if text is None:
		return _(default)
	text = text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
	text = re.sub('\s\s+', ' ', text)
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
	except UnicodeDecodeError: # for faulty mail software systems
		return textNew.decode('iso-8859-1').encode('utf-8')

IS_UNSEEN = 0
IS_SEEN = 1
IS_DELETED = 2 

class EmailScreen(Screen):
	'''
	This is the main screen for interacting with the user.
	It contains the list of mailboxes (boxlist) on the left and
	the list of messages (messagelist) on the right.
	At the bottom we have a line for info messages.
	It is specific for one account.
	'''

	width = scaleH(-1, 530)
	height = scaleV(-1, 430)
	boxlistWidth = scaleH(-1, 150)
	messagelistWidth = width - boxlistWidth
	infolabelHeight = scaleV(-1, 30)
	skin = """
		<screen position="%d,%d" size="%d,%d" title="Email" >
			<widget name="boxlist" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" />
			<widget name="messagelist" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" />
			<widget name="infolabel" position="%d,%d" size="%d,%d"   foregroundColor=\"white\" font=\"Regular;%d\" />
		</screen>""" % (
					   (DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, width, height,
					   boxlistWidth, height - infolabelHeight,
					   boxlistWidth, 0, messagelistWidth, height - infolabelHeight,
					   0, height - infolabelHeight, width, infolabelHeight, scaleV(20, 18)
					   )

	def __init__(self, session, account):
		'''
		This is the main screen for interacting with the user.
		It contains the list of mailboxes (boxlist) on the left and
		the list of messages (messagelist) on the right.
		At the bottom we have a line for info messages.
		It is specific for one account.
	
		@param session: session in which this screen is running
		@param account: account for which mailboxes are shown 
		'''
		self._session = session
		self._account = account
		self.skin = EmailScreen.skin
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["InfobarChannelSelection", "WizardActions", "DirectionActions", "MenuActions", "ShortcutActions", "GlobalActions", "HelpActions", "NumberActions", "ChannelSelectBaseActions"],
			{
			 "ok": self._ok,
			 "back": self._exit,
			 "historyNext": self._selectMessagelist,
			 "historyBack": self._selectBoxlist,
			 "nextBouquet": self._selectMessagelist,
			 "prevBouquet": self._selectBoxlist,
			 "down": self._down,
			 "up": self._up,
			 "left": self._left,
			 "right": self._right,
			 }, -1)
		self["messagelist"] = MenuList([], content=eListboxPythonMultiContent)
		self["messagelist"].l.setItemHeight(scaleV(70, 60))
		self["messagelist"].l.setFont(0, gFont("Regular", scaleV(20, 18))) # new
		self["messagelist"].l.setFont(1, gFont("Regular", scaleV(18, 16))) # deleted
		self["messagelist"].l.setFont(2, gFont("Regular", scaleV(18, 16))) # seen

		if self._account.isConnected():
			self["infolabel"] = Label("")
			self["boxlist"] = MenuList(self._account.mailboxList)
			self.onLayoutFinish.append(self._finishBoxlist)
		else:
			self["infolabel"] = Label(_("account not connected"))
			self["boxlist"] = MenuList([])
		self.currList = "boxlist"

	def _exit(self):
		self.close()

	def _finishBoxlist(self):
		# pylint: disable-msg=W0212
		self.setTitle(_("%(name)s (%(user)s@%(server)s)")
				% {
				'name':self._account._name,
				'user':self._account._user,
				'server':self._account._server
				})
		self["boxlist"].moveToIndex(self._account.inboxPos - 1)
		self._selectBoxlist()
		self._onBoxSelected()
	
	def _selectBoxlist(self):
		self.currList = "boxlist"
		self["messagelist"].selectionEnabled(0)
		self["boxlist"].selectionEnabled(1)

	def _selectMessagelist(self):
		self.currList = "messagelist"
		self["boxlist"].selectionEnabled(0)
		self["messagelist"].selectionEnabled(1)

	def _up(self):
		self[self.currList].up()

	def _down(self):
		self[self.currList].down()

	def _left(self):
		self[self.currList].pageUp()

	def _right(self):
		self[self.currList].pageDown()

	def _ok(self):
		if self.currList == "boxlist":
			self._onBoxSelected()
		else:
			self._onMessageSelected()

	def _ebNotify(self, where, what):
		'''
		Error notification via calling back
		@param where: location, where the error occurred
		@param what: message, what happened
		'''
		# pylint: disable-msg=W0212
		debug("[EmailScreen] _ebNotify error in %s: %s" % (where, what))
		self.session.open(MessageBox, _("EmailClient for %(account)s:\n\n%(error)s") % {'account': self._account._name, 'error':what}, type=MessageBox.TYPE_ERROR, timeout=config.plugins.emailimap.timeout.value)

	def _onBoxSelected(self):
		self["messagelist"].l.setList([])
		self._onBoxSelectedNoClear()

	def _onBoxSelectedNoClear(self):
		self["infolabel"].setText(_("loading headers ..."))
		if self["boxlist"].getCurrent():
			if self._account.getMessageList(self._onHeaderList, self["boxlist"].getCurrent()):
				self._selectMessagelist()
			else:
				self["infolabel"].setText(_("account not connected"))
		else:
			self["infolabel"].setText(_("no mailbox?!?!"))
			

	def _onHeaderList(self, result, flagsList):
		'''
		
		@param result: list of message
		@param flagsList: list of corresponding flags
		'''
		debug("[EmailScreen] onHeaderList: %s" % len(result))
		self["infolabel"].setText(_("headers loaded, now parsing ..."))
		self._flagsList = flagsList
		mylist = []
		for m in result:
			state = IS_UNSEEN
			# debug("onHeaderList :" + repr(flagsList[m]['FLAGS']))
			if '\\Seen' in flagsList[m]['FLAGS']:
				state = IS_SEEN
			if '\\Deleted' in flagsList[m]['FLAGS']:
				if not config.plugins.emailimap.showDeleted.value:
					continue
				else:
					state = IS_DELETED
			mylist.append(self._buildMessageListItem(MessageHeader(m, result[m]['RFC822.HEADER']), state))

		mylist.sort(key=lambda x: x[0].getTimestampUTC(), reverse=True)
		self["messagelist"].l.setList(mylist)
		if len(mylist) > 0:
			self["infolabel"].setText(_("have %d messages") % (len(mylist)))
		else:
			self["infolabel"].setText(_("have no messages"))
			# self.onBoxSelected() # brings us into endless loop, when still deleted messages are in there...
			self._selectBoxlist()

	def _onMessageSelected(self):
		self["infolabel"].setText(_("getting message ..."))
		c = self["messagelist"].getCurrent()
		if c is not None:
			if not self._account.getMessage(c[0], self._onMessageLoaded, self._ebNotify):
				self["infolabel"] = Label(_("account not connected"))

	def _onMessageLoaded(self, result, message):
		self["infolabel"].setText(_("parsing message ..."))
		debug("[EmailScreen] onMessageLoaded") #,result,message
		try:
			msgstr = result[message.uid]['RFC822']
		except KeyError:
			self._account.getMessage(message, self._onMessageLoaded, self._ebNotify)
			# self.loadMessage(message)
			return
		msg = email.Parser.Parser().parsestr(msgstr) #@UndefinedVariable # pylint: disable-msg=E1101
		msg.messagebodys = []
		msg.attachments = []

		if msg.is_multipart():
			for part in msg.walk():
				if part.get_content_maintype() == "multipart":
					continue
				if part.get_content_maintype() == 'text' and part.get_filename() is None:
					if part.get_content_subtype() == "html":
						msg.messagebodys.append(EmailBody(part))
					elif part.get_content_subtype() == "plain":
						msg.messagebodys.append(EmailBody(part))
					else:
						debug("[EmailScreen] onMessageLoaded: unknown content type=%s/%s" % (str(part.get_content_maintype()), str(part.get_content_subtype())))
				else:
					debug("[EmailScreen] onMessageLoaded: found Attachment with  %s and name %s" % (str(part.get_content_type()), str(part.get_filename())))
					msg.attachments.append(EmailAttachment(part.get_filename(), part.get_content_type(), part.get_payload()))
		else:
			msg.messagebodys.append(EmailBody(msg))
		debug("[EmailScreen] onMessageLoaded:" + str(message.uid) + ';' + repr(self._flagsList[message.uid]['FLAGS']))
		self.session.open(ScreenMailView, self._account, msg, message.uid, self._flagsList[message.uid]['FLAGS']).onHide.append(self._onBoxSelectedNoClear)
		self["infolabel"].setText("")

	def _buildMessageListItem(self, message, state):
		'''
		Construct a MultiContentEntryText from parameters
		@param message: message
		@param state: IS_UNSEEN (grey), IS_DELETED (red) are especially colored
		'''
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
			MultiContentEntryText(pos=(5, 0), size=(self.messagelistWidth, scaleV(20, 18) + 5), font=font, text=message.getSenderString(), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, scaleV(20, 18) + 1), size=(self.messagelistWidth, scaleV(20, 18) + 5), font=font, text=message.getLocalDateTimeString(), color=color, color_sel=color),
			MultiContentEntryText(pos=(5, 2 * (scaleV(20, 18) + 1)), size=(self.messagelistWidth, scaleV(20, 18) + 5), font=font, text=message.getSubject(), color=color, color_sel=color)
		]

class ScreenMailView(Screen):
	skin = ""
	def __init__(self, session, account, message, uid, flags):
		'''
		Principal screen to show one mail message.
		@param session:
		@param account: mail acoount, this message is coming from 
		@param message: the message itself
		@param uid: uid of the message, needed to (un)delete and unmark
		@param flags: the flags of the message, needed to check, whether IS_DELETED
		'''
		self._session = session
		self._email = message
		self._account = account
		# debug('ScreenMailView ' + repr(email) + ' dir: ' + repr(dir(email)))
		width = max(4 * 140, scaleH(-1, 550))
		height = scaleV(-1, 476)
		fontSize = scaleV(24, 20)
		lineHeight = fontSize + 5
		buttonsGap = (width - 4 * 140) / 5
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
		</screen>""" % (
					   (DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, width, height,
					   0, 0, width, lineHeight, fontSize - 1, # from
					   0, lineHeight, width, lineHeight, fontSize - 1, # date
					   0, 2 * lineHeight, width, lineHeight, fontSize - 1, # subject 
					   0, 3 * lineHeight + 1, width, # line 
					   0, 3 * lineHeight + 5, width, height - 3 * lineHeight - 5 - 5 - 30 - 5, fontSize, # body
					   buttonsGap, height - 30 - 5,
					   2 * buttonsGap + 140, height - 30 - 5,
					   3 * buttonsGap + 2 * 140, height - 30 - 5,
					   4 * buttonsGap + 3 * 140, height - 30 - 5,
					   buttonsGap, height - 30 - 5, scaleV(18, 16),
					   2 * buttonsGap + 140, height - 30 - 5, scaleV(18, 16),
					   3 * buttonsGap + 2 * 140, height - 30 - 5, scaleV(18, 16),
					   4 * buttonsGap + 3 * 140, height - 30 - 5, scaleV(18, 16),
					   )
		Screen.__init__(self, session)
		self["from"] = Label(decodeHeader(_("From") + ": %s" % self._email.get('from', _('no from'))))
		msgdate = email.utils.parsedate_tz(self._email.get("date", ""))
		self["date"] = Label(_("Date") + ": %s" % (time.ctime(email.utils.mktime_tz(msgdate)) if msgdate else _("no date")))
		self["subject"] = Label(decodeHeader(_("Subject") + ": %s" % self._email.get('subject', _('no subject'))))
		self["body"] = ScrollLabel(_(self._email.messagebodys[0].getData()))
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
			 "red": self._selectBody,
			 "green": self._selectAttachment,
			 "yellow": self._markUnread,
			 "blue": self._delete,

			 }, -1)
		self._uid = uid
		self._flags = flags
		self.onLayoutFinish.append(self._updateButtons)

	def _delete(self):
		if '\\Deleted' in self._flags:
			self.session.openWithCallback(self._deleteCB, MessageBox, _("really undelete mail?"), type=MessageBox.TYPE_YESNO, timeout=config.plugins.emailimap.timeout.value)
		else:
			self.session.openWithCallback(self._deleteCB, MessageBox, _("really delete mail?"), type=MessageBox.TYPE_YESNO, timeout=config.plugins.emailimap.timeout.value)

	def _deleteCB(self, returnValue):
		if returnValue:
			if '\\Deleted' in self._flags:
				if not self._account.undelete(self._uid):
					self.session.open(MessageBox, _("account not connected"), type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
			else:
				if not self._account.delete(self._uid):
					self.session.open(MessageBox, _("account not connected"), type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
			debug("[ScreenMailView] deleteCB: %s" % repr(self._email))
			self.close()

	def _markUnread(self):
		if not self._account.unread(self._uid):
			self.session.open(MessageBox, _("account not connected"), type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
		self.close()

	def _updateButtons(self):
		if len(self._email.messagebodys):
			self["buttonred"].setText(_("Bodys"))
		else:
			self["buttonred"].setText("")
		if len(self._email.attachments):
			self["buttongreen"].setText(_("Attachments"))
		else:
			self["buttongreen"].setText("")

	def _selectBody(self):
		if len(self._email.messagebodys):
			mylist = []
			for a in self._email.messagebodys:
				mylist.append((a.getContenttype(), a))
			self.session.openWithCallback(self._selectBodyCB, ChoiceBox, _("select Body"), mylist)

	def _selectBodyCB(self, choice):
		if choice is not None:
			self["body"].setText(choice[1].getData())

	def _selectAttachment(self):
		if len(self._email.attachments):
			mylist = []
			for a in self._email.attachments:
				name = a.getFilename()
				if name:
					mylist.append((a.getFilename(), a))
				else:
					mylist.append((_("no filename"), a))
			debug("[ScreenMailView] selectAttachment : " + repr(mylist))
			self.session.openWithCallback(self._selectAttachmentCB, ChoiceBox, _("select Attachment"), mylist)

	def _selectAttachmentCB(self, choice):
		if choice:
			if choice[1].getFilename():
				debug("[ScreenMailView] Attachment selected: " + choice[1].getFilename())
			else:
				debug("[ScreenMailView] Attachment with no filename selected")
			# nothing happens here. What shall we do now with the attachment?

############
class EmailBody:
	def __init__(self, data):
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

	def save(self, folder):
		try:
			fp = open(folder + "/" + self.getFilename(), "wb")
			fp.write(self.data)
			fp.close()
		except Exception as e:
			debug("[EmailAttachment] save %s" % str(e))
			return False
		return True

	def getFilename(self):
		return self.filename

	def getContenttype(self):
		return self.contenttype

	def getData(self):
		return self.data

def UTF7toUTF8(string): # pylint: disable-msg=C0103
	return imap4.decoder(string)[0]

def UTF8toUTF7(string): # pylint: disable-msg=C0103
	return imap4.encoder(string.decode('utf-8'))[0]


class CheckMail:
	def __init__(self, acc):
		'''
		Mail checker object for one account
		@param acc: the account to be checked periodically, each account has
					at most one checker
		@type acc: EmailAccount
		'''
		# pylint: disable-msg=W0212
		import random
		self._name = acc._name
		self._account = acc
		self._timer = eTimer()
		self._timer.callback.append(self._checkMail)
		# I guess, users tend to use identical intervals, so make them a bit different :-)
		# constant stolen from ReconnectingFactory
		self._interval = int(self._account._interval) * 60 * 1000
		self._interval = int(random.normalvariate(self._interval, self._interval * 0.11962656472))
		debug("[CheckMail] %(name)s: __init__: checking all %(interval)s seconds"
			% {'name':self._name, 'interval':self._interval / 1000})
		self._timer.start(self._interval) # it is minutes
		self._unseenList = None
		self._checkMail()

	def exit(self):
		debug("[CheckMail] %s: exit" % (self._name))
		self._timer.stop()

	def stopChecking(self):
		'''
		Just stop the timer, don't empty the unseenList.
		'''
		debug("[CheckMail] %s: stopChecking" % (self._name))
		self._timer.stop()

	def reStartChecking(self):
		'''
		Start the timer again and immediately do a check.
		'''
		debug("[CheckMail] %s: reStartChecking" % (self._name))
		self._timer.start(self._interval)
		self._checkMail()

	def _checkMail(self):
		# debug("[CheckMail] _checkMail for %s" %self._name)
		self._account.getUnseenHeaders(self._filterNewUnseen)

	def _filterNewUnseen(self, newUnseenList):
		'''
		Main method in this class: get the list of unseen messages
		and check them against the last list. New unseen messages
		are then displayed via _onHeaderList
		@param newUnseenList: new list of unseen messages
		'''
		debug('[CheckMail] %s: _filterNewUnseen: %s' % (self._name, repr(newUnseenList)))
		if self._unseenList is None:
			debug('[CheckMail] %s: _filterNewUnseen: init' % (self._name))
			# Notifications.AddNotification(MessageBox, str(len(newUnseenList)) + ' ' + _("unread messages in mailbox %s") %self._name, type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
		else:
			newMessages = filter(lambda x: x not in self._unseenList, newUnseenList)
			if newMessages:
				debug("[CheckMail] %s: _filterNewUnseen: new message(s): %s" % (self._name, repr(newMessages)))
				# construct MessageSet from list of message numbers
				# newMessageSet = reduce(lambda x,y: y.add(x), newMessages, imap4.MessageSet())
				newMessageSet = imap4.MessageSet()
				for i in newMessages:
					newMessageSet.add(i)
				if not self._account.getHeaders(self._onHeaderList, newMessageSet):
					debug("[CheckMail] %s: _filterNewUnseen: could not get Headers" % (self._name))

		self._unseenList = newUnseenList

	def _onHeaderList(self, headers):
		'''
		Notify about the list of headers.
		@param headers: list of headers
		'''
		# debug("[CheckMail] _onHeaderList headers: %s" %repr(headers))
		message = _("New mail arrived for account %s:\n\n") % self._name
		for h in headers:
			m = MessageHeader(h, headers[h]['RFC822.HEADER'])
			message += m.getSenderString() + '\n' + m.getSubject() + '\n\n'
		Notifications.AddNotification(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)

class MessageHeader(object):
	def __init__(self, uid, message):
		self.uid = uid #must be int
		self.message = email.Parser.HeaderParser().parsestr(message) #@UndefinedVariable # pylint: disable-msg=E1101

	def getSenderString(self):
		return decodeHeader(self.get("from"), _("no sender"))

	def getSubject(self):
		return decodeHeader(self.get("subject"), _("no subject"))

	def getLocalDateTimeString(self):
		msgdate = email.utils.parsedate_tz(self.get("date", ""))
		if msgdate:
			return time.ctime(email.utils.mktime_tz(msgdate))
		else:
			return self.get("date", _("no date"))

	def getTimestampUTC(self):
		ts = 0
		msgdate = email.utils.parsedate_tz(self.get("date", ''))
		if msgdate:
			ts = email.utils.mktime_tz(msgdate)
		return ts

	def get(self, key, default=None):
		return self.message.get(key, failobj=default)

	def __str__(self):
		return "<MessageHeader uid=" + str(self.uid) + ", subject=" + self.getSubject() + ">"

@implementer(imap4.IMailboxListener)
class EmailAccount():
	'''
	Principal class to hold an account.
	'''

	def __init__(self, params, afterInit=None):
		'''
		Principal class to hold an account.
		@param params: (name, server, port, user, password, interval, maxmail)
		@param afterInit: to be called, when init is done. Needed to writeAccounts AFTER this one is added
		'''
		# TODO: decrypt password
		(self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, listall) = params
		# debug("[EmailAccount] %s: __init__: %s" %(self._name, repr(params)))
		self._listall = (listall == 1)
		self._factory = createFactory(self, self._user, self._server, int(self._port))
		self._proto = None
		self._mailChecker = None
		self.inboxPos = 0
		self.mailboxList = None
		self._failureReason = ""
		self._connectCallback = None 
		mailAccounts.append(self)
		if afterInit:
			afterInit()

	def exit(self):
		mailAccounts.remove(self)
		# stop checker and get rid of it
		self.stopChecker()
		self._mailChecker = None
		# stop factory and get rid of it
		if self._factory:
			self._factory.stopTrying()
		self._factory = None # I am not sure to stop the factory, though...
		# if we still have a proto, logout and dump it
		if self._proto:
			self._proto.logout()
		self._proto = None

	def isConnected(self):
		return self._proto is not None and self.mailboxList is not None

	def forceRetry(self, connectCallback):
		'''
		reset delays and retry
		@param connectCallback: call this function on successful connect, used by EmailAccountList
		'''
		self._connectCallback = connectCallback 
		if self._factory and self._factory.connector:
			self._factory.resetDelay()
			self._factory.retry()
		else:
			self._factory = createFactory(self, self._user, self._server, int(self._port))

	def removeCallback(self):
		self._connectCallback = None 

	def getConfig(self):
		# TODO: encrypt passwd
		return (self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, (1 if self._listall else 0))

	def _ebNotify(self, result, where, what):
		debug("[EmailAccount] %s: _ebNotify error in %s: %s: %s" % (self._name, where, what, result.getErrorMessage()))
		if config.plugins.emailimap.verbose.value:
			Notifications.AddNotification(MessageBox, "EmailClient for %(account)s:\n\n%(error)s" % {'account': self._name, 'error':what}, type=MessageBox.TYPE_ERROR, timeout=config.plugins.emailimap.timeout.value)

	def startChecker(self):
		# debug("[EmailAccount] %s: startChecker?" %self._name)
		if int(self._interval) != 0:
			if self._mailChecker:
				# so, we already have seen an unseenList
				# debug("[EmailAccount] %s: startChecker again" %self._name)
				self._mailChecker.reStartChecking()
			else:
				# debug("[EmailAccount] %s: startChecker new" %self._name)
				self._mailChecker = CheckMail(self)

	def stopChecker(self):
		if self._mailChecker:
			self._mailChecker.stopChecking()

	def undelete(self, uid):
		'''
		undelete a message
		@param uid: uid of message
		'''
		if self._proto:
			self._proto.removeFlags(uid, ["\\Deleted"])
			return True
		else:
			return False

	def delete(self, uid):
		'''
		mark message as deleted 
		@param uid: uid of message
		'''
		if self._proto:
			self._proto.addFlags(uid, ["\\Deleted"])
			return True
		else:
			return False

	def unread(self, uid):
		'''
		mark message as unread, remove \\Seen
		@param uid: uis of message
		'''
		if self._proto:
			self._proto.removeFlags(uid, ["\\Seen"])
			return True
		else:
			return False

	def getUnseenHeaders(self, callback):
		# debug('[EmailAccount] %s: getUnseenHeaders' %self._name)
		if self._proto:
			self._proto.examine('inbox').addCallback(self._doSearchUnseen, callback).addErrback(self._ebNotify, "getUnseenHeaders", _("cannot access inbox"))
			return True
		else:
			return False

	def _doSearchUnseen(self, result, callback): #@UnusedVariable # pylint: disable-msg=W0613
		# debug('[EmailAccount] %s: _doSearchUnseen' %(self._name))
		self._proto.search(imap4.Query(unseen=1)).addCallback(callback).addErrback(self._ebNotify, '_doSearchUnseen', _("cannot get list of new messages"))

	def getMessageList(self, callback, mbox):
		if self._proto:
			self._proto.select(mbox.decode('utf-8')).addCallback(self._onSelect, callback).addErrback(self._onSelectFailed, callback, mbox)
			return True
		else:
			return False

	def _onSelect(self, result, callback):
		# debug("[EmailAccount] _onExamine: " + str(result))
		numMessagesinFolder = int(result['EXISTS'])
		if numMessagesinFolder <= 0:
			callback([], [])
		else:
			if int(self._maxmail) > 0:
				maxMessagesToFetch = int(self._maxmail)
				startmsg = numMessagesinFolder - maxMessagesToFetch + 1
				if startmsg <= 0:
					startmsg = 1
				rangeToFetch = [startmsg, numMessagesinFolder]
			else:
				rangeToFetch = [1, numMessagesinFolder]
			try:
				self._proto.fetchFlags('%i:%i' % (rangeToFetch[0], rangeToFetch[1])	#'1:*'
						   ).addCallback(self._onFlagsList, callback, rangeToFetch)

			except imap4.IllegalServerResponse as e:
				debug("[EmailAccount] _onExamine exception: " + str(e))
				callback([], [])

	def _onSelectFailed(self, failure, callback, mboxname):
		debug("[EmailAccount] %s: _onSelectFailed: %s %s" % (self._name, mboxname, str(failure)))
		callback([], [])

	def _onFlagsList(self, flagsList, callback, rangeToFetch):
		self._proto.fetchHeaders('%i:%i' % (rangeToFetch[0], rangeToFetch[1])	#'1:*'
				   ).addCallback(callback, flagsList)

	def getMessage(self, message, callback, errCallback):
		debug("[EmailAccount] %s: getMessage: %s" % (self._name, str(message)))
		if self._proto:
			self._proto.fetchSize(message.uid
				).addCallback(self._onMessageSizeLoaded, message, callback, errCallback 
				).addErrback(self._onMessageLoadFailed, message, errCallback
				)
			return True
		else:
			return False

	def _onMessageSizeLoaded(self, result, message, callback, errCallback):
		debug("[EmailAccount] %s: _onMessageSizeLoaded: %s %s" % (self._name, str(result), str(message)))
		size = int(result[message.uid]['RFC822.SIZE'])
		if size >= 4000000:
			#ask here to open message
			debug("[EmailAccount] _onMessageSizeLoaded: message to large to open (size=%d)" % size)
			errCallback('', _("message too large"))
		else:
			self._proto.fetchMessage(message.uid
				).addCallback(callback, message,
				).addErrback(self._onMessageLoadFailed, message, errCallback
				)

	def _onMessageLoadFailed(self, failure, message, errCallback):
		debug("[EmailAccount] %s: onMessageLoadFailed: %s %s" % (self._name, str(failure), str(message)))
		errCallback('', _("failed to load message") + ': ' + failure.getErrorMessage())

	def getHeaders(self, callback, messageSet):
		debug('[EmailAccount] %s: getHeaders' % self._name)
		if self._proto:
			self._proto.fetchHeaders(messageSet).addCallback(callback).addErrback(self._ebNotify, 'getHeaders', _("cannot get headers of new messages"))
			return True
		else:
			return False

	def onConnect(self, proto):
		debug("[EmailAccount] %s: %s@%s:%s: onConnect" % (self._name, self._user, self._server, self._port))
		self._factory.resetDelay()
		self._proto = proto
		self._failureReason = ""
		if self._connectCallback:
			self._connectCallback()
			self._connectCallback = None
		proto.getCapabilities().addCallback(self._cbCapabilities).addErrback(self._ebCapabilities)

	def onConnectionFailed(self, reason):
		debug("[EmailAccount] %s@%s:%s: onConnectFailed: %s" % (self._user, self._server, self._port, reason.getErrorMessage()))
		reasonString = reason.getErrorMessage()
		if reasonString != self._failureReason:
			self._ebNotify(reason, 'onConnectionFailed', _("connection failed - retrying") + '\n' + reason.getErrorMessage())
			self._failureReason = reasonString
		self._proto = None
		# don't retry, if we do not check this account
		if int(self._interval) == 0 and self._factory:
			self._factory.stopTrying()
		# self.stopChecker() not necessary, because we don't have an active connection...

	def onConnectionLost(self, reason):
		debug("[EmailAccount] %s@%s:%s: onConnectFailed: %s" % (self._user, self._server, self._port, reason.getErrorMessage()))
		# too noisy... self._ebNotify(reason, 'onConnectionLost', _("connection lost - retrying"))
		self._proto = None
		self.stopChecker()
		# don't retry, if we do not check this account
		if int(self._interval) == 0 and self._factory:
			self._factory.stopTrying()

	def _cbCapabilities(self, reason):
		debug(_("[EmailAccount] %(name)s: _cbCapabilities:\n\
####################################################################################################\n\
# If you have problems to log into your imap-server, please send me the output of the following line\n\
# cbCapabilities: %(capa)s\n\
####################################################################################################\n")
			% {'name':self._name, 'capa':str(reason)})
		self._doLogin()

	def _ebCapabilities(self, reason):
		debug("[EmailAccount] %s: _ebCapabilities: %s" % (self._name, str(reason)))

	def _doLogin(self):
		debug("[EmailAccount] %s: _doLogin secure" % (self._name))
		d = self._proto.authenticate(self._password)
		d.addCallback(self._onAuthentication)
		d.addErrback(self._onAuthenticationFailed)
		return d

	def _onAuthentication(self, result):
		# better use LSUB here to get only the subscribed to mailboxes
		debug("[EmailAccount] %s: _onAuthentication: %s" % (self._name, str(result)))
		self.startChecker()
		self.getMailboxList()
		
	def getMailboxList(self):
		if self._listall:
			debug("[EmailAccount] %s: getMailboxList list" % (self._name))
			self._proto.list("", "*").addCallback(self._onMailboxList)
		else:
			debug("[EmailAccount] %s: getMailboxList lsub" % (self._name))
			self._proto.lsub("", "*").addCallback(self._onMailboxList)

	def _onAuthenticationFailed(self, failure):
		# If it failed because no SASL mechanisms match
		debug("[EmailAccount] %s: onAuthenticationFailed: %s" % (self._name, failure.getErrorMessage()))
		try:
			failure.trap(imap4.NoSupportedAuthentication)
			self._doLoginInsecure()
		except Exception as e:
			debug("[EmailAccount] %s: _onAuthenticationFailed: %s" % (self._name, e.message))
			print(e, e.message)

	def _doLoginInsecure(self):
		debug("[EmailAccount] %s: _doLoginInsecure" % (self._name))
		self._proto.login(self._user, self._password).addCallback(self._onAuthentication).addErrback(self._onInsecureAuthenticationFailed)

	def _onInsecureAuthenticationFailed(self, failure):
		debug("[EmailAccount] %s: _onInsecureAuthenticationFailed: %s" % (self._name, failure.getErrorMessage()))
		self._proto = None
		#=======================================================================
		# Notifications.AddNotification(
		#	MessageBox,
		#	_("error logging %(who)s in:\n%(failure)s")
		#		%{
		#		'who':"%s@%s" %(self._user, self._server),
		#		'failure':failure.getErrorMessage()
		#		}, type=MessageBox.TYPE_ERROR, timeout=config.plugins.emailimap.timeout.value)
		#=======================================================================
		self._ebNotify(failure, "_onInsecureAuthenticationFailed",
					_("error logging %(who)s in:\n%(failure)s")
					% {
					'who':"%s@%s" % (self._user, self._server),
					'failure':failure.getErrorMessage()
					})

	def _onMailboxList(self, result):
		mylist = [UTF7toUTF8(mb[2]).encode('utf-8') for mb in result if '\\Noselect' not in mb[0]]
		debug("[EmailAccount] %s: onMailboxList: %s selectable mailboxes" % (self._name, len(mylist)))
		# debug("[EmailAccount] %s: onMailboxList:\n%s" %(self._name, str(mylist)))
		mylist.sort()
		try:
			self.inboxPos = map(lambda x: x.lower(), mylist).index('inbox') + 1
		except ValueError:
			debug("[EmailAccount] onMailboxList: no inbox?!?!")
			mylist = ['INBOX']
			self.inboxPos = 1
		self.mailboxList = mylist

class EmailAccountList(Screen):
	# pylint: disable-msg=W0212
	def __init__(self, session):
		'''
		Entry screen holding the list of accounts.
		Offering to add, edit or remove one. Also configuration through <menu> 
		'''
		debug("[EmailAccountList] __init__")
		noButtons = 3
		width = max(noButtons * 140 + 35 + 100, DESKTOP_WIDTH / 3)
		self.width = width
		height = max(5 * 30 + 50, DESKTOP_HEIGHT / 3)
		buttonsGap = (width - (noButtons) * 140 - 35) / (noButtons + 2)
		self.skin = """
			<screen position="%d,%d" size="%d,%d" title="Accounts list" >
			<widget name="accounts" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" 	size="35,25" pixmap="skin_default/buttons/key_menu.png" 	alphatest="on" />
			<widget name="buttonred" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="buttongreen" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="buttonyellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
						(DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, width, height,
						width, height,  # config
						buttonsGap, height - 45,
						2 * buttonsGap + 140, height - 45,
						3 * buttonsGap + 2 * 140, height - 45,
						4 * buttonsGap + 3 * 140, height - 38,
						buttonsGap, height - 45, scaleV(22, 18),
						2 * buttonsGap + 140, height - 45, scaleV(22, 18),
						3 * buttonsGap + 2 * 140, height - 45, scaleV(22, 18)
						)
		Screen.__init__(self, session)
		self["buttonred"] = Label(_("remove"))
		self["buttongreen"] = Label(_("add"))
		self["buttonyellow"] = Label(_("edit"))
		self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "MenuActions"],
		{
			"menu": self._config,
			"red": self._remove,
			"green": self._add,
			"yellow": self._edit,
			"cancel": self._exit,
			"ok": self._action,
		}, -2)
		for acc in mailAccounts:
			if not acc.isConnected():
				acc.forceRetry(self._layoutFinish)
		self["accounts"] = MenuList([], content=eListboxPythonMultiContent)
		self["accounts"].l.setItemHeight(scaleV(20, 18) + 5)
		self["accounts"].l.setFont(0, gFont("Regular", scaleV(20, 18)))
		self.onLayoutFinish.append(self._layoutFinish)

	def _layoutFinish(self):
		self.setTitle(_("Accounts list"))
		accList = []
		for acc in mailAccounts:
			if acc.isConnected():
				color = 0x00FFFFFF
			else:
				color = 0x00888888
			accList.append([acc, MultiContentEntryText(pos=(0, 0), size=(self.width, scaleV(20, 18) + 5), text=acc._name, color=color, color_sel=color)])
		self["accounts"].l.setList(accList)

	def _config(self):
		debug("[EmailAccountList] _config")
		self.session.open(EmailConfigOptions, "Rev " + "$Revision$"[11: - 1] + "$Date$"[7:23])

	def _action(self):
		if self["accounts"].getCurrent():
			debug("[EmailAccountList] _action: %s" % self["accounts"].getCurrent()[0]._name)
			account = self["accounts"].getCurrent()[0]
			if account and account.isConnected():
				self.session.open(EmailScreen, account)
				self._layoutFinish()
			else:
				self.session.open(MessageBox,
								_("account %s is not connected") % self["accounts"].getCurrent()[0]._name,
								type=MessageBox.TYPE_INFO,
								timeout=config.plugins.emailimap.timeout.value)
		else:
			debug("[EmailAccountList] _action: no account selected")
			self.session.open(MessageBox,
							_("no account selected"),
							type=MessageBox.TYPE_ERROR,
							timeout=config.plugins.emailimap.timeout.value)

	def _add(self):
		debug("[EmailAccountList] _add")
		self.session.openWithCallback(self._cbAdd, EmailConfigAccount)

	def _cbAdd(self, params):
		if params:
			# TODO: encrypt passwd
			EmailAccount(params, writeAccounts)
		self.close()

	def _edit(self):
		debug("[EmailAccountList] _edit")
		if self["accounts"].getCurrent():
			self.session.openWithCallback(self._cbEdit, EmailConfigAccount, self["accounts"].getCurrent()[0].getConfig())
		else:
			self.session.openWithCallback(self._cbAdd, EmailConfigAccount)

	def _cbEdit(self, params):
		if params:
			self["accounts"].getCurrent()[0].exit()
			# TODO: encrypt passwd
			EmailAccount(params, writeAccounts)
		self.close()
		
	def _remove(self):
		debug("[EmailAccountList] _remove")
		if self["accounts"].getCurrent():
			self.session.openWithCallback(
				self._cbRemove,
				MessageBox,
				_("Really delete account %s?") % self["accounts"].getCurrent()[0]._name)
		else:
			self.session.open(MessageBox,
							_("no account selected"),
							type=MessageBox.TYPE_ERROR,
							timeout=config.plugins.emailimap.timeout.value)

	def _cbRemove(self, ret):
		if ret:
			self["accounts"].getCurrent()[0].exit()
			writeAccounts()
		self._layoutFinish()

	def _exit(self):
		for acc in mailAccounts:
			acc.removeCallback()
		self.close()

from Tools.Directories import resolveFilename, SCOPE_SYSETC, SCOPE_CONFIG, SCOPE_PLUGINS
import csv

from six.moves import reduce


MAILCONF = resolveFilename(SCOPE_CONFIG, "EmailClient.csv")

#
# we need versioning on the config data
#
CONFIG_VERSION = 1
def writeAccounts():
	fd = open(MAILCONF, 'w')
	fd.write(str(CONFIG_VERSION) + '\n')
	out = csv.writer(fd, quotechar='"', lineterminator='\n')
	for acc in mailAccounts:
		out.writerow(acc.getConfig())
	fd.close()

def getAccounts():
	debug("[] getAccounts")

	if not os.path.exists(MAILCONF):
		fMAILCONF_XML = resolveFilename(SCOPE_SYSETC, "mailconf.xml")
		debug("[] getAccounts: check for %s" % fMAILCONF_XML)
		if os.path.exists(fMAILCONF_XML):
			from xml.dom.minidom import parse
			Notifications.AddNotification(MessageBox, _("importing configurations from %s") % fMAILCONF_XML, type=MessageBox.TYPE_INFO, timeout=config.plugins.emailimap.timeout.value)
			maildom = parse(fMAILCONF_XML)
			for top in maildom.getElementsByTagName("list"):
				for acc in top.getElementsByTagName("account"):
					name = str(acc.getElementsByTagName("name")[0].childNodes[0].data)
					server = str(acc.getElementsByTagName("server")[0].childNodes[0].data)
					port = str(acc.getElementsByTagName("port")[0].childNodes[0].data)
					user = str(acc.getElementsByTagName("user")[0].childNodes[0].data)
					password = str(acc.getElementsByTagName("pass")[0].childNodes[0].data)
					interval = str(acc.getElementsByTagName("interval")[0].childNodes[0].data)
					maxmail = str(acc.getElementsByTagName("MaxMail")[0].childNodes[0].data)
					debug("[EmailClient] - Autostart: import account %s" % acc(name, server, port, user, password, interval, maxmail))
					EmailAccount((name, server, port, user, password, interval, maxmail, 0))
		else:
			debug("[] getAccounts: no file found, exiting")
	else:
		debug("[] getAccounts: reading %s" % MAILCONF)
		fd = open(MAILCONF)
		accounts = csv.reader(fd, quotechar='"')
		version = 0
		for acc in accounts:
			if len(acc) == 1:
				version = int(acc[0])
				continue
			debug("[EmailClient] - Autostart: add account %s" % acc[0])
			if version == 0:
				# add listall param at the end to get version 1
				(name, server, port, user, password, interval, maxmail) = acc
				acc = (name, server, port, user, password, interval, maxmail, 0)
			EmailAccount(acc)
		fd.close()
		if version != CONFIG_VERSION:
			writeAccounts()

def main(session, **kwargs): #@UnusedVariable kwargs # pylint: disable-msg=W0613
	session.open(EmailAccountList)

def autostart(reason, **kwargs): #@UnusedVariable reason
	debug("[EmailClient] - Autostart reason: %d kwargs: %s" % (reason, repr(kwargs)))
	debug("[EmailClient] " + "$Revision$"[1:-1] + "$Date$"[7:23] + " starting")
	import shutil
	if os.path.isdir('/usr/lib/python2.6') and not os.path.isfile('/usr/lib/python2.6/uu.pyo'):
		shutil.copy(resolveFilename(SCOPE_PLUGINS, "Extensions/EmailClient/uu.pyo"), '/usr/lib/python2.6/uu.pyo')
	elif os.path.isdir('/usr/lib/python2.5') and not os.path.isfile('/usr/lib/python2.5/uu.py'):
		shutil.copy(resolveFilename(SCOPE_PLUGINS, "Extensions/EmailClient/uu.pyo"), '/usr/lib/python2.5/uu.pyo')

	if reason == 0:
		getAccounts()
	else:
		for acc in mailAccounts:
			acc.exit()

initLog()

def Plugins(path, **kwargs): #@UnusedVariable kwargs # pylint: disable-msg=W0613,C0103
	return [
			 PluginDescriptor(name=_("Email Client"), description=_("view Emails via IMAP4"),
			 where=PluginDescriptor.WHERE_PLUGINMENU,
			 fnc=main,
			 icon="plugin.png"
			 ),
			 PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)
		]
