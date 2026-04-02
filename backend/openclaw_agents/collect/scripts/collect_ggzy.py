import argparse
import base64
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targeting-json-b64", default="")
    parser.add_argument("--profile-key", default="")
    parser.add_argument("--profile-title", default="")
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--region", action="append", default=[])
    parser.add_argument("--qualification-term", action="append", default=[])
    parser.add_argument("--industry-term", action="append", default=[])
    return parser.parse_args()


def decode_targeting_payload(raw_value: str) -> dict:
    if not raw_value.strip():
        return {}

    try:
        padding = "=" * (-len(raw_value) % 4)
        decoded = base64.urlsafe_b64decode(f"{raw_value}{padding}".encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}


def main() -> int:
    backend_dir = Path(__file__).resolve().parents[3]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from modules.agent.ggzy_collector import GgzyCollector

    args = parse_args()
    targeting = decode_targeting_payload(args.targeting_json_b64)
    if not targeting:
        targeting = {
            "mode": "targeted"
            if any(
                [
                    args.keyword,
                    args.region,
                    args.qualification_term,
                    args.industry_term,
                ]
            )
            else "broad",
            "profile_key": args.profile_key,
            "profile_title": args.profile_title,
            "keywords": args.keyword,
            "regions": args.region,
            "qualification_terms": args.qualification_term,
            "industry_terms": args.industry_term,
        }

    payload = GgzyCollector(targeting=targeting).collect()
    print(json.dumps({"projects": payload.get("projects", [])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
