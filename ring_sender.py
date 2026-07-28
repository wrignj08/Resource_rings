import subprocess as sp
import sys
import time
from typing import Callable, Dict, List, NamedTuple, Optional

import psutil
import serial
from serial.tools.list_ports import comports
from tqdm.auto import tqdm

# Constants
teensy_serial_id = "8434600"
leds_per_ring = 16
gpu_max_temperature = 100
gpu_min_temperature = 20
cpu_max_temperature = 100
cpu_min_temperature = 20

poll_interval = 0.4
reconnect_interval = 2.0
nvidia_smi_timeout = 2.0
nvidia_smi_retry_interval = 30.0
cpu_sensor_names = ("k10temp", "coretemp", "zenpower", "cpu_thermal", "acpitz")
cpu_sensor_labels = ("tctl", "tdie", "package id 0")

# Last known good value per metric, used when a source stops responding.
last_good_values: Dict[str, float] = {}
# Errors already reported, so a permanently broken source is not logged forever.
reported_errors: set = set()
# Time before which nvidia-smi should not be called again after a failure.
nvidia_smi_retry_after = 0.0


# Utility functions
def convert_output_to_list(output: bytes) -> List[str]:
    """
    Converts the output from bytes to list of strings.
    :param output: The output in bytes.
    :return: List of strings.
    """
    return output.decode("ascii").split("\n")[:-1]


def write(message: str) -> None:
    """
    Prints a message on the same stream as the progress bars, so it is not
    corrupted by them or lost to buffering.
    :param message: The message to print.
    """
    tqdm.write(message, file=sys.stderr)


def log_once(key: str, message: str) -> None:
    """
    Prints a message the first time a given failure is seen.
    :param key: Identifier for the failure.
    :param message: The message to print.
    """
    if key not in reported_errors:
        reported_errors.add(key)
        write(message)


def safe_metric(name: str, getter: Callable[[], float]) -> float:
    """
    Calls a metric getter, falling back to the last known good value (or 0) if it
    fails, so one dead source cannot stop the other rings.
    :param name: Name of the metric, used for caching and error reporting.
    :param getter: Callable returning the metric as a 0-1 fraction.
    :return: The metric clamped to 0-1.
    """
    try:
        value = getter()
        if value != value:  # NaN
            raise ValueError("metric returned NaN")
        value = min(1.0, max(0.0, float(value)))
        last_good_values[name] = value
        reported_errors.discard(name)
        return value
    except Exception as e:
        log_once(name, f"{name} unavailable ({type(e).__name__}: {e}), using fallback")
        return last_good_values.get(name, 0.0)


# GPU polling
class GpuStats(NamedTuple):
    temperature: Optional[float]
    memory_used: Optional[float]
    memory_total: Optional[float]
    utilization: Optional[float]


def parse_float(value: str) -> Optional[float]:
    """
    Parses a value from nvidia-smi, tolerating "N/A" and other junk.
    :param value: The raw field value.
    :return: The value as a float, or None if it is not numeric.
    """
    try:
        return float(value.strip().split()[0])
    except (ValueError, IndexError):
        return None


def get_gpu_stats() -> GpuStats:
    """
    Queries all GPU values in a single nvidia-smi call. Any failure (driver
    missing, timeout, unparsable output) yields empty stats rather than raising,
    and backs off so a broken driver is not probed every cycle.
    :return: The GPU stats, with None for any field that could not be read.
    """
    global nvidia_smi_retry_after

    if time.monotonic() < nvidia_smi_retry_after:
        return GpuStats(None, None, None, None)

    command = (
        "nvidia-smi --query-gpu=temperature.gpu,memory.used,memory.total,"
        "utilization.gpu --format=csv,noheader,nounits"
    )
    try:
        output = sp.check_output(
            command.split(), stderr=sp.DEVNULL, timeout=nvidia_smi_timeout
        )
    except Exception as e:
        nvidia_smi_retry_after = time.monotonic() + nvidia_smi_retry_interval
        log_once(
            "nvidia-smi",
            f"nvidia-smi unavailable ({type(e).__name__}: {e}), "
            f"retrying every {nvidia_smi_retry_interval:.0f}s",
        )
        return GpuStats(None, None, None, None)

    nvidia_smi_retry_after = 0.0
    reported_errors.discard("nvidia-smi")
    lines = convert_output_to_list(output)
    if not lines:
        return GpuStats(None, None, None, None)

    fields = lines[0].split(",")
    if len(fields) < 4:
        return GpuStats(None, None, None, None)

    return GpuStats(*(parse_float(field) for field in fields[:4]))


def get_gpu_temperature(stats: GpuStats) -> float:
    """
    Calculates the percentage of the max temperature that the current GPU
    temperature represents.
    :param stats: The GPU stats for this cycle.
    :return: The percentage of the max temperature.
    """
    if stats.temperature is None:
        raise ValueError("no GPU temperature reading")
    return (stats.temperature - gpu_min_temperature) / (
        gpu_max_temperature - gpu_min_temperature
    )


def get_gpu_memory_usage(stats: GpuStats) -> float:
    """
    Calculates the percentage of GPU memory that is currently used.
    :param stats: The GPU stats for this cycle.
    :return: The percentage of GPU memory that is currently used.
    """
    if stats.memory_used is None or not stats.memory_total:
        raise ValueError("no GPU memory reading")
    return stats.memory_used / stats.memory_total


