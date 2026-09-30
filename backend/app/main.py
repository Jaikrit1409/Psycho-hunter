from fastapi import FastAPI

from app.api.routes.clients import router as clients_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.insights import router as insights_router
from app.api.routes.sources import router as sources_router

app = FastAPI(
    title="Psycho Hunter API",
    version="0.1.0",
    description=(
        "Backend for an evidence-based public-source client intelligence and "
        "meeting briefing platform."
    ),
)

app.include_router(health_router)
app.include_router(clients_router)
app.include_router(sources_router)
app.include_router(insights_router)
app.include_router(documents_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Psycho Hunter API is running"}
