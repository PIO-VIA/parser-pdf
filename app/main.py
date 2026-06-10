import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    auth_router,
    pdf_router,
    polysomnographie_router,
    polygraphie_ppc_router,
    efr_standard_router,
    efr_avancee_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global router inclusion
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(pdf_router, prefix="/api/v1/pdf", tags=["PDF Upload"])
app.include_router(polysomnographie_router, prefix="/api/v1/polysomnographie", tags=["Polysomnographie"])
app.include_router(polygraphie_ppc_router, prefix="/api/v1/polygraphie-ppc", tags=["Polygraphie PPC"])
app.include_router(efr_standard_router, prefix="/api/v1/efr/standard", tags=["EFR Standard"])
app.include_router(efr_avancee_router, prefix="/api/v1/efr/avancee", tags=["EFR Avancée"])

@app.get("/", tags=["Health"])
async def root():
    return {"code": 200, "message": f"{settings.APP_NAME} v{settings.APP_VERSION} is running", "data": None}

@app.get("/health", tags=["Health"])
async def health():
    return {"code": 200, "message": "OK", "data": {"status": "healthy"}}
