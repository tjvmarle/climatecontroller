"""Main module to manage DB access. No there isn't any protection against SQL-injection.
"""

from typing import List, Tuple, Callable
import sqlite3 as db
import datetime as dt

DB_NAME: str = "garlicbox_db"
TEMP_DB = "ds18b20"
HUMID_DB = "dht20"
GLOBAL_DB = "global_state"
_db_connection: db.Connection | None = None

start_time = dt.datetime.now()

probes = {1: "probe_1",
          2: "probe_2"}


def _commit(func: Callable):
    """Decorator to automatically commit the db-transactions.

    Args:
        func (Callable): any method that writes to the db.
    """
    def auto_commit(*args, **kwargs):
        func(*args, **kwargs)
        if _db_connection:
            _db_connection.commit()
    return auto_commit


@_commit
def _clear_all() -> None:
    """Clears all tables. Mostly for manual resets.
    """
    # _get_cursor().execute(f"DELETE FROM {TEMP_DB};")
    # _get_cursor().execute(f"DELETE FROM {HUMID_DB};")
    _get_cursor().execute(f"UPDATE {GLOBAL_DB} set heater_time=0 WHERE id='global';")

    print("Cleared all data.")


def _print_all_temps() -> None:
    """Print out all temperature entries. Mostly for debugging purposes.
    """
    temps = _get_cursor().execute(f"SELECT * FROM {TEMP_DB}").fetchall()
    if not temps:
        print(f"Table {TEMP_DB} is empty.")
        return

    for row in temps:
        probe_id, temp, timestamp = row
        print(f"Probe: {probe_id}, temp: {temp}, timestamp: {timestamp}.")


def _init_db(clear: bool = False) -> db.Cursor:
    """Opens the database connection. Creates tables if the don't already exist. Optionally delete all data.

    Returns:
        db.Cursor: db-cursor, required for CRUD-access to the database contents.
    """
    global _db_connection
    _db_connection = db.connect(DB_NAME)
    cur = _db_connection.cursor()
    # TODO: Check all tables for existance? Makes it easer to add new ones.
    if cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TEMP_DB}';").fetchone() is None:
        _create_tables()
        print("Tabellen aangemaakt")

    if clear:
        _clear_all()

    return cur


def _create_tables() -> None:
    """Create the required tables for this project. Remember to update the column names in the write functions if you 
    change them here.
    """
    cur = _get_cursor()
    cur.execute(f"CREATE TABLE {TEMP_DB} (\
        sensor_id INTEGER, \
        temperature REAL, \
        time TIMESTAMP default CURRENT_TIMESTAMP NOT NULL\
        );")

    cur.execute(f"CREATE TABLE {HUMID_DB} (\
        temperature REAL, \
        humidity REAL, \
        time TIMESTAMP default CURRENT_TIMESTAMP NOT NULL\
        );")

    cur.execute(f"CREATE TABLE {GLOBAL_DB} (\
        id TEXT, \
        heater_time INTEGER \
        );")

    # TODO: some init that checks if only 1 row exists
    cur.execute(f"INSERT INTO {GLOBAL_DB} (id, heater_time) VALUES ('global', 0);")


def _get_cursor() -> db.Cursor:
    """Retrieves the db-cursor. Required for all CRUD-access.

    Returns:
        db.Cursor: access handle to the db-contents.
    """
    return _init_db() if not _db_connection else _db_connection.cursor()


@_commit
def _write_temperature(probe_id: int, temp: float) -> None:
    """Write the probe temperature data to the database.

    Args:
        probe_id (str): ID of the probe.
        temp (float): Temperature measurement of the probe.
    """
    _get_cursor().execute(f"INSERT INTO {TEMP_DB} (sensor_id, temperature) VALUES ({probe_id}, {temp});")


@_commit
def _write_humidity(temp: float, humid: float) -> None:
    _get_cursor().execute(f"INSERT INTO {HUMID_DB} (temperature, humidity) VALUES ({temp:.1f}, {humid:.1f});")


