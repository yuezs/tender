import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
import sys

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class ConfigEnvLoadingTests(unittest.TestCase):
    def test_load_env_file_sets_missing_values_without_overriding_existing_env(self):
        from core import config

        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "MYSQL_HOST=10.0.0.5\nMYSQL_PORT=4406\nOPENCLAW_GATEWAY_TOKEN=demo-token\n",
                encoding="utf-8",
            )

            original = dict(os.environ)
            try:
                os.environ.pop("MYSQL_HOST", None)
                os.environ["MYSQL_PORT"] = "3307"
                os.environ.pop("OPENCLAW_GATEWAY_TOKEN", None)

                config._load_env_file(env_path)

                self.assertEqual(os.environ["MYSQL_HOST"], "10.0.0.5")
                self.assertEqual(os.environ["MYSQL_PORT"], "3307")
                self.assertEqual(os.environ["OPENCLAW_GATEWAY_TOKEN"], "demo-token")
            finally:
                os.environ.clear()
                os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
