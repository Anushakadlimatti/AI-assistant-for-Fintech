import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Chat from './components/Chat';

// Create a custom Material UI theme matching premium banking aesthetics
const theme = createTheme({
  palette: {
    primary: {
      main: '#1A365D',      // Deep Navy
      light: '#E2E8F0',     // Light Slate Accent
      dark: '#0F172A',      // Slate 900
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#0D9488',      // Teal
      light: '#CCFBF1',     // Soft Teal
      dark: '#115E59',      // Dark Teal
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F8FAFC',   // Very Light Gray/Blue
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1E293B',   // Slate 800 (Charcoal)
      secondary: '#64748B', // Slate 500
    },
    divider: '#E2E8F0',
  },
  typography: {
    fontFamily: [
      'Inter',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h6: {
      fontWeight: 700,
    },
    subtitle1: {
      fontWeight: 600,
    },
    subtitle2: {
      fontWeight: 600,
    },
    body1: {
      fontSize: '0.95rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Chat />
    </ThemeProvider>
  );
}

export default App;
