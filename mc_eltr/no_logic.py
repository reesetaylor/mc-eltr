import random
from mc_eltr.loot_tables_sqlite import LootTables

class NoLogic(LootTables):
    def randomize(self, seed):
        # get a list of blocks that drop themselves
        blocks = self.conn.execute(
            """
            SELECT blocks.block
            FROM blocks INNER JOIN drops
            ON blocks.block = drops.block
            AND type = 'block'
            AND drops.block = drops.item
            """
        ).fetchall()

        # randomize the list order
        random.seed(seed)
        random.shuffle(blocks)

        # length of the list
        length = len(blocks)

        # iterate over each numeric index in the list
        for i in range(length):
            # the block at the current index
            block = blocks[i]
            # the next block in the list, computed as the block at the current index + 1, modulo length
            # because we take the modulus by the length, the "next" block from the last block is the first block
            next_block = blocks[(i + 1) % length]
            # recall that every block in the list drops from its own loot table
            # assign the current block the loot table of the next block, causing it to drop the next block
            self.assign_block_loot(block, next_block)
        
        # the relationship between these blocks is now such that if you
        # 1. break a block
        # 2. place the block that it drops
        # 3. repeat
        # a sufficient number of times, you will eventually get the block you started with

        # the list of blocks, entities, etc. that need to be assigned loot tables
        remaining_blocks = self.conn.execute(
            """
            SELECT blocks.block
            FROM blocks
            EXCEPT
            SELECT assigned.block
            FROM assigned
            """
        ).fetchall()

        # length of the list
        length = len(remaining_blocks)

        # keep track of which blocks' loot tables have not been assigned
        remaining_loot = remaining_blocks.copy()

        # randomize the list order
        random.shuffle(remaining_loot)

        for i in range(length):
            self.assign_block_loot(remaining_blocks[i], remaining_loot[i])

        return self

    def assign_block_loot(self, block, loot):
        self.conn.execute(
            "INSERT INTO assigned(block,loot) VALUES (?,?)", (block, loot)
        )

    def write_to_datapack(self, dp_name, dp_description, dp_reset_msg, dp_filename):
        super().write_to_datapack(dp_name, dp_description, dp_reset_msg, dp_filename)

    def write_cheatsheet(self, fname):
        super().write_cheatsheet(fname)
    