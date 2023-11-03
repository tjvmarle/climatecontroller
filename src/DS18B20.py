"""Module to take temperature measurements with this probe. 
"""

from typing import List, Tuple
from w1thermsensor import W1ThermSensor, Sensor

import datetime as dt

probes = {"020891778863": "probe_1",
          "02099177d0a2": "probe_2"}


def get_temps() -> List[Tuple[str, float]]:
    """Retrieves temperature readings from connected probes.

    Returns:
        List[float]: List of temperatures, to one decimal.
    """
    results = []
    for sensor in W1ThermSensor.get_available_sensors([Sensor.DS18B20]):
        sensor_temp = round(sensor.get_temperature(), 1)
        results.append((probes[sensor.id], sensor_temp))

    temp_text = [f"{temp}°C" for _, temp in results]
    print(f"Probe temps: {', '.join(temp_text)}.")
    return results


if __name__ == "__main__":
    temps = get_temps()
    for probe_id, probe_temp in temps:
        print(f"Probe: {probe_id}, Temp: {probe_temp}")
