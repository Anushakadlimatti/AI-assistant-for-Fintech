from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChartDataset(BaseModel):
    label: str
    data: List[float]

class ChartData(BaseModel):
    type: str  # 'bar', 'line', 'pie'
    title: str
    labels: List[str]
    datasets: List[ChartDataset]

class ChatResponse(BaseModel):
    answer: str
    table: Optional[List[Dict[str, Any]]] = None
    charts: Optional[List[ChartData]] = None
    pdf_available: bool = False
    session_id: Optional[str] = None
