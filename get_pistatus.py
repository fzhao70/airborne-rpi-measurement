import subprocess as sp

def call(x):
    while True:
        result = sp.check_output(x, shell = True)
        if result:
            return result.decode('utf-8').strip()

def get_pistatus():
    rpiv = call("vcgencmd measure_volts core").split('=')[1]
    rpit = call("vcgencmd measure_temp").split('=')[1]
    return [rpiv, rpit]

if __name__ == "__main__":
    print(get_pistatus())
