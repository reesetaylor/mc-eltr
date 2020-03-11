import random

def no_logic(tables, seed):
    
    # seed RNG
    random.seed(seed)

    # each block starts out unpaired
    unpaired_blocks = tables.unpaired_blocks()

    # we assign each one a random loot table that is also unpaired
    for block in unpaired_blocks:
        # randomly choose loot that has not been paired yet
        loot = random.choice(tuple(tables.unpaired_loot()))
        # pair the block with loot
        tables.pair_block_loot(block, loot)

    return tables