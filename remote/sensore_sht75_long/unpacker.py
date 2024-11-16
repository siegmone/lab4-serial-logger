from datetime import datetime as dt
import numpy as np

path = "/home/simon/projects/lab4/remote/sensore_sht75_notte/data"
# filename = f"{path}/sht75_Hum_Temp_RUN_20231214035426_15_h_RAW.txt"
filename = f"{path}/sht75_Hum_Temp_RUN_20231214040926_15_h_RAW.txt"
sleep_time = 1200


def convert_temp(temp_raw):
    d1, d2 = -39.7, 0.01
    return d1 + d2 * temp_raw


def convert_rh(rh_raw, temp):
    c1, c2, c3 = -2.0468, 0.0367, -1.5955e-6
    rh = c1 + c2 * rh_raw + c3 * (rh_raw ** 2)
    t1, t2 = 0.01, 0.00008
    return (temp - 25) * (t1 + t2 * rh_raw) + rh


def hex2dec(h):
    return int(h, base=16)


def split_bytes(string):
    return [string[i:i+4] for i in range(0, len(string), 4)]


data = np.loadtxt(filename, delimiter=" ", dtype=str, skiprows=2, unpack=True)
N, seconds_in_day, n_bytes, incoming_data = data
length = len(N)

bytes_matrix = []
for i in range(length):
    bytes_matrix.extend(split_bytes(incoming_data[i]))

bytes_transf, n_call = [], []
for b in incoming_data:
    count = 0
    for i in range(0, len(b), 2):
        bytes_transf.append(b[i:i+2])
        if b[i:i+4] == 'aaaa':
            count += 1
    n_call.append(count)

data_packet = []
for i in range(len(bytes_transf)):
    if len(bytes_transf) >= (i+6) and bytes_transf[i] == 'aa' and bytes_transf[i+1] == 'aa':
        data_packet.append(bytes_transf[i:i+6])

times = []
for t in range(len(seconds_in_day)):
    for n in range(n_call[t]):
        times.append('{:.3f}'.format(
            float(seconds_in_day[t]) + float(n)*sleep_time/float(n_call[t])))
times.pop()

count_eff = []
for i in range(1, len(times) + 1):
    count_eff.append(i)


bytes_list = []
for i in bytes_matrix:
    if i == 'aaaa':
        bytes_list = bytes_matrix[bytes_matrix.index(i):]


aaaa_pos = []

for i in range(0, len(bytes_list) - 1):
    if bytes_list[i] == 'aaaa':
        aaaa_pos.append(i)
aaaa_pos.pop()

temp_raw = []
hum_raw = []
temp_conv = []
hum_conv = []

for i in aaaa_pos:
    hum_hex = bytes_list[i+1]
    temp_hex = bytes_list[i+2]
    raw_hum = hex2dec(hum_hex)
    raw_temp = hex2dec(temp_hex)
    temp = convert_temp(raw_temp)
    hum = convert_rh(raw_hum, temp)
    hum_raw.append(raw_hum)
    temp_raw.append(raw_temp)
    hum_conv.append(hum)
    temp_conv.append(temp)


dtStart = dt.now()


with open('reconstructed.txt', 'w') as f:
    columns = [
        'Ntrigger',
        'Anno', 'Mese', 'Giorno', 'SecondiInGiorno',
        'HUM_RAW', 'HUM_REC', 'TEMP_RAW', 'TEMP_REC'
    ]
    f.write(" ".join(columns) + "\n")
    for n in range(len(temp_conv)):
        datetime = f"{dtStart.year} {dtStart.month} {dtStart.day} {times[n]}"
        hum = f"{hum_raw[n]} {hum_conv[n]:.2f}"
        temp = f"{temp_raw[n]} {temp_conv[n]:.2f}"
        f.write(
            f"{n+1} {datetime} {hum} {temp}\n"
        )
