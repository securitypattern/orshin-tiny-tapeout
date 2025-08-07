#=================================================
# Copyright (c) 2025, Security Pattern
# All rights reserved.
#
#    This file is part of: Side-channel analysis of three designs in Tiny Tapeout board.
#    
#    SPDX-License-Identifier: MIT 
#=================================================

############
## IMPORT ##
############

import glob
import numpy as np
# modify the default parameters of np.load
np_load = np.load
load_mod = lambda *a,**k: np_load(*a, allow_pickle=True, **k)
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.palettes import Category10 as palette
colors = palette[10]
from bokeh.resources import INLINE
import zarr
from os.path import basename
from os.path import join

# Bokeh colors legend:
# 0 -> blue
# 1 -> orange
# 2 -> green
# 3 -> red
# 4 -> purple
# 5 -> brown
# 6 -> pink
# 7 -> gray
# 8 -> green/yellow
# 9 -> light blue

###########################
## SHOW FIGURE FUNCTIONS ##
###########################

# show one figure figure
# def show_fig(trace,Title="",int_col=0):
#     output_notebook()
#     p = figure(title=Title)
#     p.xaxis.axis_label = "Samples"
#     xrange = list(range(len(trace)))
#     p.line(xrange, trace, line_color=colors[int_col])
#     show(p)
    
# # show one figure with trigger
# def show_fig_trigger(trace,trigger,Title="",int_col=0):
#     output_notebook(INLINE)
#     p = figure(title=Title)
#     p.xaxis.axis_label = "Samples"
#     xrange = list(range(len(trace)))
#     p.line(xrange, trace, line_color=colors[int_col])
#     p.line(xrange, trigger, line_color=colors[8])
#     show(p)

# show many figures together
def show_many_figs(traces,Title="",int_col=0):
    output_notebook(INLINE)
    p = figure(title=Title)
    p.xaxis.axis_label = "Samples"
    xrange = list(range(len(traces[0])))
    i = 0
    for t in traces:
        p.line(xrange, t, line_color=colors[int_col[i]])
        i = i+1
    show(p)

# def align_trace(traces):
#     M = np.mean(traces, axis=0)
#     return M - M[0]*np.ones(len(M))

#############################
## FUNCTIONS ON THE TRACES ##
#############################
 
# Load data and traces from acquisitions -> very slow function
def load_data_traces(folder): 
    count = 0
    c = 0
    for file_data in glob.glob(folder+"/data*"):
        c = c+1
        if c%100==0:
            print(c)
        s = file_data[len(file_data)-19:]
        file_traces = glob.glob(folder+"/traces*"+s)
        t = load_mod(file_traces[0])
        if len(t)>0:
            if count == 0 : 
                traces = t
                data = load_mod(file_data)
                count += 1
            else : 
                if len(t[0])==len(traces[0]):
                    traces = np.concatenate((traces, t))
                    data = np.concatenate((data, load_mod(file_data)))    
    traces = np.array(traces)
    return(data,traces)

# Load all traces into a zarr file
def load_traces(file_path, num_traces, trace_len, traces_per_file, zarr_path):
    trace_file_pattern = "traces_*.npy"
    skip_traces = []
    # Set Zarr output file
    target_chunk_size = traces_per_file*25
    traces = zarr.open(zarr_path, mode='w', shape=(num_traces, trace_len),
                      chunks=(target_chunk_size, trace_len), dtype='float32')    
    # Get traces files
    fnames = glob.glob(join(file_path, trace_file_pattern))
    #print(join(file_path, trace_file_pattern))
    #print(f"Found {len(fnames)} traces files\n")    
    buffer = []
    start = 0
    current_count = 0
    for fname in sorted(fnames):
        # Load npy file
        #print("Processing file: ", basename(fname))
        tblock = np.load(fname)
        if (len(tblock)==0) or (len(tblock[0])!=trace_len):
            skip_traces = skip_traces + [fname[len(fname)-19:]]
            continue
        #print(f"{tblock.shape[0]} traces loaded")
        # Temporarily accumulate traces until chunk size reached
        buffer.append(tblock)
        current_count += tblock.shape[0]
        # Store new chunk
        if current_count >= target_chunk_size:
            chunk = np.concatenate(buffer, axis=0)
            traces[start:start + current_count] = chunk.astype(np.float32)
            start += current_count
            buffer = []
            current_count = 0
    # Finish storing last traces in case they don't fill a whole chunk
    if(current_count > 0):
        chunk = np.concatenate(buffer, axis=0)
        traces[start:start + current_count] = chunk.astype(np.float32)            
    print(f"Zarr dataset created at {zarr_path}, shape={traces.shape}\n")
    return skip_traces

