import base64
from typing import Dict, Tuple


class DataSegmenter:

    def __init__(self, data_path: str, segment_len: int = 512):
        self.data_path = data_path
        self.segment_len = segment_len
        self.data: bytes = b""
        self.segments: Tuple[int, bytes] = ()
        self._load_data()
        self._segment_data()

    def _load_data(self):
        with open(self.data_path, "rb") as f:
            self.data = f.read()

    def _segment_data(self):
        self._load_data()
        segment_num = 0
        for i in range(0, len(self.data), self.segment_len):
            self.segments += ((segment_num, self.data[i : i + self.segment_len]),)
            segment_num += 1

    def get_segments(self) -> Tuple[int, bytes]:
        print("Data segmented successfully")
        return self.segments


class DataAssembler:
    def __init__(self) -> None:
        self.data: bytes = b""
        self.segments: list[bytes] = []

    def add_segment(self, segment: str) -> None:
        segment_byte = base64.b64decode(segment)
        self.segments.append(segment_byte)

    def assemble(self):
        for segment in self.segments:
            self.data += segment
        print("Data assembled successfully")
        return self.data
