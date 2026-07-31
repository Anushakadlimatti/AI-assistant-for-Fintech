import axios from 'axios';

// Default FastAPI backend URL
const API_BASE_URL = 'http://localhost:8008';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChartDataset {
  label: string;
  data: number[];
}

export interface ChartData {
  type: string;  // 'bar', 'line', 'pie'
  title: string;
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChatResponse {
  answer: string;
  table?: Record<string, any>[];
  charts?: ChartData[];
  pdf_available: boolean;
  session_id: string;
}

export const sendChatMessage = async (
  message: string,
  sessionId?: string
): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/chat', {
    message,
    session_id: sessionId,
  });
  return response.data;
};

export const getDownloadReportUrl = (): string => {
  return `${API_BASE_URL}/download-report`;
};
