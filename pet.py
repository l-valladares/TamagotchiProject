class Pet:
    def __init__(self, name):
        self.name = name
        self.hunger = 50
        self.happy = 80
        self.energy = 80
        self.dirty = 0

    def tick(self):
        if self.hunger > 0:
            self.hunger -= 1
        if self.energy > 0:
            self.energy -= 1
        if self.dirty < 100:
            self.dirty += 2
        if self.happy > 0 and (self.hunger < 30 or self.energy < 30 or self.dirty > 60):
            self.happy -= 2

    def feed(self):
        self.hunger = min(100, self.hunger + 25)
        self.energy = min(100, self.energy + 5)

    def play(self):
        if self.energy > 10 and self.hunger > 10:
            self.happy = min(100, self.happy + 18)
            self.energy = max(0, self.energy - 10)
            self.hunger = max(0, self.hunger - 8)

    def clean(self):
        self.dirty = max(0, self.dirty - 40)
        self.happy = min(100, self.happy + 10)

    def mood(self):
        if self.hunger < 20 or self.energy < 20 or self.dirty > 80:
            return "Sad"
        if self.happy > 70 and self.dirty < 50:
            return "Happy"
        return "OK"
