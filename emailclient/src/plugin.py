from Screens.Screen import Screen
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Screens.ChoiceBox import ChoiceBox
from Components.MenuList import MenuList
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox,gFont
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText
from Plugins.Plugin import PluginDescriptor

from EmailConfig import EmailConfigScreen

from twisted.mail import imap4
from zope.interface import implements
import uu
import email

import protocol


config.plugins.emailimap = ConfigSubsection()
config.plugins.emailimap.username = ConfigText("user",fixed_size=False)
config.plugins.emailimap.password = ConfigText("password",fixed_size=False)
config.plugins.emailimap.server = ConfigText("please.config.first",fixed_size=False)
config.plugins.emailimap.port = ConfigInteger(143,limits = (1, 65536))

# 0= fetch all header , 10= fetch only the last 10 headers/messages of a mailbox
config.plugins.emailimap.maxheadertoload = ConfigInteger(0,limits = (1, 100)) 

class EmailHandler:
    def __init__(self):
        pass
    def onConnect(self,proto):
        pass

class EmailScreen(Screen,EmailHandler):
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
        protocol.createFactory(self,config.plugins.emailimap.username.value,config.plugins.emailimap.server.value,config.plugins.emailimap.port.value)

        self["actions"] = ActionMap(["InfobarChannelSelection","WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions","NumberActions"], 
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
                               ).addCallback(self.onExamine,c[0] ,self.proto
                              ).addErrback(self.onExamineFailed, self.proto
                              )
    
    def onMessageSelected(self):
        c = self["messagelist"].getCurrent()
        if c is not None:
            self.fetchMessageSize(c[0])
            
    def fetchMessageSize(self,message):
        self.proto.fetchSize(message.get("uid")
            ).addCallback(self.onMessageSizeLoaded,message, self.proto
            ).addErrback(self.onMessageLoadFailed,message.get("uid"), self.proto
            )
            
    def onMessageSizeLoaded(self,result,message,proto):
        print "onMessageSizeLoaded",result,message
        size = int(result[message.get("uid")]['RFC822.SIZE'])
        self.MAX_MESSAGE_SIZE_TO_OPEN = 5667555
        if size >= self.MAX_MESSAGE_SIZE_TO_OPEN:
            #ask here to open message
            print "message to large to open (size=",size,")"
        else:
            self.loadMessage(message)
        
    def fetchBodyStructure(self,message):
        self.proto.fetchBodyStructure(message.get("uid")
            ).addCallback(self.onBodystructureLoaded,message, self.proto
            ).addErrback(self.onMessageLoadFailed,message.get("uid"), self.proto
            )
    
    def loadMessage(self,message):
        self["infolabel"].setText("loading message")
        
        self.proto.fetchMessage(message.get("uid")
            ).addCallback(self.onMessageLoaded,message, self.proto
            ).addErrback(self.onMessageLoadFailed,message.get("uid"), self.proto
            )
    
    def onMessageLoaded(self,result,message,proto):
        self["infolabel"].setText("parsing message")
        print "onMessageLoaded"#,result,message
        msgstr = result[message.get("uid")]['RFC822']
        import email.Parser
        msg = email.Parser.Parser().parsestr(msgstr)
        msg.messagebodys = []
        msg.attachments = []
        
        if msg.is_multipart():
            partCounter=1
            for part in msg.walk():
                if part.get_content_maintype()=="multipart":
                    continue
                print "+"*30
                print "filename",part.get_filename()
                print "part.get_content_maintype() ", part.get_content_maintype()
                print "part.get_subtype()",part.get_content_subtype()
                if part.get_content_maintype() == 'text' and part.get_filename() is None:
                    if part.get_content_subtype() == "html":
                        msg.messagebodys.append(EmailBody(part.get_content_type(),part.get_payload(decode=True)))
                    elif part.get_content_subtype() == "plain":
                        msg.messagebodys.append(EmailBody(part.get_content_type(),part.get_payload(decode=True)))
                    else:
                        print "unkown content type= ",part.get_content_maintype(),"/",part.get_content_subtype()
                        
                else:
                     print "found Attachment with  ",part.get_content_type(),"and name",part.get_filename()
                     msg.attachments.append(EmailAttachment(part.get_filename(),part.get_content_type(),part.get_payload()))    
                partCounter+=1

        else:
            msg.messagebodys.append(EmailBody("text/plain",msg.get_payload(decode=True)))
        self.session.open(ScreenMailView,msg)
        
    def onBodystructureLoaded(self,result,message,proto):
        print "onBodystructureLoaded",result,message
        structures = result[message.get('uid')]['BODYSTRUCTURE']
        bodys = []
        if isinstance(structures[0],type([])):
            for struc in structures:
                print "#"*10
                if isinstance(struc,type([])):
                    if struc[0] != "boundary":
                        bodys.append(struc)
        else:
            print "#"*10
            bodys.append(structures)
        print "HAVE",len(bodys)," BODYPARTS"
            
    def onMessageLoadFailed(self,failure,uid,proto):
        print "onMessageLoadFailed",failure,uid
        self["infolabel"].setText(failure.getErrorMessage())
        

    def action_exit(self):
        if self.proto is not None:
            self.proto.logout(
                            ).addCallback(self.onLogedOut, self.proto
                            ).addErrback(self.onLogedOut, self.proto
                            )
        else:
            self.close()
    
    def onLogedOut(self,result,proto):
        print "onLogedOut",result
        self.close()
        
            
    def onConnect(self,proto):
        self["infolabel"].setText("connected")
        self.doLogin(proto)
        
    def onConnectFailed(self,reason):
        self["infolabel"].setText(reason.getErrorMessage())

    def onAuthentication(self,result,proto):
        self.proto = proto
        self["infolabel"].setText("logged in")
        proto.list("", "*"
        ).addCallback(self.onMailboxList, proto
        )
        
    def doLogin(self,proto):
        print "login secure"
        proto.authenticate(config.plugins.emailimap.password.value
                           ).addCallback(self.onAuthentication, proto
                           ).addErrback(self.onAuthenticationFailed, proto
                           )

    def onAuthenticationFailed(self,failure, proto):
        # If it failed because no SASL mechanisms match
        print "onAuthenticationFailed",failure, proto
        self["infolabel"].setText(failure.getErrorMessage())
        failure.trap(imap4.NoSupportedAuthentication)
        self.doLoginInsecure(proto)
    
    def doLoginInsecure(self,proto):
        print "login INSECURE"
        proto.login(config.plugins.emailimap.username.value, config.plugins.emailimap.password.value
                ).addCallback(self.onAuthentication, proto
                ).addErrback(self.onInsecureAuthenticationFailed, proto
                )
    
    def onInsecureAuthenticationFailed(self,failure,proto):
        print "onInsecureAuthenticationFailed",failure, proto
        self["infolabel"].setText(failure.getErrorMessage())
        
    def onMailboxList(self,result,proto):
        print "onMailboxList"#,result,proto
        list = []
        for i in result:
            flags,hierarchy_delimiter,name = i
            list.append((UTF7toUTF8(name).encode('utf-8'),i))
        self["boxlist"].l.setList(list) 
        
    def onExamine(self,result,mboxname,proto):
        print "onExamine", result,mboxname
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
                rangeToFetch = [startmsg,numMessagesinFolder]
            else:
                rangeToFetch = [1,numMessagesinFolder]
            self["infolabel"].setText("loading headers "+str(rangeToFetch[0])+"-"+str(rangeToFetch[1])+" of Box '"+mboxname+"'")
            
            try:
                proto.fetchEnvelope('%i:%i'%(rangeToFetch[0],rangeToFetch[1])    #'1:*'
                           ).addCallback(self.onHeaderList, proto
                           )
            except imap4.IllegalServerResponse,e:
                print e
                
    def onExamineFailed(self,failure,proto):
        print "onExamineFailed",failure, proto
        self["infolabel"].setText(failure.getErrorMessage())
        
    def onHeaderList(self,result,proto):
        print "onHeaderList"#,result,proto
        self["infolabel"].setText("headers loaded, now parsing ...")
        list = []
        for m in result:
            #print "#"*20
            x = Message(m,result[m])
            list.append(self.buildMessageListItem(x))
        list.reverse()
        self["messagelist"].l.setList(list) 
        self["infolabel"].setText("have "+str(len(result))+" messages ")
            
    def buildMessageListItem(self,message):
        res = [ message ]
        res.append(MultiContentEntryText(pos=(5, 0), size=(380, 19), font=0, text=message.getSenderString()))
        res.append(MultiContentEntryText(pos=(5,19),size=(380, 19), font=0,text=message.get('date',default='kein Datum')))
        res.append(MultiContentEntryText(pos=(5,38),size=(380, 19), font=0,text=message.get('subject',default='kein Betreff')))
        return res  
    #
    # IMailboxListener methods
    #
    def modeChanged(self, writeable):
        print "modeChanged",writeable

    def flagsChanged(self, newFlags):
        print "flagsChanged",newFlags

    def newMessages(self, exists, recent):
        print "newMessages", exists, recent
      
