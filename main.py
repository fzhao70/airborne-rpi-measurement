"""
raspberry pi 4 airborne measurement system

Press is start
Up is Pause
Down is Resume

"""
import time
import datetime
import functools
from threading import Thread
from sense_hat import SenseHat
from get_gps import gps_init, get_gps, gps_clean
from get_sense import get_sense
from get_sensor import get_sensor
from get_pistatus import get_pistatus

def starter(sense):
    sense.clear()
    while True:
        sense.show_message("Welcome", scroll_speed = 0.05)
        for event in sense.stick.get_events():
            if event.action == "pressed":
                if event.direction == "middle":
                    sense.show_message("Start", scroll_speed = 0.05)
                    return 0

        time.sleep(0.1)

def logger(log_name, data):
    #print(data)
    with open(log_name, "a") as fout:
        for i in data:
            fout.write(str(i)+',')

        fout.write('\n')

    return 0

def logger_init():
    header = "time,lat,lon,alt,speed,climb,track,pressure,rh,temp,rx,ry,rz,accx,accy,accz,volt,pi_temp,"
    curr = datetime.datetime.now()
    log_name = f"logger_{curr.year:04d}-{curr.month:02d}-{curr.day:02d}_{curr.hour:02d}-{curr.minute:02d}-{curr.second:02d}.log"
    with open(log_name, "w") as fout:
        print("Start Logging at " + log_name)
        fout.write(header + "\n")

    return log_name

def thread_host(func, result, index, *args):
    try:
        result[index] = func(*args)
    except Exception as e:
        result[index] = f"Error: {e}"

if __name__ == "__main__":
    while True:
        try:
            gpsd_socket, data_stream = gps_init()
            sense_device = SenseHat()
            break
        except OSError:
            continue

    sense_device.clear()
    sense_device.show_message("Start", scroll_speed = 0.05)
    pause_flag = False

    results = [None] * 3
    params_sensor_1 = (gpsd_socket, data_stream)
    params_sensor_2 = sense_device

    starter(sense_device)
    file_out = logger_init()

    while True:
        while True:
            for event in sense_device.stick.get_events():
                if event.action == "pressed":
                    if event.direction == "up":
                        sense_device.show_message("Pause", scroll_speed = 0.05)
                        pause_flag = True
                    elif event.direction == "down":
                        sense_device.show_message("Resume", scroll_speed = 0.05)
                        pause_flag = False

            if pause_flag:
                continue
                time.sleep(0.5)
            else:
                break

        thread_list = [
                 Thread(target=thread_host, args=(get_gps, results, 0, *params_sensor_1)),
                 Thread(target=thread_host, args=(get_sense, results, 1, params_sensor_2)),
                 Thread(target=thread_host, args=(get_pistatus, results, 2)),
               ]

        for thread_item in thread_list:
            thread_item.start()

        for thread_item in thread_list:
            thread_item.join()

        result_item = functools.reduce(lambda a, b: a+b, results)

        logger(file_out, result_item)

        sense_device.clear()

