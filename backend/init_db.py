from core.database import Base, engine
from modules.knowledge.model import KnowledgeChunk, KnowledgeDocument


def init_knowledge_tables() -> None:
    Base.metadata.create_all(
        bind=engine,
        tables=[
            KnowledgeDocument.__table__,
            KnowledgeChunk.__table__,
        ],
    )


if __name__ == "__main__":
    init_knowledge_tables()
    print("knowledge tables initialized")
