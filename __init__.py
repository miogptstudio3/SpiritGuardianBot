from .start import router as start_router
from .game import router as game_router
from .admin import router as admin_router

def register_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(admin_router)
