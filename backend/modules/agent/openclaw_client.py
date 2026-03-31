import json
import platform
import time
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.config import settings
from core.exceptions import BusinessException

try:
    from websocket import create_connection
except ImportError:  # pragma: no cover - optional until dependency is installed
    create_connection = None


SUCCESS_STATUSES = {"ok", "success", "completed"}


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
        auth: dict[str, str] = {}
        if settings.openclaw_gateway_token:
            auth["token"] = settings.openclaw_gateway_token
        if settings.openclaw_gateway_password:
            auth["password"] = settings.openclaw_gateway_password

        payload: dict[str, Any] = {
            "minProtocol": 3,
            "maxProtocol": 3,
            "client": {
                "id": "gateway-client",
                "displayName": settings.app_name,
                "version": settings.app_env,
                "platform": platform.system().lower() or "unknown",
                "mode": "backend",
                "instanceId": "ai-tender-assistant",
            },
            "caps": [],
            "role": "operator",
            "scopes": ["operator.read", "operator.write", "operator.admin"],
            "locale": "zh-CN",
            "userAgent": "ai-tender-assistant/backend",
        }
        if auth:
            payload["auth"] = auth
        return payload

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
            raise BusinessException(
                f"OpenClaw Gateway request timed out after {settings.openclaw_timeout_seconds}s."
            )
        if status and status not in SUCCESS_STATUSES:
            error = str(wait_payload.get("error") or "unknown error").strip()
            raise BusinessException(f"OpenClaw Gateway request failed: {error}")

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
        if assistant_text:
            return assistant_text

        transcript = connection.request(
            "sessions.get",
            {
                "key": session_key,
                "limit": 200,
            },
        )
        assistant_text = self._extract_latest_assistant_text(transcript.get("messages"))
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
