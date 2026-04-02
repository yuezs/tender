from sqlalchemy import inspect, text

from core.database import Base, engine
from modules.discovery.model import ProjectDiscoveryRun, ProjectLead
from modules.knowledge.model import KnowledgeChunk, KnowledgeDocument


DISCOVERY_RUN_COLUMNS = {
    "targeting_snapshot": "ALTER TABLE project_discovery_runs ADD COLUMN targeting_snapshot TEXT NULL",
}

DISCOVERY_LEAD_COLUMNS = {
    "targeting_match_score": "ALTER TABLE project_leads ADD COLUMN targeting_match_score INT NOT NULL DEFAULT 0",
    "profile_key": "ALTER TABLE project_leads ADD COLUMN profile_key VARCHAR(128) NOT NULL DEFAULT ''",
    "profile_title": "ALTER TABLE project_leads ADD COLUMN profile_title VARCHAR(255) NOT NULL DEFAULT ''",
}


def init_tables() -> None:
    for table in (
        KnowledgeDocument.__table__,
        KnowledgeChunk.__table__,
        ProjectDiscoveryRun.__table__,
        ProjectLead.__table__,
    ):
        table.create(bind=engine, checkfirst=True)
    _ensure_discovery_columns()


def _ensure_discovery_columns() -> None:
    inspector = inspect(engine)
    run_columns = {item["name"] for item in inspector.get_columns("project_discovery_runs")}
    lead_columns = {item["name"] for item in inspector.get_columns("project_leads")}

    with engine.begin() as connection:
        for column_name, statement in DISCOVERY_RUN_COLUMNS.items():
            if column_name not in run_columns:
                connection.execute(text(statement))
        for column_name, statement in DISCOVERY_LEAD_COLUMNS.items():
            if column_name not in lead_columns:
                connection.execute(text(statement))


if __name__ == "__main__":
    init_tables()
    print("knowledge and discovery tables initialized")
