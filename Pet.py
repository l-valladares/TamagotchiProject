# Pet.py
class Pet:
    def __init__(self, name="Mochi"):
        self.name = name
        self.mood = 5
        self.hunger = 5
        self.energy = 5

    def feed(self):
        self.hunger = max(0, self.hunger - 2)
        self.mood = min(10, self.mood + 1)

    def play(self):
        self.mood = min(10, self.mood + 2)
        self.energy = max(0, self.energy - 1)
        self.hunger = min(10, self.hunger + 1)

    def sleep(self):
        self.energy = min(10, self.energy + 3)
        self.hunger = min(10, self.hunger + 1)

    def get_status(self):
        return f"M:{self.mood} H:{self.hunger} E:{self.energy}"
