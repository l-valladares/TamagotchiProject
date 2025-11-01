# DisplayILI9341_Lite.py
from machine import Pin, SPI
import utime, framebuf

_SWRESET=0x01; _SLPOUT=0x11; _DISPON=0x29
_CASET=0x2A; _RASET=0x2B; _RAMWR=0x2C; _MADCTL=0x36; _COLMOD=0x3A
_MX=0x40; _MY=0x80; _MV=0x20; _BGR=0x08
_RGB565 = framebuf.RGB565

class DisplayILI9341:
    def __init__(self, *, spi_id=0, sck=2, mosi=3, miso=-1, cs=5, dc=6, rst=20, bl=None,
                 width=320, height=240, rotation=1, baudrate=40_000_000):
        self.width, self.height, self.rotation = width, height, rotation & 3
        args=dict(baudrate=baudrate, polarity=0, phase=0, sck=Pin(sck), mosi=Pin(mosi))
        if miso >= 0: args["miso"]=Pin(miso)
        self.spi = SPI(spi_id, **args)
        self.cs, self.dc, self.rst = Pin(cs, Pin.OUT, value=1), Pin(dc, Pin.OUT, value=0), Pin(rst, Pin.OUT, value=1)
        self.bl = Pin(bl, Pin.OUT, value=1) if bl is not None else None

        self._rowbuf = bytearray(self.width * 2)
        self._rowfb  = framebuf.FrameBuffer(self._rowbuf, self.width, 1, _RGB565)
        self._band_h = 16
        self._bandbuf = bytearray(self.width * self._band_h * 2)
        self._bandfb  = framebuf.FrameBuffer(self._bandbuf, self.width, self._band_h, _RGB565)

        self._reset(); self._init(); self.clear()

    def _reset(self):
        self.rst.value(0); utime.sleep_ms(50); self.rst.value(1); utime.sleep_ms(120)

    def _cmd(self, c):
        self.cs.value(0); self.dc.value(0); self.spi.write(bytearray([c])); self.cs.value(1)
    def _data(self, b):
        self.cs.value(0); self.dc.value(1); self.spi.write(b); self.cs.value(1)

    def _init(self):
        self._cmd(_SWRESET); utime.sleep_ms(120)
        self._cmd(_SLPOUT);  utime.sleep_ms(120)
        self._cmd(_COLMOD);  self._data(bytearray([0x55]))
        mad = _BGR
        if   self.rotation == 0: mad |= 0
        elif self.rotation == 1: mad |= _MV | _MY
        elif self.rotation == 2: mad |= _MX | _MY
        else: mad |= _MV | _MX
        mad ^= _MX   # flip horizontally so text isn’t mirrored
        self._cmd(_MADCTL); self._data(bytearray([mad]))
        self._cmd(_DISPON); utime.sleep_ms(20)

    def _set_window(self,x0,y0,x1,y1):
        self._cmd(_CASET); self._data(bytearray([(x0>>8)&255,x0&255,(x1>>8)&255,x1&255]))
        self._cmd(_RASET); self._data(bytearray([(y0>>8)&255,y0&255,(y1>>8)&255,y1&255]))
        self._cmd(_RAMWR)

    def clear(self,color=0x0000): self.fill(color)
    def fill(self,color):
        hi,lo=(color>>8)&255,color&255
        rb=self._rowbuf
        for i in range(0,len(rb),2): rb[i]=hi; rb[i+1]=lo
        for y in range(self.height):
            self._set_window(0,y,self.width-1,y)
            self._data(rb)

    def rect(self,x,y,w,h,color,fill=True):
        if fill:
            hi,lo=(color>>8)&255,color&255
            rb=self._rowbuf
            x0=max(0,x); x1=min(self.width,x+w)
            if x0>=x1:return
            roww=x1-x0
            for i in range(0,roww*2,2): rb[i]=hi; rb[i+1]=lo
            for yy in range(max(0,y),min(self.height,y+h)):
                self._set_window(x0,yy,x1-1,yy)
                self._data(memoryview(rb)[:roww*2])
        else:
            self.hline(x,y,w,color); self.hline(x,y+h-1,w,color)
            self.vline(x,y,h,color); self.vline(x+w-1,y,h,color)
    def hline(self,x,y,w,color): self.rect(x,y,w,1,color,True)
    def vline(self,x,y,h,color): self.rect(x,y,1,h,color,True)

    def _push_band(self,y):
        y0=max(0,y); y1=min(self.height-1,y+self._band_h-1)
        self._set_window(0,y0,self.width-1,y1)
        rows=(y1-y0+1)
        self._data(memoryview(self._bandbuf)[:self.width*rows*2])

    def showText(self,text,row_px=0,col_px=0,color=0xFFFF,bg=0x0000):
        fb=self._bandfb; fb.fill(bg)
        try: fb.text(str(text),col_px,0,color)
        except: fb.text(str(text),col_px,0)
        self._push_band(row_px)

    def showStatus(self,pet):
        self.showText(pet.name,8,8,0xFFE0,0x0000)
        def bar(y,label,val,color,invert=False):
            self.showText(label,y,8,0xFFFF,0x0000)
            maxw=200
            v=val if not invert else(10-val)
            w=int(max(0,min(10,v))/10*maxw)
            self.rect(60,y,maxw,10,0x2104,True)
            self.rect(60,y,w,10,color,True)
        bar(40,"Mood",pet.mood,0x07E0)
        bar(60,"Hunger",pet.hunger,0xF800,True)
        bar(80,"Energy",pet.energy,0x001F)

    def blit_rgb565(self, buf, w, h, x, y):
        if x<0 or y<0 or x+w>self.width or y+h>self.height: return
        self._set_window(x,y,x+w-1,y+h-1)
        self._data(memoryview(buf))

    @staticmethod
    def rgb565(r,g,b):
        return ((r&0xF8)<<8)|((g&0xFC)<<3)|(b>>3)
