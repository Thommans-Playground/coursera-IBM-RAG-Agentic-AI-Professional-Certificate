from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/knowledge")


def container(request: Request):
    return request.app.state.container


@router.get("")
async def documents(request: Request):
    docs = await container(request).knowledge.list_knowledge.execute()
    return [
        {"id": d.id, "key": d.key, "title": d.title, "status": d.status.value, "chunks": d.chunks, "error": d.error}
        for d in docs
    ]


@router.post("/load")
async def load(request: Request):
    return {"queued": await container(request).knowledge.load_knowledge_base.execute()}
