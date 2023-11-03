from src.db_access import execute_query


def read_db() -> int:
    while True:
        query = input()
        if query == "exit":
            return 0

        try:
            execute_query(query)
        except Exception as e:
            print(f"query failed with error: {e}")

    return 1


if __name__ == "__main__":
    read_db()
