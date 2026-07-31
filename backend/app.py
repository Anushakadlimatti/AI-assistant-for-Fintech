import os
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from schemas import ChatRequest, ChatResponse
from services.chat_service import process_chat_message, PDF_OUTPUT_PATH

app = FastAPI(
    title="AI Banking Assistant API",
    description="Backend API for Fixed Deposit (FD) and Recurring Deposit (RD) analytics.",
    version="1.0.0"
)

# Enable CORS for frontend connection
frontend_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
extra_origins = os.getenv("CORS_ORIGINS", "")
if extra_origins:
    frontend_origins.extend(
        origin.strip() for origin in extra_origins.split(",") if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "AI Banking Assistant API is running."}

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Endpoint to send user questions to the AI assistant.
    Maintains chat history across calls using session_id.
    """
    try:
        response_data = process_chat_message(
            message=request.message,
            session_id=request.session_id
        )
        return response_data
    except ValueError as ve:
        # e.g., missing API key or parsing issues
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # General server exceptions
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/download-report")
def download_report_endpoint():
    """
    Downloads the latest generated PDF report.
    """
    if not os.path.exists(PDF_OUTPUT_PATH):
        raise HTTPException(
            status_code=404, 
            detail="No report PDF available. Please request the assistant to generate a report first."
        )
    
    return FileResponse(
        path=PDF_OUTPUT_PATH,
        media_type="application/pdf",
        filename="deposit_analytics_report.pdf"
    )

# Local: /chat ; Vercel rewrite keeps /api prefix, so also mount under /api
app.include_router(router)
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    # Make sure static directory exists
    os.makedirs(os.path.dirname(PDF_OUTPUT_PATH), exist_ok=True)
    uvicorn.run("app:app", host="0.0.0.0", port=8008, reload=True)
