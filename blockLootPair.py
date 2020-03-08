from collections import UserDict
from pathlib import Path

class BlockLootPair(UserDict):
    # destination filename is the file this data will be written to
    # data is a json dict of the files contents
    # data source filename is the file that was the source of the data
    # meta is for any miscellaneous information we may want to tag
    def __init__(self, destPath, data: dict, dataSrcPath, meta=None):
        self.destPath = Path(destPath)
        self.data = data
        self.dataSrcPath = Path(dataSrcPath)
        self.meta = meta
    