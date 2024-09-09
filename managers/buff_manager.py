class BuffManager:
    def __init__(self):
        self.buffs = []

    def add_buff(self, buff):
        if buff is None:
            return 0
        self.buffs.append(buff)
        return buff.value

    def use(self):
        total = 0

        for buff in self.buffs:
            total += buff.use()
            if buff.duration == 0:
                self.buffs.remove(buff)

        return total
