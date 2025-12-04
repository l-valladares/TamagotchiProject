import time
from Button import Button
from pet import Pet
from StateModel import StateModel
from sprites_dog import DOG_IDLE
from sprites_tools import FOOD_ICON, PLAY_ICON, CLEAN_ICON
from sprites_dog_play import DOG_PLAY
from sprites_dog_eat import DOG_EAT
from sprites_dog_clean import DOG_CLEAN
from sprites_death import DEATH_SEQUENCE, DEATH_GHOST_LOOP

# Logical states for StateModel (used only for tracking, not for driving buttons)
STATE_IDLE = 0
STATE_PLAYING = 1
STATE_EATING = 2
STATE_CLEANING = 3
STATE_DEAD = 4


class TamaInputHandler:
    def __init__(self, game, buzzer):
        self.game = game
        self.buzzer = buzzer

    def buttonPressed(self, name):
        g = self.game
        try:
            print("buttonPressed called with:", name)
        except:
            pass

        # If the pet is dead, use feed+clean combo to revive
        if g.is_dead:
            if name == "feed":
                g.left_down = True
            elif name == "clean":
                g.right_down = True

            if g.left_down and g.right_down:
                g.revive_pet()
            return

        # Normal controls when alive
        if name == "feed":
            g.selected = (g.selected - 1) % len(g.menu_items)
            self.buzzer.beep(tone=500)

        elif name == "clean":
            g.selected = (g.selected + 1) % len(g.menu_items)
            self.buzzer.beep(tone=500)

        elif name == "play":
            current = g.menu_items[g.selected]
            if current == "food":
                g.start_eat_animation()
            elif current == "play":
                g.start_play_animation()
            elif current == "clean":
                g.start_clean_animation()

    def buttonReleased(self, name):
        g = self.game
        if name == "feed":
            g.left_down = False
        elif name == "clean":
            g.right_down = False


class TamaDisplay:
    def __init__(self, game):
        self.game = game

    def draw_sprite(self, x, y, sprite):
        g = self.game
        d = g.d
        for row, line in enumerate(sprite):
            for col, bit in enumerate(line):
                if bit == "1":
                    d.pixel(x + col, y + row, 1)

    def draw_icon(self, x, y, icon):
        g = self.game
        d = g.d
        for row, line in enumerate(icon):
            for col, pixel in enumerate(line):
                if pixel == "1":
                    d.pixel(x + col, y + row, 1)

    def draw_toolbar(self):
        g = self.game
        d = g.d
        y = 48
        d.fill_rect(0, y, 128, 16, 0)

        if g.is_dead:
            d.text("Game Over", 0, y, 1)
            d.text("Hold L+R", 0, y + 8, 1)
            return

        for i, item in enumerate(g.menu_items):
            x = 8 + i * 40
            if item == "food":
                icon = FOOD_ICON
            elif item == "play":
                icon = PLAY_ICON
            else:
                icon = CLEAN_ICON

            # Selected item: draw an underline instead of a box
            if i == g.selected:
                # underline under the icon area
                d.fill_rect(x - 4, y + 14, 24, 1, 1)

            self.draw_icon(x, y, icon)

    def draw_stat_hint(self):
        g = self.game
        d = g.d
        y = 40
        d.fill_rect(0, y, 128, 8, 0)
        if g.is_dead:
            d.text("RIP", 0, y, 1)
            return

        item = g.menu_items[g.selected]
        if item == "food":
            d.text("Food:{}".format(g.pet.hunger), 0, y, 1)
        elif item == "play":
            d.text("Happy:{}".format(g.pet.happy), 0, y, 1)
        elif item == "clean":
            d.text("Dirty:{}".format(g.pet.dirty), 0, y, 1)

    def draw_pet(self, x, y):
        g = self.game
        d = g.d

        if g.is_dead:
            if g.death_index < len(DEATH_SEQUENCE):
                sprite = DEATH_SEQUENCE[g.death_index]
            else:
                loop_idx = (g.death_index - len(DEATH_SEQUENCE)) % len(DEATH_GHOST_LOOP)
                sprite = DEATH_GHOST_LOOP[loop_idx]
            d.fill_rect(x, y, 32, 32, 0)
            self.draw_sprite(x, y, sprite)
            return

        if g.is_playing:
            sprite = DOG_PLAY[g.play_index]
        elif g.is_eating:
            sprite = DOG_EAT[g.eat_index]
        elif g.is_cleaning:
            sprite = DOG_CLEAN[g.clean_index]
        else:
            sprite = DOG_IDLE[g.frame]

        d.fill_rect(x, y, 32, 32, 0)
        self.draw_sprite(x, y, sprite)

    def draw(self):
        g = self.game
        d = g.d
        d.fill(0)
        d.text(g.pet.name, 0, 0, 1)
        d.text(g.pet.mood(), 80, 0, 1)
        self.draw_pet(48, 12)
        self.draw_stat_hint()
        self.draw_toolbar()
        d.show()


