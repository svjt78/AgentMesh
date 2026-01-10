from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import registries, runs, dlq

app = FastAPI(title="AgentMesh Integration Fabric", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(registries.router)
app.include_router(runs.router)
app.include_router(dlq.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
