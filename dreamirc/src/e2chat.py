# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

#

"""Base classes for Instance Messenger clients."""
from __future__ import print_function
from __future__ import absolute_import
from enigma import *
from Screens.Screen import Screen

from Components.Pixmap import *
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ScrollLabel import ScrollLabel
from Components.GUIComponent import *
from Components.MenuList import MenuList
from Components.Input import Input
from Components.Label import Label
from Components.config import *
from Components.ConfigList import ConfigList
from Plugins.Plugin import PluginDescriptor
from Tools.NumericalTextInput import *
from Tools.Directories import *

from .locals import OFFLINE, ONLINE, AWAY
from . import dreamIRCTools
from enigma import *
from .dreamIRCTools import *
#from myScrollLabel import *
#from dreamIRCMainMenu import *


class ContactsList:
    """A GUI object that displays a contacts list"""

    def __init__(self, chatui):
        """
        @param chatui: ???
        @type chatui: L{ChatUI}
        """
        self.chatui = chatui
        self.contacts = {}
        self.onlineContacts = {}
        self.clients = []

    def setContactStatus(self, person):
        """Inform the user that a person's status has changed.

        @type person: L{Person<interfaces.IPerson>}
        """
        if person.name not in self.contacts:
            self.contacts[person.name] = person
        if person.name not in self.onlineContacts and \
            (person.status == ONLINE or person.status == AWAY):
            self.onlineContacts[person.name] = person
        if person.name in self.onlineContacts and \
           person.status == OFFLINE:
            del self.onlineContacts[person.name]

    def registerAccountClient(self, client):
        """Notify the user that an account client has been signed on to.

        @type client: L{Client<interfaces.IClient>}
        """
        if client not in self.clients:
            self.clients.append(client)

    def unregisterAccountClient(self, client):
        """Notify the user that an account client has been signed off
        or disconnected from.

        @type client: L{Client<interfaces.IClient>}
         """
        if client in self.clients:
            self.clients.remove(client)

    def contactChangedNick(self, person, newnick):
        oldname = person.name
        if oldname in self.contacts:
            del self.contacts[oldname]
            person.name = newnick
            self.contacts[newnick] = person
            if oldname in self.onlineContacts:
                del self.onlineContacts[oldname]
                self.onlineContacts[newnick] = person


class Conversation:
    """A GUI window of a conversation with a specific person"""

    def __init__(self, person, chatui):
        """
        @type person: L{Person<interfaces.IPerson>}
        @type chatui: L{ChatUI}
        """
        self.chatui = chatui
        self.person = person
        self.pipe = MessagePipe()
        self.timer = eTimer()
        self.timer.timeout.get().append(self.sendOutPipe)
        self.timer.start(100)

    def show(self):
        """Displays the ConversationWindow"""
 #       raise NotImplementedError("Subclasses must implement this method")

    def hide(self):
        """Hides the ConversationWindow"""
#        raise NotImplementedError("Subclasses must implement this method")

    def sendText(self, text):
        """Sends text to the person with whom the user is conversing.
        @returntype: L{Deferred<twisted.internet.defer.Deferred>}
        """
        self.person.sendMessage(text, None)
        self.pipe.add("%s" % text)
        self.pipe.clearOutText()

    def sendOutPipe(self):
        if len(str(self.pipe.getOutText())) > 0:
            if (self.pipe.getOutText() == "/QUIT"):
                self.pipe.debug("/quit detected....")
                self.pipe.clearOutText()
                self.person.bye()
            else:
                self.pipe.debug("sending chat : %s" % str(self.pipe.getOutText()))
                self.sendText(str(self.pipe.getOutText()))
                self.pipe.clearOutText()

    def showMessage(self, text, metadata=None):
        """Display a message sent from the person with whom she is conversing

        @type text: string
        @type metadata: dict
        """
        self.pipe.add("<%s> %s" % (self.person.name, text))

    def contactChangedNick(self, person, newnick):
        """Change a person's name.

        @type person: L{Person<interfaces.IPerson>}
        @type newnick: string
        """
        self.person.name = newnick
        self.pipe.add("-!- %s is now known as %s" % (person.name, newnick))

    def serverMsg(self, message):
        """Displays a serverMsg in the group conversation window

        @type message: string
        """
        self.pipe.add("-!- %s " % (message))


