class Buff:
    def __init__(self, name, duration, value):
        self.name = name
        self.duration = duration
        self.value = value

    def use(self):
        self.duration -= 1
        if self.duration == 0:
            return -self.value
        return 0
