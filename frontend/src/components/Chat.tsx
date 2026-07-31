import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  List, 
  ListItemButton, 
  ListItemText, 
  Divider, 
  Paper, 
  CircularProgress, 
  Alert, 
  IconButton,
} from '@mui/material';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { sendChatMessage } from '../services/api';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  table?: Record<string, any>[];
  charts?: any[];
  pdf_available?: boolean;
}

const SAMPLE_QUESTIONS = [
  "How many FDs were created today?",
  "How many RDs were created this month?",
  "Total FD amount today.",
  "Show top branches by FD amount.",
  "Compare today's bookings with yesterday.",
  "What is the average FD amount this month?",
  "Give me today's report as PDF."
];

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: "Welcome to the AI Banking Assistant! I can help you analyze Fixed Deposit (FD) and Recurring Deposit (RD) bookings. Ask me anything about deposit counts, values, trends, or branch metrics. You can also ask me to export reports as PDF!"
    }
  ]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (text: string) => {
    const userMessageId = Math.random().toString();
    const newUserMessage: Message = {
      id: userMessageId,
      sender: 'user',
      text
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(text, sessionId);
      
      const aiMessage: Message = {
        id: Math.random().toString(),
        sender: 'ai',
        text: response.answer,
        table: response.table,
        charts: response.charts,
        pdf_available: response.pdf_available
      };

      setMessages((prev) => [...prev, aiMessage]);
      setSessionId(response.session_id);
    } catch (err: any) {
      console.error(err);
      let errorMsg = "Unable to connect to the backend server. Make sure it is running on http://localhost:8000.";
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([
      {
        id: 'welcome',
        sender: 'ai',
        text: "Started a new conversation session. How can I help you analyze Fixed Deposits (FD) or Recurring Deposits (RD) bookings today?"
      }
    ]);
    setSessionId(undefined);
    setError(null);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'grey.50' }}>
      
      {/* 1. Sidebar Panel */}
      <Paper
        elevation={0}
        sx={{
          width: 320,
          display: { xs: 'none', md: 'flex' },
          flexDirection: 'column',
          borderRight: '1px solid',
          borderColor: 'divider',
          bgcolor: 'primary.dark',
          color: 'common.white',
          borderRadius: 0,
        }}
      >
        {/* Sidebar Header */}
        <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <PsychologyIcon fontSize="large" color="secondary" />
          <Box>
            {/* <Typography variant="h6" sx={{ fontWeight: 'bold', lineHeight: 1.2 }}>
              Apex Bank
            </Typography> */}
            <Typography variant="h6" sx={{ opacity: 0.8 }}>
              AI BANKING ASSISTANT
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ bgcolor: 'rgba(255, 255, 255, 0.12)' }} />

        {/* Action Button */}
        <Box sx={{ p: 2 }}>
          <Button
            fullWidth
            variant="contained"
            color="secondary"
            // startIcon={<AddF />}
            onClick={handleNewChat}
            sx={{ 
              borderRadius: 2, 
              textTransform: 'none', 
              fontWeight: 'bold',
              py: 1,
              boxShadow: '0 4px 10px rgba(13, 148, 136, 0.3)'
            }}
          >
            New Analytics Session
          </Button>
        </Box>

        {/* Suggested Queries List */}
        <Box sx={{ flex: 1, overflowY: 'auto', px: 2 }}>
          <Typography variant="caption" sx={{ px: 2, pb: 1, display: 'block', opacity: 0.5, fontWeight: 'bold' }}>
            DEMO QUESTIONS
          </Typography>
          <List dense>
            {SAMPLE_QUESTIONS.map((question, idx) => (
              <ListItemButton
                key={idx}
                onClick={() => handleSendMessage(question)}
                disabled={loading}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  py: 1,
                  bgcolor: 'rgba(255, 255, 255, 0.04)',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                  }
                }}
              >
                {/* <ListItemIcon sx={{ minWidth: 32, color: 'secondary.light' }}>
                  <HelpIcon fontSize="small" />
                </ListItemIcon> */}
                <ListItemText>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontSize: '0.85rem', 
                      fontWeight: 500, 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis', 
                      whiteSpace: 'nowrap',
                      color: 'rgba(255,255,255,0.9)'
                    }}
                  >
                    {question}
                  </Typography>
                </ListItemText>
              </ListItemButton>
            ))}
          </List>
        </Box>

        <Divider sx={{ bgcolor: 'rgba(255, 255, 255, 0.12)' }} />

        {/* Sidebar Status Info */}
        {/* <Box sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.15)' }}>
          <Stack spacing={1.5}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <StorageIcon fontSize="inherit" color="secondary" />
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Database: <strong>Connected (Port 5434)</strong>
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PsychologyIcon fontSize="inherit" color="secondary" />
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                LLM Model: <strong>gpt-4o-mini</strong>
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon fontSize="inherit" color="secondary" />
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Scope: <strong>Customers & Deposits</strong>
              </Typography>
            </Box>
          </Stack>
        </Box> */}
      </Paper>

      {/* 2. Main Conversation Pane */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        
        {/* Main Workspace Header */}
        <Box 
          sx={{ 
            height: 64, 
            px: 3, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            bgcolor: 'background.paper', 
            borderBottom: '1px solid', 
            borderColor: 'divider' 
          }}
        >
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'primary.dark' }}>
              Deposit Analytics Chat
            </Typography>
          </Box>
          
          {/* Mobile visible action icon */}
          <IconButton 
            color="primary" 
            sx={{ display: { md: 'none' } }}
            onClick={handleNewChat}
          >
            <DeleteSweepIcon />
          </IconButton>
        </Box>

        {/* Scrollable Conversation List */}
        <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Typing Loading indicator */}
          {loading && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <CircularProgress size={20} color="secondary" />
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                Analyzing database and formatting response...
              </Typography>
            </Box>
          )}

          {/* API Error Box */}
          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 3, borderRadius: 2 }}
              action={
                error.includes("Key is missing") ? (
                  <Button size="small" color="inherit" onClick={() => window.location.reload()}>
                    Reload App
                  </Button>
                ) : undefined
              }
            >
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Error Response:</Typography>
              <Typography variant="body2">{error}</Typography>
              {error.includes("Key is missing") && (
                <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                  Make sure to set the <strong>GROQ_API_KEY</strong> environment variable in your <strong>backend/.env</strong> file and restart the backend server.
                </Typography>
              )}
            </Alert>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Bottom Input Area */}
        <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
      </Box>
    </Box>
  );
};
export default Chat;
