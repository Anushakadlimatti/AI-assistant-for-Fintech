# AI Banking Assistant POC

This is a production-quality Proof of Concept (POC) for a natural language AI Banking Assistant designed to answer business questions about **Fixed Deposits (FD)** and **Recurring Deposits (RD)**.

It uses a FastAPI backend that exposes analytics query helper tools (ensuring no raw SQL injection is performed by the LLM) and integrates with the OpenAI Chat Completion API (using Tool/Function Calling) to provide an interactive, conversational ChatGPT-like interface. It also includes dynamic, interactive tables, charts, and auto-generated professional PDF reports.

---

## 🛠 Tech Stack

- **Frontend**: React (TypeScript), Vite, Material UI (MUI), Axios, Recharts (Responsive charts), React Markdown (for conversational outputs).
- **Backend**: FastAPI, Python 3.14 (fully compatible with 3.12+), SQLAlchemy ORM, PostgreSQL, OpenAI API (Tool/Function Calling), ReportLab (Professional PDF reports).
- **Database**: PostgreSQL (Docker-based).

---

## 📂 Project Structure

```
AIABS/
├── docker-compose.yml       # Starts PostgreSQL on port 5434
├── README.md                # System documentation
├── backend/
│   ├── .env                 # Environment configuration (requires OpenAI API key)
│   ├── app.py               # FastAPI router and server entrypoint
│   ├── database.py          # SQLAlchemy engine and session dependency
│   ├── models.py            # Customers, FDs, and RDs DB schemas
│   ├── schemas.py           # Pydantic request/response structures
│   ├── seed.py              # Seeds 10,000+ realistic records covering past 12 months
│   ├── tools.py             # DB query helper functions (SQL-free AI interface)
│   ├── test_tools.py        # Integration verification script
│   └── services/
│       ├── pdf_service.py   # Generates styled Reports using ReportLab
│       └── chat_service.py  # Handles LLM tool calling, session, and date parsing
└── frontend/
    ├── vite.config.ts       # Build configuration
    ├── index.html           # Main browser HTML container
    ├── package.json         # Client dependencies
    └── src/
        ├── App.tsx          # Root theme configuration and layout
        ├── index.css        # Clean styles reset
        ├── services/
        │   └── api.ts       # Axios client connection
        └── components/
            ├── Chat.tsx         # Sidebar, demo list, and scroll controller
            ├── ChatMessage.tsx  # Message bubbles, interactive tables, and charts
            └── ChatInput.tsx    # Sleek chat text box
```

---

## 🚀 Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Node.js](https://nodejs.org/) (v18 or higher recommended)
- [Python 3.12+](https://www.python.org/downloads/)
- An OpenAI API Key (to run the conversational agent)

---

### Step 1: Start the Database Container

Start the PostgreSQL database service in the background:
```bash
docker compose up -d
```
*Note: The database runs on port `5434` to prevent any conflict with default installations running on port `5432`.*

---

### Step 2: Configure and Seed the Backend

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Open `.env` and fill in your OpenAI API Key:
   ```env
   OPENAI_API_KEY=your-actual-api-key-here
   ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Seed the database with 10,000 mock deposit records (takes less than 3 seconds):
   ```bash
   python seed.py
   ```
5. *(Optional)* Run the query tool verification test to verify the database and SQL mapping:
   ```bash
   python test_tools.py
   ```
6. Start the FastAPI development server:
   ```bash
   python app.py
   ```
   The backend API will run on **`http://localhost:8000`**.

---

### Step 3: Run the React Frontend

1. Open a new terminal window and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open **`http://localhost:5173`** in your browser to interact with the application.

---

## 💬 Sample Prompts to Try

The assistant automatically parses relative date phrases based on today's simulated system date (**Wednesday, July 22, 2026**). Try entering:

- **Simple aggregation**: `"How many FDs were created today?"`
- **Date range**: `"How many RDs were created this month?"`
- **Volume checking**: `"Total FD amount today."`
- **Comparative checking**: `"Compare today's bookings with yesterday."`
- **Branch breakdown**: `"Show top branches by FD amount."` (Displays an interactive table and comparison bar chart).
- **List view**: `"Show top 5 deposits."` (Displays top Fixed Deposits).
- **Trend analysis**: `"Show trend for previous 30 days."` (Renders a double-axis Line chart of booking amounts).
- **PDF Report Generation**: `"Give me today's report as PDF."` or `"Download report"` (Creates a beautiful, branded report and exposes a direct PDF download button).
- **Context/Follow-up**:
  - *User*: `"How many FDs today?"`
  - *User*: `"What about yesterday?"` (Correctly remembers context and checks for yesterday).

---

## 📝 Design & Architecture Highlights

- **SQL Injection Prevention**: The LLM has zero direct database query access and does **not** write or run raw SQL. Instead, it interacts strictly through a defined set of Python tools, preserving security.
- **Strict Date Understanding**: The agent resolves relative terms ("this week", "last month") dynamically based on the current date provided in its system prompt, ensuring robust query results.
- **Component-based Rendering**: The API returns structured JSON metadata representing tables and charts alongside conversational text. The React frontend reads this schema to dynamically render interactive tables and animated charts.
- **Professional PDF Generation**: The PDF generator utilizes ReportLab's flowable architecture with a modern corporate banking design system (primary navy headers, key statistics grid, alternating row colors in tables, and two-pass page numbering).
