#! /usr/bin/python3

import sys
import os
import argparse
import serial
from serial import Serial
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE
import time
from datetime import datetime
import subprocess

import threading
import queue

DATA_QUEUE = queue.Queue()
SERIAL_OPEN = False
STOP_EVENT = threading.Event()  # Global stop signal

PACKET_SIZE = 6


def convert_rh(rh_raw, temp) -> float:
    c1 = -2.0468
    c2 = 0.0367
    c3 = -1.5955e-6
    rh1 = c1 + c2 * rh_raw + c3 * (rh_raw ** 2)
    t1 = 0.01
    t2 = 0.00008
    return (temp - 25) * (t1 + t2 * rh_raw) + rh1


def convert_temp(temp_raw) -> float:
    d1 = -39.7
    d2 = 0.01
    return d1 + d2 * temp_raw


def reset_arduino(ser: Serial) -> None:
    ser.setDTR(False)
    time.sleep(1)
    ser.setDTR(True)


def parse_arguments():
    # init parser
    parser = argparse.ArgumentParser(
        description="Data acquisition script for lab4.",
        epilog="For any doubts, ask Simone."
    )

    # add arguments
    parser.add_argument(
        "hours",
        type=float,
        help="How many hours should the program run."
    )

    parser.add_argument(
        "-p", "--port",
        default="/dev/ttyUSB0",
        type=str,
        metavar="<port>",
        help="Specify which port to use. (default: '/dev/ttyUSB0')\n"
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
    return args

def serial_thread(port: str, sleep_time: int, data_queue: queue.Queue) -> None:
    global SERIAL_OPEN
    try:
        ser = serial.Serial(port=port, baudrate=115200, bytesize=EIGHTBITS,
                            parity=PARITY_NONE, stopbits=STOPBITS_ONE)
        if ser.isOpen():
            SERIAL_OPEN = True
            print("Port opened correctly")

        time.sleep(2)

        subprocess.run(f"cat -v < {port}", shell=True, stdout=subprocess.PIPE)
        print(f"Buffer cleared on {port}")

        while not STOP_EVENT.is_set():
            data = ser.read_all()
            data_queue.put(data)  # Add data to the queue
            time.sleep(sleep_time / 1000)
        ser.close()

    except Exception as e:
        print(f"Serial exception: {e}")
    finally:
        SERIAL_OPEN = False
        sys.exit(1)


def main() -> None:
    args = parse_arguments()
    hours = args.hours
    port = args.port
    sleep_time = args.sleep

    dt = datetime.now()
    dt_fmt = dt.strftime("%Y-%m-%d_%H-%M-%S")  # format
    filename = f"UtenteX_Gruppo21_{dt_fmt}"

    subprocess.run("mkdir -p data", shell=True, stdout=subprocess.PIPE)

    file_raw = open(f"./data/{filename}_RAW.txt", "w")
    file_data = open(f"./data/{filename}.txt", "w")

    file_raw.write(f"{dt_fmt}\n")
    file_data.write("Trigger Data Ora RH_Raw T_Raw RH T\n")

    buf = bytearray()
    header = b"\xAA\xAA"
    header_size = len(header)

    trigger, count = 0, 0
    start = time.time()
    now = start
    max_seconds = hours * 3600

    thread_serial = threading.Thread(
        target=serial_thread, args=(port, sleep_time, DATA_QUEUE))

    try:
        while now - start < max_seconds:
            if thread_serial is None or not thread_serial.is_alive():
                # Create a new thread instance every time it needs to be restarted
                thread_serial = threading.Thread(
                    target=serial_thread, args=(port, sleep_time, DATA_QUEUE))
                thread_serial.start()
                start = time.time()
                now = start

            count += 1

            # Redundant time calculation
            now = time.time()
            dt_now = datetime.now()
            dt_now_fmt = dt_now.strftime("%H:%M:%S.%f")[:-3]  # format

            try:
                data = DATA_QUEUE.get(timeout=10 * sleep_time / 1000)
            except queue.Empty:
                print(f"[{dt_now_fmt}] - No data received.")
                continue

            buf += data
            print(f"[{dt_now_fmt}] - got {len(data)} bytes: {data.hex()}")
            file_raw.write(f"{dt_now_fmt} {count} {data.hex()}\n")

            while len(buf) >= PACKET_SIZE:
                idx = buf.find(header)
                if idx == -1:
                    break
                elif len(buf) - idx >= PACKET_SIZE:
                    trigger += 1

                    rh_raw = int.from_bytes(
                        buf[idx + 2: idx + 4], byteorder="big")
                    t_raw = int.from_bytes(
                        buf[idx + 4: idx + 6], byteorder="big")

                    t = convert_temp(t_raw)
                    rh = convert_rh(rh_raw, t)

                    quotient = int(len(buf) / PACKET_SIZE)
                    milli = (dt_now.microsecond / 1000) - \
                        sleep_time + (sleep_time / quotient)
                    dt_now_date = dt_now.strftime("%Y-%m-%d")
                    dt_now_tod = dt_now.strftime("%H:%M")
                    file_data.write(f"{trigger:8d} {dt_now_date} {dt_now_tod}:{
                        (dt_now.second + (milli/1000)):3.3f} {rh_raw} {t_raw} {rh:.3f} {t:.3f}\n")

                    buf = buf[idx + PACKET_SIZE:]
                else:
                    break
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        STOP_EVENT.set()

        if thread_serial is not None:
            thread_serial.join()
        file_raw.close()
        file_data.close()


if __name__ == "__main__":
    main()
