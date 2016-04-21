from utils.smartplug import SmartPlug


p = SmartPlug("edimax.fritz.box", ('admin', '1234'))
p.state = "OFF"
p.state = "ON"
print(p.state)

