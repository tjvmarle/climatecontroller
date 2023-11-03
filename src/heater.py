"""Module to manage the heater. Turn it on when temp gets too low and off when it gets too high.
"""
from typing import Tuple
from time import sleep
import datetime as dt
import RPi.GPIO as GPIO  # type: ignore
from src.DS18B20 import get_temps
from src.db_access import write_heating_time

# TODO: Een manier om dit runtime te wijzigen, uitlezen uit config file?
# 70 is ong optimaal
MIN_TEMP: float = 67.5  # min temperature for any probe
MAX_TEMP: float = 72.5  # max temperature for any probe

heater_ts = dt.datetime.now()  # Used for any change in state of the heater

# TODO: Connect relais and fans
HEATER_PIN = 13
FANS_PIN = 11  # Both fans on a single pin


def _is_active(pin: int) -> bool:
    """Returns if a specific pin is set to high.

    Args:
        pin (int): the GPIO-pin to check.

    Returns:
        bool: True is pin is set to HIGH, false if set to LOW
    """
    return GPIO.input(pin) == GPIO.HIGH


def _toggle_heating(turn_on: bool) -> None:
    """Switches the heater on or off.

    Args:
        turn_on (bool): turns on heating when True, else turns it off.
    """
    if turn_on == _is_active(HEATER_PIN):
        return  # No change in state, so nothing to do

    global heater_ts
    now = dt.datetime.now()

    if turn_on:
        print("Turn on heating.")
        GPIO.output(HEATER_PIN, GPIO.HIGH)  # type: ignore
    else:
        print("Turn off heating.")
        GPIO.output(HEATER_PIN, GPIO.LOW)   # type: ignore
        delta = now - heater_ts
        write_heating_time(delta)

    heater_ts = now


def _activate_fans(turn_on: bool) -> None:
    state = GPIO.HIGH if turn_on else GPIO.LOW  # type: ignore
    GPIO.output(FANS_PIN, state)                # type: ignore


def _toggle_fans() -> None:
    """Turns on the fans when heating is active. Turns them off one minute after heating has stopped.
    """
    # TODO: We could use dependency injection for the GPIO, increasing UT-ability. Also shuts up the linter.
    fans_active = _is_active(FANS_PIN)
    heater_active = _is_active(HEATER_PIN)
    if heater_active and fans_active:
        return

    if heater_active and not fans_active:
        _activate_fans(True)
        return

    fan_run_time = (dt.datetime.now() - heater_ts).seconds
    if not heater_active and fans_active and fan_run_time > 59:
        print("Fans have run for a minute, turn off.")
        _activate_fans(False)


def _init():
    # Ignore linting errors, the import is a bit borked
    print("Init GPIO pins.")
    GPIO.setmode(GPIO.BOARD)               # type: ignore

    GPIO.setup(HEATER_PIN, GPIO.OUT)       # type: ignore
    GPIO.setup(FANS_PIN, GPIO.OUT)         # type: ignore

    GPIO.output(HEATER_PIN, GPIO.LOW)      # type: ignore
    GPIO.output(FANS_PIN, GPIO.LOW)        # type: ignore


_init()  # Trigger at import


def check_heating() -> None:
    """Check if heating needs to be turned on or off.
    """
    temps: Tuple[float]
    _, temps = zip(*get_temps())    # type: ignore

    if min(temps) < MIN_TEMP and max(temps) > MAX_TEMP:
        # TODO: create a warning, this implies a convection/heat distribution problem!
        print(f"Warning: both probes outside of range, min:{min(temps)}, max: {max(temps)}.")
        _toggle_heating(False)
        _activate_fans(True)
        return

    temp: float = max(temps) if _is_active(HEATER_PIN) else min(temps)
    _toggle_heating(temp <= (MAX_TEMP if _is_active(HEATER_PIN) else MIN_TEMP))
    _toggle_fans()


def turn_on_fans(turn_on: bool) -> None:
    _activate_fans(turn_on)


def shutdown() -> None:
    if not _is_active(HEATER_PIN):
        return

    _toggle_heating(False)
    _activate_fans(True)
    print("Please wait 30s for the heating coil to cool down.")
    sleep(30)


if __name__ == "__main__":
    check_heating()
