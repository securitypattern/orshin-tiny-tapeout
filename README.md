# Power analysis of three designs in TinyTapeout 02 board

This GitHub project enables the acquisition and analysis of power traces using a Teledyne LeCroy oscilloscope connected to a TinyTapeout board. For further information, refer to Deliverable D3.3 of the ORSHIN project.

## Devices

- TinyTapeout 02 board (https://tinytapeout.com/runs/tt02/)
- ESP32 board
- Teledyne LeCroy oscilloscope with probes (https://www.teledynelecroy.com/oscilloscope/) for the acquisitions
- Power supply

## Organization of the repository

- [TTSerial] is a Python file that allows to connect to the TinyTapeout board throug the serial port
- [TT02_traces_acquisition] is a Python script that connects to the oscilloscope and, utilizing functions from [TTSerial], acquires power traces from the TT02 while it runs one of the three specific studied designs: projects 44, 91, or 92.
- [Analysis_with_LED_connected], [Analysis_with_LED_disconnected] and [Deeper_analysis_with_more_acq_traces] are notebooks that allow to replicate the analysis done in deliverable D3.3 of the ORSHIN project.
- Common functions used in all the three notebooks are collected in [TT02_functions_for_analysis_library].
- The power traces upladed in the notebooks are saved in [acquisition] folder.

## How to use the repository

- [Analysis of traces]: in the folder [acquisition] there are some previously acquired traces, that can be uploaded and analysed running code in the notebooks.
- [Acquisition of new traces]: it is possible to acquire new traces running the Python file [TT02_traces_acquisition]. Note that for each acquisition campaign the name of the folder in which the traces are saved should be changed, and the acquisition values should be checked.