class GroupConversation:
    """A conversation with a group of people."""

    def __init__(self, group, chatui):
        """
        @type group: L{Group<interfaces.IGroup>}
        @param chatui: ???
        @type chatui: L{ChatUI}
        """
        self.chatui = chatui
        self.group = group
        self.members = []
        self.pipe = MessagePipe()
        self.timer = eTimer()
        self.timer.timeout.get().append(self.sendOutPipe)
        self.timer.start(100)

    def show(self):
        """Displays the GroupConversationWindow."""
#        raise NotImplementedError("Subclasses must implement this method")

    def hide(self):
        """Hides the GroupConversationWindow."""
#        raise NotImplementedError("Subclasses must implement this method")

    def sendText(self, text):
        """Sends text to the group.
        @type text: string
        @returntype: L{Deferred<twisted.internet.defer.Deferred>}
        """
        self.group.sendGroupMessage(text, None)
        self.pipe.add("%s" % text)
        self.pipe.clearOutText()

    def sendOutPipe(self):
        if len(str(self.pipe.getOutText())) > 0:
            if (self.pipe.getOutText() == "/QUIT"):
                self.pipe.debug("/quit detected....")
                self.pipe.clearOutText()
                self.group.bye()
            else:
                self.pipe.debug("sending group chat : %s" % str(self.pipe.getOutText()))
                self.sendText(str(self.pipe.getOutText()))
                self.pipe.clearOutText()

    def showGroupMessage(self, sender, text, metadata=None):
        """Displays to the user a message sent to this group from the given sender
        @type sender: string (XXX: Not Person?)
        @type text: string
        @type metadata: dict
        """
        self.pipe.add("<%s/%s> %s" % (sender, self.group.name, text))

    def setGroupMembers(self, members):
        """Sets the list of members in the group and displays it to the user
        """
        self.members = members
        self.refreshMemberList()

    def setTopic(self, topic, author):
        """Displays the topic (from the server) for the group conversation window

        @type topic: string
        @type author: string (XXX: Not Person?)
        """
        self.pipe.add("-!- %s set the topic of %s to: %s" % (author, self.group.name, topic))

    def serverMsg(self, message):
        """Displays a serverMsg in the group conversation window

        @type message: string
        """
        self.pipe.add("-!- %s " % (message))

    def memberJoined(self, member):
        """Adds the given member to the list of members in the group conversation
        and displays this to the user

        @type member: string (XXX: Not Person?)
        """
        if member not in self.members:
            self.members.append(member)
        self.pipe.add("-!- %s joined %s" % (member, self.group.name))
        self.refreshMemberList()

    def memberChangedNick(self, oldnick, newnick):
        """Changes the oldnick in the list of members to newnick and displays this
        change to the user

        @type oldnick: string
        @type newnick: string
        """
        if oldnick in self.members:
            self.members.remove(oldnick)
            self.members.append(newnick)
            #self.chatui.contactChangedNick(oldnick, newnick)
        self.pipe.add("-!- %s is now known as %s in %s" % (oldnick, newnick, self.group.name))
        self.refreshMemberList()

    def memberLeft(self, member):
        """Deletes the given member from the list of members in the group
        conversation and displays the change to the user

        @type member: string
        """
        if member in self.members:
            self.members.remove(member)
        self.pipe.add("-!- %s left %s" % (member, self.group.name))
        self.refreshMemberList()

    def refreshMemberList(self):
        self.pipe.clearBuddyList()
        self.members.sort(lambda x, y: cmp(x.lower(), y.lower()))
        self.pipe.getCannelName(self.group.name)
        for member in self.members:
            self.pipe.buildBuddyList(str(member))
        print("Buddylist of #%s : \n%s" % (self.group.name, self.pipe.showBuddyList()))
        self.pipe.updateBuddyWindow()


