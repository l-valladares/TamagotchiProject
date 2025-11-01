# ActionService.py
import utime

class ActionService:
    def __init__(self, display, lights, buzzer, animator=None):
        self.display, self.lights, self.buzzer, self.anim = display, lights, buzzer, animator

    def doFeed(self, pet):
        pet.feed()
        self.display.showText(f"{pet.name} is eating!",110,8)
        self.lights.setColor((0,200,80)); self.buzzer.beep(440,120)
        utime.sleep_ms(150); self.lights.off(); self.display.showStatus(pet)
        if self.anim:
            self.anim.happy_wiggle(16, 120, loops=2)

    def doPlay(self, pet):
        pet.play()
        self.display.showText("Play time!",110,8)
        self.lights.run(1); self.buzzer.beep(659,100)
        self.display.showStatus(pet)
        if self.anim:
            self.anim.happy_wiggle(16, 120, loops=2)

    def doSleep(self, pet):
        pet.sleep()
        self.display.showText("Nap time...",110,8)
        self.lights.run(0); self.buzzer.beep(392,80)
        self.display.showStatus(pet)
        if self.anim: self.anim.happy_wiggle(16, 118, loops=2)
