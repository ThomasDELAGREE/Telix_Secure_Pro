from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_corporate, auth_visitor, health
from app.core.config import settings

app = FastAPI(
    title="Telix_Secure_Pro — Auth Service",
    description="Service d'authentification du portail captif (AD/Azure AD/SMS OTP)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(auth_corporate.router, prefix="/auth", tags=["Corporate Auth"])
app.include_router(auth_visitor.router, prefix="/auth", tags=["Visitor Auth"])
