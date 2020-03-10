import pytest
from mc_eltr.loot_tables import LootTables
import os
from pathlib import Path
import json

JAR_PATH = next(
    (Path(os.getenv("APPDATA")) / ".minecraft" / "versions/").glob("*/*.jar")
)

RANDOMIZE_ALL = json.loads(
    '{ "blocks": "true", "chests": "true", "entities": "true", "gameplay/fishing/": "true", "gameplay/fishing.json": "true", "gameplay/hero_of_the_village/": "true", "gameplay/cat_morning_gift.json": "true"}'
)

COBBLESTONE = Path("data/loot_tables/blocks/cobblestone.json").as_posix()
OAK_LOG = Path("data/loot_tables/blocks/oak_log.json").as_posix()

@pytest.fixture
def lt():
    return LootTables(JAR_PATH, RANDOMIZE_ALL)

@pytest.fixture
def lt_with_pair():
    lt = LootTables(JAR_PATH, RANDOMIZE_ALL)
    lt.pair_block_loot("cobblestone", "oak_log")
    lt.pair_block_loot("cobblestone", "oak_log")
    pb = lt.paired_blocks()
    pl = lt.paired_loot()
    ub = lt.unpaired_blocks()
    ul = lt.unpaired_loot()
    return (lt, pb, ub, pl, ul)

def test_lt_instance():
    # make sure I didn't accidentally override the constructor again
    assert LootTables() == {}


def test_lt_constructor(lt):
    assert lt.original_pairings
    assert lt.original_blocks is not None
    # all blocks and loot should start out unpaired
    assert lt.unpaired_blocks() == lt.original_blocks
    assert lt.unpaired_loot() == lt.original_blocks

# TODO: test that the drops from oak_log are obtainable
def test_lt_pair_block_loot(lt_with_pair):
    lt, pb, ub, pl, ul = lt_with_pair
    # cobblestone is in paired blocks
    assert "cobblestone" in pb
    # oak log is in paired loot
    assert "oak_log" in pl
    # cobblestone is not in unpaired blocks
    assert "cobblestone" not in ub
    # oak log is not in unpaired loot
    assert "oak_log" not in ul
    assert lt.get_block_loot("cobblestone") == "oak_log"