class ChatUI:
    """A GUI chat client"""

    def __init__(self):
        self.conversations = {}      # cache of all direct windows
        self.groupConversations = {}  # cache of all group windows
        self.persons = {}            # keys are (name, client)
        self.groups = {}             # cache of all groups
        self.onlineClients = []      # list of message sources currently online
        self.contactsList = ContactsList(self)
        self.pipe = MessagePipe()
        self.helper = ""

    def registerAccountClient(self, client):
        """Notifies user that an account has been signed on to.

        @type client: L{Client<interfaces.IClient>}
        @returns: client, so that I may be used in a callback chain
        """
        self.pipe.debug("signing onto %s" % client.accountName)
        self.onlineClients.append(client)
        self.contactsList.registerAccountClient(client)
        self.helper = client
        self.pipe.debug(" --- %s ---" % self.helper)
        self.pipe.add("signing onto %s" % client)
        self.pipe.add("signing onto %s" % client.accountName)
        return client

    def unregisterAccountClient(self, client):
        """Notifies user that an account has been signed off or disconnected

        @type client: L{Client<interfaces.IClient>}
        """
        self.pipe.debug("signing off from %s" % client.accountName)
        self.onlineClients.remove(client)
        self.contactsList.unregisterAccountClient(client)

    def remClient(self):
        """Notifies user that an account has been signed off or disconnected

        @type client: L{Client<interfaces.IClient>}
        """
        self.pipe.debug(" --- %s ---" % self.helper)
        self.pipe.debug("signing off from %s" % self.helper.accountName)
        self.pipe.add("signing off %s" % helper)
        self.pipe.add("signing off %s" % helper.accountName)
        self.onlineClients.remove(helper)
        self.contactsList.unregisterAccountClient(helper)

    def getContactsList(self):
        """
        @returntype: L{ContactsList}
        """
        self.pipe.debug("contactlist = %s" % self.contactsList)
        return self.contactsList

    def getConversation(self, person, Class=Conversation, stayHidden=0):
        """For the given person object, returns the conversation window
        or creates and returns a new conversation window if one does not exist.

        @type person: L{Person<interfaces.IPerson>}
        @type Class: L{Conversation<interfaces.IConversation>} class
        @type stayHidden: boolean

        @returntype: L{Conversation<interfaces.IConversation>}
        """
        conv = self.conversations.get(person)
        if not conv:
            conv = Class(person, self)
            self.conversations[person] = conv
        if stayHidden:
            conv.hide()
        else:
            conv.show()
        return conv

    def getGroupConversation(self, group, Class=GroupConversation, stayHidden=0):
        """For the given group object, returns the group conversation window or
        creates and returns a new group conversation window if it doesn't exist

        @type group: L{Group<interfaces.IGroup>}
        @type Class: L{Conversation<interfaces.IConversation>} class
        @type stayHidden: boolean

        @returntype: L{GroupConversation<interfaces.IGroupConversation>}
        """
        conv = self.groupConversations.get(group)
        if not conv:
            conv = Class(group, self)
            self.groupConversations[group] = conv
        if stayHidden:
            conv.hide()
        else:
            conv.show()
#        print "[dreamIRC] : " , conv
        return conv

    def getPerson(self, name, client):
        """For the given name and account client, returns the instance of the
        AbstractPerson subclass, or creates and returns a new AbstractPerson
        subclass of the type Class

        @type name: string
        @type client: L{Client<interfaces.IClient>}

        @returntype: L{Person<interfaces.IPerson>}
        """
        account = client.account
        p = self.persons.get((name, account))
        if not p:
            p = account.getPerson(name)
            self.persons[name, account] = p
        return p

    def getGroup(self, name, client):
        """For the given name and account client, returns the instance of the
        AbstractGroup subclass, or creates and returns a new AbstractGroup
        subclass of the type Class

        @type name: string
        @type client: L{Client<interfaces.IClient>}

        @returntype: L{Group<interfaces.IGroup>}
        """
        # I accept 'client' instead of 'account' in my signature for
        # backwards compatibility.  (Groups changed to be Account-oriented
        # in CVS revision 1.8.)
        account = client.account
        g = self.groups.get((name, account))
        if not g:
            g = account.getGroup(name)
            self.groups[name, account] = g
#        self.pipe.add("joined %s" % g)
        return g

    def contactChangedNick(self, oldnick, newnick):
        """For the given person, changes the person's name to newnick, and
        tells the contact list and any conversation windows with that person
        to change as well.

        @type oldnick: string
        @type newnick: string
        """
        if (person.name, person.account) in self.persons:
            conv = self.conversations.get(person)
            if conv:
                conv.contactChangedNick(person, newnick)

            self.contactsList.contactChangedNick(person, newnick)

            del self.persons[person.name, person.account]
            person.name = newnick
            self.persons[person.name, person.account] = person

    def sendOutPipe(self):
        print("groupchat %s" % self.pipe.OutText)
        if len(self.pipe.OutText()) > 0:
            self.sendText(self.pipe.OutText())
            self.pipe.clearOutText()
