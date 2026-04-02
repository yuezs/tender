from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.response import success_response
from modules.discovery.schema import DiscoveryRunRequest
from modules.discovery.service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])
service = DiscoveryService()


@router.get("/status")
def get_discovery_module_status():
    return success_response(service.get_module_status())


@router.get("/profile")
def get_discovery_profile(db: Session = Depends(get_db)):
    result = service.get_profile(db)
    return success_response(result, message="企业能力画像获取成功。")


@router.post("/runs")
def run_discovery_collection(payload: DiscoveryRunRequest, db: Session = Depends(get_db)):
    result = service.run_collection(db, payload.source, payload.model_dump())
    return success_response(result, message="项目采集执行成功。")


@router.get("/runs")
def list_discovery_runs(db: Session = Depends(get_db)):
    result = service.list_runs(db)
    return success_response(result, message="项目采集记录获取成功。")


@router.get("/projects")
def list_discovery_projects(
    keyword: str = "",
    region: str = "",
    notice_type: str = "",
    recommendation_level: str = "",
    profile_key: str = "",
    recommended_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    result = service.list_projects(
        db,
        keyword=keyword,
        region=region,
        notice_type=notice_type,
        recommendation_level=recommendation_level,
        profile_key=profile_key,
        recommended_only=recommended_only,
        page=page,
        page_size=page_size,
    )
    return success_response(result, message="项目线索列表获取成功。")


@router.get("/projects/{lead_id}")
def get_discovery_project_detail(lead_id: str, db: Session = Depends(get_db)):
    result = service.get_project_detail(db, lead_id)
    return success_response(result, message="项目线索详情获取成功。")
