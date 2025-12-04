import time
from machine import Pin, I2C
import ssd1306

from Log import Log
from Buzzer import PassiveBuzzer
from Sensors import DigitalSensor

from tama import TamaGame


def main():
    Log.i("Starting Mochi Tama")

    time.sleep(0.1)

    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)

    buzzer = PassiveBuzzer(pin=14, name="Buzz")
    pir = DigitalSensor(pin=10, name="PIR", lowActive=False)

    game = TamaGame(
        display=display,
        buzzer=buzzer,
        feed_pin=18,   # left nav
        play_pin=17,   # select button
        clean_pin=16,  # right nav
        pir_sensor=pir
    )
    game.run()


if __name__ == "__main__":
    main()
