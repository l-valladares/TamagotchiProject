# PetSprite.py
# 24x24 multi-frame dog, scaled with rects (no big buffers) for Pico + ILI9341 lite driver.
import utime

W, H = 24, 24

# Legend: '.' = background, 'D' = brown body, 'K' = black (eyes/nose)
# You can paste your own rows for DOG0_ROWS ... DOG7_ROWS later. Must be 24 strings of 24 chars each.

DOG0_ROWS = [
"..........DDDD....DDDD..",
"..........DDDD....DDDD..",
"............DDDDDDDD....",
"............DDDDDDDD....",
"............DDKKDDKKDD..",
"............DDKKDDKKDD..",
"............DDKKDDKKDDKK",
"..DD........DDDDDDDDDDKK",
"..DD........DDDDDDDDDD..",
"DD..........DDDDDDDDDD..",
"DD..........DDDDDDDDDD..",
"DD....DDDDDDDDDDDDDD....",
"DD....DDDDDDDDDDDDDD....",
"..DDDDDDDDDDDDDDDD......",
"..DDDDDDDDDDDDDDDD......",
"....DDDDDDDDDDDDDD......",
"....DDDDDDDDDDDDDD......",
"....DDDDDDDDDDDDDD......",
"....DDDDDDDDDDDDDD......",
"....DDDDDDDDDDDDDD......",
"....DD..DD..DD..DD......",
"....DD..DD..DD..DD......",
"....DD..DD..DD..DD......",
"....DD..DD..DD..DD......",
]

# Slight variations to create an 8-frame idle cycle (tail/ear/torso nudges).
# Replace any of these with your extracted frames DOG1_ROWS..DOG7_ROWS if you want exact art.

DOG1_ROWS = [r for r in DOG0_ROWS]
row = list(DOG1_ROWS[7]);  row[2] = '.'; DOG1_ROWS[7] = "".join(row)          # tail tip down 1
row = list(DOG1_ROWS[8]);  row[2] = 'D'; DOG1_ROWS[8] = "".join(row)

DOG2_ROWS = [r for r in DOG0_ROWS]
row = list(DOG2_ROWS[4]);  row[12] = 'D'; DOG2_ROWS[4] = "".join(row)         # tiny chest lift
row = list(DOG2_ROWS[5]);  row[12] = 'D'; DOG2_ROWS[5] = "".join(row)

DOG3_ROWS = [r for r in DOG1_ROWS]
row = list(DOG3_ROWS[5]);  row[12] = '.'; DOG3_ROWS[5] = "".join(row)         # chest relax
row = list(DOG3_ROWS[6]);  row[12] = '.'; DOG3_ROWS[6] = "".join(row)

DOG4_ROWS = [r for r in DOG0_ROWS]
row = list(DOG4_ROWS[0]);  row[10] = '.'; row[11] = 'D'; DOG4_ROWS[0] = "".join(row)  # ear tweak

DOG5_ROWS = [r for r in DOG1_ROWS]
row = list(DOG5_ROWS[0]);  row[10] = 'D'; row[11] = '.'; DOG5_ROWS[0] = "".join(row)  # ear back

DOG6_ROWS = [r for r in DOG0_ROWS]
row = list(DOG6_ROWS[20]); row[6]  = '.'; DOG6_ROWS[20]= "".join(row)         # paw nudge
row = list(DOG6_ROWS[21]); row[6]  = 'D'; DOG6_ROWS[21]= "".join(row)

DOG7_ROWS = [r for r in DOG1_ROWS]
row = list(DOG7_ROWS[20]); row[10] = '.'; DOG7_ROWS[20]= "".join(row)
row = list(DOG7_ROWS[21]); row[10] = 'D'; DOG7_ROWS[21]= "".join(row)

FRAMES_ROWS = [DOG0_ROWS, DOG1_ROWS, DOG2_ROWS, DOG3_ROWS, DOG4_ROWS, DOG5_ROWS, DOG6_ROWS, DOG7_ROWS]

def _pack_monohlsb(rows, char):
    """Pack rows for specific 'char' into 1-bit MONO_HLSB mask (3 bytes per row for 24 px)."""
    b = bytearray(H * (W // 8))  # 24 px -> 3 bytes/row
    for y in range(H):
        row = rows[y]
        for x in range(W):
            if row[x] == char:
                idx = y * 3 + (x >> 3)
                b[idx] |= (1 << (x & 7))  # LSB is leftmost pixel
    return b

# Build masks for all frames (body + eyes)
FRAMES_MASKS = []
for rows in FRAMES_ROWS:
    body = _pack_monohlsb(rows, 'D')
    eyes = _pack_monohlsb(rows, 'K')
    FRAMES_MASKS.append((body, eyes))

class PetAnimator:
    def __init__(self, display, *, body_rgb565=0xC480, eye_rgb565=0x0000, bg_rgb565=0xFFFF, shadow_rgb565=0x4208, scale=2):
        self.d = display
        self.body = body_rgb565
        self.eye  = eye_rgb565
        self.bg   = bg_rgb565
        self.shadow = shadow_rgb565
        self.scale = max(1, int(scale))
        self.n = len(FRAMES_MASKS)

    @staticmethod
    def _mask_bit(mask, x, y):
        return (mask[y*3 + (x>>3)] >> (x & 7)) & 1

    def _draw_mask_scaled(self, x0, y0, mask, color):
        s = self.scale
        for y in range(H):
            yy = y0 + y * s
            run = 0
            start = 0
            for x in range(W):
                on = self._mask_bit(mask, x, y)
                if on and run == 0:
                    start = x; run = 1
                elif on:
                    run += 1
                elif run:
                    self.d.rect(x0 + start*s, yy, run*s, s, color, True)
                    run = 0
            if run:
                self.d.rect(x0 + start*s, yy, run*s, s, color, True)

    def _draw_frame_scaled(self, x0, y0, body_mask, eye_mask):
        s = self.scale
        self.d.rect(x0 + 2*s, y0 + H*s, W*s, 2*s, self.shadow, True)  # shadow
        self._draw_mask_scaled(x0, y0, body_mask, self.body)
        self._draw_mask_scaled(x0, y0, eye_mask,  self.eye)

    def draw(self, x, y, frame_idx=0):
        self.d.rect(x, y, W*self.scale, H*self.scale + 2*self.scale, self.bg, True)  # clear
        body, eyes = FRAMES_MASKS[frame_idx % self.n]
        self._draw_frame_scaled(x, y, body, eyes)

    # --- animations ---
    def idle_cycle(self, x, y, loops=1, delay_ms=120):
        for _ in range(loops):
            for i in range(self.n):
                self.draw(x, y, i)
                utime.sleep_ms(delay_ms)
        self.draw(x, y, 0)

    def happy_wiggle(self, x, y, loops=1, delay_ms=90):
        for _ in range(loops):
            self.draw(x, y, 0); utime.sleep_ms(delay_ms)
            self.draw(x, y, 3); utime.sleep_ms(delay_ms)
        self.draw(x, y, 0)
