from datetime import datetime, timezone

from pydantic import BaseModel, Field

from graph_service.dto.common import Message


class SearchQuery(BaseModel):
    group_ids: list[str] | None = Field(
        None, description='The group ids for the memories to search'
    )
    query: str
    max_facts: int = Field(default=10, description='The maximum number of facts to retrieve')


class FactResult(BaseModel):
    uuid: str
    name: str
    fact: str
    valid_at: datetime | None
    invalid_at: datetime | None
    created_at: datetime
    expired_at: datetime | None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class SearchResults(BaseModel):
    facts: list[FactResult]


class AdvancedSearchQuery(BaseModel):
    group_ids: list[str] | None = Field(
        None, description='The group ids for the memories to search'
    )
    query: str
    center_node_uuid: str | None = Field(
        None, description='The uuid of the node to center the retrieval on'
    )
    limit: int = Field(default=10, description='The maximum number of results to retrieve')


class EntityNodeResult(BaseModel):
    uuid: str
    name: str
    summary: str
    group_id: str
    created_at: datetime
    labels: list[str]
    attributes: dict | None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class EntityEdgeResult(BaseModel):
    uuid: str
    source_node_uuid: str
    target_node_uuid: str
    name: str
    fact: str
    group_id: str
    created_at: datetime
    valid_at: datetime | None
    invalid_at: datetime | None
    expired_at: datetime | None
    attributes: dict | None

    class Config:
        json_encoders = {datetime: lambda v: v.astimezone(timezone.utc).isoformat()}


class AdvancedSearchResults(BaseModel):
    edges: list[EntityEdgeResult]
    nodes: list[EntityNodeResult]


class GetMemoryRequest(BaseModel):
    group_id: str = Field(..., description='The group id of the memory to get')
    max_facts: int = Field(default=10, description='The maximum number of facts to retrieve')
    center_node_uuid: str | None = Field(
        ..., description='The uuid of the node to center the retrieval on'
    )
    messages: list[Message] = Field(
        ..., description='The messages to build the retrieval query from '
    )


class GetMemoryResponse(BaseModel):
    facts: list[FactResult] = Field(..., description='The facts that were retrieved from the graph')
