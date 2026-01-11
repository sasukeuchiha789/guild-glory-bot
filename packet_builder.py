# ==========================================================
#  SYSTEM      : Guild Glory Core Runtime
#  MODULE      : Packet Construction Engine
#  FILE        : packet_builder.py
# ==========================================================

import time
import json
import logging
from typing import Dict, Any

from crypto_layer import CryptoEngine

log = logging.getLogger("GuildGloryRuntime.Packet")

# ----------------------------------------------------------
# OPCODES
# ----------------------------------------------------------

OP_HANDSHAKE = 0x01
OP_HEARTBEAT = 0x02
OP_EVENT = 0x10
OP_CONTROL = 0x20

# ----------------------------------------------------------
# PACKET HEADER
# ----------------------------------------------------------

class PacketHeader:
    """
    Packet metadata container.
    """

    def __init__(self, opcode: int, seq: int):
        self.opcode = opcode
        self.sequence = seq
        self.timestamp = int(time.time() * 1000)

    def serialize(self) -> Dict[str, Any]:
        return {
            "op": self.opcode,
            "seq": self.sequence,
            "ts": self.timestamp
        }

# ----------------------------------------------------------
# PACKET BUILDER
# ----------------------------------------------------------

class PacketBuilder:
    """
    Constructs structured packets for transport layer.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.crypto = CryptoEngine(session_id)

    # ------------------------------------------------------

    def build_handshake(self, seq: int) -> bytes:
        header = PacketHeader(OP_HANDSHAKE, seq)
        payload = {
            "session": self.session_id,
            "stage": "INIT"
        }
        return self._finalize(header, payload)

    def build_heartbeat(self, seq: int) -> bytes:
        header = PacketHeader(OP_HEARTBEAT, seq)
        payload = {
            "status": "ALIVE"
        }
        return self._finalize(header, payload)

    def build_event(self, seq: int, event_name: str, data: Dict) -> bytes:
        header = PacketHeader(OP_EVENT, seq)
        payload = {
            "event": event_name,
            "data": data
        }
        return self._finalize(header, payload)

    # ------------------------------------------------------

    def _finalize(self, header: PacketHeader, payload: Dict) -> bytes:
        packet = {
            "hdr": header.serialize(),
            "body": payload
        }

        signed = self.crypto.sign_payload(packet)
        encoded = json.dumps(signed).encode()

        encrypted = self.crypto.encrypt_stub(encoded)

        log.debug(
            f"Packet built | op={header.opcode} seq={header.sequence}"
        )

        return encrypted