# -*- coding: utf-8 -*-
# Congratulations to the author
# I only adapted the plugin to Enigma2 Python3
# lululla coder - mmark skinner
from enigma import gFont, eTimer, getDesktop, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.CanvasSource import CanvasSource
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from random import shuffle
from os import system
VERSION = "7.1r0"


def argb(a, r, g, b):
	return (a << 24) | (r << 16) | (g << 8) | b


def getDesktopSize():
	s = getDesktop(0).size()
	return (s.width(), s.height())


def isFHD():
	desktopSize = getDesktopSize()
	return desktopSize[0] == 1920


class Tile(object):

	shapes = {
		" ": ["                "],
		"I": ["    IIII        ", " I   I   I   I  ", "    IIII        ", " I   I   I   I  "],
		"J": [" J   JJJ        ", "  J   J  JJ     ", "     JJJ   J    ", "  JJ  J   J     "],
		"L": ["  L LLL         ", "LL   L   L      ", "    LLL L       ", " L   L   LL     "],
		"O": [" OO  OO         ", " OO  OO         ", " OO  OO         ", " OO  OO         "],
		"S": [" SS SS          ", "S   SS   S      ", " SS SS          ", "S   SS   S      "],
		"T": [" TTT  T         ", "  T   TT  T     ", "  T  TTT        ", "   T  TT   T    "],
		"Z": [" ZZ   ZZ        ", "  Z  ZZ  Z      ", " ZZ   ZZ        ", "  Z  ZZ  Z      "]
	}

	def __init__(self, shape):
		self.shape = self.shapes[shape]
		self.x = 0
		self.y = 0
		self.face = 0


