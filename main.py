# main.py
from Gadget import Gadget

def main():
    g = Gadget(
        btn_pins=(16, 17, 18),
        strip_pin=9, strip_count=16,
        buz_pin=14,
        spi_id=0, sck=2, mosi=3, miso=-1, cs=5, dc=6, rst=20,
        rotation=1
    )
    g.run()

if __name__ == "__main__":
    main()
