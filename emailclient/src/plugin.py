from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap, MovingPixmap
from Components.ScrollLabel import ScrollLabel
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText
from EmailConfig import EmailConfigScreen
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from enigma import eListboxPythonMultiContent, eListbox, gFont
from twisted.mail import imap4
from zope.interface import implements
import email
import email.Parser
from TagStrip import TagStrip
import protocol
import uu





config.plugins.emailimap = ConfigSubsection()
config.plugins.emailimap.username = ConfigText("user", fixed_size=False)
config.plugins.emailimap.password = ConfigText("password", fixed_size=False)
config.plugins.emailimap.server = ConfigText("please.config.first", fixed_size=False)
config.plugins.emailimap.port = ConfigInteger(143, limits = (1, 65536))

# 0= fetch all header , 10= fetch only the last 10 headers/messages of a mailbox
config.plugins.emailimap.maxheadertoload = ConfigInteger(0, limits = (1, 100)) 

class EmailHandler:
    def __init__(self):
        pass
    def onConnect(self, proto):
        pass

class EmailScreen(Screen, EmailHandler):
    implements(imap4.IMailboxListener)
    
    skin = """
        <screen position="110,83" size="530,430" title="Email" >
            <widget name="boxlist" position="0,0" size="150,400" scrollbarMode="showOnDemand" />            
            <widget name="messagelist" position="150,0" size="380,400" scrollbarMode="showOnDemand" />            
            <widget name="infolabel" position="0,400" size="530,30"   foregroundColor=\"white\" font=\"Regular;18\" />           
        </screen>"""
         
    currentmailbox = None
    proto = None
    
    def __init__(self, session, args = 0):
        EmailHandler.__init__(self)
        self.session = session
        
        self.skin = EmailScreen.skin
        Screen.__init__(self, session)
        protocol.createFactory(self, config.plugins.emailimap.username.value, config.plugins.emailimap.server.value, config.plugins.emailimap.port.value)

        self["actions"] = ActionMap(["InfobarChannelSelection", "WizardActions", "DirectionActions", "MenuActions", "ShortcutActions", "GlobalActions", "HelpActions", "NumberActions"], 
            {
             "ok": self.action_ok, 
             "back": self.action_exit, 
             "historyNext": self.selectMessagelist, 
             "historyBack": self.selectBoxlist, 
             "down":        self.down, 
             "up":          self.up, 
             "left":        self.left, 
             "right":       self.right, 
             "menu":        self.action_menu, 
             }, -1)
        self["boxlist"] = MenuList([])
        self["messagelist"] = MailList([])
        self["infolabel"] = Label("")
        self.onLayoutFinish.append(self.selectBoxlist)
        
    def action_menu(self):
        self.session.open(EmailConfigScreen)
        
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
            self.proto.examine(UTF7toUTF8(c[1][2])
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
        
#    def fetchBodyStructure(self, message):
#        print "fetchBodyStructure",message
#        self.proto.fetchBodyStructure(message.uid
#            ).addCallback(self.onBodystructureLoaded, message, self.proto
#            ).addErrback(self.onMessageLoadFailed, message, self.proto
#            )
    
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
        self.session.open(ScreenMailView, msg)
            
    def onMessageLoadFailed(self, failure, message, proto):
        print "onMessageLoadFailed", failure, message
        self["infolabel"].setText(failure.getErrorMessage())

    def action_exit(self):
        if self.proto is not None:
            self.proto.logout(
                            ).addCallback(self.onLogedOut, self.proto
                ).addErrback(self.onLogedOut, self.proto
                            )
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
        print "cbCapabilities",reason
        
        self.doLogin(proto)

    def ebCapabilities(reason,proto):
        print "ebCapabilities",reason
        
    def onConnectFailed(self, reason):
        self["infolabel"].setText(reason.getErrorMessage())

    def onAuthentication(self, result, proto):
        self.proto = proto
        self["infolabel"].setText("logged in")
        proto.list("", "*"
        ).addCallback(self.onMailboxList, proto
        )
        
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
        for i in result:
            flags, hierarchy_delimiter, name = i
            list.append((UTF7toUTF8(name).encode('utf-8'), i))
        self["boxlist"].l.setList(list) 
        
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
#                proto.fetchEnvelope('%i:%i'%(rangeToFetch[0], rangeToFetch[1])    #'1:*'
#                           ).addCallback(self.onEnvelopeList, proto
#                           )
                proto.fetchHeaders('%i:%i'%(rangeToFetch[0], rangeToFetch[1])    #'1:*'
                           ).addCallback(self.onHeaderList, proto
                           )

            except imap4.IllegalServerResponse, e:
                print e
                
    def onExamineFailed(self, failure, proto):
        print "onExamineFailed", failure, proto
        self["infolabel"].setText(failure.getErrorMessage())

    def onHeaderList(self, result, proto):
        print "onHeaderList"#,result,proto
        self["infolabel"].setText("headers loaded, now parsing ...")
        list = []
        for m in result:
            try:
                list.append(self.buildMessageListItem(MessageHeader(m, result[m]['RFC822.HEADER'])))
            except Exception,e:
                print e
        list.reverse()
        self["messagelist"].l.setList(list) 
        self["infolabel"].setText("have "+str(len(result))+" messages ")
            
    def buildMessageListItem(self, message):
        res = [ message ]
        res.append(MultiContentEntryText(pos=(5, 0), size=(380, 19), font=0, text=message.getSenderString()))
        res.append(MultiContentEntryText(pos=(5, 19), size=(380, 19), font=0, text=message.get('date', default='kein Datum')))
        res.append(MultiContentEntryText(pos=(5, 38), size=(380, 19), font=0, text=message.getSubject()))
        return res  
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
    def __init__(self, session, email, args = 0):
        self.session = session
        self.email = email
        self.skin = "<screen position=\"85,80\" size=\"550,476\" title=\"view Email\" >"
        self.skin +=  """<widget name="from" position="0,0" size="550,25"  font="Regular;20" />
            <widget name="date" position="0,25" size="550,25"  font="Regular;20" />
            <widget name="subject" position="0,50" size="550,25"  font="Regular;20" />
            <widget name="body" position="0,75" size="550,375"  font="Regular;20" />
            <widget name="buttonred" position="10,436" size="100,30" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;16"/> 
            <widget name="buttongreen" position="120,436" size="100,30" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;16"/> 
            <widget name="buttonyellow" position="230,436" size="100,30" backgroundColor="yellow" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;16"/> 
            <widget name="buttonblue" position="340,436" size="100,30" backgroundColor="blue" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;16"/>            
        </screen>""" 
        Screen.__init__(self, session)
        self["from"] = Label(_("From: %s" %self.email.get('from', 'no-from')))
        self["date"] = Label(_("Date: %s" %self.email.get('date', 'no-date')))
        self["subject"] = Label(_(self.email.get('subject', 'no-subject')))
        self["body"] = ScrollLabel(_(self.email.messagebodys[0].getData()))
        self["buttonred"] = Label("")
        self["buttongreen"] = Label("")
        self["buttonyellow"] =  Label("Headers")
        self["buttonblue"] =  Label(_("delete"))
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions", "ShortcutActions"], 
            {
             "back": self.close, 
             "up": self["body"].pageUp, 
             "down": self["body"].pageDown, 
             "left": self["body"].pageUp, 
             "right": self["body"].pageDown, 
             "red": self.selectBody, 
             "green": self.selectAttachment, 
             "yellow": self.openMessagesHeaders, 
             "blue": self.delete, 
             
             }, -1)
        self.onLayoutFinish.append(self.updateButtons)
        
    def delete(self):
        pass #self.session.openWithCallback(self.deleteCB, ChoiceBox, title="really delete Mail?", list=[(_("yes"), True),(_("no"), False)])

    def deleteCB(self, returnValue):
        if returnValue[1] is True:
            pass
        
    def openMessagesHeaders(self):
        pass #self.session.open(ScreenMailViewHeader,self.profil,self.email)
                   
    def updateButtons(self):
        self["buttonred"].setText(_("Bodys"))
        if len(self.email.attachments):
            self["buttongreen"].setText("Attachments")
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
                list.append((a.getFilename(), a))
            self.session.openWithCallback(self.selectAttachmentCB, ChoiceBox, _("select Attachment"), list)
            
    def selectAttachmentCB(self, choice):
        if choice is not None:
            print "Attachment selected", choice[1].getFilename()
            #showMessageBox(self.session)
    
