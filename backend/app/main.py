from fastapi import FastAPI

app = FastAPI(title="Flowlist API")


@app.get("/flowlist/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
