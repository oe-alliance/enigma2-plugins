# -*- coding: ISO-8859-1 -*-
#===============================================================================
# eSame Game Plugin by DarkVolli 2009
# Original Game kSame by Marcus Kreutzberger
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

import random
from six.moves import range

class Stone:
	color = 0
	changed = False
	marked = False

# This class is derived from StoneField.cpp (kSame) by Marcus Kreutzberger	
class StoneField:
	def __init__(self, width, height, colors, board):
		self.sizex = width
		self.sizey = height
		self.maxstone = self.sizex * self.sizey

		self.field = []
		for i in range(self.maxstone):
			tmp = Stone()
			self.field.append(tmp)

		self.newGame(board, colors)
		self.m_gotBonus = False

	def count(self, color):
		c = 0
		for stone in self.field:
			if stone.color == color:
				c += 1
		return c
	
	def width(self):
		return self.sizex;
	
	def height(self):
		return self.sizey

	def newGame(self, board, colors):
		if colors < 1:
			colors = 3
		if colors > 7:
			colors = 7
		self.colors = colors
		self.board = board
		self.reset()

	def reset(self):
		random.seed(self.board)
		i=0
		for stone in self.field:
			if i < 75:
				stone.color = 1
			else:
				stone.color = 2
			i += 1
			stone.color = random.randint(1, self.colors)
			stone.marked = False
			stone.changed = True

		self.gameover = -1
		self.score = 0
		self.marked = 0

		self.c = []
		for i in range(7):
			self.c.append(0)

		for stone in self.field:
			self.c[stone.color] += 1

	def Map(self, x, y):
		return x + y * self.sizex

	def mark1(self, x, y, force = False):
		index = self.Map(x, y)

		if index < 0:
			self.unmark()
			return 0

		if self.field[index].marked:
			return -1
		self.unmark()

		self.mark2(index, self.field[index].color)

		if self.marked == 1 and not force:
			self.field[index].marked = False
			self.marked = 0

		return self.marked

	def mark2(self, index, color):
		if index < 0 or index >= self.maxstone:
			return

		stone = self.field[index]

		if stone.marked:
			return

		if not stone.color or stone.color != color:
			return

		stone.changed = True
		stone.marked = True
		self.marked += 1

		# mark left
		if index % self.sizex != 0: 
			self.mark2(index - 1, color)
		# mark right
		if (index + 1) % self.sizex != 0:
			self.mark2(index + 1, color)
		# mark upward
		if index >= self.sizex: 
			self.mark2(index - self.sizex, color)
		# mark downward
		if index < (self.sizex - 1) * self.sizey:
			self.mark2(index + self.sizex, color)

	def unmark(self):
		if not self.marked:
			return

		for stone in self.field:
			stone.marked = False;
			stone.changed = True;

		self.marked = 0

	def remove(self, x, y, force = False):
		index = self.Map(x, y)

		if index < 0:
			return 0

		if not self.field[index].marked:
			self.mark1(x, y, force)

		if not self.marked:
			return 0

		# remove a single stone?
		if self.marked == 1 and not force:
			return 0

		# increase score
		if self.marked > 2:
			self.score += (self.marked - 2) * (self.marked - 2)

		# remove marked stones
		for stone in self.field:
			if stone.marked:
				stone.color = 0
				stone.changed = True
				stone.marked = False
		removed = self.marked
		self.marked = 0

		#for (int col=0;col<sizex;col++) {
		for col in range(self.sizex):
			i1 = col + self.maxstone - self.sizex
			while i1 >= 0 and self.field[i1].color:
				i1 -= self.sizex
			i2 = i1
			while i2 >= 0:
				while i2 >= 0 and not self.field[i2].color:
					i2 -= self.sizex
				while i2 >= 0 and self.field[i2].color:
					self.field[i1].color = self.field[i2].color
					self.field[i1].changed = True
					self.field[i2].color = 0
					self.field[i2].changed = True
					i1 -= self.sizex
					i2 -= self.sizex

		# find the last column that has something
		lastcol = self.sizex
		while lastcol > 0 and not self.field[self.Map(lastcol-1, self.sizey-1)].color:
			lastcol -= 1

		#for (int col=0;col<lastcol-1;) {
		for col in range(lastcol-1):
			empty = True
			#for (int row = 0; row < sizey; row++)
			for row in range (self.sizey):
				if self.field[self.Map(col, row)].color:
					empty = False
					break

			if not empty:
				col += 1
				continue

			nextfullcol = col + 1
			while nextfullcol < self.sizex and not self.field[self.Map(nextfullcol, self.sizey - 1)].color:
				nextfullcol += 1

			if nextfullcol > self.sizex - 1:
				break # we're ready

			#for (int row=0; row < sizey; row++) {
			for row in range(self.sizey):
				source = self.Map(nextfullcol, row)
				dest = self.Map(col, row)
				self.field[dest].color = self.field[source].color
				self.field[dest].changed = True
				self.field[source].color = 0
				self.field[source].changed = True

		# add a bonus, if field is empty
		if not self.field[self.Map(0, self.sizey-1)].color:
			self.score += 1000
			self.m_gotBonus = True

		# gameover is undefined
		self.gameover = -1
		return removed

	def isGameover(self):
		i = self.maxstone - 1
		#register unsigned char color;
		
		if self.gameover >= 0:
			return bool(self.gameover)
		
		while i >= 0:
			# ignore empty fields
			while  i >= 0 and self.field[i].color == 0:
				i -= 1
			# Wenn Stein gefunden,
			# dann die Nachbarn auf gleiche Farbe pruefen.
			color = self.field[i].color
			while i >= 0 and color:
				# check left
				if i % self.sizex != 0 and self.field[i - 1].color==color:
					self.gameover = (i < 0)
					return bool(self.gameover)
				# check upward
				if i >= self.sizex and self.field[i - self.sizex].color==color:
					self.gameover = (i < 0)
					return bool(self.gameover)
				i -= 1
				color = self.field[i].color

		self.gameover = (i < 0)
		return bool(self.gameover)

	def hasBonus(self):
		return self.m_gotBonus
	
	def getBoard(self):
		return self.board
	
	def getScore(self):
		return self.score
	
	def getColors(self):
		return self.colors
	
	def getMarked(self):
		return self.marked
	
	def getFieldSize(self):
		return self.maxstone
	
	def getField(self):
		return self.field

