import asyncio
from typing import Tuple

import pdu
from data_processor import DataSegmenter
from pdu import Datagram
from quic import QuicConnection, QuicStreamEvent


class ServerState:
    def __init__(self, server: "ServerContext"):
        self.server = server

    async def handle_incoming_event(self, event: QuicStreamEvent):
        raise NotImplementedError("handle_incoming_event not implemented")


class IdleState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)
        stream_id = event.stream_id

        if dgram_in.mtype == pdu.MSG_TYPE_REQUEST_UPDATE:
            # Set the state to SendingState
            self.server.set_state(SendingState(self.server))
            await self._send_firmware(
                stream_id, firmware_path="firmware_send/firmware.bin"
            )

    async def _send_firmware(
        self, stream_id: int, firmware_path: str = "firmware_send/firmware.bin"
    ) -> None:

        data_segmenter = DataSegmenter(firmware_path)
        segments: Tuple[int, bytes] = data_segmenter.get_segments()

        # Send the first n-1 segments
        total_segments = len(segments) - 1
        for segment_num, segment_data in segments[:-1]:
            dgram_out = Datagram(pdu.MSG_TYPE_START_SND_DATA, segment_data)
            response_event = QuicStreamEvent(stream_id, dgram_out.to_bytes(), False)
            await self.server.conn.send(response_event)
            print(f"Segment {segment_num:2d}/{total_segments} sent")
            await asyncio.sleep(0)  # awaitable that doesn't block

        # send last segment
        dgram_out = Datagram(pdu.MSG_TYPE_FINISH_SND_DATA, segments[-1][1])
        response_event = QuicStreamEvent(stream_id, dgram_out.to_bytes(), True)
        await self.server.conn.send(response_event)
        print(f"Segment {segments[-1][0]:2d}/{total_segments} sent")
        # Set the state to AwaitingAckState
        self.server.set_state(AwaitingAckState(self.server))


class SendingState(ServerState):
    """
    Sending state for the server.
    It does not handle any incoming events.
    it transitions to AwaitingAckState after sending the firmware.
    """

    pass


class AwaitingAckState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)

        if dgram_in.mtype == pdu.MSG_TYPE_RECEIVE_ACK:
            print("Received ACK from client")
            self.server.set_state(IdleState(self.server))


class ServerContext:
    def __init__(self, conn: QuicConnection):
        self.conn = conn
        self.state = IdleState(self)

    def set_state(self, state: ServerState):
        self.state = state

    async def handle_incoming_event(self, event: QuicStreamEvent):
        await self.state.handle_incoming_event(event)
