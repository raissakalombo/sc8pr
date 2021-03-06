# Copyright 2015-2016 D.G. MacCarthy <http://dmaccarthy.github.io>
#
# This file is part of "sc8pr".
#
# "sc8pr" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "sc8pr" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "sc8pr".  If not, see <http://www.gnu.org/licenses/>.


from traceback import format_exc
from sys import stderr
from json import dumps, loads
from tempfile import mkdtemp
from random import randint
from pygame import Color, Rect
from pygame.mixer import Sound
from pygame.constants import QUIT, KEYDOWN, KEYUP, MOUSEMOTION, MOUSEBUTTONDOWN as MOUSEDOWN, MOUSEBUTTONUP as MOUSEUP, VIDEORESIZE as RESIZE
from subprocess import call
from tempfile import mkstemp
import pygame, sc8pr, os


# Type styles...
BOLD = 1
ITALIC = 2

# Cursors...
ARROW = pygame.cursors.arrow
DIAMOND = pygame.cursors.diamond
MOVE = ((16,16),(9,8),(1,128,3,192,7,224,1,128,1,128,17,136,49,140,127,254,127,254,49,140,17,136,1,128,1,128,7,224,3,192,1,128),(3,192,7,224,15,240,7,224,3,192,59,220,127,254,255,255,255,255,127,254,59,220,3,192,7,224,15,240,7,224,3,192))
TEXT = ((16,16),(4,7),(119,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,119,0),(119,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,8,0,119,0))
CROSS = ((16,16),(8,8),(1,0,1,0,1,0,1,0,1,0,0,0,0,0,248,62,0,0,0,0,1,0,1,0,1,0,1,0,1,0,0,0),(1,0,1,0,1,0,1,0,1,0,0,0,0,0,248,62,0,0,0,0,1,0,1,0,1,0,1,0,1,0,0,0))
HAND = ((16,24),(6,1),(6,0,9,0,9,0,9,0,9,192,9,56,9,38,105,37,153,37,136,37,64,1,32,1,16,1,8,1,8,1,4,1,4,2,3,252,0,0,0,0,0,0,0,0,0,0,0,0),(6,0,15,0,15,0,15,0,15,192,15,184,15,254,111,253,255,253,255,255,127,255,63,255,31,255,15,255,15,255,7,255,7,254,3,252,0,0,0,0,0,0,0,0,0,0,0,0))
MENU = ((16,16),(3,2),(0,0,127,254,127,254,0,0,0,0,0,0,127,254,127,254,0,0,0,0,0,0,127,254,127,254,0,0,0,0,0,0),(255,255,255,255,255,255,255,255,0,0,255,255,255,255,255,255,255,255,0,0,255,255,255,255,255,255,255,255,0,0,0,0))
NO_CURSOR = ((8,8),(5,4),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))


# JSON binary operations...

def jdump(obj): return bytes(dumps(obj), encoding="utf8")
def jload(data): return loads(str(data, encoding="utf8"))


def defaultExtension(name, ext):
    return name if "." in name.replace("\\","/").split("/")[-1] else name + ext

def tempDir(path):
    "Create a temporary directory for images"
    if "?" in path:
        fldr, path = path.split("?")
        path = mkdtemp(dir=fldr) + path
    return path

#def nothing(*args): pass
def logError(): print(format_exc(), file=stderr)

def setCursor(c):
    if not c: c = ARROW
    pygame.mouse.set_cursor(*c)

def randPixel(obj):
    "Return random coordinates within an image, sketch, or similar object"
    w, h = obj.size
    return randint(0, w-1), randint(0, h-1)

def rgba(*args):
    "Return a color or list of colors from str or tuple data"
    c = [Color(*c) if type(c) is tuple else Color(c) for c in args]
    return c[0] if len(c) == 1 else c

def hsvaColor(h, s, v, a=100):
    "Create color from HSVA values"
    c = Color(0)
    c.hsva = h % 360 if h >= 360 else h, s, v, a
    return c

def randColor(alpha=False):
    "Return a random color"
    return Color(*[randint(0,255) for i in range(4 if alpha else 3)])

def noise(c, amt=8, alpha=None):
    "Add randomness to a color"
    c = Color(*[min(255, max(0, val + randint(-amt, amt))) for val in c])
    if alpha is not None: c.a = alpha
    return c

def getAlpha(c):
    "Get the alpha value of a color"
    if type(c) in (tuple, list):
        return c[3] if len(c) == 4 else 255
    return None if c is None else c.a

SHIFT = pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT
CTRL = pygame.KMOD_LCTRL | pygame. KMOD_RCTRL
ALT = pygame.KMOD_LALT | pygame. KMOD_RALT
ANY = SHIFT | CTRL | ALT

def capsLock(): return pygame.key.get_mods() & pygame.KMOD_CAPS != 0
def altKey(): return pygame.key.get_mods() & ALT != 0
def controlKey(): return pygame.key.get_mods() & CTRL != 0
def shiftKey(): return pygame.key.get_mods() & SHIFT != 0
def keyMod(): return pygame.key.get_mods() & ANY != 0

def dragging(ev, button=None):
    if ev.type == MOUSEMOTION:
        return (max(ev.buttons) if button is None else ev.buttons[button-1]) > 0
    return False