class TetrisBoard(object):

	# cellwidth = 43
	if isFHD():
		cellwidth = 43
	else:
		cellwidth = 27

	pieceColors = {
		" ": argb(0, 0x00, 0x00, 0x00),
		"I": argb(0, 0xFF, 0xFF, 0x00),  # yellow
		"J": argb(0, 0x00, 0x00, 0xFF),  # blue
		"L": argb(0, 0xFF, 0x80, 0x00),  # orange
		"O": argb(0, 0xFF, 0x00, 0xFF),  # magenta
		"S": argb(0, 0xFF, 0x00, 0x00),  # red
		"T": argb(0, 0x00, 0xFF, 0xFF),  # cyan
		"Z": argb(0, 0x00, 0xFF, 0x00),  # green
	}

	levels = [1000, 800, 720, 630, 540, 470, 370, 300, 220, 150]

	def __init__(self, canvas):
		self.canvas = canvas
		self.canvas.fill(0, 0, 430, 860, argb(0, 0, 0, 0))
		self.setupBoard()
		self.drawBoard(self.board)
		self.moveTimer = eTimer()
		self.moveTimer.callback.append(self.moveDown)

	def setupBoard(self):
		self.lines = 0
		self.level = 0
		self.points = 0
		self.timeout = self.levels[self.level]
		self.accelerate = False
		self.board = "WWWWWWWWWWWW"
		for i in range(0, 20):
			self.board += "W          W"
		self.board += "WWWWWWWWWWWW"

	def drawBoard(self, board):
		pos = 0
		for c in board:
			if c != 'W':
				x = pos % 10
				y = pos // 10
				self.drawPiece(x, y, c)
				pos += 1
		self.canvas.flush()

	def drawPiece(self, x, y, piece):
		frameColor = argb(0x00, 0xd9, 0xd9, 0xc5)
		color = self.pieceColors[piece]

		x = x * self.cellwidth
		y = y * self.cellwidth

		self.canvas.fill(x,   y,   self.cellwidth,   self.cellwidth,   frameColor)
		self.canvas.fill(x+1, y+1, self.cellwidth-2, self.cellwidth-2, color)

	def spawn(self, tile, callback):
		self.onDown = callback
		self.accelerate = False
		self.tile = tile
		self.tile.x = 4
		self.tile.y = 1
		layer = self.buildLayer()
		if layer:
			self.drawBoard(layer)
			self.moveTimer.start(self.timeout, True)
		else:
			self.onDown(False)

	def rotateTile(self, dir):
		face = self.tile.face
		self.tile.face = (self.tile.face + dir) % 4
		layer = self.buildLayer()
		if layer:
			self.drawBoard(layer)
		else:
			self.tile.face = face

		self.dropCache()

	# lululla add
	def dropCache(self):
		system("echo 3 > /proc/sys/vm/drop_caches")
		print("[CacheFlush]")
		return

	def moveTile(self, dir):
		x = self.tile.x
		self.tile.x += dir
		layer = self.buildLayer()
		if layer:
			self.drawBoard(layer)
		else:
			self.tile.x = x

	def moveDown(self):
		self.tile.y += 1
		layer = self.buildLayer()
		if layer:
			self.drawBoard(layer)
			timeout = self.timeout
			if self.accelerate:
				timeout = min(self.timeout, 100)
			self.moveTimer.start(timeout, True)
		else:
			self.tile.y -= 1
			self.mergeLayer()
			self.onDown(True)

	def eliminateLines(self):
		eliminated = 0
		for line in range(1, 21):
			start = line * 12
			end = start + 12
			segment = self.board[start:end]
			if not " " in segment:
				tmp = "WWWWWWWWWWWWW          W" + self.board[12:start] + self.board[end:]
				self.board = tmp
				self.lines += 1
				eliminated += 1
				if self.lines % 5 == 0:
					self.level += 1
					if len(self.levels) > self.level:
						self.timeout = self.levels[self.level]
		self.points += [0, 100, 300, 500, 800][eliminated] * (self.level+1)

	def buildLayer(self):
		shape = self.tile.shape[self.tile.face]
		layer = list(self.board)
		pos = self.tile.y * 12 + self.tile.x
		cpos = 0
		offset = 0
		for c in shape:
			if c != ' ':
				if layer[pos+offset] != ' ':
					return False
				layer[pos+offset] = c
			cpos += 1
			offset = (cpos % 4) + (cpos // 4) * 12
		return ''.join(layer)

	def mergeLayer(self):
		self.board = self.buildLayer()
		self.eliminateLines()


class PreviewBoard(TetrisBoard):

	def __init__(self, canvas):
		self.canvas = canvas
		self.canvas.fill(0, 0, 196, 196, argb(33, 255, 255, 255))

	def drawBoard(self, piece):
		pos = 0
		for c in piece:
			x = pos % 4
			y = pos // 4
			self.drawPiece(x, y, c)
			pos += 1
		self.canvas.flush()


class Board(Screen):
	if isFHD():
		print('is fhd----------------------------')
		skin = """
				<screen name="Tetrisfhd" position="center,100" size="1800,940" title="Tetris" backgroundColor="#101010">
					<ePixmap position="0,0" size="1800,940" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Tetris/pic/tetris.jpg" />
					<widget source="canvas"  render="Canvas" position="center ,40" size="430,860" backgroundColor="#60ffffff" transparent="1" alphatest="blend" zPosition="2" />
					<widget source="preview" render="Canvas" position="1230,100" size="176,174" zPosition="3" />
					<widget name="previewtext" position="1220,30" size="210,40" valign="center" halign="center" font="Regular;34" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
					<widget name="state"       position="241,255" size="500,80" valign="center" halign="center" font="Regular;50" foregroundColor="red" backgroundColor="#000000" transparent="1" zPosition="3" />
					<ePixmap position="60,50" pixmap="buttons/key_green.png" size="80,40" alphatest="blend" scale="1" zPosition="2" />
					<widget name="key_green" position="160,50" size="200,40" font="Regular;30" halign="left" valign="center" foregroundColor="green" backgroundColor="black" zPosition="1" transparent="1" />
					<ePixmap position="60,100" pixmap="buttons/key_red.png" size="80,40" alphatest="blend" scale="1" zPosition="2" />
					<widget name="key_red" position="160,100" size="200,40" font="Regular;30" halign="left" valign="center" foregroundColor="red" backgroundColor="black" zPosition="1" transparent="1" />
					<eLabel position="60,210" size="310,3" backgroundColor="#404040" zPosition="1" />
					<widget name="points" position="60,230" size="200,40" valign="center" halign="left" font="Regular;30" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
					<widget name="lines"  position="60,280" size="200,40" valign="center" halign="left" font="Regular;30" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
					<widget name="level"  position="60,330" size="200,40" valign="center" halign="left" font="Regular;30" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
				</screen>
				"""
	else:
		print('is hd----------------------------')
		skin = """
			<screen name="Tetrishd" position="0,0" size="1280,720" title="Tetris" flags="wfNoBorder">
				<ePixmap position="0,0" size="1280,720" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Tetris/pic/tetrishd.jpg" />
				<widget source="canvas" render="Canvas" position="508,75" size="272,541" zPosition="1" />
				<widget source="preview" render="Canvas" position="883,77" size="110,110" zPosition="2" />
				<widget name="state" position="34,50" size="237,54" font="Regular; 34" foregroundColor="#00cc0000" zPosition="2" />
				<widget name="previewtext" position="866,26" size="145,30" font="Regular; 20" zPosition="2" />
				<widget name="points" position="33,163" size="236,40" font="Regular; 24" zPosition="2" />
				<widget name="lines" position="33,205" size="236,40" font="Regular; 22" zPosition="2" />
				<widget name="level" position="33,248" size="236,40" font="Regular; 24" zPosition="2" />
				<widget name="key_red" position="150,670" size="187,37" zPosition="1" font="Regular; 16" halign="center" valign="center" foregroundColor="#00ffffff" backgroundColor="#9f1313" />
				<widget name="key_green" position="377,670" size="187,37" zPosition="1" font="Regular; 16" halign="center" valign="center" foregroundColor="#00ffffff" backgroundColor="#1f771f" />
				<widget name="key_yellow" position="604,670" size="187,37" zPosition="1" font="Regular; 16" halign="center" valign="center" foregroundColor="#00ffffff" backgroundColor="#a08500" />
				<widget name="key_blue" position="830,670" size="187,37" zPosition="1" font="Regular; 16" halign="center" valign="center" foregroundColor="#00ffffff" backgroundColor="#18188b" />
			</screen>
			"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		# self.skinName = "Tetris_v1"
		if isFHD():
			self.skinName = "Tetrisfhd"
		else:
			self.skinName = "Tetrishd"
		self.setTitle("Tetris %s" % VERSION)
		self["actions"] = ActionMap(["TetrisActions"], {
			"cancel":   self.cancel,
			"up":       self.up,
			"down":     self.down,
			"left":     self.left,
			"right":    self.right,
			"ok":       self.ok,
			"red":      self.red,
			"green":    self.green,
			"yellow":   self.yellow,
			"blue":     self.blue,
		}, -1)

		self["canvas"] = CanvasSource()
		self["preview"] = CanvasSource()
		self["previewtext"] = Label("Next Block:")
		self["key_red"] = Label("Exit")
		self["key_green"] = Label("Tetris Start")
		self["state"] = Label()
		self["lines"] = Label()
		self["level"] = Label()
		self["points"] = Label()
		self.onLayoutFinish.append(self.setupBoard)

	def setupBoard(self):
		self.stopped = True
		self.board = TetrisBoard(self["canvas"])
		self.preview = PreviewBoard(self["preview"])
		# edit lululla
		self["lines"].setText("Lines: 0")
		self["level"].setText("Level: 0")
		self["points"].setText("Points: 0")
		# end edit
		self.tetrominos = ["I", "J", "L", "O", "S", "T", "Z"]
		shuffle(self.tetrominos)
		self.nexttile = self.tetrominos[0]
		self.updatePreview(" ")

	def updatePreview(self, tile):
		previewPiece = Tile(tile)
		self.preview.drawBoard(previewPiece.shape[0])

	def eventLoop(self, state):
		self["lines"].setText("Lines: %d" % self.board.lines)
		self["level"].setText("Level: %d" % (self.board.level+1))
		self["points"].setText("Points: %d" % (self.board.points))
		if not state:
			self.gameOver()
		else:
			tile = self.nexttile
			piece = Tile(tile)
			shuffle(self.tetrominos)
			self.nexttile = self.tetrominos[0]
			self.updatePreview(self.nexttile)
			self.board.spawn(piece, self.eventLoop)
		# edit lululla
		self.board.dropCache()

	def gameOver(self):
		self.updatePreview(" ")
		self["state"].setText("Game Over")
		self.stopped = True

	def cancel(self):
		self.board.moveTimer.stop()
		self.close()

	def up(self):
		if not self.stopped:
			self.board.rotateTile(1)

	def down(self):
		if not self.stopped:
			self.board.rotateTile(-1)

	def left(self):
		if not self.stopped:
			self.board.moveTile(-1)

	def right(self):
		if not self.stopped:
			self.board.moveTile(1)

	def ok(self):
		if not self.stopped:
			self.board.accelerate = not self.board.accelerate

	def red(self):
		pass

	def green(self):
		if self.stopped:
			self["state"].setText("")
			self.stopped = False
			self.board.setupBoard()
			self.eventLoop(True)

	def yellow(self):
		pass

	def blue(self):
		pass
