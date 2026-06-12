from pydantic import BaseModel, ConfigDict


class AppSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
