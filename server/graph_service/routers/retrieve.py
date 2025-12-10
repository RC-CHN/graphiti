from datetime import datetime, timezone

from fastapi import APIRouter, status

from graphiti_core.search.search_config import SearchConfig
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_CROSS_ENCODER

from graph_service.dto import (
    AdvancedSearchQuery,
    AdvancedSearchResults,
    EntityEdgeResult,
    EntityNodeResult,
    GetMemoryRequest,
    GetMemoryResponse,
    Message,
    SearchQuery,
    SearchResults,
)
from graph_service.zep_graphiti import (
    ZepGraphitiDep,
    get_entity_edge_result_from_edge,
    get_entity_node_result_from_node,
    get_fact_result_from_edge,
)

router = APIRouter()


@router.post('/search', status_code=status.HTTP_200_OK)
async def search(query: SearchQuery, graphiti: ZepGraphitiDep):
    relevant_edges = await graphiti.search(
        group_ids=query.group_ids,
        query=query.query,
        num_results=query.max_facts,
    )
    facts = [get_fact_result_from_edge(edge) for edge in relevant_edges]
    return SearchResults(
        facts=facts,
    )


@router.post('/search/advanced', status_code=status.HTTP_200_OK)
async def advanced_search(query: AdvancedSearchQuery, graphiti: ZepGraphitiDep):
    config = COMBINED_HYBRID_SEARCH_CROSS_ENCODER
    config.limit = query.limit

    results = await graphiti.search_(
        query=query.query,
        group_ids=query.group_ids,
        center_node_uuid=query.center_node_uuid,
        config=config,
    )

    return AdvancedSearchResults(
        edges=[get_entity_edge_result_from_edge(edge) for edge in results.edges],
        nodes=[get_entity_node_result_from_node(node) for node in results.nodes],
    )


@router.get('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def get_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    entity_edge = await graphiti.get_entity_edge(uuid)
    return get_fact_result_from_edge(entity_edge)


@router.get('/episodes/{group_id}', status_code=status.HTTP_200_OK)
async def get_episodes(group_id: str, last_n: int, graphiti: ZepGraphitiDep):
    episodes = await graphiti.retrieve_episodes(
        group_ids=[group_id], last_n=last_n, reference_time=datetime.now(timezone.utc)
    )
    return episodes


@router.post('/get-memory', status_code=status.HTTP_200_OK)
async def get_memory(
    request: GetMemoryRequest,
    graphiti: ZepGraphitiDep,
):
    combined_query = compose_query_from_messages(request.messages)
    result = await graphiti.search(
        group_ids=[request.group_id],
        query=combined_query,
        num_results=request.max_facts,
    )
    facts = [get_fact_result_from_edge(edge) for edge in result]
    return GetMemoryResponse(facts=facts)


def compose_query_from_messages(messages: list[Message]):
    combined_query = ''
    for message in messages:
        combined_query += f'{message.role_type or ""}({message.role or ""}): {message.content}\n'
    return combined_query
