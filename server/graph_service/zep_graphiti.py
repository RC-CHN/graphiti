import logging
from typing import Annotated

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti  # type: ignore
from graphiti_core.edges import EntityEdge  # type: ignore
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError
from graphiti_core.llm_client import LLMClient  # type: ignore
from graphiti_core.nodes import EntityNode, EpisodicNode  # type: ignore

from graph_service.config import ZepEnvDep
from graph_service.dto import EntityEdgeResult, EntityNodeResult, FactResult

logger = logging.getLogger(__name__)


class ZepGraphiti(Graphiti):
    def __init__(self, uri: str, user: str, password: str, llm_client: LLMClient | None = None):
        super().__init__(uri, user, password, llm_client)

    async def save_entity_node(self, name: str, uuid: str, group_id: str, summary: str = ''):
        new_node = EntityNode(
            name=name,
            uuid=uuid,
            group_id=group_id,
            summary=summary,
        )
        await new_node.generate_name_embedding(self.embedder)
        await new_node.save(self.driver)
        return new_node

    async def get_entity_node(self, uuid: str):
        try:
            node = await EntityNode.get_by_uuid(self.driver, uuid)
            return node
        except NodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def search_entity_nodes(
        self, query: str | None, group_ids: list[str] | None, limit: int = 10
    ):
        if query:
            # Simple fuzzy search using Cypher
            # Note: This is a basic implementation. For production, consider full-text indexes.
            cypher_query = """
            MATCH (n:Entity)
            WHERE ($group_ids IS NULL OR n.group_id IN $group_ids)
              AND toLower(n.name) CONTAINS toLower($query)
            RETURN n.uuid AS uuid
            LIMIT $limit
            """
            records, _, _ = await self.driver.execute_query(
                cypher_query, query=query, group_ids=group_ids, limit=limit
            )
            uuids = [record['uuid'] for record in records]
            if not uuids:
                return []
            return await EntityNode.get_by_uuids(self.driver, uuids)
        elif group_ids:
            return await EntityNode.get_by_group_ids(self.driver, group_ids, limit=limit)
        else:
            # If no query and no group_ids, return empty or default behavior?
            # Let's require at least one filter or return empty to avoid dumping the whole DB
            return []

    async def update_entity_node(
        self,
        uuid: str,
        name: str | None = None,
        summary: str | None = None,
        labels: list[str] | None = None,
        attributes: dict | None = None,
    ):
        node = await self.get_entity_node(uuid)

        if name is not None:
            node.name = name
            # Regenerate embedding if name changes
            await node.generate_name_embedding(self.embedder)

        if summary is not None:
            node.summary = summary

        if labels is not None:
            node.labels = labels

        if attributes is not None:
            node.attributes = attributes

        await node.save(self.driver)
        return node

    async def get_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            return edge
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_group(self, group_id: str):
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
        except GroupsEdgesNotFoundError:
            logger.warning(f'No edges found for group {group_id}')
            edges = []

        nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])

        episodes = await EpisodicNode.get_by_group_ids(self.driver, [group_id])

        for edge in edges:
            await edge.delete(self.driver)

        for node in nodes:
            await node.delete(self.driver)

        for episode in episodes:
            await episode.delete(self.driver)

    async def delete_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            await edge.delete(self.driver)
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_episodic_node(self, uuid: str):
        try:
            episode = await EpisodicNode.get_by_uuid(self.driver, uuid)
            await episode.delete(self.driver)
        except NodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e


async def get_graphiti(settings: ZepEnvDep):
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    if settings.openai_base_url is not None:
        client.llm_client.config.base_url = settings.openai_base_url
    if settings.openai_api_key is not None:
        client.llm_client.config.api_key = settings.openai_api_key
    if settings.model_name is not None:
        client.llm_client.model = settings.model_name

    try:
        yield client
    finally:
        await client.close()


async def initialize_graphiti(settings: ZepEnvDep):
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await client.build_indices_and_constraints()


def get_fact_result_from_edge(edge: EntityEdge):
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


def get_entity_node_result_from_node(node: EntityNode):
    return EntityNodeResult(
        uuid=node.uuid,
        name=node.name,
        summary=node.summary,
        group_id=node.group_id,
        created_at=node.created_at,
        labels=node.labels,
        attributes=node.attributes,
    )


def get_entity_edge_result_from_edge(edge: EntityEdge):
    return EntityEdgeResult(
        uuid=edge.uuid,
        source_node_uuid=edge.source_node_uuid,
        target_node_uuid=edge.target_node_uuid,
        name=edge.name,
        fact=edge.fact,
        group_id=edge.group_id,
        created_at=edge.created_at,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        expired_at=edge.expired_at,
        attributes=edge.attributes,
    )


ZepGraphitiDep = Annotated[ZepGraphiti, Depends(get_graphiti)]
