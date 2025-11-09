import time
from gps3 import gps3
from threading import Thread

def gps_init():
    gpsd_socket = gps3.GPSDSocket()
    gpsd_socket.connect()
    gpsd_socket.watch()
    data_stream = gps3.DataStream()

    return gpsd_socket, data_stream

def get_gps(gps_socket, data_stream):
    for new_data in gps_socket:
        if new_data:
            data_stream.unpack(new_data)
            data_list = [data_stream.TPV['time'],data_stream.TPV['lon'],data_stream.TPV['lat'],data_stream.TPV['alt'],
                         data_stream.TPV['speed'],data_stream.TPV['climb'],data_stream.TPV['track']]

            if (None in data_list) or ('n/a' in data_list):
                continue
            else:
                return data_list

        time.sleep(0.1)

def gps_clean(gpsd_socket):
    gpsd_socket.close()

def thread_host(func, result, index, *args):
    try:
        result[index] = func(*args)
    except Exception as e:
        result[index] = f"Error: {e}"

if __name__ == "__main__":
    gpsd_socket, data_stream = gps_init()
    results = [None, None]

    # Parameters for the sensor functions
    params_sensor_1 = (gpsd_socket, data_stream)

    # Start threads
    while True:
        # Create threads
        thread1 = Thread(target=thread_host, args=(get_gps, results, 0, *params_sensor_1))
        thread1.start()

        # Wait for threads to complete
        thread1.join()

        print(results)


    gps_clean(gpsd_socket)
