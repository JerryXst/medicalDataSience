from pathlib import Path


def archive_raw_file(source: Path, storage_root: Path) -> Path:
    storage_root.mkdir(parents=True, exist_ok=True)
    target = storage_root / source.name
    target.write_bytes(source.read_bytes())
    return target