class TamaGame:
    def __init__(self, display, buzzer, feed_pin, play_pin, clean_pin, pir_sensor=None):
        self.d = display
        self.buzzer = buzzer
        self.pet = Pet("Mochi")

        self.menu_items = ["food", "play", "clean"]
        self.selected = 0

        # idle frame
        self.frame = 0
        self.last_anim = time.ticks_ms()
        self.last_tick = time.ticks_ms()

        # play animation
        self.is_playing = False
        self.play_index = 0
        self.last_play_frame = time.ticks_ms()

        # eat animation
        self.is_eating = False
        self.eat_index = 0
        self.eat_loops = 0
        self.last_eat_frame = time.ticks_ms()

        # clean animation
        self.is_cleaning = False
        self.clean_index = 0
        self.clean_loops = 0
        self.last_clean_frame = time.ticks_ms()

        # death / revive
        self.is_dead = False
        self.zero_since = None
        self.death_index = 0
        self.death_last_frame = time.ticks_ms()
        self.left_down = False
        self.right_down = False

        # PIR sensor
        self.pir_sensor = pir_sensor
        if self.pir_sensor is not None:
            self.pir_sensor.setHandler(self)

        # Helper classes
        self.input_handler = TamaInputHandler(self, buzzer)
        self.display = TamaDisplay(self)

        # Buttons wired to TamaInputHandler (WORKING PATH)
        self.feed_button = Button(pin=feed_pin, name="feed", handler=self.input_handler)
        self.play_button = Button(pin=play_pin, name="play", handler=self.input_handler)
        self.clean_button = Button(pin=clean_pin, name="clean", handler=self.input_handler)

        # --- StateModel integration (tracking only, doesn't own buttons) ---
        self.state_model = StateModel(5, handler=self, debug=False)
        self.current_state = STATE_IDLE
        self.state_model.start()

    # ======= StateModel handler methods (minimal) =======

    def stateEntered(self, state, event):
        # We already set flags in start_* methods; no extra work needed here.
        # This exists so we are a valid StateModel handler for the assignment.
        pass

    def stateLeft(self, state, event):
        pass

    def stateEvent(self, state, event):
        # We are not using event-driven transitions right now.
        return False

    def stateDo(self, state):
        # We are not using stateModel.run(), so this is unused.
        pass

    # ======= Sensor callbacks (for PIR) =======

    def sensorTripped(self, name):
        if name == "PIR":
            if self.is_dead:
                return
            if not (self.is_playing or self.is_eating or self.is_cleaning):
                self.play_happy_jingle()
                if self.pet.happy < 10:
                    self.pet.happy += 1
                self.start_play_animation()

    def sensorUntripped(self, name):
        pass

    # ======= Mechanics / animations =======

    def revive_pet(self):
        old_name = self.pet.name
        self.pet = Pet(old_name)

        self.is_dead = False
        self.zero_since = None
        self.death_index = 0
        self.death_last_frame = time.ticks_ms()

        self.is_playing = False
        self.is_eating = False
        self.is_cleaning = False

        self.left_down = False
        self.right_down = False

        # reset stats
        self.pet.hunger = 80
        self.pet.happy = 80
        self.pet.energy = 80
        self.pet.dirty = 0

        # update logical state
        self.current_state = STATE_IDLE
        self.state_model.gotoState(STATE_IDLE, "revive_combo")

    def start_play_animation(self):
        if self.is_dead:
            return
        self.is_playing = True
        self.is_eating = False
        self.is_cleaning = False
        self.play_index = 0
        self.last_play_frame = time.ticks_ms()
        self.buzzer.beep(tone=1000)

        self.current_state = STATE_PLAYING
        self.state_model.gotoState(STATE_PLAYING, "start_play")

    def start_eat_animation(self):
        if self.is_dead:
            return
        self.pet.feed()
        self.is_eating = True
        self.is_playing = False
        self.is_cleaning = False
        self.eat_index = 0
        self.eat_loops = 0
        self.last_eat_frame = time.ticks_ms()
        self.buzzer.beep(tone=750)

        self.current_state = STATE_EATING
        self.state_model.gotoState(STATE_EATING, "start_eat")

    def start_clean_animation(self):
        if self.is_dead:
            return
        self.pet.clean()
        self.is_cleaning = True
        self.is_playing = False
        self.is_eating = False
        self.clean_index = 0
        self.clean_loops = 0
        self.last_clean_frame = time.ticks_ms()
        self.buzzer.beep(tone=600)

        self.current_state = STATE_CLEANING
        self.state_model.gotoState(STATE_CLEANING, "start_clean")

    def play_happy_jingle(self):
        for tone in (1200, 1500, 1800):
            self.buzzer.beep(tone=tone)
            time.sleep_ms(80)

    def check_death_condition(self):
        if self.is_dead:
            return
        if (
            self.pet.hunger == 0
            and self.pet.happy == 0
            and self.pet.energy == 0
            and self.pet.dirty == 100
        ):
            now = time.ticks_ms()
            if self.zero_since is None:
                self.zero_since = now
            else:
                if time.ticks_diff(now, self.zero_since) >= 5:
                    self.start_death_animation()
        else:
            self.zero_since = None

    def start_death_animation(self):
        self.is_dead = True
        self.is_playing = False
        self.is_eating = False
        self.is_cleaning = False
        self.death_index = 0
        self.death_last_frame = time.ticks_ms()

        self.current_state = STATE_DEAD
        self.state_model.gotoState(STATE_DEAD, "stats_zero")

    def update_pet(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_tick) >= 1000:
            self.last_tick = now
            if not self.is_dead:
                self.pet.tick()
            self.check_death_condition()

    def update_anim(self):
        now = time.ticks_ms()

        if self.is_dead:
            if time.ticks_diff(now, self.death_last_frame) >= 250:
                self.death_last_frame = now
                self.death_index += 1
            return

        if time.ticks_diff(now, self.last_anim) >= 200:
            self.last_anim = now
            self.frame = (self.frame + 1) % len(DOG_IDLE)

        if self.is_playing and time.ticks_diff(now, self.last_play_frame) >= 160:
            self.last_play_frame = now
            self.play_index = (self.play_index + 1) % len(DOG_PLAY)
            if self.play_index == 0:
                self.is_playing = False
                # one-shot transition back to idle
                self.current_state = STATE_IDLE
                self.state_model.gotoState(STATE_IDLE, "anim_done_play")

        if self.is_eating and time.ticks_diff(now, self.last_eat_frame) >= 180:
            self.last_eat_frame = now
            self.eat_index = (self.eat_index + 1) % len(DOG_EAT)
            if self.eat_index == 0:
                self.eat_loops += 1
                if self.eat_loops >= 2:
                    self.is_eating = False
                    self.eat_loops = 0
                    self.current_state = STATE_IDLE
                    self.state_model.gotoState(STATE_IDLE, "anim_done_eat")

        if self.is_cleaning and time.ticks_diff(now, self.last_clean_frame) >= 180:
            self.last_clean_frame = now
            self.clean_index = (self.clean_index + 1) % len(DOG_CLEAN)
            if self.clean_index == 0:
                self.clean_loops += 1
                if self.clean_loops >= 3:
                    self.is_cleaning = False
                    self.clean_loops = 0
                    self.current_state = STATE_IDLE
                    self.state_model.gotoState(STATE_IDLE, "anim_done_clean")

    def draw(self):
        self.display.draw()

    def run(self):
        while True:
            self.update_pet()
            self.update_anim()
            self.draw()
            time.sleep_ms(30)
