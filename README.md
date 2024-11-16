# Lab4 Serial Logger
This is a logger I developed for the class *"Laboratorio di Fisica"* during my Master's Degree in Physics at the University of Naples Federico II.

## Description
This is a simple logger that reads data from a serial port in the following hexadecimal format:
```
0xAAAA 0xXXXX 0xXXXX
```
Where the first two bytes `0xAAAA` are a header to pinpoint the start of a data packet.
And the following 4 bytes represent the data, divided in 2 bytes each in a *Relative Humidity* measurement
and a *Temperature* measurement.

The logger reads the data from the serial port, converts it and logs it into a pair of files
with timestamp information.
