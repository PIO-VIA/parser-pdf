from app.routers.auth import router as auth_router
from app.routers.pdf import router as pdf_router
from app.routers.polysomnographie import router as polysomnographie_router
from app.routers.polygraphie_ppc import router as polygraphie_ppc_router
from app.routers.efr_standard import router as efr_standard_router
from app.routers.efr_avancee import router as efr_avancee_router

__all__ = [
    "auth_router",
    "pdf_router",
    "polysomnographie_router",
    "polygraphie_ppc_router",
    "efr_standard_router",
    "efr_avancee_router",
]
