#=================================================
# Copyright (c) 2025, Security Pattern
# All rights reserved.
#
#    This file is part of: Side-channel analysis of three designs in Tiny Tapeout board.
#    This file allows to connect to an oscilloscope and to acquire from that power traces from a Tiny Tapeout board.
#
#    SPDX-License-Identifier: MIT 
#=================================================

import pyvisa as visa
from pyvisa.resources import MessageBasedResource
import numpy as np
import time
import os
import datetime
from TTSerial import TTSerial
import random

#############################
## Definition of functions ##
#############################


# input: integer n
# output: bitstring which value corrensponds to n
def bitfield(n):
    return [1 if digit=='1' else 0 for digit in bin(n)[2:]]


# inputs: 
# - i is the input expressed as integer
# - p is the gadget under analysis 
#          p = 0 for chi with DOM
#          p = 1 for chi with 2 shares
#          p = 2 for chi with 3 shares
# output: bitstring which value corrensponds to n, ready to be given as input to Tiny Tapeout
def arrange_input(i,p):
    if p < 0 or p > 2: return print("no correct project")
    i_bin = (bitfield(i))
    i_bin.reverse()   
    if (p == 0):
        i_bin = [0] + i_bin
    elif(p == 1):
        i_bin = [0,0,0,0] + i_bin             
    for j in range(8-len(i_bin)): i_bin = i_bin + [0]
    return i_bin


# Call the oscilloscope
# Note: change with the VICP of your instrument
rm = visa.ResourceManager()
scope = rm.open_resource('VICP::169.254.241.160::INSTR', resource_pyclass=MessageBasedResource)
print(scope.query("*IDN?"))
scope.write("COMM_HEADER OFF")


# Capture traces function
# inputs:
# - ser: serial port which comunicates with Tiny Tapeout
# - input: input that are transmitted to the Tiny Tapeout
# - channel: the channel in which are read the traces on the Oscilloscope
# - acq: True if the read traces are qcuired, False otherwise
def capture_trace(ser, input, channel, acq=True):
    # Arm the oscilloscope
    if type(scope) == MessageBasedResource:
        scope.write(r"""vbs 'app.acquisition.triggermode = "stop" ' """)
        scope.write(r"""vbs 'app.acquisition.triggermode = "single" ' """)
    else:
        scope.arm()
    time.sleep(1)
    # Connect throught the serial
    ser.set_input(input)
    time.sleep(1.5)
    out = ser.read_output()
    time.sleep(1)
    # Acquisition
    if acq == True:
        if type(scope) == MessageBasedResource:
            curve = scope.query(r"""vbs? 'return=Join(app.Acquisition.{}.Out.Result.DataArray(0),",")' """.format(channel))
            t = np.array([int(x) / 256 for x in curve.strip().split(',')], dtype=np.float32)
        else:
            scope.capture()
            t = scope.get_last_trace()
    else:
        t = []
    dataout = [input]+[out]
    return dataout, t


# Acquisition traces function
# inputs:
# - project_name: name of the folder in which the traces are saved
# - ser: serial port which comunicates with Tiny Tapeout
# - input: input that are transmitted to the Tiny Tapeout
# - channel: the channel in which are read the traces on the Oscilloscope
# - acq: True if the read traces are qcuired, False otherwise
def acqTrace(project_name, ser, input, channel, acq=True):
    project = [project_name]
    for pn in project:
        if not os.path.exists(pn):
            os.makedirs(pn)
    traces = []
    data = []
    res, t = capture_trace(ser, input, channel, acq=acq)
    if res is not None:
        traces.append(t)
        data.append(res)       
    timestr = time.strftime("%Y%m%d-%H%M%S")
    for i, pn in enumerate(project):
        np.save(os.path.join(pn, "traces_" + timestr + ".npy"), traces)
        np.save(os.path.join(pn, "data_" + timestr + ".npy"), data)



############
### MAIN ###
############

ser = TTSerial('\COM5') 
# choose the project: 
# p = 0 for chi with DOM
# p = 1 for chi with 2 shares
# p = 2 for chi with 3 shares
p = 1
# ntraces = number of traces
n_traces = 1000
# State the project, define n = 2^(numb of bits in input), name the folder
if (p == 0):
    ser.set_project(44)
    n = 128
    project_file = "./acquisition/chiDOM"
elif(p == 1):
    ser.set_project(91)
    n = 16
    project_file = "./acquisition/chi2shares"
elif(p == 2):
    ser.set_project(92)
    n = 256
    project_file = "./acquisition/chi3shares"
else:
    print("Error in the choice of the project")
# Name the folder of the test: remember to modify it at each execution!
project_file = project_file+"/Date_Bandwidth_Numberofsamples_Frequency_Secperdiv_Otherinfo" 
# Inpunt definition: i_t0 all the bits are 0
i_t0 = 0
i_t0_bin = arrange_input(i_t0,p)
# Inpunt definition: i_t1 all the bits are 1
i_t1 = n-1
i_t1_bin = arrange_input(i_t1,p)
# Inpunt definition: i_t2 an half of the bits are 0 and an half 1
if(p==1):
    i_t2 = 3
else:
    i_t2 = 7
i_t2_bin = arrange_input(i_t2,p)

# ACQUISITION of the trigger
now = datetime.datetime.now()
acqTrace(project_file+"/trigger", ser, i_t0_bin, "C1", acq=True)

# ACQUISITION: input at time t0 (previous input) and at time t1 (current input) are equal, and are all zeros
for k in range(n_traces):
    # computation with the input at t0 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_0", ser, i_t0_bin, "C2", acq=True)
    # computation with the input at t1 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_0", ser, i_t0_bin, "C2", acq=True)

# ACQUISITION: input at time t0 (previous input) has all bits at zero
#              input at time t1 (current input) has all bits at one
for k in range(n_traces):
    # computation with the input at t0 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_1", ser, i_t0_bin, "C2", acq=True)
    # computation with the input at t1 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_1", ser, i_t1_bin, "C2", acq=True)

# ACQUISITION: input at time t0 (previous input) and input at time t1 (current input) 
#              have an half of the bits different
for k in range(n_traces):
    # computation with the input at t0 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_7", ser, i_t0_bin, "C2", acq=True)
    # computation with the input at t1 (prec input)
    now = datetime.datetime.now()
    acqTrace(project_file+"/t0_0_t1_7", ser, i_t2_bin, "C2", acq=True)

# ACQUISITION: random inputs
for k in range(n_traces):
    i_rand = random.randint(0,n-1)
    i_rand_bit = arrange_input(i_rand,p)
    now = datetime.datetime.now()
    acqTrace(project_file+"/random", ser, i_rand_bit, "C2", acq=True)

