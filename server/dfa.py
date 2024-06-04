import asyncio
from typing import Tuple

import common.pdu as pdu
from common.custom_exceptions import (
    IncompatibleFirmwareVersion,
    IncompatibleProtocolVersion,
)
from common.data_processor import DataSegmenter
from common.pdu import Datagram
from common.quic import QuicConnection, QuicStreamEvent
from server.version import ServerVer


class ServerState:
    def __init__(self, server: "ServerContext"):
        self.server = server

    async def handle_incoming_event(self, event: QuicStreamEvent):
        raise NotImplementedError("handle_incoming_event not implemented")


class AwaitingVerExchangeState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)
        if dgram_in.mtype == pdu.MSG_TYPE_VERSION_EXCHANGE:
            print("Received version exchange request from client")
            if dgram_in.protocol_ver <= ServerVer.protocol:
                print("\tProtocol version match")
            else:
                raise IncompatibleProtocolVersion()

            if dgram_in.firmware_ver < ServerVer.firmware:
                print("\tFirmware version match")
            else:
                raise IncompatibleFirmwareVersion()

            # Send version ack
            dgram_out = Datagram(
                mtype=pdu.MSG_TYPE_VERSION_ACK,
                protocol_ver=ServerVer.protocol,
                firmware_ver=ServerVer.firmware,
            )
            response_event = QuicStreamEvent(
                event.stream_id, dgram_out.to_bytes(), True
            )
            self.server.set_state(SendingState(self.server))
            await self.server.conn.send(response_event)


class SendingState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)
        # stream_id = event.stream_id
        stream_id = event.stream_id + 1

        if dgram_in.mtype == pdu.MSG_TYPE_REQUEST_UPDATE:
            await self._send_firmware(stream_id)

    async def _send_firmware(
        self, stream_id: int, firmware_path: str = "./server/firmware/firmware.bin"
    ) -> None:
        print("Request for firmware update received")
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


class AwaitingAckState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)

        if dgram_in.mtype == pdu.MSG_TYPE_RECEIVE_ACK:
            print("Received ACK from client")
            self.server.set_state(AwaitingVerExchangeState(self.server))


class ServerContext:
    def __init__(self, conn: QuicConnection):
        self.conn = conn
        self.state = AwaitingVerExchangeState(self)

    def set_state(self, state: ServerState):
        self.state = state

    async def handle_incoming_event(self, event: QuicStreamEvent):
        await self.state.handle_incoming_event(event)
