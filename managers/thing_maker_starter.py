from data.things.potato_plant import PotatoPlant
from data.things.potato_types import PotatoType
from data.things.probetato import Probetato
from data.things.upgrade import Upgrade


class ThingMakerStarter:
    def __init__(self, thing_maker):
        self.thing_maker = thing_maker

    def start(self):
        things = [
            PotatoType("SolarPanel", power_output=0.0885),
            PotatoType("Potato", power_output=1.0),
            Probetato("Probetato", power_output=8.0),
            PotatoType("Spudnik", power_output=42.0),
            PotatoPlant("PotatoPlant", power_output=230),
        ]

        upgrades = [
            Upgrade("CleanSolarPanels", target="SolarPanel", multiplier=0.3 / 0.1, cost=140),
            Upgrade("SolarAmbience", target="SolarPanel", multiplier=0.0942 / 0.0885, cost=2600),
            Upgrade("MarisPipers", target="Potato", multiplier=2, cost=8000),
            Upgrade("PolishedSolarPanels", target="SolarPanel", multiplier=1 / 0.3, cost=15000),
            Upgrade("MarisPeers", target="Potato", multiplier=2, cost=160000),
            Upgrade("ProbetatoRoots", target="Probetato", multiplier=4, cost=180000),
            Upgrade("GoldenSolarPanels", target="SolarPanel", multiplier=4, cost=500000),
            Upgrade("GoldenSpudnikFoil", target="Spudnik", multiplier=2, cost=600000),
            Upgrade("ProbetatoPlanters", target="Probetato", multiplier=2, cost=1800000),
        ]

        for upgrade in upgrades:
            upgrade.set_injection(self.thing_maker)

        self.thing_maker.add_things(things)
        self.thing_maker.add_things(upgrades)
