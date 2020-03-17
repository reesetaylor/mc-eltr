import random
import json
from .loot_tables_sqlite import LootTables
import logging


class Skyblock(LootTables):
    def __init__(
        self, jar, settings, obtainment_data, start_block,
    ):
        super().__init__(jar, settings, obtainment_data)
        # set up progression criteria from json
        self.access_criteria = self.obt_data["access_criteria"]
        self.entities_drop_key_items = self.settings["entities_drop_key_items"]
        self.start_block = start_block

    def randomize(self, seed):
        logging.basicConfig(level=logging.INFO)
        # seed RNG
        random.seed(seed)
        # players start with overworld access
        # assign to blocks/entities available before nether and not extremely rare
        self.avail_blocks = self.conn.execute(
            "SELECT block FROM blocks WHERE area='ow' AND type='block'"
        ).fetchall()

        logging.info(
            f"found {len(self.avail_blocks)} candidate blocks for initial chain."
        )

        # TODO: second pass to check for craftable blocks
        # note that igloo_chest is not a candidate loot table even though it can drop emerald, which is the sole ingredient to craft emerald_block.
        # I'll implement a second pass to detect these cases once recipe scanning is done
        chain_loot = self.conn.execute(
            self.scripts["chain_loot"]
        ).fetchall()

        # shuffle the block queue for random assignments in grant_access
        random.shuffle(self.avail_blocks)

        # assign blocks loot tables that drop the critical items
        self.grant_access("nether", chain_loot)

        # then remove those blocks and loot tables from the pool to preserve 1:1 assignment

        # our list of available loot excludes the loot tables that were already assigned when granting nether access

        
        # assign the last block to drop the first block, closing the loop
    
        # assign start_block one of the self-dropping block loot tables
        # assign the dropped block one of the remaining self-dropping loot tables
        # repeat this process until there are not any loot tables remaining
        # assign the last block the loot table of start_block

        # the drops of all of the blocks that have been assigned are now obtainable
        # check if we can access the nether with what we have so far
        # if not assign loot tables that provide needed materials to overworld blocks

        # players now have nether access
        # assign to blocks/entities available before end
        # blocks - end blocks

        # assign the needed materials for the end

        # end access obtained
        # assign to all blocks

        # assign the needed materials to farm

        # farmland obtained
        # 6 blocks that grow on farmland are obtainable

        return self

    def grant_access(self, access, avail_loot):
        # for each critical item either
        # provide a loot table that drops it or loot tables to craft it
        criteria = self.access_criteria[access]
        for item in criteria:
            # check if item is already obtainable from an assigned loot table
            # else
            # check if any candidate loot tables will drop it
            # intersection of blocks that drop the item and available loot tables
            # if empty add loot tables for crafting
            pass

    def drops_item(self, item):
        pass

    def grant_item_components(self, items):
        # recursion time
        return True

