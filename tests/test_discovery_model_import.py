import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class DiscoveryModelImportTests(unittest.TestCase):
    def test_discovery_models_can_be_imported(self):
        from modules.discovery.model import ProjectDiscoveryRun, ProjectLead

        self.assertEqual(ProjectDiscoveryRun.__tablename__, "project_discovery_runs")
        self.assertEqual(ProjectLead.__tablename__, "project_leads")


if __name__ == "__main__":
    unittest.main()
