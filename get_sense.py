from sense_hat import SenseHat
import time

def get_sense(sense):
    while True:
        pressure = sense.get_pressure()
        if pressure <= 0:
            continue
        else:
            break
    humidity = sense.get_humidity()
    temp = sense.get_temperature()
    ori = sense.get_orientation()
    acc = sense.get_accelerometer_raw()
    return [pressure, humidity, temp,
            ori["pitch"], ori["roll"], ori["yaw"],
            acc['x'], acc['y'], acc['z'],
            ]

if __name__ == "__main__":
    while True:
        sense = SenseHat()
        print(get_sense(sense))
