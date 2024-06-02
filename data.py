from typing import Dict


class DataSegmenter:
    MAX_BYTES: int = 1024

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.data: bytes = b""
        self.segments: Dict = {}
        self._load_data()
        self._segment_data()

    def _load_data(self):
        with open(self.data_path, "rb") as f:
            self.data = f.read()

    def _segment_data(self):
        self._load_data()
        for i in range(0, len(self.data), self.MAX_BYTES):
            self.segments[i] = self.data[i : i + self.MAX_BYTES]


class DataAssembler:
    def __init__(self) -> None:
        self.data: bytes = b""
        self.segments: Dict = {}

    def add_segment(self, segment: bytes) -> None:
        self.segments[len(self.segments)] = segment

    def assemble_data(self):
        for i in range(len(self.segments)):
            self.data += self.segments[i]
        return self.data
