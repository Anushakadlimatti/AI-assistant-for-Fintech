import React, { useState } from 'react';
import type { KeyboardEvent } from 'react';
import { Paper, InputBase, IconButton, Box } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Paper
        component="form"
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        elevation={0}
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 4,
          bgcolor: 'grey.50',
          transition: 'border-color 0.2s',
          '&:focus-within': {
            borderColor: 'primary.main',
            bgcolor: 'background.paper',
          }
        }}
      >
        <InputBase
          sx={{ ml: 2, flex: 1, fontSize: '0.95rem' }}
          placeholder="Ask about Fixed Deposits (FD) or Recurring Deposits (RD)..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={disabled}
          multiline
          maxRows={4}
        />
        <IconButton 
          color="primary" 
          sx={{ p: '10px' }} 
          onClick={handleSend}
          disabled={disabled || !input.trim()}
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
};
