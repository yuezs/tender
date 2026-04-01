from core.database import Base, engine
from modules.discovery.model import ProjectDiscoveryRun, ProjectLead
from modules.knowledge.model import KnowledgeChunk, KnowledgeDocument


def init_tables() -> None:
    for table in (
        KnowledgeDocument.__table__,
        KnowledgeChunk.__table__,
        ProjectDiscoveryRun.__table__,
        ProjectLead.__table__,
    ):
        table.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    init_tables()
    print("knowledge and discovery tables initialized")
