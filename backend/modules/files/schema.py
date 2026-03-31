from pydantic import BaseModel


class FileStatusResponse(BaseModel):
    module: str
    status: str
