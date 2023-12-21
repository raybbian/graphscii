from tsm.orthogonalize import Orthogonalize


class Compaction():
    def __init__(self, orthogonalize: Orthogonalize):
        self.G = orthogonalize.G
        self.dcel = orthogonalize.dcel
        self.flow_dict = orthogonalize.flow_dict
