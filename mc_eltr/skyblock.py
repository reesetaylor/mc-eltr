import random
import json
from loot_tables_sqlite import LootTables
from logging import info


class Skyblock(LootTables):
    def __init__(
        self, jar, settings, obtainment_data, start_block,
    ):
        super().__init__(self, jar, settings, obtainment_data)
        # set up progression criteria from json
        self.access_criteria = self.obt_data["access_criteria"]
        self.special_blocks = self.obt_data["special_blocks"]
        self.entities_drop_key_items = self.settings["entities_drop_key_items"]
        self.start_block = start_block

    def randomize(self, seed):
        # players start with overworld access
        # assign to blocks/entities available before nether
        # blocks - (nether blocks + end blocks)

        # create the initial closed loop of placeable blocks starting from start_block
        # get the list of all blocks that are self-dropping

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

    def get_accessible_blocks(self, access):
        return []

    def get_updated_accesses(self, access):
        # do a map
        return access

    def item_is_obtainable(self):
        return 

    def item_is_craftable(self):
        return()