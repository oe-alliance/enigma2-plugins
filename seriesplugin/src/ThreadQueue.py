# -*- coding: utf-8 -*-
from threading import Lock
from collections import deque

class ThreadQueue:
	def __init__(self):
		self.__queue = deque()
		self.__lock = Lock()

	def empty(self):
		return not self.__queue

	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__queue.append(val)
		lock.release()

	def pop(self):
		lock = self.__lock
		lock.acquire()
		if self.__queue:
			ret = self.__queue.popleft()
		else:
			ret = None
		lock.release()
		return ret
