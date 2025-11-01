# Gadget.py
import time
from Button import Button
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from DisplayILI9341_Lite import DisplayILI9341
from Pet import Pet
from ActionService import ActionService
from PetSprite import PetAnimator

HOLD_MS_SWITCH = 2000

class Gadget:
    def __init__(self, *,
                 btn_pins=(10,11,12),
                 strip_pin=7, strip_count=16,
                 buz_pin=15,
                 spi_id=0, sck=2, mosi=3, miso=-1, cs=5, dc=6, rst=20, bl=None,
                 rotation=1):
        self.display = DisplayILI9341(spi_id=spi_id, sck=sck, mosi=mosi, miso=miso,
                                      cs=cs, dc=dc, rst=rst, bl=bl, rotation=rotation)
        self.lights  = LightStrip(pin=strip_pin, name="Strip", numleds=strip_count)
        self.buzzer  = PassiveBuzzer(buz_pin)
        self.anim = PetAnimator(self.display, body_rgb565=DisplayILI9341.rgb565(160,100,40), scale=2)

        self.svc = ActionService(self.display, self.lights, self.buzzer, animator=self.anim)

        self.pets=[Pet("Mochi"),Pet("Pico")]
        self._idx=0
        self.buttons=[Button(pin,name=f"Btn{i+1}",handler=self) for i,pin in enumerate(btn_pins)]
        self._pressed=set(); self._hold_ms=None; self._latch=False
        self._show_welcome()

    @property
    def pet(self): return self.pets[self._idx%len(self.pets)]

    def _show_welcome(self):
        self.display.clear(0x0000)
        self.display.showText(f"Hello {self.pet.name}",8,8)
        self.display.showStatus(self.pet)
        # after showStatus in _show_welcome and _rotate:
        self.anim.draw(16, 118, 0) 


    def _rotate(self):
        self._idx=(self._idx+1)%len(self.pets)
        self.display.showText(f"Pet: {self.pet.name}",8,8)
        self.lights.setColor((0,80,180)); self.buzzer.beep(523,80); self.lights.off()
        time.sleep(0.2)
        self.display.showStatus(self.pet); self.anim.draw(8,130,0)

    def buttonPressed(self,name):
        self._pressed.add(name)
        if len(self._pressed)==len(self.buttons) and not self._latch:
            self._hold_ms=time.ticks_ms()
        idx=[b._name for b in self.buttons].index(name)
        if   idx==0: self.svc.doFeed(self.pet)
        elif idx==1: self.svc.doPlay(self.pet)
        elif idx==2: self.svc.doSleep(self.pet)

    def buttonReleased(self,name):
        self._pressed.discard(name)
        self._hold_ms=None
        if not self._pressed: self._latch=False

    def run(self):
        tick = 0  # initialize the counter first
        while True:
            if self._hold_ms is not None and not self._latch:
                if time.ticks_diff(time.ticks_ms(), self._hold_ms) >= HOLD_MS_SWITCH:
                    self._rotate()
                    self._latch = True
                    self._hold_ms = None

            # small idle animation every few seconds
            if tick % 300 == 0:
                self.anim.idle_cycle(16, 118, loops=1, delay_ms=100)


            tick += 1
            time.sleep_ms(10)

