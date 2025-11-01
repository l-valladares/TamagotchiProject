# DisplayILI9341.py
from machine import Pin, SPI
import utime, framebuf

_SWRESET=0x01; _SLPOUT=0x11; _DISPON=0x29
_CASET=0x2A; _RASET=0x2B; _RAMWR=0x2C; _MADCTL=0x36; _COLMOD=0x3A
_MX=0x40; _MY=0x80; _MV=0x20; _BGR=0x08

class DisplayILI9341:
    """
    Minimal ILI9341 240x320 SPI driver with an RGB565 FrameBuffer.
    Provides: clear/fill/text/rect/lines/show + showText() + showStatus(pet).
    """
    def __init__(self, *, spi_id=0, sck=18, mosi=19, miso=-1, cs=17, dc=16, rst=20, bl=None,
                 width=240, height=320, rotation=1, baudrate=40_000_000):
        self.width, self.height, self.rotation = width, height, rotation & 3
        args = dict(baudrate=baudrate, polarity=0, phase=0, sck=Pin(sck), mosi=Pin(mosi))
        if miso >= 0: args["miso"] = Pin(miso)
        self.spi = SPI(spi_id, **args)
        self.cs, self.dc, self.rst = Pin(cs, Pin.OUT, value=1), Pin(dc, Pin.OUT, value=0), Pin(rst, Pin.OUT, value=1)
        self.bl = Pin(bl, Pin.OUT, value=1) if bl is not None else None

        self.buf = bytearray(self.width * self.height * 2)
        self.fb  = framebuf.FrameBuffer(self.buf, self.width, self.height, framebuf.RGB565)

        self._reset(); self._init(); self.clear(); self.show()

    # --- low level ---
    def _reset(self):
        self.rst.value(0); utime.sleep_ms(50); self.rst.value(1); utime.sleep_ms(50)

    def _cmd(self, c):
        self.cs.value(0); self.dc.value(0); self.spi.write(bytearray([c])); self.cs.value(1)

    def _data(self, b):
        self.cs.value(0); self.dc.value(1); self.spi.write(b); self.cs.value(1)

    def _init(self):
        self._cmd(_SWRESET); utime.sleep_ms(120)
        self._cmd(_SLPOUT);  utime.sleep_ms(120)
        self._cmd(_COLMOD);  self._data(bytearray([0x55]))  # 16-bit
        mad = _BGR
        if   self.rotation == 0: mad |= 0
        elif self.rotation == 1: mad |= _MV | _MY        # landscape
        elif self.rotation == 2: mad |= _MX | _MY
        else:                    mad |= _MV | _MX
        self._cmd(_MADCTL); self._data(bytearray([mad]))
        self._cmd(_DISPON); utime.sleep_ms(20)

    def _set_window(self, x0,y0,x1,y1):
        self._cmd(_CASET); self._data(bytearray([(x0>>8)&255,x0&255,(x1>>8)&255,x1&255]))
        self._cmd(_RASET); self._data(bytearray([(y0>>8)&255,y0&255,(y1>>8)&255,y1&255]))
        self._cmd(_RAMWR)

    # --- drawing ---
    def clear(self, color=0x0000): self.fill(color)
    def fill(self, color):
        hi, lo = (color>>8)&255, color&255
        mv=self.buf; mv[0::2]=bytes([hi])*(len(mv)//2); mv[1::2]=bytes([lo])*(len(mv)//2)

    def hline(self,x,y,w,color):
        if y<0 or y>=self.height: return
        x0=max(0,x); x1=min(self.width,x+w); 
        if x0>=x1: return
        hi,lo=(color>>8)&255,color&255; ofs=(y*self.width+x0)*2
        for _ in range(x0,x1): self.buf[ofs]=hi; self.buf[ofs+1]=lo; ofs+=2

    def vline(self,x,y,h,color):
        if x<0 or x>=self.height: pass
        y0=max(0,y); y1=min(self.height,y+h)
        if y0>=y1: return
        hi,lo=(color>>8)&255,color&255; ofs=(y0*self.width+x)*2; step=self.width*2
        for _ in range(y0,y1): self.buf[ofs]=hi; self.buf[ofs+1]=lo; ofs+=step

    def rect(self,x,y,w,h,color,fill=True):
        if fill:
            for yy in range(y,y+h): self.hline(x,yy,w,color)
        else:
            self.hline(x,y,w,color); self.hline(x,y+h-1,w,color)
            self.vline(x,y,h,color); self.vline(x+w-1,y,h,color)

    def text(self,s,x,y,color=0xFFFF):
        try: self.fb.text(str(s),x,y,color)
        except: self.fb.text(str(s),x,y)

    def show(self,x0=0,y0=0,x1=None,y1=None):
        if x1 is None: x1=self.width-1
        if y1 is None: y1=self.height-1
        x0=max(0,x0); y0=max(0,y0); x1=min(self.width-1,x1); y1=min(self.height-1,y1)
        self._set_window(x0,y0,x1,y1)
        if x0==0 and y0==0 and x1==self.width-1 and y1==self.height-1:
            self._data(memoryview(self.buf))
        else:
            for yy in range(y0,y1+1):
                rs=(yy*self.width+x0)*2; re=(yy*self.width+x1+1)*2
                self._data(memoryview(self.buf)[rs:re])

    # --- high level app helpers ---
    def showText(self, text, row_px=0, col_px=0, color=0xFFFF, bg=0x0000):
        self.rect(0,row_px,self.width,16,bg,True)
        self.text(text,col_px,row_px,color)
        self.show(0,row_px,self.width-1,row_px+16)

    def showStatus(self, pet):
        self.rect(0,0,self.width,100,0x0000,True)
        self.text(pet.name,8,8,0xFFE0)
        def bar(y,label,val,color):
            maxw=200; w=int(max(0,min(10,val))/10*maxw)
            self.text(label,8,y,0xFFFF)
            self.rect(60,y,maxw,10,0x2104,True)
            self.rect(60,y,w,10,color,True)
        bar(40,"Mood",   pet.mood,   0x07E0)
        bar(60,"Hunger", 10-pet.hunger, 0xF800)  # inverse: fuller bar = less hungry
        bar(80,"Energy", pet.energy, 0x001F)
        self.show(0,0,self.width-1,100)
