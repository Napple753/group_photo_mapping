from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.tool_a import router as tool_a_router


app = FastAPI(title="Group Photo Mapping API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tool_a_router, prefix="/api/tool-a", tags=["tool-a"])
