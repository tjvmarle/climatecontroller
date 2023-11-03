"""Main file for the garlic temp controller. It tracks temperature and humidity and keeps temp between set limits."""

import datetime as dt
import argparse
import sys
from time import sleep
from math import ceil
import RPi.GPIO as GPIO  # type: ignore

from src.measure import measure_all, sanity_check
from src.heater import check_heating, shutdown


def wait_next_minute_fraction(fraction: float) -> None:
    """Sleep until the next fraction of a whole minute is reached.

    Args:
        fraction (float): fraction of a minute to wait for. E.g., at 1/4 sleeps untill the first 0, 15, 30 or 45 second-
                          mark of a whole minute has been reached.
    """
    # Wait some amount of time until some fraction of a minute
    fraction_seconds = 60 * fraction
    now = dt.datetime.now()
    current_second = now.second + now.microsecond / 1_000_000
    next_fraction_seconds = ceil(current_second / fraction_seconds) * fraction_seconds
    sleeptime = next_fraction_seconds - current_second
    # print(f"Current time: {now}, next fraction at {next_fraction_seconds}, sleeping for {sleeptime} seconds.")
    # print(f"Sleeping for {sleeptime:.1f}s")
    sleep(sleeptime)
    print(f"{dt.datetime.now().strftime('%H:%M:%S')}: ", end="")


def run_main() -> int:
    """Mainloop of the application. Check temperature every 15 sec. Take all measurements every minute and log them in a
       db. Turn on/off fans and heater when required.
    """
    # TODO:
    # If humidity too low, send out warning!
    # Test all DB-calls
    # Check all implemented code and start a run
    if not sanity_check():
        print("Sanity check failed, aborting setup.")
        return 1

    loop_counter: int = 0
    while True:  # TODO: Some switch to turn this off?
        check_heating()

        loop_counter += 1
        if loop_counter == 4:  # Once per minute suffices
            loop_counter = 0
            measure_all()

        wait_next_minute_fraction(1/4)  # Every 15 seconds


# TODO: Argparser toevoegen
# * Option to wipe DB upon startup
# * Option to print some DB info and then exit
if __name__ == "__main__":
    exitCode: int = 1
    try:
        exitCode = run_main()
    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        shutdown()
        GPIO.cleanup()
        print("Cleanup executed.")

    sys.exit(exitCode)
