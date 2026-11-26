import json
from pathlib import Path

def save_json(data, path):
    """Write data to a json file, create parent folder if does not exist. Avoid error
       if directory already exists

    Args:
        data (Any): Any json serilizable data to save
        path (str | Path): Destination of the file path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)