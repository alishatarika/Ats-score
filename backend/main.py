from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.ats_router import router

app = FastAPI(
    title="ATS Resume Scorer",
    description="Upload a resume (PDF/DOCX) and paste a job description to get an ATS compatibility score.",
    version="2.0.0",
)

origins = [
    "http://localhost:3000",   
    "http://localhost:5173",   
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],          
)

app.include_router(router, prefix="/api", tags=["ATS"])
