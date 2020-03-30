import random
import json
from loot_tables_sqlite import LootTables
from pathlib import Path
import logging


class Skyblock(LootTables):
    def __init__(
        self, jar, settings, obtainment_data, start_block,
    ):
        super().__init__(jar, settings, obtainment_data)
        self.output_folder = Path(settings["output_folder"])
        # import required items from json
        self.required_items = self.obt_data["required_items"]
        self.start_block = start_block

    def randomize(self, seed):
        logging.basicConfig(
            filename=(self.output_folder / f"{seed}.log"),
            level=logging.INFO,
        )

        # seed RNG
        random.seed(seed)

        # before anything else, make sure that items required for beating the game are obtainable
        self.add_required_items()

        # create a starting chain of blocks that can be broken to get more blocks
        self.add_starting_chain()

        # randomize the remaining blocks without any logic

        # commit the transactions to the database
        self.conn.commit()

        return self

    def add_required_items(self):
        # when the items required to access an area are added, that area is recorded as being accessible
        accessible_areas = []
        # required items for accessing the next area are only assigned to blocks in accessible areas, avoiding a hard lock

        # add items required for access to each area, in order
        for area in self.required_items:
            # items required to access the area
            # empty list for overworld ('ow') because no items are required to access it
            required_items = self.required_items[area]
            # does not run for overworld ('ow') because there are no areas accessible before it
            if accessible_areas:
                # find blocks that are obtainable in accessible areas, have not already been assigned loot, and are not the start block
                # exclude blocks that have already been assigned loot, in order to maintain 1:1 assignment
                # the start block is reserved from being assigned loot, because we do so when building the starting chain of blocks
                self.eligible_blocks = self.conn.execute(
                    """SELECT block
                    FROM blocks
                    WHERE area
                    IN""" + " (" + str(accessible_areas)[1:-1] + ") " +
                    """AND type=\'block\'
                    AND block != ?
                    EXCEPT
                    SELECT assigned.block
                    FROM assigned"""
                    ,
                    (self.start_block,)
                ).fetchall()
                print("in add_required_items", len(self.eligible_blocks))
                # randomize the list before we use it in add_item
                random.shuffle(self.eligible_blocks)
            # this also does not run for overworld ('ow') because it has no required items
            # for each item required to access the area, assign an eligible block to drop that item
            for item in required_items:
                self.add_item(item)
            # now that blocks in the accessible areas drop the items required to access this area, it is also accessible
            logging.info(f"{area} access granted")
            accessible_areas.append(area)

    def add_item(self, item):
        # add_item uses a python list to avoid repeat assignments, because it is less overhead than
        # querying the database for an updated list of eligible_blocks after every assignment
        logging.info(f"adding item {item}")
        # check if the "item" passed in is actually a tag e.g. "logs"
        # substitute the appropriate list if it is
        if item in self.tags:
            item = self.tags[item]
        # if passed a list, check if at least one item from it is obtainable
        if isinstance(item, list) and (
            True in list(map(lambda i: self.is_dropped(i), item))
        ):
            # if none are obtainable choose a random one to be added
            item = random.choice(item)
        # check if the item is already dropped
        if not self.is_dropped(item):
            # try to find a loot table to drop the item
            loot_table = self.find_loot_that_drops(item)
            if loot_table is not None:
                logging.info(f"found loot table that drops {item} ({loot_table})")
                # assign a random eligible loot table to a random eligible block
                # e_blocks is already shuffled in the parent function add_required_items
                # pop the block from e_blocks so it will not be assigned to again
                block = self.eligible_blocks.pop()
                logging.info(f"assigning {block} {loot_table}")
                self.conn.execute(
                    "INSERT INTO assigned(block,loot) VALUES (?,?)", (block, loot_table)
                )
                logging.info(f"{item} successfully added")
            else:
                logging.info(
                    f"no loot tables found that drop {item}. recursively adding crafting ingredients"
                )
                # if there is no loot table that drops the item, add its ingredients
                ingredients = self.get_item_ingredients(item)
                for i in ingredients:
                    self.add_item(i)
        else:
            logging.info(f"{item} is already dropped")

    def is_dropped(self, item):
        return (
            item
            in self.conn.execute(
                "SELECT DISTINCT drops.item FROM assigned INNER JOIN drops ON assigned.loot = drops.block"
            ).fetchall()
        )

    def find_loot_that_drops(self, item):
        # find loot that drops item
        # exclude loot that has already been assigned to a block, in order to maintain 1:1 assignment
        # the loot of the starting block is reserved from being assigned to a block because we do so when building the starting chain of blocks
        loot_that_drops_item = self.conn.execute(
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
        if loot_that_drops_item:
            # return random loot that drops the item
            return random.choice(loot_that_drops_item)
        else:
            return None

    def get_item_ingredients(self, item):
        return self.conn.execute(
            "SELECT needs FROM recipes WHERE item = ?", (item,)
        ).fetchall()

    def add_starting_chain(self):
        # get the blocks that qualify to be part of the starting chain
        # naively checks for blocks that drop themselves, have not been assigned loot tables,
        # and have not had their loot tables assigned to other blocks.
        chain_blocks = self.conn.execute(
            """
            SELECT blocks.block
            FROM blocks INNER JOIN drops
            ON blocks.block = drops.block
            WHERE type = 'block'
            AND drops.block = drops.item
            AND blocks.block != ?
            EXCEPT
            SELECT * FROM
            (
                SELECT assigned.block
                FROM assigned
                UNION
                SELECT assigned.loot
                FROM assigned
            )
            """,
            (self.start_block,),
        ).fetchall()

        logging.info(f"found {len(chain_blocks)} chain blocks")

        random.shuffle(chain_blocks)

        # the first block to be assigned a loot table is the start block
        block = self.start_block

        # repeat until we run out of blocks
        while chain_blocks:
            # choose the loot of a random block from the list
            loot = chain_blocks.pop()
            # assign the current block that loot
            self.conn.execute("INSERT INTO assigned(block,loot) VALUES (?,?)", (block, loot))
            # recall that every block in the list has loot that drops that block
            # i.e. every block drops itself
            # so we know that the block that the loot drops is the same as the block the loot came from
            # i.e. the next block in the chain
            block = loot

        # close the loop by assigning the last block loot that drops the start block
        self.conn.execute("INSERT INTO assigned(block,loot) VALUES (?,?)", (block, self.start_block))
        logging.info(f"closed loop with {block} dropping {self.start_block}")