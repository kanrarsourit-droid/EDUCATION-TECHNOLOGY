from fastapi import APIRouter
from app.api.routes import auth, health, knowledge, learning, storage, subjects, supabase

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(subjects.router, tags=["subjects"])
api_router.include_router(knowledge.router)
api_router.include_router(learning.router)
api_router.include_router(storage.router)
api_router.include_router(supabase.router, tags=["supabase"])
