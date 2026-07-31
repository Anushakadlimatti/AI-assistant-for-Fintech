import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Avatar, 
  Stack, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Button 
} from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ReactMarkdown from 'react-markdown';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import { getDownloadReportUrl } from '../services/api';
import type { ChartData } from '../services/api';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  table?: Record<string, any>[];
  charts?: ChartData[];
  pdf_available?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

const CHART_COLORS = ['#1A365D', '#0D9488', '#D97706', '#6366F1'];

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  const handleDownloadPdf = () => {
    window.open(getDownloadReportUrl(), '_blank');
  };

  const renderTable = (data: Record<string, any>[]) => {
    if (!data || data.length === 0) return null;
    const headers = Object.keys(data[0]);

    return (
      <TableContainer component={Paper} variant="outlined" sx={{ mt: 2, mb: 2, borderRadius: 2, overflow: 'hidden' }}>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'primary.dark' }}>
            <TableRow>
              {headers.map((header) => (
                <TableCell key={header} sx={{ color: 'common.white', fontWeight: 'bold', fontSize: '0.85rem' }}>
                  {header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, idx) => (
              <TableRow 
                key={idx} 
                sx={{ 
                  '&:nth-of-type(even)': { bgcolor: 'grey.50' },
                  '&:last-child td, &:last-child th': { border: 0 },
                  // Bold the "Total" row if present
                  fontWeight: row[headers[0]] === 'Total' ? 'bold' : 'normal',
                  bgcolor: row[headers[0]] === 'Total' ? 'primary.light' : undefined
                }}
              >
                {headers.map((header) => (
                  <TableCell 
                    key={header} 
                    sx={{ 
                      fontSize: '0.85rem',
                      fontWeight: row[headers[0]] === 'Total' ? 'bold' : 'normal'
                    }}
                  >
                    {row[header]}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderCharts = (charts: ChartData[]) => {
    if (!charts || charts.length === 0) return null;

    return (
      <Box sx={{ mt: 2, mb: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
        {charts.map((chart, chartIdx) => {
          // Format data for Recharts
          // Recharts expects an array of objects where each object represents a label point, e.g.:
          // [{ name: 'Jan', 'FD Volume': 100, 'RD Volume': 50 }, ...]
          const formattedData = chart.labels.map((label, idx) => {
            const dataPoint: Record<string, any> = { name: label };
            chart.datasets.forEach((dataset) => {
              dataPoint[dataset.label] = dataset.data[idx];
            });
            return dataPoint;
          });

          return (
            <Paper key={chartIdx} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
                {chart.title}
              </Typography>
              <Box sx={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  {chart.type === 'line' ? (
                    <LineChart data={formattedData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
                      <YAxis stroke="#94A3B8" fontSize={11} tickFormatter={(val) => `$${val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val}`} />
                      <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, '']} />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      {chart.datasets.map((dataset, dsIdx) => (
                        <Line
                          key={dataset.label}
                          type="monotone"
                          dataKey={dataset.label}
                          stroke={CHART_COLORS[dsIdx % CHART_COLORS.length]}
                          strokeWidth={2.5}
                          activeDot={{ r: 6 }}
                        />
                      ))}
                    </LineChart>
                  ) : (
                    <BarChart data={formattedData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
                      <YAxis stroke="#94A3B8" fontSize={11} tickFormatter={(val) => `$${val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val}`} />
                      <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, '']} />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      {chart.datasets.map((dataset, dsIdx) => (
                        <Bar
                          key={dataset.label}
                          dataKey={dataset.label}
                          fill={CHART_COLORS[dsIdx % CHART_COLORS.length]}
                          radius={[4, 4, 0, 0]}
                        />
                      ))}
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </Box>
            </Paper>
          );
        })}
      </Box>
    );
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 3 }}>
      <Stack direction="row" spacing={2} sx={{ maxWidth: '85%', alignItems: 'flex-start' }}>
        {!isUser && (
          <Avatar sx={{ bgcolor: 'secondary.main', color: 'common.white', width: 36, height: 36 }}>
            <SmartToyIcon fontSize="small" />
          </Avatar>
        )}
        
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              borderRadius: isUser ? '16px 16px 2px 16px' : '2px 16px 16px 16px',
              bgcolor: isUser ? 'primary.main' : 'grey.100',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              border: isUser ? 'none' : '1px solid',
              borderColor: 'divider',
              boxShadow: isUser ? '0 4px 12px rgba(26, 54, 93, 0.15)' : 'none',
            }}
          >
            {isUser ? (
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                {message.text}
              </Typography>
            ) : (
              <Box sx={{ 
                fontSize: '0.9rem', 
                lineHeight: 1.6,
                '& p': { m: 0, mb: 1 },
                '& p:last-child': { mb: 0 },
                '& ul, & ol': { mt: 1, mb: 1, pl: 3 },
                '& li': { mb: 0.5 },
                '& strong': { color: 'primary.dark' }
              }}>
                <ReactMarkdown>{message.text}</ReactMarkdown>
              </Box>
            )}
          </Paper>

          {/* Render Table Data if available */}
          {!isUser && message.table && renderTable(message.table)}

          {/* Render Charts if available */}
          {!isUser && message.charts && renderCharts(message.charts)}

          {/* PDF Download Button */}
          {!isUser && message.pdf_available && (
            <Button
              variant="contained"
              color="secondary"
              startIcon={<PictureAsPdfIcon />}
              onClick={handleDownloadPdf}
              sx={{ 
                mt: 1, 
                borderRadius: 2, 
                textTransform: 'none',
                fontWeight: 'bold',
                boxShadow: '0 4px 10px rgba(13, 148, 136, 0.2)'
              }}
            >
              Download PDF Report
            </Button>
          )}
        </Box>

        {isUser && (
          <Avatar sx={{ bgcolor: 'primary.main', color: 'common.white', width: 36, height: 36 }}>
            <PersonIcon fontSize="small" />
          </Avatar>
        )}
      </Stack>
    </Box>
  );
};
