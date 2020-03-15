import pytest
from mc_eltr.loot_tables_sqlite import LootTables
import os
from pathlib import Path
import json

JAR_PATH = next(
    (Path(os.getenv("APPDATA")) / ".minecraft" / "versions/").glob("*/*.jar")
)

SETTINGS = json.loads(Path("../../../settings.json").read_text())

OBT_DATA = json.loads(Path("../../../settings.json").read_text())

COBBLESTONE = Path("data/loot_tables/blocks/cobblestone.json").as_posix()
OAK_LOG = Path("data/loot_tables/blocks/oak_log.json").as_posix()

@pytest.fixture
def lt():
    return LootTables(JAR_PATH, SETTINGS, OBT_DATA)

def test_lt_scan_drops(lt):
    # make sure every type of drop is detected
    # silk touch
    # emerald ore scans as dropping emerald ore
    # alternatives
    # elder guardian drops everything
    pass

    