import argparse
import numpy as np
import serial
from datetime import datetime, timedelta
import time
import os


def hex2dec(h):
    return int(h, base=16)


def unpack(data):
    packets= []
    for i in range(0, len(data), 4):
        if data[i:i+4] == "aaaa" and i+4 < len(data):
            packets.append(data[i+4:i+12])
    packets_raw = np.array([[p[:4],p[4:]] for p in packets if p[:4] and p[4:]])
    hums = packets_raw[:,0]
    temps = packets_raw[:,1]

    #packets_rec [[convert_rh(p[:4]), convert_temp(p[:4]) for p in data if p
    return hums, temps

# RAW -- Nlettura - tempo lettura - nbyte - byteletti
# Ntrigger - Anno - Mese - Giorno - Secondiingiorno - umiditàraw - umiditàreco - tempraw - tempreco
def data_acquisition(ser, tmax, sleep, checkpoint):
    sid = []
    t0 = time.time()
    flag = True
    data = ""
    trigger = 0
    checkpoint.write("Ntrigger TempoLettura(ms) ByteRicevuti DatiLetti")
    
    while True:
        trigger += 1
        now = time.time()
        elapsed = timedelta(seconds=(now - t0))
        dt = datetime.now()
        dt_formatted = dt.strftime("%Y-%m-%d_%H:%M:%S")  # format
        year, month, day, hour, min, sec, micro = dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond
        sid.append(hour*3600 + min*60 + sec + (micro/1e6))
        if now - t0 > tmax:
            print("Time limit reached. Acquisition stopped.")
            break
        print(f"\n{dt_formatted} - elapsed: {elapsed}")
        n_bytes = ser.in_waiting
        if n_bytes:  # read that many bytes
            print(f"Reading {n_bytes} bytes")
            incoming_data = ser.read(n_bytes).hex()
            print("Received: ", incoming_data)
            data += incoming_data
            if flag:
                start = time.time()
                flag = False
        else:
            incoming_data = b"".hex()
            print("No data received.")

        time.sleep(sleep / 1000)
        checkpoint.write(f"\n{trigger+1} {round((sid[-1]), 3)} {n_bytes} {incoming_data}")
    end = time.time()  # forse ci vuole solo tempo (elapsed?)
    return data, start, end, sid[0]


def convert_temp(temp_hex):
    d1, d2 = -39.7, 0.01
    temp_so = [hex2dec(t) for t in temp_hex if t]
    temp = [t*d2 + d1 for t in temp_so]   
    return temp


def convert_rh(rh_hex):
    c1, c2, c3 = -2.04681, 0.0367, -1.5955*10**-6
    rh_so = [hex2dec(h) for h in rh_hex if h]
    rh = [c1 + c2*r + c3*(r**2) for r in rh_so]
    return rh, rh_so


def compensate_rh(rh, rh_so, temp):
    t1, t2 = 0.01, 0.00008
    rh_comp = []
    for i in range(len(rh_so)):
        rh_comp.append((temp[i] - 25) * (t1 + t2 * rh_so[i]) + rh[i])
    return rh_comp


# init parser
parser = argparse.ArgumentParser(
        description="Data acquisition script for lab4.",
        epilog="For any doubts, ask Simone."
        )

# add arguments
parser.add_argument(
        "hours",
        type=int,
        help="How many hours should the program run."
        )

modes = ["read", "readline"]
parser.add_argument(
        "-m", "--mode",
        default="read",
        choices=modes,
        help="Specify how to read the incoming data ['read', 'readline']."
        )

ports = [f"/dev/ttyUSB{i}" for i in range(99)]
parser.add_argument(
        "-p", "--port",
        default="/dev/ttyUSB0",
        choices=ports,
        metavar="<port>",
        help="Specify which port to use. (default: '/dev/ttyUSB0')"
        )

parser.add_argument(
        "-s", "--sleep",
        default=400,
        type=int,
        metavar="<time>",
        help="Set sleep time in ms. (default: '400ms')"
        )

# parse args and set variables
args = parser.parse_args()

acqHours = args.hours
sleep = args.sleep
mode = args.mode
port = args.port

# set initial datetime
dtStart = datetime.now()
dtStartFormatted = dtStart.strftime("%Y-%m-%d %H:%M:%S")
t0 = time.time()
acqSecs = acqHours * 60  # set to 3600 to convert to seconds

# filename template
fn_dt = dtStart.strftime("%Y%m%d%H%M%S")
filename = f"data/sht75_Hum_Temp_RUN_{fn_dt}_{acqHours}_h_RAW.txt"
chk_filename = f"{filename}.checkpoint"
reconstructed = open(f"data/sht75_Hum_Temp_RUN_{fn_dt}_{acqHours}_h_RECONSTRUCTED.txt", "w")
reconstructed.write("Ntrigger Anno Mese Giorno SecondiInGiorno HUM_RAW HUM_REC TEMP_RAW TEMP_REC")
    
# init serial port
ser = serial.Serial(
        port=port,
        baudrate=115200,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
        )

while not ser.is_open:
    print("Port didn't open correctly.\nRetrying\n.\n.\n.")
    ser.open()
print(f"Port {ser.port} opened correctly.\n")

print(f"Data acquisition @ {dtStartFormatted}")

# print serial interface information
print(f"""
DEVICE:
    Name: {ser.name}
    Port: {ser.port}
    Baudrate: {ser.baudrate}
    Timeout: {ser.timeout} sec
    Bytesize: {ser.bytesize} bits
    Parity: {ser.parity}
""")

# create checkpoint file in mode "w=write"
checkpoint = open(chk_filename, "w")

print("Starting Communication...")
try:
    data, start, end, sid = data_acquisition(
            ser=ser,
            tmax=acqSecs,
            sleep=sleep,
            checkpoint=checkpoint
            )
except Exception as e:
    # safety exit to checkpoint
    print(f"Encountered exception: {e}")
except KeyboardInterrupt:
    # exit message
    print("\nAcquisition interrupted by user.")
finally:
    # cleanup
    print("\nSaving to checkpoint.")
    checkpoint.close()
    print("Closing port.")
    ser.close()
hum_raw, temp_raw = unpack(data)

temp_rec = convert_temp(temp_raw)
rh, rh_so = convert_rh(hum_raw)
hum_rec = compensate_rh(rh, rh_so, temp_rec)

N = len(temp_rec)
times = np.linspace(0, end - start, N)

for n in range(N):
    reconstructed.write(f"\n{n+1} {dtStart.year} {dtStart.month} {dtStart.day} {(sid + times[n]):.3f} {hex2dec(hum_raw[n])} {hum_rec[n]:.2f} {hex2dec(temp_raw[n])} {temp_rec[n]:.2f}")

# renaming checkpoint file to actual output file
print(f"\nWriting to file {filename}")
os.rename(chk_filename, filename)

