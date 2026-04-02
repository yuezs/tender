import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from modules.agent.openclaw_client import DeviceIdentity, GatewayRpcConnection


class OpenClawClientConnectParamsTests(unittest.TestCase):
    def test_connect_prefers_device_token_when_available(self):
        connection = GatewayRpcConnection()

        with patch(
            "modules.agent.openclaw_client.settings",
            SimpleNamespace(
                openclaw_gateway_token="shared-gateway-token",
                openclaw_gateway_password="",
                app_name="AI Tender Assistant",
                app_env="development",
            ),
        ), patch.object(
            GatewayRpcConnection,
            "_load_or_create_device_identity",
            return_value=DeviceIdentity(
                device_id="device-123",
                public_key_pem="PUBLIC",
                private_key_pem="PRIVATE",
            ),
        ), patch.object(
            GatewayRpcConnection,
            "_load_device_auth_token",
            return_value="paired-device-token",
        ), patch.object(
            GatewayRpcConnection,
            "_public_key_raw_base64url",
            return_value="public-key-b64",
        ), patch.object(
            GatewayRpcConnection,
            "_sign_device_payload",
            return_value="signature-b64",
        ):
            params = connection._build_connect_params("nonce-123")

        self.assertEqual(params["auth"]["deviceToken"], "paired-device-token")
        self.assertNotIn("token", params["auth"])
        self.assertEqual(params["client"]["platform"], sys.platform.lower())
        self.assertEqual(
            params["scopes"],
            [
                "operator.read",
                "operator.write",
                "operator.admin",
                "operator.approvals",
                "operator.pairing",
            ],
        )


if __name__ == "__main__":
    unittest.main()
