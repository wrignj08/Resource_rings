import time
import serial
import psutil
import subprocess as sp
from serial.tools.list_ports import comports
from typing import List

# Constants
teensy_serial_id = "8434600"
leds_per_ring = 16
gpu_max_temperature = 90
gpu_min_temperature = 50
cpu_max_temperature = 90
cpu_min_temperature = 38


# Utility function
def convert_output_to_list(output: bytes) -> List[str]:
    """
    Converts the output from bytes to list of strings.
    :param output: The output in bytes.
    :return: List of strings.
    """
    return output.decode("ascii").split("\n")[:-1]


# Functions
def get_gpu_temperature() -> float:
    """
    Gets the current GPU temperature and calculates the percentage it represents
    of the max temperature. :return: The percentage of the max temperature that
    the current temperature represents.
    """
    command = "nvidia-smi --query-gpu=temperature.gpu --format=csv"
    gpu_temp_info = convert_output_to_list(sp.check_output(command.split()))[1:]
    gpu_temperature = int(gpu_temp_info[0].split()[0])
    temperature_percentage = (gpu_temperature - gpu_min_temperature) / (
        gpu_max_temperature - gpu_min_temperature
    )
    return max(0, temperature_percentage)


def get_gpu_memory_usage() -> float:
    """
    Calculates the percentage of GPU memory that is currently used.
    :return: The percentage of GPU memory that is currently used.
    """
    command = "nvidia-smi --query-gpu=memory.used --format=csv"
    memory_used_info = convert_output_to_list(sp.check_output(command.split()))[1:]
    memory_used = int(memory_used_info[0].split()[0])

    command = "nvidia-smi --query-gpu=memory.total --format=csv"
    memory_total_info = convert_output_to_list(sp.check_output(command.split()))[1:]
    memory_total = int(memory_total_info[0].split()[0])

    percent_used = memory_used / memory_total
    return percent_used


def get_gpu_utilization() -> float:
    """
    Gets the current GPU utilization.
    :return: The current GPU utilization.
    """
    command = "nvidia-smi --query-gpu=utilization.gpu --format=csv"
    utilization_info = convert_output_to_list(sp.check_output(command.split()))[1:]
    gpu_utilization = float(utilization_info[0].split(" %")[0]) / 100
    return gpu_utilization


def get_ram_usage() -> float:
    """
    Gets the percentage of virtual memory that is currently used.
    :return: The percentage of virtual memory that is currently used.
    """
    ram_usage = psutil.virtual_memory().percent / 100
    return ram_usage


def get_total_cpu_usage() -> float:
    """
    Gets the percentage of CPU that is currently being used.
    :return: The percentage of CPU that is currently being used.
    """
    total_cpu_usage = psutil.cpu_percent(interval=0.1) / 100
    return total_cpu_usage


def get_max_cpu_core_usage() -> float:
    """
    Gets the maximum CPU core utilization.
    :return: The maximum CPU core utilization.
    """
    max_cpu_usage = max(psutil.cpu_percent(interval=0.1, percpu=True)) / 100.0  # type: ignore  # noqa: E501
    return max_cpu_usage


def get_cpu_temperature() -> float:
    """
    Gets the current CPU temperature and calculates the percentage it represents
    of the max temperature. :return: The percentage of the max temperature that
    the current temperature represents.
    """
    cpu_temperature = psutil.sensors_temperatures()["k10temp"][1].current
    temperature_percentage = (cpu_temperature - cpu_min_temperature) / (
        cpu_max_temperature - cpu_min_temperature
    )
    return max(0, temperature_percentage)


while True:
    try:
        ports = comports(include_links=False)
        teensy_port = next(
            (i for i, port in enumerate(ports) if teensy_serial_id in port.hwid), None
        )

        if teensy_port is not None:
            with serial.Serial(ports[teensy_port].device, 9600, timeout=0.1) as arduino:
                total_cpu_usage = str(round(leds_per_ring * get_total_cpu_usage()))
                max_cpu_core_usage = str(
                    round(leds_per_ring * get_max_cpu_core_usage())
                )
                cpu_temperature = str(round(leds_per_ring * get_cpu_temperature()))
                ram_usage = str(round(leds_per_ring * get_ram_usage()))
                gpu_memory_usage = str(round(leds_per_ring * get_gpu_memory_usage()))
                gpu_utilization = str(round(leds_per_ring * get_gpu_utilization()))
                gpu_temperature = str(round(leds_per_ring * get_gpu_temperature()))

                arduino.write(
                    f"<{max_cpu_core_usage},{total_cpu_usage},{ram_usage},{gpu_utilization},{gpu_memory_usage},{gpu_temperature},{cpu_temperature}>".encode()
                )

                print(
                    f"Max core usage = {max_cpu_core_usage}\n"
                    f"Total CPU usage = {total_cpu_usage}\n"
                    f"RAM usage = {ram_usage}\n"
                    f"GPU usage = {gpu_utilization}\n"
                    f"GPU memory usage = {gpu_memory_usage}\n"
                    f"GPU temperature = {gpu_temperature}\n"
                    f"CPU temperature = {cpu_temperature}\n"
                )
                time.sleep(0.5)
    except Exception as e:
        print(e)
        time.sleep(1)
        print("retry")
