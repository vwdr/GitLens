from fastapi import APIRouter

router = APIRouter()


@router.get("/hello/{name}")
async def read_hello(name: str):
    return {"message": f"Hello World, {name}"}
