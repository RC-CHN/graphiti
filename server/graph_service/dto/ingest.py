from pydantic import BaseModel, Field

from graph_service.dto.common import Message


class AddMessagesRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the messages to add')
    messages: list[Message] = Field(..., description='The messages to add')


class AddEntityNodeRequest(BaseModel):
    uuid: str = Field(..., description='The uuid of the node to add')
    group_id: str = Field(..., description='The group id of the node to add')
    name: str = Field(..., description='The name of the node to add')
    summary: str = Field(default='', description='The summary of the node to add')


class BuildCommunitiesRequest(BaseModel):
    group_ids: list[str] | None = Field(None, description='The group ids to build communities for')


class SearchNodeRequest(BaseModel):
    query: str | None = Field(None, description='The query to search for')
    group_ids: list[str] | None = Field(None, description='The group ids to search in')
    limit: int = Field(default=10, description='The maximum number of nodes to retrieve')


class UpdateEntityNodeRequest(BaseModel):
    name: str | None = Field(None, description='The new name of the node')
    summary: str | None = Field(None, description='The new summary of the node')
    labels: list[str] | None = Field(None, description='The new labels of the node')
    attributes: dict | None = Field(None, description='The new attributes of the node')
