from datetime import datetime, UTC


def main() -> None:
    print(f"rpa-worker ready at {datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    main()