class MailList(MenuList, HTMLComponent, GUIComponent):
    def __init__(self, list):
        MenuList.__init__(self, list)
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.list = list
        self.l.setList(list)
        self.l.setFont(0, gFont("Regular", 18))
        self.l.setFont(1, gFont("Regular", 20))
        
    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        instance.setItemHeight(60)

class MessageHeader(object):        
    def __init__(self, uid, message):
        self.uid = uid #must be int
        self.message = email.Parser.Parser().parsestr(message)
        
    def getSenderString(self):
        if self.get("from") is None:
            return "no sender"
        else:
            return self.get("from")
        
    def getSubject(self):
        if self.get("subject") is None:
            return "no subject"
            """
        # need some decoding for subjects like =?iso-8859-1?Q?=DCbermut?=
        elif self.get("subject").startswith("=?") and self.get("subject").endswith("?="):
            c = self.get("subject").split("?")
            print c
            codec = c[1]
            text = "?".join(c[3:])
            
            
            print "CODEC",codec
            print "TEXT",text
            return text.decode(codec).encode("utf-8")
            """
        else:
            return self.get("subject")
            
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
        if self.getEncoding() is not None:
            print "decoding text with charset ",self.getEncoding()
            text = text.decode(self.getEncoding())            
        if self.getContenttype() == "text/html":
            print "stripping html"
            text = TagStrip().strip_readable(text)
        try:
            return text.encode('utf-8')
        except Exception,e:
            print e
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
    session.open(EmailScreen)    

def Plugins(path, **kwargs):
    global plugin_path
    plugin_path = path
    return [
             PluginDescriptor(name="Email Client", description="view Emails via IMAP4", 
             where = PluginDescriptor.WHERE_PLUGINMENU, 
             fnc = main,
             icon="plugin.png"
             ), 
             #PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = startScrobbler)
        ]
