from uuid import uuid4

from fastapi import FastAPI

from app.core.errors import ApiError, api_error_handler
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router

app = FastAPI(title="Flowlist API")
app.add_exception_handler(ApiError, api_error_handler)
app.include_router(auth_router)
app.include_router(tasks_router)


@app.middleware("http")
async def assign_request_id(request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/flowlist/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
