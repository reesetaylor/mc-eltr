import random
import json
from loot_tables_sqlite import LootTables
import logging


class Skyblock(LootTables):
    def __init__(
        self, jar, settings, obtainment_data, start_block,
    ):
        super().__init__(jar, settings, obtainment_data)
        # import access criteria from json
        self.access_criteria = self.obt_data["access_criteria"]
        self.start_block = start_block

    def randomize(self, seed):
        logging.basicConfig(level=logging.INFO)
        # seed RNG
        random.seed(seed)
        # players start with access to overworld blocks
        # blocks eligible to be assigned critical items for nether access
        # entities can be hard to find, so we restrict this to blocks
        # since most blocks are seen in the initial chain
        crit_block_candidates = self.conn.execute(
            "SELECT block FROM blocks WHERE area='ow' AND type='block' AND block != ?",
            (self.start_block,),
        ).fetchall()

        # randomly shuffle the blocks
        random.shuffle(crit_block_candidates)

        # assign critical items for nether access to random eligible blocks
        self.grant_access("nether", crit_block_candidates)

        # repeat the process for the end

        # and farmland

        # chain_blocks = []
        # TODO: second pass to check for craftable blocks
        # note that igloo_chest is not a candidate loot table even though it can drop emerald, which is the sole ingredient to craft emerald_block.
        # chain_loot = []

        # shuffle the block queue for random assignments in grant_access
        # random.shuffle(chain_blocks)

        # return self

        self.conn.commit()

        return self

    def grant_access(self, access, crit_block_candidates):
        # for each critical item either assign a loot table that drops it
        # or assign loot tables that drop its components
        criteria = self.access_criteria[access]
        for item in criteria:
            self.add_item(item, crit_block_candidates)

    def is_dropped(self, item):
        if item in [
            self.conn.execute(
                "SELECT DISTINCT drops.item FROM assigned INNER JOIN drops ON assigned.loot = drops.block"
            ).fetchone()
        ]:
            return True
        else:
            return False

    def find_candidate_loot(self, item):
        candidates = self.conn.execute(
            """
            SELECT DISTINCT blocks.block
            FROM blocks INNER JOIN drops
            ON drops.block = blocks.block
            WHERE drops.item = ?
            AND drops.block != ? 
            EXCEPT
            SELECT assigned.loot
            FROM assigned
            """,
            (item, self.start_block),
        ).fetchall()
        if candidates:
            return candidates
        else:
            return None

    def get_item_ingredients(self, item):
        return self.conn.execute(
            "SELECT needs FROM recipes WHERE item = ?", (item,)
        ).fetchall()

    def add_item(self, item, crit_block_candidates):
        logging.info(f"adding item {item}")
        # check if the "item" passed in is actually a tag
        # substitute the appropriate list if it is
        if item in self.tags:
            item = self.tags[item]
        # if passed a list, check if at least one is obtainable
        if isinstance(item, list) and (
            True in list(map(lambda i: self.is_dropped(i), item))
        ):
            # if none are obtainable add a random one
            item = random.choice(item)
        # check if the item is already dropped
        if not self.is_dropped(item):
            # try to find a candidate loot table to drop the item
            candidates = self.find_candidate_loot(item)
            if candidates is not None:
                logging.info(f"found {len(candidates)} loot tables that drop {item} ({candidates})")
                # assign a random candidate loot table to a random candidate block
                # recall that crit_block_candidates was shuffled before entering grant_access
                block = crit_block_candidates.pop(0)
                loot_table = random.choice(candidates)
                logging.info(f"inserting {block} {loot_table}")
                self.conn.execute(
                    "INSERT INTO assigned(block,loot) VALUES (?,?)",
                    (block, loot_table)
                )
                logging.info(f"{item} successfully added")
            else:
                logging.info(
                    f"no loot tables found that drop {item}. recursively adding crafting ingredients"
                )
                # if there is no loot table that drops the item, add
                ingredients = self.get_item_ingredients(item)
                # not working for some reason
                for i in ingredients:
                    self.add_item(i, crit_block_candidates)
        else:
            logging.info(f"{item} is already dropped")

