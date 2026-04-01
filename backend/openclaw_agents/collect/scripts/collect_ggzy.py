import json
import sys
from pathlib import Path


def main() -> int:
    backend_dir = Path(__file__).resolve().parents[3]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from modules.agent.ggzy_collector import GgzyCollector

    payload = GgzyCollector().collect()
    print(json.dumps({"projects": payload.get("projects", [])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
