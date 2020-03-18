import pytest
from mc_eltr.skyblock import Skyblock
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
def sb():
    return Skyblock(JAR_PATH, SETTINGS, OBT_DATA, "dirt")

def test_sb_init(sb):
    # make sure every type of drop is detected
    # silk touch
    # emerald ore scans as dropping emerald ore
    # alternatives
    # elder guardian drops everything
    pass

def test_lt_scan_recipes(lt):
    pass

    