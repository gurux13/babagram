import Mock.GPIO as MockGPIO

overrides = {}

def override_value(channel, value):
    global overrides
    overrides[channel] = value

def input(channel):
    if channel in overrides:
        return overrides[channel]
    return MockGPIO.HIGH

MockGPIO.input = input