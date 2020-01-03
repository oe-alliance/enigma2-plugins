# -*- coding: utf-8 -*-
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""IRC support for Instance Messenger."""

import string

from protocols import irc
from twisted.internet import defer, reactor, protocol
from twisted.internet.defer import succeed
import e2support, interfaces,dreamIRCTools
from zope.interface import implements

class IRCPerson(e2support.AbstractPerson):

    def imperson_whois(self):
        if self.account.client is None:
            return 0
        self.account.client.sendLine("WHOIS %s" % self.name)

    ### interface impl

    def isOnline(self):
        return ONLINE

    def getStatus(self):
        return ONLINE

    def setStatus(self,status):
        self.status=status
        self.chat.getContactsList().setContactStatus(self)

    def sendMessage(self, text, meta=None):
        if self.account.client is None:
            return 0
        for line in string.split(text, '\n'):
            if meta and meta.get("style", None) == "emote":
                self.account.client.ctcpMakeQuery(self.name,[('ACTION', line)])
            else:
                self.account.client.msg(self.name, line)
        return succeed(text)

    def bye(self):
        if self.account.client is None:
            print "not connected"
        else:
        	  self.account.client.quit("user logged off")    	  


class IRCGroup(e2support.AbstractGroup):

    implements(interfaces.IGroup)

    def imgroup_testAction(self):
        print 'action test!'

    def imtarget_kick(self, target):
        if self.account.client is None:
            return 0
        reason = "... and justice for all!"
        self.account.client.sendLine("KICK #%s %s :%s" % (
            self.name, target.name, reason))

    ### Interface Implementation

    def setTopic(self, topic):
        if self.account.client is None:
            return 0
        self.account.client.topic(self.name, topic)

    def sendGroupMessage(self, text, meta={}):
        if self.account.client is None:
            return 0
        if meta and meta.get("style", None) == "emote":
            self.account.client.me(self.name,text)
            return succeed(text)
        #standard shmandard, clients don't support plain escaped newlines!
        for line in string.split(text, '\n'):
            self.account.client.say(self.name, line)
        return succeed(text)

    def leave(self):
        if self.account.client is None:
            return 0
        self.account.client.leave(self.name)
        self.account.client.getGroupConversation(self.name,1)
        
    def bye(self):
        if self.account.client is None:
            print "not connected"
        else:
        	self.account.client.quit("user logged off")    	  


class IRCProto(e2support.AbstractClientMixin, irc.IRCClient):
    def __init__(self, account, chatui, logonDeferred=None):
        e2support.AbstractClientMixin.__init__(self, account, chatui,
                                                 logonDeferred)
        self._namreplies={}
        self._ingroups={}
        self._groups={}
        self._topics={}
        self.pipe = dreamIRCTools.MessagePipe()

    def getGroupConversation(self, name, hide=0):
        name=string.lower(name)
        return self.chat.getGroupConversation(self.chat.getGroup(name, self),
                                              stayHidden=hide)

    def getPerson(self,name):
        return self.chat.getPerson(name, self)

    def connectionMade(self):
        # XXX: Why do I duplicate code in IRCClient.register?
        try:
            print 'connection made on irc service!?', self
            self.pipe.debug("connection made on irc service!?")
            if self.account.password:
                self.sendLine("PASS :%s" % self.account.password)
            self.setNick(self.account.username)
            self.sendLine("USER %s foo bar :dreamIRC e2 v1.0 user" % (self.nickname))
            for channel in self.account.channels:
                self.pipe.debug("joining channel: %s" % channel)
                self.joinGroup(channel)
            self.account._isOnline=1
            self.pipe.debug("uh, registering irc acct")
            if self._logonDeferred is not None:
                self._logonDeferred.callback(self)
            self.chat.getContactsList()
        except:
            import traceback
            traceback.print_exc()

    def setNick(self,nick):
        self.name=nick
        self.accountName="%s (IRC)"%nick
        irc.IRCClient.setNick(self,nick)
        
    def quit(self,message='bye bye'):
#         self.quit_str=str("QUIT :%s" % message)
         self.sendLine("QUIT :%s" % message)

    def kickedFrom(self, channel, kicker, message):
        """Called when I am kicked from a channel.
        """
        self.pipe.debug('wow i was kicked form %s by %s cause of %s' %  (channel, kicker, message))
        return self.chat.getGroupConversation(
            self.chat.getGroup(channel[1:], self), 1)

    def userKicked(self, kickee, channel, kicker, message):
        self.pipe.debug('whew somebody else %s %s %s %s' % (kickee, channel, kicker, message))

    def noticed(self, username, channel, message):
        self.privmsg(username, channel, message, {"dontAutoRespond": 1})

    def privmsg(self, username, channel, message, metadata=None):
        if metadata is None:
            metadata = {}
        username=string.split(username,'!',1)[0]
        if username==self.name: return
        if channel[0]=='#':
            group=channel[1:]
            self.getGroupConversation(group).showGroupMessage(username, message, metadata)
            return
        self.chat.getConversation(self.getPerson(username)).showMessage(message, metadata)

    def action(self,username,channel,emote):
        username=string.split(username,'!',1)[0]
        if username==self.name: return
        meta={'style':'emote'}
        if channel[0]=='#':
            group=channel[1:]
            self.getGroupConversation(group).showGroupMessage(username, emote, meta)
            return
        self.chat.getConversation(self.getPerson(username)).showMessage(emote,meta)

    def irc_RPL_NAMREPLY(self,prefix,params):
        """
        RPL_NAMREPLY
        >> NAMES #bnl
        << :Arlington.VA.US.Undernet.Org 353 z3p = #bnl :pSwede Dan-- SkOyg AG
        """
        group=string.lower(params[2][1:])
        users=string.split(params[3])
        for ui in range(len(users)):
            while users[ui][0] in ["@","+"]: # channel modes
                users[ui]=users[ui][1:]
        if not self._namreplies.has_key(group):
            self._namreplies[group]=[]
        self._namreplies[group].extend(users)
        for nickname in users:
                try:
                    self._ingroups[nickname].append(group)
                except:
                    self._ingroups[nickname]=[group]

    def irc_RPL_ENDOFNAMES(self,prefix,params):
        group=params[1][1:]
        self.getGroupConversation(group).setGroupMembers(self._namreplies[string.lower(group)])
        del self._namreplies[string.lower(group)]

    def irc_RPL_TOPIC(self,prefix,params):
        self._topics[params[1][1:]]=params[2]

    def irc_333(self,prefix,params):
        group=params[1][1:]
        self.getGroupConversation(group).setTopic(self._topics[group],params[2])
        del self._topics[group]

    def irc_TOPIC(self,prefix,params):
        nickname = string.split(prefix,"!")[0]
        group = params[0][1:]
        topic = params[1]
        self.getGroupConversation(group).setTopic(topic,nickname)

    def irc_JOIN(self,prefix,params):
        nickname=string.split(prefix,"!")[0]
        group=string.lower(params[0][1:])
        if nickname!=self.nickname:
            try:
                self._ingroups[nickname].append(group)
            except:
                self._ingroups[nickname]=[group]
            self.getGroupConversation(group).memberJoined(nickname)

    def irc_PART(self,prefix,params):
        nickname=string.split(prefix,"!")[0]
        group=string.lower(params[0][1:])
        if nickname!=self.nickname:
            if group in self._ingroups[nickname]:
                self._ingroups[nickname].remove(group)
                self.getGroupConversation(group).memberLeft(nickname)
            else:
                self.pipe.debug("%s left %s, but wasn't in the room."%(nickname,group))

    def irc_QUIT(self,prefix,params):
        nickname=string.split(prefix,"!")[0]
        if self._ingroups.has_key(nickname):
            for group in self._ingroups[nickname]:
                self.getGroupConversation(group).memberLeft(nickname)
            self._ingroups[nickname]=[]
        else:
            self.pipe.debug('*** WARNING: ingroups had no such key %s' % nickname)

    def irc_NICK(self, prefix, params):
        fromNick = string.split(prefix, "!")[0]
        toNick = params[0]
        if not self._ingroups.has_key(fromNick):
            self.pipe.debug("%s changed nick to %s. But she's not in any groups!?" % (fromNick, toNick))
            return
        for group in self._ingroups[fromNick]:
            self.getGroupConversation(group).memberChangedNick(fromNick, toNick)
        self._ingroups[toNick] = self._ingroups[fromNick]
        del self._ingroups[fromNick]

    def irc_unknown(self, prefix, command, params):
        self.pipe.debug("unknown message from IRCserver. prefix: %s, command: %s, params: %s" % (prefix, command, params))

    # GTKIM calls
    def joinGroup(self,name):
        self.join(name)
        self.getGroupConversation(name)

class IRCAccount(e2support.AbstractAccount):
    implements(interfaces.IAccount)
    gatewayType = "IRC"

    _groupFactory = IRCGroup
    _personFactory = IRCPerson

    def __init__(self, accountName, autoLogin, username, password, host, port, channels=''):
        e2support.AbstractAccount.__init__(self, accountName, autoLogin, username, password, host, port)
        self.channels = map(string.strip,string.split(channels,','))
        if self.channels == ['']:
            self.channels = []

    def _startLogOn(self, chatui):
        logonDeferred = defer.Deferred()
        cc = protocol.ClientCreator(reactor, IRCProto, self, chatui, logonDeferred)
        d = cc.connectTCP(self.host, self.port)
        d.addErrback(logonDeferred.errback)
        return logonDeferred
        
