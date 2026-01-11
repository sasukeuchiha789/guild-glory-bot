# ==========================================================
#  SYSTEM      : Guild Glory Core Runtime
#  MODULE      : Cryptographic Abstraction Layer
#  FILE        : crypto_layer.py
# ==========================================================

import os
import time
import json
import hmac
import base64
import hashlib
import logging
from typing import Dict

log = logging.getLogger("GuildGloryRuntime.Crypto")

# ----------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------

DEFAULT_HASH = "sha256"
KEY_ROTATION_INTERVAL = 60 * 15  # 15 minutes

# ----------------------------------------------------------
# KEY MATERIAL
# ----------------------------------------------------------

class KeyMaterial:
    """
    Holds derived key material for a session lifecycle.
    """

    def __init__(self, seed: str):
        self.seed = seed
        self.created_at = time.time()
        self.current_key = self._derive(seed)

    def _derive(self, seed: str) -> bytes:
        log.debug("Deriving cryptographic key material")
        return hashlib.sha256(seed.encode()).digest()

    def rotate_if_needed(self):
        age = time.time() - self.created_at
        if age > KEY_ROTATION_INTERVAL:
            log.info("Rotating session key material")
            self.current_key = self._derive(
                base64.b64encode(self.current_key).decode()
            )
            self.created_at = time.time()

# ----------------------------------------------------------
# CRYPTO ENGINE
# ----------------------------------------------------------

class CryptoEngine:
    """
    Lightweight crypto abstraction.
    NOTE: Used only for internal payload integrity simulation.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key_material = KeyMaterial(session_id)

    # ------------------------------------------------------

    def sign_payload(self, payload: Dict) -> Dict:
        """
        Attach integrity signature to payload.
        """
        self.key_material.rotate_if_needed()

        encoded = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            self.key_material.current_key,
            encoded,
            hashlib.sha256
        ).digest()

        payload["_sig"] = base64.b64encode(signature).decode()
        return payload

    # ------------------------------------------------------

    def verify_payload(self, payload: Dict) -> bool:
        """
        Verify integrity signature.
        """
        if "_sig" not in payload:
            log.warning("Payload missing signature field")
            return False

        sig = payload.pop("_sig")

        encoded = json.dumps(payload, sort_keys=True).encode()
        expected = hmac.new(
            self.key_material.current_key,
            encoded,
            hashlib.sha256
        ).digest()

        valid = hmac.compare_digest(
            base64.b64encode(expected).decode(),
            sig
        )

        if not valid:
            log.error("Payload signature mismatch detected")

        return valid

    # ------------------------------------------------------

    def encrypt_stub(self, data: bytes) -> bytes:
        """
        Placeholder encryption routine.
        """
        log.debug("Encrypting payload (stub)")
        return base64.b64encode(data)

    def decrypt_stub(self, data: bytes) -> bytes:
        """
        Placeholder decryption routine.
        """
        log.debug("Decrypting payload (stub)")
        return base64.b64decode(data)