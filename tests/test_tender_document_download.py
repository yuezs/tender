import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from modules.tender.repository import TenderRepository


class TenderDocumentDownloadTests(unittest.TestCase):
    def test_repository_can_find_record_by_document_id(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch(
                "modules.tender.repository.settings",
                SimpleNamespace(storage_root=Path(tmp_dir)),
            ):
                repository = TenderRepository()
                repository.create_record(
                    {
                        "file_id": "demo-file",
                        "file_name": "demo.txt",
                        "source_type": "upload",
                        "source_url": "",
                        "extension": "txt",
                        "storage_path": "storage/tender/files/demo.txt",
                        "size": 128,
                        "parse_status": "success",
                        "extract_status": "success",
                        "judge_status": "success",
                        "generate_status": "success",
                        "parsed_text": "demo",
                        "text_path": "storage/tender/parsed/demo.txt",
                        "extract_result": {},
                        "judge_result": {},
                        "generate_result": {
                            "company_intro": "demo",
                            "project_cases": "demo",
                            "implementation_plan": "demo",
                            "business_response": "demo",
                            "download_ready": True,
                            "document_id": "doc-001",
                            "document_file_name": "proposal.docx",
                            "download_url": "/api/tender/documents/doc-001/download",
                        },
                        "generate_document": {
                            "document_id": "doc-001",
                            "file_name": "proposal.docx",
                            "storage_path": str(Path(tmp_dir) / "proposal.docx"),
                            "download_url": "/api/tender/documents/doc-001/download",
                        },
                    }
                )

                record = repository.find_record_by_document_id("doc-001")
                self.assertEqual(record["file_id"], "demo-file")
                self.assertEqual(
                    record["generate_document"]["file_name"],
                    "proposal.docx",
                )


if __name__ == "__main__":
    unittest.main()
