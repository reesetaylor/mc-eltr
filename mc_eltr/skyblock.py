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
        self.start_block = start_block

    def randomize(self, seed):
        logging.basicConfig(level=logging.INFO)
        # seed RNG
        random.seed(seed)
        # players start with overworld access
        # assign to blocks/entities available before nether and not extremely rare

        # blocks eligible to be assigned critical items for nether access
        crit_block_candidates = self.conn.execute(
            "SELECT block FROM blocks WHERE area='ow' AND type='block'"
        ).fetchall()

        # all blocks' loot tables are searched for dropping critical items for nether access
        #crit_loot_candidates = self.conn.execute(
        #    "SELECT block FROM blocks"
        #).fetchall()

        # assign critical items for nether access to random eligible blocks
        self.grant_access("nether", crit_block_candidates)

        chain_blocks = []
        # TODO: second pass to check for craftable blocks
        # note that igloo_chest is not a candidate loot table even though it can drop emerald, which is the sole ingredient to craft emerald_block.
        # I'll implement a second pass to detect these cases once recipe scanning is done
        chain_loot = self.conn.execute(self.scripts["chain_loot"]).fetchall()

        # shuffle the block queue for random assignments in grant_access
        random.shuffle(chain_blocks)

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

    def grant_access(self, access, crit_block_candidates):
        # for each critical item either assign a loot table that drops it
        # or assign loot tables that drop its components
        criteria = self.access_criteria[access]
        for item in criteria:
            self.add_item(item)

    def add_item(self, item):
        def is_dropped(item):
            return self.conn.execute("? IN (SELECT drops.item)", item).fetchone()

        def find_candidate_loot(item):
            return []

        def get_item_components(item):
            return []
        
        # if passed a list, check if at least one is obtainable
        if isinstance(item, list) and (1 not in list(map(lambda i: self.is_dropped(i), item))):
            # if none are obtainable add a random one
            item = random.choice(item)
        # check if the item is already dropped
        if not is_dropped(item):
            # try to find a candidate loot table to drop the item
            candidates = find_candidate_loot(item)
            if candidates is not None:
                # assign a candidate loot table to a candidate block
            else:
                # get the components required to craft the item
                # for each component, recursively add its components


