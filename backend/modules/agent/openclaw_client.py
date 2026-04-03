import base64
import json
import platform
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.config import settings
from core.exceptions import BusinessException

try:
    from websocket import create_connection
except ImportError:  # pragma: no cover - optional until dependency is installed
    create_connection = None

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:  # pragma: no cover - optional until dependency is installed
    serialization = None
    ed25519 = None


SUCCESS_STATUSES = {"ok", "success", "completed"}
DEVICE_IDENTITY_VERSION = 1
ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    public_key_pem: str
    private_key_pem: str


class GatewayRpcConnection(AbstractContextManager):
    def __init__(self) -> None:
        self.ws = None

    def __enter__(self) -> "GatewayRpcConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        if create_connection is None:
            raise BusinessException(
                "Missing dependency 'websocket-client'. Install backend requirements first."
            )

        try:
            self.ws = create_connection(
                settings.openclaw_gateway_url,
                timeout=settings.openclaw_timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - depends on runtime network
            raise BusinessException(f"OpenClaw Gateway connect failed: {exc}") from exc

        challenge = self._receive_frame(expected_event="connect.challenge")
        nonce = str((challenge.get("payload") or {}).get("nonce", "")).strip()
        if not nonce:
            raise BusinessException("OpenClaw Gateway connect challenge is missing nonce.")

        hello = self.request(
            "connect",
            self._build_connect_params(nonce),
            timeout_seconds=min(settings.openclaw_timeout_seconds, 15),
        )
        if str(hello.get("type", "")).strip() != "hello-ok":
            raise BusinessException("OpenClaw Gateway did not return hello-ok.")

    def close(self) -> None:
        if self.ws is None:
            return
        try:
            self.ws.close()
        except Exception:
            pass
        self.ws = None

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        if self.ws is None:
            raise BusinessException("OpenClaw Gateway is not connected.")

        request_id = uuid4().hex
        payload = {
            "type": "req",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        self._send_json(payload)
        frame = self._receive_frame(
            expected_response_id=request_id,
            timeout_seconds=timeout_seconds,
        )

        if not frame.get("ok", False):
            error = frame.get("error") or {}
            message = str(error.get("message") or f"gateway request failed: {method}").strip()
            raise BusinessException(f"OpenClaw Gateway {method} failed: {message}")

        response_payload = frame.get("payload")
        if response_payload is None:
            return {}
        if not isinstance(response_payload, dict):
            raise BusinessException(f"OpenClaw Gateway {method} returned an unexpected payload.")
        return response_payload

    def _build_connect_params(self, nonce: str) -> dict[str, Any]:
        role = "operator"
        scopes = [
            "operator.read",
            "operator.write",
            "operator.admin",
        ]
        platform_name = self._resolve_platform_name()
        device_identity = self._load_or_create_device_identity()
        device_token = self._load_device_auth_token(
            device_id=device_identity.device_id,
            role=role,
        )

        auth: dict[str, str] = {}
        if device_token:
            auth["deviceToken"] = device_token
        elif settings.openclaw_gateway_token:
            auth["token"] = settings.openclaw_gateway_token
        elif settings.openclaw_gateway_password:
            auth["password"] = settings.openclaw_gateway_password
        signature_token = (
            auth.get("token")
            or auth.get("deviceToken")
            or auth.get("bootstrapToken")
            or ""
        )
        signed_at_ms = int(time.time() * 1000)
        device_payload = self._build_device_auth_payload(
            device_id=device_identity.device_id,
            client_id="gateway-client",
            client_mode="backend",
            role=role,
            scopes=scopes,
            signed_at_ms=signed_at_ms,
            token=signature_token,
            nonce=nonce,
            platform_name=platform_name,
            device_family="",
        )
        device = {
            "id": device_identity.device_id,
            "publicKey": self._public_key_raw_base64url(device_identity.public_key_pem),
            "signature": self._sign_device_payload(
                device_identity.private_key_pem,
                device_payload,
            ),
            "signedAt": signed_at_ms,
            "nonce": nonce,
        }

        payload: dict[str, Any] = {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": "gateway-client",
                "displayName": settings.app_name,
                "version": settings.app_env,
                "platform": platform_name,
                "mode": "backend",
                "instanceId": "ai-tender-assistant",
            },
            "caps": [],
            "role": role,
            "scopes": scopes,
            "device": device,
            "locale": "zh-CN",
            "userAgent": "ai-tender-assistant/backend",
        }
        if auth:
            payload["auth"] = auth
        return payload

    def _load_device_auth_token(self, *, device_id: str, role: str) -> str:
        auth_store_path = settings.openclaw_state_dir / "identity" / "device-auth.json"
        if not auth_store_path.exists():
            return ""
        try:
            raw = json.loads(auth_store_path.read_text(encoding="utf-8"))
        except Exception:
            return ""

        if str(raw.get("deviceId", "")).strip() != device_id:
            return ""
        tokens = raw.get("tokens")
        if not isinstance(tokens, dict):
            return ""
        entry = tokens.get(role)
        if not isinstance(entry, dict):
            return ""
        return str(entry.get("token", "")).strip()

    def _load_or_create_device_identity(self) -> DeviceIdentity:
        if serialization is None or ed25519 is None:
            raise BusinessException(
                "Missing dependency 'cryptography'. Install backend requirements first."
            )

        identity_path = settings.openclaw_state_dir / "identity" / "device.json"
        identity_path.parent.mkdir(parents=True, exist_ok=True)

        if identity_path.exists():
            try:
                raw = json.loads(identity_path.read_text(encoding="utf-8"))
                device_id = str(raw.get("deviceId", "")).strip()
                public_key_pem = str(raw.get("publicKeyPem", "")).strip()
                private_key_pem = str(raw.get("privateKeyPem", "")).strip()
                if device_id and public_key_pem and private_key_pem:
                    derived_id = self._fingerprint_public_key(public_key_pem)
                    identity = DeviceIdentity(
                        device_id=derived_id or device_id,
                        public_key_pem=public_key_pem,
                        private_key_pem=private_key_pem,
                    )
                    if derived_id and derived_id != device_id:
                        self._write_device_identity(identity_path, identity)
                    return identity
            except Exception:
                pass

        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        identity = DeviceIdentity(
            device_id=self._fingerprint_public_key(public_key_pem),
            public_key_pem=public_key_pem,
            private_key_pem=private_key_pem,
        )
        self._write_device_identity(identity_path, identity)
        return identity

    def _write_device_identity(self, identity_path: Path, identity: DeviceIdentity) -> None:
        stored = {
            "version": DEVICE_IDENTITY_VERSION,
            "deviceId": identity.device_id,
            "publicKeyPem": identity.public_key_pem,
            "privateKeyPem": identity.private_key_pem,
            "createdAtMs": int(time.time() * 1000),
        }
        identity_path.write_text(
            f"{json.dumps(stored, ensure_ascii=False, indent=2)}\n",
            encoding="utf-8",
        )

    def _build_device_auth_payload(
        self,
        *,
        device_id: str,
        client_id: str,
        client_mode: str,
        role: str,
        scopes: list[str],
        signed_at_ms: int,
        token: str,
        nonce: str,
        platform_name: str,
        device_family: str,
    ) -> str:
        return "|".join(
            [
                "v3",
                device_id,
                client_id,
                client_mode,
                role,
                ",".join(scopes),
                str(signed_at_ms),
                token,
                nonce,
                self._normalize_device_metadata(platform_name),
                self._normalize_device_metadata(device_family),
            ]
        )

    def _normalize_device_metadata(self, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else ""

    def _resolve_platform_name(self) -> str:
        system_name = platform.system().lower()
        if system_name == "windows":
            return "windows"
        return system_name or "unknown"

    def _sign_device_payload(self, private_key_pem: str, payload: str) -> str:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
        )
        signature = private_key.sign(payload.encode("utf-8"))
        return self._base64url(signature)

    def _public_key_raw_base64url(self, public_key_pem: str) -> str:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        try:
            raw = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except ValueError:
            raw = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            if raw.startswith(ED25519_SPKI_PREFIX):
                raw = raw[len(ED25519_SPKI_PREFIX) :]
        return self._base64url(raw)

    def _fingerprint_public_key(self, public_key_pem: str) -> str:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        try:
            raw = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except ValueError:
            raw = public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            if raw.startswith(ED25519_SPKI_PREFIX):
                raw = raw[len(ED25519_SPKI_PREFIX) :]
        import hashlib

        return hashlib.sha256(raw).hexdigest()

    def _base64url(self, payload: bytes) -> str:
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    def _send_json(self, payload: dict[str, Any]) -> None:
        if self.ws is None:
            raise BusinessException("OpenClaw Gateway is not connected.")
        try:
            self.ws.send(json.dumps(payload, ensure_ascii=False))
        except Exception as exc:  # pragma: no cover - depends on runtime socket
            raise BusinessException(f"OpenClaw Gateway send failed: {exc}") from exc

    def _receive_frame(
        self,
        *,
        expected_event: str | None = None,
        expected_response_id: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        if self.ws is None:
            raise BusinessException("OpenClaw Gateway is not connected.")

        timeout_value = timeout_seconds or settings.openclaw_timeout_seconds
        try:
            self.ws.settimeout(timeout_value)
        except Exception:
            pass

        deadline = time.monotonic() + timeout_value
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BusinessException("OpenClaw Gateway request timed out.")
            try:
                self.ws.settimeout(remaining)
            except Exception:
                pass
            try:
                raw_message = self.ws.recv()
            except Exception as exc:  # pragma: no cover - depends on runtime socket
                raise BusinessException(f"OpenClaw Gateway receive failed: {exc}") from exc

            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8", errors="replace")

            try:
                frame = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            if not isinstance(frame, dict):
                continue

            frame_type = str(frame.get("type", "")).strip()
            if expected_event and frame_type == "event":
                if str(frame.get("event", "")).strip() == expected_event:
                    return frame
                continue

            if expected_response_id and frame_type == "res":
                if str(frame.get("id", "")).strip() == expected_response_id:
                    return frame
                continue


class OpenClawClient:
    def is_enabled(self) -> bool:
        return settings.agent_use_real_llm

    def check_health(self) -> dict[str, Any]:
        with GatewayRpcConnection() as connection:
            return connection.request("health", {})

    def run_agent(
        self,
        *,
        agent_id: str,
        message: str,
        session_key: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        with GatewayRpcConnection() as connection:
            run_id = self._submit_agent_run(
                connection=connection,
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                idempotency_key=idempotency_key,
            )
            assistant_text = self._wait_for_agent_result(
                connection=connection,
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                run_id=run_id,
                idempotency_key=idempotency_key,
            )

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "text": assistant_text,
            "run_id": run_id,
            "session_key": session_key,
            "debug": {
                "provider": "openclaw-gateway",
                "agent_id": agent_id,
                "run_id": run_id,
                "session_key": session_key,
                "idempotency_key": idempotency_key,
                "duration_ms": duration_ms,
                "used_fallback": False,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def wait_agent_run(
        self,
        *,
        agent_id: str,
        message: str,
        session_key: str,
        run_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        with GatewayRpcConnection() as connection:
            assistant_text = self._wait_for_agent_result(
                connection=connection,
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                run_id=run_id,
                idempotency_key=idempotency_key,
            )

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "text": assistant_text,
            "run_id": run_id,
            "session_key": session_key,
            "debug": {
                "provider": "openclaw-gateway",
                "agent_id": agent_id,
                "run_id": run_id,
                "session_key": session_key,
                "idempotency_key": idempotency_key,
                "duration_ms": duration_ms,
                "used_fallback": False,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "resumed": True,
            },
        }

    def parse_json_object(self, raw_text: str) -> dict[str, Any]:
        candidate = raw_text.strip()
        if not candidate:
            raise BusinessException("OpenClaw returned empty text.")

        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            if "\n" in candidate:
                candidate = candidate.split("\n", 1)[1]
            if candidate.endswith("```"):
                candidate = candidate[:-3]
            candidate = candidate.strip()

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start < 0 or end <= start:
                raise BusinessException("OpenClaw returned non-JSON content.")
            try:
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError as exc:
                raise BusinessException("OpenClaw returned invalid JSON.") from exc

        if not isinstance(parsed, dict):
            raise BusinessException("OpenClaw returned a JSON value that is not an object.")

        return parsed

    def _submit_agent_run(
        self,
        *,
        connection: GatewayRpcConnection,
        agent_id: str,
        message: str,
        session_key: str,
        idempotency_key: str,
    ) -> str:
        response = connection.request(
            "agent",
            self._build_agent_request(
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                idempotency_key=idempotency_key,
            ),
        )
        run_id = str(response.get("runId") or idempotency_key).strip()
        if not run_id:
            raise BusinessException("OpenClaw Gateway did not return run id.")
        return run_id

    def _wait_for_agent_result(
        self,
        *,
        connection: GatewayRpcConnection,
        agent_id: str,
        message: str,
        session_key: str,
        run_id: str,
        idempotency_key: str,
    ) -> str:
        wait_payload = connection.request(
            "agent.wait",
            {
                "runId": run_id,
                "timeoutMs": settings.openclaw_timeout_seconds * 1000,
            },
            timeout_seconds=settings.openclaw_timeout_seconds + 5,
        )
        status = str(wait_payload.get("status", "")).strip().lower()
        if status == "timeout":
            assistant_text = self._load_available_agent_result(
                connection=connection,
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                idempotency_key=idempotency_key,
            )
            if assistant_text:
                return assistant_text
            raise BusinessException(
                f"OpenClaw Gateway request timed out after {settings.openclaw_timeout_seconds}s."
            )
        if status and status not in SUCCESS_STATUSES:
            error = str(wait_payload.get("error") or "unknown error").strip()
            raise BusinessException(f"OpenClaw Gateway request failed: {error}")

        assistant_text = self._load_available_agent_result(
            connection=connection,
            agent_id=agent_id,
            message=message,
            session_key=session_key,
            idempotency_key=idempotency_key,
        )
        if assistant_text:
            return assistant_text

        raise BusinessException("OpenClaw Gateway finished but no assistant reply was found.")

    def _build_agent_request(
        self,
        *,
        agent_id: str,
        message: str,
        session_key: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        request = {
            "message": message,
            "agentId": agent_id,
            "sessionKey": session_key,
            "thinking": settings.openclaw_thinking,
            "timeout": settings.openclaw_timeout_seconds,
            "idempotencyKey": idempotency_key,
        }
        return request

    def _extract_payload_text(self, payload: dict[str, Any]) -> str:
        payloads = payload.get("payloads")
        if not isinstance(payloads, list):
            return ""

        texts: list[str] = []
        for item in payloads:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            if text:
                texts.append(text)
        return "\n".join(texts).strip()

    def _load_available_agent_result(
        self,
        *,
        connection: GatewayRpcConnection,
        agent_id: str,
        message: str,
        session_key: str,
        idempotency_key: str,
    ) -> str:
        cached_payload = connection.request(
            "agent",
            self._build_agent_request(
                agent_id=agent_id,
                message=message,
                session_key=session_key,
                idempotency_key=idempotency_key,
            ),
        )
        assistant_text = self._extract_payload_text(cached_payload.get("result", {}))
        if assistant_text and not self._is_timeout_placeholder_text(assistant_text):
            return assistant_text

        transcript = connection.request(
            "sessions.get",
            {
                "key": session_key,
                "limit": 200,
            },
        )
        return self._extract_latest_assistant_text(transcript.get("messages"))

    def _extract_latest_assistant_text(self, messages: Any) -> str:
        if not isinstance(messages, list):
            return ""

        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            if str(message.get("role", "")).strip() != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text
                continue
            if isinstance(content, list):
                text = self._collect_text_blocks(content)
                if text:
                    return text
        return ""

    def _collect_text_blocks(self, content: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", "")).strip().lower()
            if item_type != "text":
                continue
            text = str(item.get("text", "")).strip()
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    def _is_timeout_placeholder_text(self, text: str) -> bool:
        candidate = text.strip().lower()
        return candidate.startswith("request timed out before a response was generated")