# Load input data into a Numpy array
def load_inputs(file_path, skip_traces):    
    data_file_pattern = "data_*.npy"
    # inputs = np.empty(num_traces, dtype='|S576') # need to know input length in advance 
    inputs = []
    fnames = glob.glob(join(file_path, data_file_pattern))
    for fname in sorted(fnames):
        if fname[len(fname)-19:] in skip_traces:
            continue
        #print("Processing file: ", basename(fname))
        block = np.load(fname)
        #print(f"{len(block)} inputs loaded")        
        inputs.append(block)
    return np.concatenate(inputs, axis=0)

# Function that removes the traces that are not correct
def clean_traces(traces,data):
    t = [traces[0]]
    d = [data[0]]
    for i in range(len(traces)-1):
        if(not(all(traces[i]==traces[i+1]))):
            t = t + [traces[i+1]]
            d = d + [data[i+1]]
    return t,d

# In the set of traces that are such that:
# - at time t0 the input bits are all zero
# - at time t1 the input bits are different
# This function takes only the data and traces that describe the transition from t0 to t1
def traces_from_zero_to_not_zero(traces,data):
    t = []
    d = []
    for i in range(len(traces)):
        if(sum(data[i][0])>0):
            t = t + [traces[i]]
            d = d + [data[i]]
    return t,d

# In the set of traces that are such that:
# - at time t0 the input bits are all zero
# - at time t1 the input bits are different
# This function takes only the data and traces that describe the transition from t1 to t0
def traces_from_not_zero_to_zero(traces,data):
    t = []
    d = []
    for i in range(len(traces)):
        if(sum(data[i][0])==0):
            t = t + [traces[i]]
            d = d + [data[i]]
    return t,d

# Compute the derivation of the traces, that is the difference between trace at time t and trace at time t+1
def deriv(traces,data):
    dif = []
    for i in range(len(traces)-1):
        dif = dif + [traces[i+1]-traces[i]]
    diff_data = data[1:]
    return dif,diff_data

# Defference of means
def DoM(data,traces,sel_func):
    traces_secret_0 = []
    traces_secret_1 = []
    for l in range(len(data)):
        if(sel_func(data[l][0])):
            traces_secret_1 = traces_secret_1 + [traces[l]]
        else:
            traces_secret_0 = traces_secret_0 + [traces[l]]
    diff = np.mean(traces_secret_1,axis=0)-np.mean(traces_secret_0,axis=0)
    return diff, traces_secret_0, traces_secret_1

# t-test
def tvla_1_Order(traces_fixed, traces_random):
    nb_of_traces_fixed = traces_fixed.shape[0]
    nb_of_traces_random = traces_random.shape[0]
    M1_r = np.mean(traces_random, axis=0)
    CM2_r = np.var(traces_random, axis=0)
    M1_f = np.mean(traces_fixed, axis=0)
    CM2_f = np.var(traces_fixed, axis=0)
    dist = M1_f - M1_r
    den = np.sqrt((CM2_f/nb_of_traces_fixed) + (CM2_r/nb_of_traces_random))
    return dist/den

# definition of the sets h0 and h1 depending on a "sel function", sets fo the t-test
def definition_h0_h1(data, traces, sel_fun):
    traces_2s_h0 = []
    traces_2s_h1 = []
    for i in range(len(traces)):
        if(sel_fun(data[i][0])):
            traces_2s_h1 = traces_2s_h1 + [traces[i]]
        else:
            traces_2s_h0 = traces_2s_h0 + [traces[i]]
    return traces_2s_h0,traces_2s_h1

#####################
## OTHER FUNCTIONS ##
#####################

# Hamming weight
def HW(input):
    for i in range(len(input)): 
        if input[i]>1:        
            return print("error: a string of bit is required as input")
    return sum(input)

# Hamming distance
def HD(input1, input2):
    if len(input1) != len(input2): return print("error: the len of the inputs is different")
    for i in range(len(input1)): 
        if input1[i]>1 or input2[i]>1:        
            return print("error: a string of bit is required as input")
    res = []
    for i in range(len(input1)):
        res = res + [(input1[i] + input2[i])%2]
    return sum(res)


