import json
import pandas as pd
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

def load_json(path):
    """Read json file and return its contents

    Args:
        path (_type_): _description_
    """
    with Path(path).open() as f:
        return json.load(f)
    
def save_csv(rows, path):
    """Write list of dicts to csv file, create parent folder if needed

    Args:
        rows (_type_): _description_
        path (_type_): _description_
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False) # dont add meaningless first col row numbers