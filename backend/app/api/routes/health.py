from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health Check")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify that the service is healthy."""
    return {"status": "healthy"}
