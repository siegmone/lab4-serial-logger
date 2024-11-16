import argparse
import serial
from datetime import datetime, timedelta
import time
import os
import numpy as np
from utils import parse_arguments



def secs_in_day(dt):
    return dt.hour*3600 + dt.minute*60 + dt.seconds


def hex2dec(h):
    return int(h, base=16)


def unpack_from_raw(data):
    start = data.find("aaaa")
    data = data[start:].split("aaaa")
    p_raw = np.array([[p[:4], p[4:]] for p in data if p])
    p_rec = np.array([[convert_rh(p[:4]), convert_temp(p[4:])]
                     for p in data if p])
    return p_raw, p_rec


def unpack_from_array(data):
    data[0] = data[0][data[0].find("aaaa"):]
    return "\n".join(data)


def print_info(dt, now, t0):
    elapsed = timedelta(seconds=(now - t0))
    dt_formatted = dt.strftime("%Y-%m-%d_%H:%M:%S")  # format
    print(f"\n{dt_formatted} - elapsed: {elapsed}")


# RAW -- Nlettura - tempo lettura - nbyte - byteletti
# Ntrigger - Anno - Mese - Giorno - Secondiingiorno - umiditàraw - umiditàreco - tempraw - tempreco
def data_acquisition(ser, tmax, sleep, checkpoint):
    t0 = time.time()
    raw_data = ""
    header_raw = "Ntrigger\tTempoLettura(ms)\tByteRicevuti\tDatiLetti"
    checkpoint.write(header_raw)
    idx, rd_tme, dts, n_bytes, data = [], [], [], [], []
    while True:
        idx.append(idx[-1])
        now = time.time()
        dts.append(datetime.now())
        print_info(dts[-1], now, t0)
        if now - t0 > tmax:
            print("Time limit reached. Acquisition stopped.")
            break
        read(ser, raw_data, data, n_bytes)
        rd_tme.append(round((time.time() - now) * 1000, 3))
        time.sleep(sleep / 1000)
        checkpoint.write(
            f"\n{idx[-1]}\t{rd_tme[-1]}\t{n_bytes[-1]}\t{data[-1]}"
        )
    return idx, rd_tme, dts, n_bytes, data, raw_data


def read(ser, raw_data, data, n_bytes):
    incoming_data = ""
    n = ser.in_waiting
    if n:  # read that many bytes
        print(f"Reading {n} bytes")
        incoming_data = ser.read(n).hex()
        print("Received: ", incoming_data)
        raw_data += incoming_data
        data.append(incoming_data)
        n_bytes.append(n)
    else:
        print("No data received.")


def convert_temp(temp_hex):
    d1 = 1
    d2 = 1
    temp = hex2dec(temp_hex)
    return d1 + d2 * temp


def convert_rh(rh_hex):
    rh = hex2dec(rh_hex)
    c1, c2, c3 = 1, 1, 1
    return c1 + c2 * rh + c3 * (rh ** 2)
