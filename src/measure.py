"""Collection of methods to take measurements with the sensors connected to to GPIO's."""
from src.DHT20 import get_temp_and_humid
from src.DS18B20 import get_temps
from src.db_access import write_temperatures, write_humidity


def measure_all() -> None:
    """Takes all the required measurements and writes them into the DB."""
    write_temperatures(get_temps())  # 2x DS18B20
    write_humidity(*get_temp_and_humid())  # 1x DHT20


def sanity_check() -> bool:
    """Basic integrity check to see if all sensors respond.

    Returns:
        bool: True if all sensors respond, False if any fail.
    """

    sane = True
    if not (count := len(get_temps())) == 2:
        print(f"Missing temperature probes, expected 2, found {count}.")
        sane = False

    if not len(get_temp_and_humid()) == 2:
        print(f"Missing humidity sensor.")
        sane = False

    return sane


if __name__ == "__main__":
    if sanity_check():
        print("Success!")
    # measure_all()
