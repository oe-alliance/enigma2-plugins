from enigma import ePythonMessagePump
import threading
from twisted.internet import defer

class SimpleThread(threading.Thread):
	def __init__(self, fnc):
		threading.Thread.__init__(self)
		self.deferred = defer.Deferred()
		self.__pump = ePythonMessagePump()
		self.__pump.recv_msg.get().append(self.gotThreadMsg)
		self.__asyncFunc = fnc
		self.__result = None
		self.__err = None

	def gotThreadMsg(self, msg):
		if self.__err:
			self.deferred.errback(self.__err)
		else:
			self.deferred.callback(self.__result)
		del self.__pump.recv_msg.get()[:]

	def run(self):
		try:
			self.__result = self.__asyncFunc()
		except Exception as e:
			self.__err = e
		finally:
			self.__pump.send(0)

__all__ = ['SimpleThread']