class ScreenMailView(Screen):
    skin=""
    def __init__(self, session,email, args = 0):
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
        self["from"] = Label(_("From: %s" %self.email.get('from','no-from')))
        self["date"] = Label(_("Date: %s" %self.email.get('date','no-date')))
        self["subject"] = Label(_(self.email.get('subject','no-subject')))
        self["body"] = ScrollLabel(_(self.email.messagebodys[0].getData()))
        self["buttonred"] = Label("")
        self["buttongreen"] = Label("")
        self["buttonyellow"] =  Label("Headers")
        self["buttonblue"] =  Label(_("delete"))
        self["actions"] = ActionMap(["WizardActions", "DirectionActions","MenuActions","ShortcutActions"], 
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

    def deleteCB(self,returnValue):
        if returnValue[1]is True:
            pass
        
    def openMessagesHeaders(self):
        pass #self.session.open(ScreenMailViewHeader,self.profil,self.email)
                   
    def updateButtons(self):
        if len(self.email.messagebodys)>=2:
            self["buttonred"].setText(_("Bodys"))
        else:
            self["buttonred"].setText("")  
        if len(self.email.attachments):
            self["buttongreen"].setText("Attachments")
        else:
            self["buttongreen"].setText("")  
    
    def selectBody(self):
        if len(self.email.messagebodys):
            list = []
            for a in self.email.messagebodys:
                list.append((a.getContenttype(),a))
            self.session.openWithCallback(self.selectBodyCB,ChoiceBox,_("select Body"),list)
            
    def selectBodyCB(self,choice):
        if choice is not None:
            self["body"].setText(choice[1].getData())
            
    def selectAttachment(self):
        if len(self.email.attachments):
            list = []
            for a in self.email.attachments:
                list.append((a.getFilename(),a))
            self.session.openWithCallback(self.selectAttachmentCB,ChoiceBox,_("select Attachment"),list)
            
    def selectAttachmentCB(self,choice):
        if choice is not None:
            print "Attachment selected",choice[1].getFilename()
            #showMessageBox(self.session)
    
class MailList(MenuList, HTMLComponent, GUIComponent):
    def __init__(self, list):
        MenuList.__init__(self,list)
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

class Message(object):        
    def __init__(self,uid,strraw):
        self.__setattr__("uid",uid)
        print "parsing message"
        try:
            _date, _subject, _from, _sender, _reply_to, _to, _cc, _bcc, _in_reply_to, _message_id = strraw['ENVELOPE']
            self.__setattr__("date",_date)
            if _subject is None:
                self.__setattr__("subject","kein Betreff")
            else:
                self.__setattr__("subject",_subject)
    
            self.__setattr__("from",_from[0])
            self.__setattr__("sender",_sender)
            self.__setattr__("reply_to",_reply_to)
            self.__setattr__("to",_to)
            self.__setattr__("cc",_cc)
            self.__setattr__("bcc",_bcc)
            self.__setattr__("in_reply_to",_in_reply_to)
            self.__setattr__("message_id",_message_id)
        except Exception,e:
            print e,strraw
        
    def getSenderString(self):
        if self.get("from") is None:
            return "no sender"
        else:
            if self.get("from")[0] is not None:
                sender = self.get("from")[0]
            else:
                sender = self.get("from")[2]+"@"+self.get("from")[3]
            return sender
        
    def get(self,key,default=None):
        try:
            return self.__getattribute__(key)    
        except:
            return default
    def __str__(self):
        return "Message "+self.subject
############
class EmailBody:
    def __init__(self,contenttype,data):
        self.contenttype = contenttype
        self.data = data
    def getData(self):
        return self.data 
    def getContenttype(self):
        return self.contenttype 
############
class EmailAttachment:
    def __init__(self,filename,contenttype,data):
        self.filename = filename
        self.contenttype = contenttype
        self.data = data
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

def main(session,**kwargs):
    session.open(EmailScreen)    

def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    return [
             PluginDescriptor(name="Email Client", description="view Emails via IMAP4", 
             where = PluginDescriptor.WHERE_PLUGINMENU,
             fnc = main
             ),
             #PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = startScrobbler)
        ]