def isChar(u): return ord(u) >= 32 if len(u) else False
def isEnter(k): return k.key in (10, 13)
def isHome(k): return k.key == pygame.K_HOME or k.key == pygame.K_KP7 and k.unicode == ""
def isEnd(k): return k.key == pygame.K_END or k.key == pygame.K_KP1 and k.unicode == ""
def isPgUp(k): return k.key == pygame.K_PAGEUP or k.key == pygame.K_KP9 and k.unicode == ""
def isPgDn(k): return k.key == pygame.K_PAGEDOWN or k.key == pygame.K_KP3 and k.unicode == ""
def isLeft(k): return k.key == pygame.K_LEFT or k.key == pygame.K_KP4 and k.unicode == ""
def isRight(k): return k.key == pygame.K_RIGHT or k.key == pygame.K_KP6 and k.unicode == ""
def isUp(k): return k.key == pygame.K_UP or k.key == pygame.K_KP8 and k.unicode == ""
def isDown(k): return k.key == pygame.K_DOWN or k.key == pygame.K_KP2 and k.unicode == ""
def isIncr(k): return k.key in (pygame.K_UP, pygame.K_RIGHT) or k.key in (pygame.K_KP8, pygame.K_KP6) and k.unicode == ""
def isDecr(k): return k.key in (pygame.K_DOWN, pygame.K_LEFT) or k.key in (pygame.K_KP2, pygame.K_KP4) and k.unicode == ""

def addToMap(m, key, items):
    if key in m: m[key] |= items
    else: m[key] = items
    
def copyAttr(src, dest):
    "Copy all attributes from an object or dict to another object"
    if type(src) != dict: src = src.__dict__
    for k in src: setattr(dest, k, src[k])

def getValues(*args, **kwargs):
    "Extract multiple items from a dict"
    return tuple([kwargs.get(k) for k in args])

def eventKey(ev, eMap):
    "Determine eventMap key: (1) ev.type, (2) type(ev), (3) None"
    if ev.type in eMap: key = ev.type
    elif type(ev) in eMap: key = type(ev)
    else: key = None
    return key

def handleEvent(obj, ev):
    "Call an event handler from an object's eventMap attribute"
    eMap = obj.eventMap
    key = eventKey(ev, eMap)
    return eMap[key](obj, ev) if key in eMap else None

def bind(obj, func, attr=None):
    "Bind a function as an object method"
    if attr is None: attr = func.__name__
    setattr(obj, attr, func.__get__(obj, obj.__class__))

def fontHeight(f):
    if not isinstance(f, pygame.font.Font): f = f.font
    return f.get_linesize() + 1

def containsAny(obj, items='*?|<>"'):
    for i in items:
        if i in obj: return True
    return False

def sc8prPath(rel=""):
    "Return path to sc8pr folder"
    path = sc8pr.__path__[0]
    if rel: path += "/" + rel
    return os.path.normpath(path)

# Anchoring...

CENTER = 0
WEST = 1
EAST = 2
NORTH = 4
SOUTH = 8
NW = NORTH | WEST
NE = NORTH | EAST
SW = SOUTH | WEST
SE = SOUTH | EAST

def rectAnchor(posn, size, anchor=NW):
    "Returns a rectangle using a position relative to the specified anchor point"
    w, h = size
    r = Rect(posn + size)
    dx = 0 if anchor & WEST else w if anchor & EAST else w // 2
    dy = 0 if anchor & NORTH else h if anchor & SOUTH else h // 2
    return r.move(-dx, -dy)

def coords(size, anchor=NW, offset=0):
    "Return coordinates relative to an anchor point of the image"
    r = Rect((0,0) + size)
    x = 0 if anchor & WEST else (r.right-1) if anchor & EAST else r.centerx
    y = 0 if anchor & NORTH else (r.bottom-1) if anchor & SOUTH else r.centery
    if offset:
        if type(offset) is int:
            mx = offset * (1 if anchor & WEST else -1 if anchor & EAST else 0)
            my = offset * (1 if anchor & NORTH else -1 if anchor & SOUTH else 0)
        else:
            mx, my = offset
        x += mx
        y += my
    return x, y

def position(srcSize, destSize=None, anchor=NW, offset=0):
    "Position one rectangle within another"
    if destSize is None:
        destSize = pygame.display.get_surface().get_size()
    posn = coords(destSize, anchor, offset)
    return rectAnchor(posn, srcSize, anchor).topleft


# Numerical integration...

def _step(dt, *derivs):
    n = 0
    f = dt
    for d in derivs:
        n += 1
        if n == 1: val = list(d)
        else:
            val = [val[i] + d[i] * f for i in range(len(d))]
            f *= dt / n
    return tuple(val)

def step(dt, *args):
    return [_step(dt, *args[i:]) for i in range(len(args)-1)]


# Prevent crash when using sound files that cannot be loaded

class NoSound:
    "A class to represent Sound objects that fail to load"
    def play(self, **kwargs): pass

    __init__ = play
    set_volume = play

def loadSound(fn):
    "Attempt to load a sound file using pygame.mixer.Sound"
    try: s = Sound(fn)
    except:
        s = NoSound()
        print("Unable to load {}".format(fn), file=stderr)
    return s


# Classes...

class StaticClassException(Exception):
    def __init__(self, cls): super().__init__("{} is static; constructor should not be called".format(cls))

class Data:
    "Object-oriented dict-like data structure"
    def get(self, key): return self.__dict__.get(key)
    def attr(self, **kwargs): self.__dict__.update(**kwargs)
    def keys(self): return self.__dict__.keys()
    def empty(self): self.__dict__.clear()
    __init__ = attr
    
    def __str__(self):
        t = type(self)
        return "<{}.{} {}>".format(t.__module__, t.__name__, self.__dict__)
