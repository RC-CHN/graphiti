import asyncio
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.nodes import EpisodeType  # type: ignore
from graphiti_core.utils.bulk_utils import RawEpisode
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # type: ignore

from graph_service.dto import (
    AddEntityNodeRequest,
    AddMessagesRequest,
    BuildCommunitiesRequest,
    EntityNodeResult,
    Message,
    Result,
    SearchNodeRequest,
    UpdateEntityNodeRequest,
)
from graph_service.zep_graphiti import ZepGraphitiDep, get_entity_node_result_from_node


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None

    async def worker(self):
        while True:
            try:
                print(f'Got a job: (size of remaining queue: {self.queue.qsize()})')
                job = await self.queue.get()
                await job()
            except asyncio.CancelledError:
                break

    async def start(self):
        self.task = asyncio.create_task(self.worker())

    async def stop(self):
        if self.task:
            self.task.cancel()
            await self.task
        while not self.queue.empty():
            self.queue.get_nowait()


async_worker = AsyncWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_worker.start()
    yield
    await async_worker.stop()


router = APIRouter(lifespan=lifespan)


@router.post('/messages', status_code=status.HTTP_202_ACCEPTED)
async def add_messages(
    request: AddMessagesRequest,
    graphiti: ZepGraphitiDep,
):
    async def add_messages_task(m: Message):
        await graphiti.add_episode(
            uuid=m.uuid,
            group_id=request.group_id,
            name=m.name,
            episode_body=f'{m.role or ""}({m.role_type}): {m.content}',
            reference_time=m.timestamp,
            source=EpisodeType.message,
            source_description=m.source_description,
        )

    for m in request.messages:
        await async_worker.queue.put(partial(add_messages_task, m))

    return Result(message='Messages added to processing queue', success=True)


@router.post('/ingest/batch', status_code=status.HTTP_200_OK)
async def ingest_batch(
    request: AddMessagesRequest,
    graphiti: ZepGraphitiDep,
):
    episodes = [
        RawEpisode(
            uuid=m.uuid,
            name=m.name,
            content=f'{m.role or ""}({m.role_type}): {m.content}',
            reference_time=m.timestamp,
            source=EpisodeType.message,
            source_description=m.source_description,
        )
        for m in request.messages
    ]

    await graphiti.add_episode_bulk(
        bulk_episodes=episodes,
        group_id=request.group_id,
    )

    return Result(message='Batch ingestion completed', success=True)


@router.post('/communities/build', status_code=status.HTTP_200_OK)
async def build_communities(
    request: BuildCommunitiesRequest,
    graphiti: ZepGraphitiDep,
):
    await graphiti.build_communities(group_ids=request.group_ids)
    return Result(message='Communities built', success=True)


@router.post('/entity-node', status_code=status.HTTP_201_CREATED, response_model=EntityNodeResult)
async def add_entity_node(
    request: AddEntityNodeRequest,
    graphiti: ZepGraphitiDep,
):
    node = await graphiti.save_entity_node(
        uuid=request.uuid,
        group_id=request.group_id,
        name=request.name,
        summary=request.summary,
    )
    return get_entity_node_result_from_node(node)


@router.get('/entity-node/{uuid}', status_code=status.HTTP_200_OK, response_model=EntityNodeResult)
async def get_entity_node(uuid: str, graphiti: ZepGraphitiDep):
    node = await graphiti.get_entity_node(uuid)
    return get_entity_node_result_from_node(node)


@router.post(
    '/entity-node/search',
    status_code=status.HTTP_200_OK,
    response_model=list[EntityNodeResult],
)
async def search_entity_nodes(
    request: SearchNodeRequest,
    graphiti: ZepGraphitiDep,
):
    nodes = await graphiti.search_entity_nodes(
        query=request.query, group_ids=request.group_ids, limit=request.limit
    )
    return [get_entity_node_result_from_node(node) for node in nodes]


@router.patch(
    '/entity-node/{uuid}', status_code=status.HTTP_200_OK, response_model=EntityNodeResult
)
async def update_entity_node(
    uuid: str,
    request: UpdateEntityNodeRequest,
    graphiti: ZepGraphitiDep,
):
    node = await graphiti.update_entity_node(
        uuid=uuid,
        name=request.name,
        summary=request.summary,
        labels=request.labels,
        attributes=request.attributes,
    )
    return get_entity_node_result_from_node(node)


@router.delete('/entity-node/{uuid}', status_code=status.HTTP_200_OK)
async def delete_entity_node(uuid: str, graphiti: ZepGraphitiDep):
    node = await graphiti.get_entity_node(uuid)
    await node.delete(graphiti.driver)
    return Result(message='Entity Node deleted', success=True)


@router.delete('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def delete_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_entity_edge(uuid)
    return Result(message='Entity Edge deleted', success=True)


@router.delete('/group/{group_id}', status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_group(group_id)
    return Result(message='Group deleted', success=True)


@router.delete('/episode/{uuid}', status_code=status.HTTP_200_OK)
async def delete_episode(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_episodic_node(uuid)
    return Result(message='Episode deleted', success=True)


@router.post('/clear', status_code=status.HTTP_200_OK)
async def clear(
    graphiti: ZepGraphitiDep,
):
    await clear_data(graphiti.driver)
    await graphiti.build_indices_and_constraints()
    return Result(message='Graph cleared', success=True)
