import json

from core.config import settings
from core.exceptions import BusinessException
from modules.agent.ggzy_collector import GgzyCollector
from modules.agent.openclaw_client import OpenClawClient
from modules.agent.output_parser import ensure_collect_result
from modules.agent.prompt_templates import build_collect_prompt


class CollectAgent:
    def __init__(self) -> None:
        self.client = OpenClawClient()
        self.ggzy_collector = GgzyCollector()

    def build_prompt(self, source: str) -> str:
        return build_collect_prompt(source)

    def run(
        self,
        *,
        source: str,
        execution_context: dict | None = None,
        prompt: str | None = None,
    ) -> dict:
        prompt = prompt or self.build_prompt(source)
        execution_context = execution_context or {}
        failure_reasons: list[str] = []

        if source == "ggzy" and settings.discovery_collect_use_openclaw_agent:
            try:
                llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
                raw_result = self.client.parse_json_object(llm_response["text"])
                normalized_result = ensure_collect_result(raw_result)
                if not normalized_result["projects"]:
                    raise BusinessException("OpenClaw collect agent returned no collectable projects.")
                llm_response["debug"]["collect_mode"] = "openclaw-agent"
                return {
                    "result": normalized_result,
                    "debug": llm_response["debug"],
                    "prompt": prompt,
                    "raw_text": llm_response["text"],
                }
            except BusinessException as exc:
                failure_reasons.append(f"openclaw-agent: {exc.message}")

        if source == "ggzy" and settings.discovery_collect_use_real_ggzy:
            try:
                collector_payload = self.ggzy_collector.collect()
                normalized_result = ensure_collect_result(collector_payload)
                if not normalized_result["projects"]:
                    raise BusinessException("ggzy collector returned no collectable projects.")
                return {
                    "result": normalized_result,
                    "debug": {
                        "provider": "ggzy-http",
                        "agent_id": settings.openclaw_agent_collect,
                        "used_fallback": False,
                        "list_url": collector_payload.get("meta", {}).get("list_url", ""),
                        "candidate_count": collector_payload.get("meta", {}).get("candidate_count", 0),
                        "project_count": collector_payload.get("meta", {}).get("project_count", 0),
                        "failure_count": collector_payload.get("meta", {}).get("failure_count", 0),
                        "failures": collector_payload.get("meta", {}).get("failures", []),
                        "fallback_from": "openclaw-agent" if failure_reasons else "",
                        "failure_reason": "; ".join(failure_reasons),
                        "session_key": execution_context.get("session_key", ""),
                        "run_id": execution_context.get("run_id", ""),
                        "idempotency_key": execution_context.get("idempotency_key", ""),
                    },
                    "prompt": prompt,
                    "raw_text": json.dumps(normalized_result, ensure_ascii=False, indent=2),
                }
            except BusinessException as exc:
                failure_reasons.append(f"ggzy-http: {exc.message}")

        if settings.agent_use_real_llm and source != "ggzy":
            try:
                llm_response = self._run_llm(prompt=prompt, execution_context=execution_context)
                raw_result = self.client.parse_json_object(llm_response["text"])
                normalized_result = ensure_collect_result(raw_result)
                if not normalized_result["projects"]:
                    raise BusinessException("OpenClaw returned no collectable projects.")
                return {
                    "result": normalized_result,
                    "debug": llm_response["debug"],
                    "prompt": prompt,
                    "raw_text": llm_response["text"],
                }
            except BusinessException as exc:
                fallback_result = ensure_collect_result(self._build_fallback_result(source))
                return {
                    "result": fallback_result,
                    "debug": {
                        "provider": "fallback-mock",
                        "agent_id": settings.openclaw_agent_collect,
                        "used_fallback": True,
                        "failure_reason": "; ".join([*failure_reasons, exc.message]),
                        "session_key": execution_context.get("session_key", ""),
                        "run_id": execution_context.get("run_id", ""),
                        "idempotency_key": execution_context.get("idempotency_key", ""),
                    },
                    "prompt": prompt,
                    "raw_text": json.dumps(fallback_result, ensure_ascii=False, indent=2),
                }

        fallback_result = ensure_collect_result(self._build_fallback_result(source))
        return {
            "result": fallback_result,
            "debug": {
                "provider": "fallback-mock",
                "agent_id": settings.openclaw_agent_collect,
                "used_fallback": True,
                "failure_reason": "; ".join(failure_reasons) or "AGENT_USE_REAL_LLM is disabled.",
                "session_key": execution_context.get("session_key", ""),
                "run_id": execution_context.get("run_id", ""),
                "idempotency_key": execution_context.get("idempotency_key", ""),
            },
            "prompt": prompt,
            "raw_text": json.dumps(fallback_result, ensure_ascii=False, indent=2),
        }

    def _run_llm(self, *, prompt: str, execution_context: dict) -> dict:
        run_id = str(execution_context.get("run_id", "")).strip()
        common_kwargs = {
            "agent_id": settings.openclaw_agent_collect,
            "message": prompt,
            "session_key": execution_context["session_key"],
            "idempotency_key": execution_context["idempotency_key"],
        }
        if run_id:
            return self.client.wait_agent_run(run_id=run_id, **common_kwargs)
        return self.client.run_agent(**common_kwargs)

    def _build_fallback_result(self, source: str) -> dict:
        if source != "ggzy":
            return {"projects": []}
        return {
            "projects": [
                {
                    "source": "ggzy",
                    "source_notice_id": "GSS2026016",
                    "title": "区域核与辐射应急监测物资储备库（西北库）项目勘察招标公告",
                    "notice_type": "招标公告",
                    "region": "甘肃",
                    "published_at": "2026-03-09 00:00:00",
                    "detail_url": "https://pzxx.ggzyjy.gansu.gov.cn/f/newprovince/tenderproject/NTk4MjE=/tenderprojectIndex?area=620000",
                    "canonical_url": "https://pzxx.ggzyjy.gansu.gov.cn/f/newprovince/tenderproject/NTk4MjE=/tenderprojectIndex?area=620000",
                    "project_code": "GSS2026016",
                    "tender_unit": "生态环境部核与辐射安全中心",
                    "budget_text": "60.35万元",
                    "deadline_text": "2026-04-15 09:30",
                    "detail_text": (
                        "项目名称：区域核与辐射应急监测物资储备库（西北库）项目勘察\n"
                        "招标人：生态环境部核与辐射安全中心\n"
                        "项目编号：GSS2026016\n"
                        "预算金额：60.35万元\n"
                        "投标截止时间：2026-04-15 09:30\n"
                        "资格要求：具备工程勘察相关资质，具有类似项目业绩。"
                    ),
                    "qualification_requirements": ["具备工程勘察相关资质", "具有类似项目业绩"],
                    "keywords": ["核与辐射", "应急监测", "勘察"],
                },
                {
                    "source": "ggzy",
                    "source_notice_id": "GSXYZ20260328",
                    "title": "某市智慧园区综合管理平台建设项目公开招标公告",
                    "notice_type": "公开招标公告",
                    "region": "甘肃",
                    "published_at": "2026-03-28 10:00:00",
                    "detail_url": "https://www.ggzy.gov.cn/example/detail/GSXYZ20260328",
                    "canonical_url": "https://www.ggzy.gov.cn/example/detail/GSXYZ20260328",
                    "project_code": "GSXYZ20260328",
                    "tender_unit": "某市大数据管理局",
                    "budget_text": "500万元",
                    "deadline_text": "2026-04-18 09:00",
                    "detail_text": (
                        "项目名称：某市智慧园区综合管理平台建设项目\n"
                        "采购单位：某市大数据管理局\n"
                        "项目编号：GSXYZ20260328\n"
                        "预算金额：500万元\n"
                        "投标截止时间：2026-04-18 09:00\n"
                        "资格要求：具备软件企业相关资质证书，具有智慧园区或政务信息化项目案例。"
                    ),
                    "qualification_requirements": [
                        "具备软件企业相关资质证书",
                        "具有智慧园区或政务信息化项目案例",
                    ],
                    "keywords": ["智慧园区", "平台建设", "政务信息化"],
                },
            ]
        }