def write_temperatures(temps: List[Tuple[str, float]]) -> None:
    """Write a list of temperatures to the database.

    Args:
        temps (List[Tuple[str, float]]): List of probe id's and their temperatures.
    """
    for probe_id, temp in temps:
        _write_temperature(int(probe_id[-1]), temp)  # E.q. we take the '1' of 'probe_1'


def write_humidity(temp: float, humid: float) -> None:
    """Write the temp and humidity measurement of the single DHT20 to the DB.

    Args:
        temp (float): Temperature measurement of the sensor.
        humid (float): Humidity measurement of the sensor.
    """
    _write_humidity(temp, humid)


@_commit
def write_heating_time(time_on: dt.timedelta) -> None:
    """Update the accumulated time the heater is on.

    Args:
        time_on (dt.timedelta): duration of a single instance the heater was on.
    """
    heating_timer, *_ = _get_cursor().execute(f"SELECT heater_time FROM {GLOBAL_DB};").fetchone()
    total_seconds = time_on.seconds
    if heating_timer == 0:
        hours = (int(total_seconds / 3600), "h")
        minutes = (int(total_seconds / 60) % 60, "m")
        seconds = (total_seconds % 60, "s")
        timeText = " ".join([f"{time}{suffix}" for time, suffix in [hours, minutes, seconds] if time > 0])
        print(f"Finished startup heating in {timeText}.")

        global start_time
        start_time = dt.datetime.now()  # Don't count initial startup phase
        _get_cursor().execute(f"UPDATE {GLOBAL_DB} set heater_time=1 WHERE id='global';")  # insert dummy value of 1s
        return

    new_total = time_on.seconds + int(heating_timer)
    _get_cursor().execute(f"UPDATE {GLOBAL_DB} set heater_time={new_total} WHERE id='global';")
    run_time = dt.datetime.now() - start_time
    run_time_sec = int(run_time.total_seconds())
    percentage = (new_total / run_time_sec) * 100
    print(f"Cumulatieve verwarming: {new_total}s over {run_time_sec}s, {percentage:.1f}%.")


def execute_query(query: str) -> None:
    _init_db()
    result = _get_cursor().execute(query).fetchall()
    print(f"Executed [{query}]")

    if len(result) == 0:
        print("0 results")
        return

    maxResults = min(len(result), 30)  # Don't print too many
    for count, line in enumerate(result[0:maxResults]):
        print(f"#{count}: {line}")


if __name__ == "__main__":

    # now = dt.datetime.now()
    # past_time = now - dt.timedelta(seconds=3912)
    _init_db()
    _clear_all()
    # _print_all_temps()
    # write_heating_time(dt.timedelta(seconds=3912))
    # write_heating_time(dt.timedelta(seconds=3912))

    # cur = _init_db(True)
    # cur = _init_db(False)
    # entry_id, runtime = cur.execute(f"Select (id, heater_time) from {GLOBAL_DB};").fetchone()
    # runtime = cur.execute(f"Select heater_time from {GLOBAL_DB} where id = 'global';").fetchone()[0]
    # print(f"id: global, runtime: {runtime}")

    # cur = _get_cursor()
    # _clear_all()
    # _print_all_temps()
    # tables = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    # print(f"Available tables: {tables}")

    # cur.execute(f"INSERT INTO {GLOBAL_DB} (id, heater_time) VALUES ('global', 0);")
    # heatingtime, *_ = _get_cursor().execute(f"SELECT heater_time FROM {GLOBAL_DB};").fetchone()

    # _get_cursor().execute(f"UPDATE {GLOBAL_DB} set heater_time={int(heatingtime) + 15} WHERE id='global';")
    # if _db_connection:
    #     _db_connection.commit()

    # heatingtime, *_ = _get_cursor().execute(f"SELECT heater_time FROM {GLOBAL_DB};").fetchone()

    # print(f"Cumulative heating time: {heatingtime}")
