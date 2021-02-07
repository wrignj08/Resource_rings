import os
import sys
import time
import serial
import serial.tools.list_ports
import psutil
import subprocess as sp

teensy_serial_ID = '8434600'

leds_per_ring = 16

GPU_max_temp = 90
GPU_min_temp = 50

CPU_max_temp = 90
CPU_min_temp = 38

def get_GPU_temp():
    _output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]

    COMMAND = "nvidia-smi --query-gpu=temperature.gpu --format=csv"
    GPU_temp_info = _output_to_list(sp.check_output(COMMAND.split()))[1:]
    GPU_temp = [int(x.split()[0]) for i, x in enumerate(GPU_temp_info)]
    temp_pct = (GPU_temp[0]-GPU_min_temp)/(GPU_max_temp-GPU_min_temp)
    return temp_pct

def get_GPU_mem():
    _output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]

    COMMAND = "nvidia-smi --query-gpu=memory.used --format=csv"
    memory_used_info = _output_to_list(sp.check_output(COMMAND.split()))[1:]
    memory_used_values = [int(x.split()[0]) for i, x in enumerate(memory_used_info)]

    COMMAND = "nvidia-smi --query-gpu=memory.total --format=csv"
    memory_total_info = _output_to_list(sp.check_output(COMMAND.split()))[1:]
    memory_total_values = [int(x.split()[0]) for i, x in enumerate(memory_total_info)]

    pct_used = memory_used_values[0]/memory_total_values[0]
    return pct_used

def get_gpu_utilization():
    _output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]
    COMMAND = "nvidia-smi --query-gpu=utilization.gpu --format=csv"
    utilization_info = _output_to_list(sp.check_output(COMMAND.split()))[1:]
    utilization_values = [int(x.split()[0]) for i, x in enumerate(utilization_info)]
    
    gpu_utilization = float(utilization_info[0].split(' %')[0])/100
    return gpu_utilization

def get_ram():
    ram = dict(psutil.virtual_memory()._asdict())['percent']/100
    return ram

def get_total_cpu():
    total_cpu = psutil.cpu_percent(interval=.1)/100
    return total_cpu

def get_max_CPU_core():
    max_CPU = max(psutil.cpu_percent(interval=.1, percpu=True))/100
    return max_CPU

def get_CPU_temp():
    CPU_temp = psutil.sensors_temperatures()['coretemp'][0].current
    temp_pct = (CPU_temp-CPU_min_temp)/(CPU_max_temp-CPU_min_temp)
    return temp_pct
    
# loop forever
while True:
    ports = serial.tools.list_ports.comports(include_links=False)
    port_num = 0
    for port in ports:
        if teensy_serial_ID in port.hwid:
            teensy_port = port_num

        
        port_num += 1
        
    try:
        ports = serial.tools.list_ports.comports(include_links=False)
        
        arduino = serial.Serial(ports[teensy_port].device, 9600, timeout=.1)
        
        total_CPU = str(round(leds_per_ring*get_total_cpu()))
        max_CPU_core = str(round(leds_per_ring*get_max_CPU_core()))
        CPU_temp = str(round(leds_per_ring*get_CPU_temp()))
        
        RAM = str(round(leds_per_ring*get_ram()))
        
        GPU_RAM = str(round(leds_per_ring*get_GPU_mem()))
        GPU_util = str(round(leds_per_ring*get_gpu_utilization()))
        GPU_temp = str(round(leds_per_ring*get_GPU_temp()))

        arduino.write(str.encode('<'+max_CPU_core+','+total_CPU+','+RAM+','+GPU_util+','+GPU_RAM+','+GPU_temp+','+CPU_temp+'>'))
        print('max core =',max_CPU_core)
        print('total CPU =',total_CPU)
        print('RAM =',RAM)
        print('GPU =',GPU_util)
        print('VRM =',GPU_RAM)
        print('GPU = ',GPU_RAM)
        print('CPU = ',CPU_temp)
        time.sleep(0.5)
        
    except (OSError,IndexError):
        time.sleep(1)
        print('retry')
    