def get_gpu_utilization(stats: GpuStats) -> float:
    """
    Gets the current GPU utilization.
    :param stats: The GPU stats for this cycle.
    :return: The current GPU utilization.
    """
    if stats.utilization is None:
        raise ValueError("no GPU utilization reading")
    return stats.utilization / 100


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


def read_cpu_temperature() -> float:
    """
    Reads the CPU temperature from whichever sensor this machine exposes.
    :return: The CPU temperature in degrees C.
    """
    sensors = psutil.sensors_temperatures()  # type: ignore[attr-defined]
    if not sensors:
        raise ValueError("no temperature sensors exposed")

    names = [name for name in cpu_sensor_names if name in sensors]
    names += [name for name in sensors if name not in names]

    for name in names:
        entries = [e for e in sensors[name] if e.current]
        if not entries:
            continue
        for entry in entries:
            if (entry.label or "").lower() in cpu_sensor_labels:
                return entry.current
        return max(entry.current for entry in entries)

    raise ValueError("no usable temperature sensor reading")


def get_cpu_temperature() -> float:
    """
    Calculates the percentage of the max temperature that the current CPU
    temperature represents.
    :return: The percentage of the max temperature.
    """
    cpu_temperature = read_cpu_temperature()
    return (cpu_temperature - cpu_min_temperature) / (
        cpu_max_temperature - cpu_min_temperature
    )


def find_teensy_port() -> Optional[str]:
    """
    Finds the serial device for the teensy, if it is currently attached.
    :return: The device path, or None if it is not present.
    """
    try:
        ports = comports(include_links=False)
    except Exception as e:
        log_once("comports", f"could not list serial ports ({type(e).__name__}: {e})")
        return None

    reported_errors.discard("comports")
    for port in ports:
        if teensy_serial_id in (port.hwid or ""):
            return port.device
    return None


descs = [
    "Max CPU core usage",
    "Total CPU usage",
    "RAM usage",
    "GPU memory usage",
    "GPU utilization",
    "GPU temperature",
    "CPU temperature",
]
colours = [
    "magenta",
    "cyan",
    "magenta",
    "magenta",
    "magenta",
    "red",
    "red",
]

max_desc_len = max(len(d) for d in descs)

pbars = {}
for desc, colour in zip(descs, colours):
    pbar = tqdm(
        total=leds_per_ring,
        desc=desc.ljust(max_desc_len),
        unit="led",
        bar_format="{desc:<10}{n_fmt:>3}/{total_fmt} |{bar}|",
        colour=colour,
    )
    pbars[desc] = pbar

arduino: Optional[serial.Serial] = None

try:
    while True:
        try:
            if arduino is None:
                device = find_teensy_port()
                if device is None:
                    log_once("teensy", f"teensy {teensy_serial_id} not found, waiting")
                    time.sleep(reconnect_interval)
                    continue
                arduino = serial.Serial(device, 9600, timeout=0.1)
                reported_errors.discard("teensy")
                reported_errors.discard("serial")
                write(f"connected to teensy on {device}")

            gpu_stats = get_gpu_stats()

            fractions = {
                "Max CPU core usage": safe_metric(
                    "Max CPU core usage", get_max_cpu_core_usage
                ),
                "Total CPU usage": safe_metric("Total CPU usage", get_total_cpu_usage),
                "RAM usage": safe_metric("RAM usage", get_ram_usage),
                "GPU memory usage": safe_metric(
                    "GPU memory usage", lambda: get_gpu_memory_usage(gpu_stats)
                ),
                "GPU utilization": safe_metric(
                    "GPU utilization", lambda: get_gpu_utilization(gpu_stats)
                ),
                "GPU temperature": safe_metric(
                    "GPU temperature", lambda: get_gpu_temperature(gpu_stats)
                ),
                "CPU temperature": safe_metric("CPU temperature", get_cpu_temperature),
            }

            leds = {
                desc: round(leds_per_ring * value) for desc, value in fractions.items()
            }

            arduino.write(
                f"<{leds['Max CPU core usage']},{leds['Total CPU usage']},"
                f"{leds['RAM usage']},{leds['GPU utilization']},"
                f"{leds['GPU memory usage']},{leds['GPU temperature']},"
                f"{leds['CPU temperature']}>".encode()
            )

            for desc, pbar in pbars.items():
                pbar.n = leds[desc]
                pbar.refresh()

            time.sleep(poll_interval)

        except (serial.SerialException, OSError) as e:
            log_once("serial", f"serial error ({type(e).__name__}: {e}), reconnecting")
            log_once(
                "serial permissions",
                "for permission errors try running sudo usermod -a -G dialout $USER",
            )
            if arduino is not None:
                try:
                    arduino.close()
                except Exception:
                    pass
                arduino = None
            time.sleep(reconnect_interval)

        except Exception as e:
            write(f"unexpected error ({type(e).__name__}: {e}), retrying")
            time.sleep(reconnect_interval)

except KeyboardInterrupt:
    pass

finally:
    if arduino is not None:
        try:
            arduino.close()
        except Exception:
            pass
    for pbar in pbars.values():
        pbar.close()
