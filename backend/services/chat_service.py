import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Import database query tools
import tools
from services.pdf_service import generate_pdf_report

load_dotenv()

# In-memory session history storage
# Maps session_id -> list of message dicts: [{"role": "user"/"assistant"/"system", "content": "..."}]
SESSIONS: Dict[str, List[Dict[str, Any]]] = {}

# Constants
CURRENT_DATE = "2026-07-22"
CURRENT_DAY = "Wednesday"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# PDF file path
PDF_OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "report.pdf")

def get_groq_client() -> OpenAI:
    """Instantiate Groq client (OpenAI-compatible API) using the key from env."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API Key is missing. Please set GROQ_API_KEY in backend/.env")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

def get_session_history(session_id: Optional[str]) -> Tuple[str, List[Dict[str, Any]]]:
    """Retrieve or create session history."""
    if not session_id or session_id not in SESSIONS:
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = []
    
    # Cap history to the last 16 messages to prevent context overflow
    if len(SESSIONS[session_id]) > 16:
        # Keep system prompt if it was there, otherwise just slice
        SESSIONS[session_id] = SESSIONS[session_id][-16:]
        
    return session_id, SESSIONS[session_id]

# LLM tool definitions (OpenAI-compatible format, used with Groq)
LLM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_fd_summary",
            "description": "Get summary of Fixed Deposits (FD) booked between start_date and end_date (inclusive). Returns counts, total volume, average booking size, rates, and status breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in 'YYYY-MM-DD' format"},
                    "end_date": {"type": "string", "description": "End date in 'YYYY-MM-DD' format"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rd_summary",
            "description": "Get summary of Recurring Deposits (RD) booked between start_date and end_date (inclusive). Returns counts, total monthly volume, and status breakdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in 'YYYY-MM-DD' format"},
                    "end_date": {"type": "string", "description": "End date in 'YYYY-MM-DD' format"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_branch_summary",
            "description": "Get branch-wise summary of Fixed Deposits (FD) and Recurring Deposits (RD) bookings created between start_date and end_date (inclusive). Useful for branch analytics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in 'YYYY-MM-DD' format"},
                    "end_date": {"type": "string", "description": "End date in 'YYYY-MM-DD' format"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_fd",
            "description": "Get top Fixed Deposits (FD) by booking amount. Useful for listing high-value depositors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of deposits to retrieve, defaults to 5"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_trend",
            "description": "Get trend of FD and RD bookings. If a month is provided in 'YYYY-MM' format, returns daily trend for that month. If no month is provided, returns monthly trend for the last 12 months.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Optional month in 'YYYY-MM' format (e.g. '2026-07'). If omitted, returns last 12 months trend."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_summary",
            "description": "Get aggregate summary metrics of both FD and RD bookings created on a specific single date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Target date in 'YYYY-MM-DD' format"}
                },
                "required": ["date"]
            }
        }
    }
]

SYSTEM_PROMPT = f"""You are a professional AI Banking Assistant for a retail bank.
Your primary role is to answer business questions related to Fixed Deposits (FD) and Recurring Deposits (RD) bookings.

Context information:
- Today's date is: {CURRENT_DATE}
- Today is: {CURRENT_DAY}

Guidelines for Date Understanding:
- You must understand relative date terms and map them to absolute date parameters when calling tools:
  - "today" -> {CURRENT_DATE} to {CURRENT_DATE}
  - "yesterday" -> 2026-07-21 to 2026-07-21
  - "this week" -> Monday 2026-07-20 to Sunday 2026-07-26 (or {CURRENT_DATE})
  - "last week" -> Monday 2026-07-13 to Sunday 2026-07-19
  - "this month" -> 2026-07-01 to {CURRENT_DATE}
  - "last month" -> 2026-06-01 to 2026-06-30
  - "this year" -> 2026-01-01 to 2026-12-31
  - "previous year" -> 2025-01-01 to 2025-12-31
  - "last 30 days" -> 2026-06-22 to {CURRENT_DATE}
  - "last 7 days" -> 2026-07-15 to {CURRENT_DATE}

CRITICAL Tool Rules:
- For ANY question about counts, amounts, averages, branches, trends, comparisons, or reports, you MUST call the appropriate tool(s) via the function-calling API.
- NEVER describe a tool call in plain text. NEVER say you will "run", "try", or "call" a tool.
- NEVER invent placeholder values (e.g. "X deposits") or apologize that data is unavailable.
- NEVER mention tool names like get_rd_summary in your user-facing answer.
- If the user asks for a PDF/report/export, call the needed analytics tools first, then say the PDF is ready to download.

Response Style:
- After tools return results, answer with concrete numbers from those results only.
- Keep answers professional, quantitative, and clear.
"""

_ANALYTICS_KEYWORDS = (
    "fd", "rd", "deposit", "how many", "total", "branch", "today", "yesterday",
    "month", "week", "year", "report", "pdf", "average", "compare", "trend",
    "top", "volume", "booking", "created", "summary",
)

_TOOL_NARRATION_MARKERS = (
    "get_rd_summary", "get_fd_summary", "get_branch_summary", "get_top_fd",
    "get_monthly_trend", "get_daily_summary",
    "i will run", "let me try", "without the actual data",
    "assuming the tool", "tool with the date", "unfortunately, without",
)

def _is_analytics_question(message: str) -> bool:
    msg = message.lower()
    return any(k in msg for k in _ANALYTICS_KEYWORDS)

def _looks_like_tool_narration(text: Optional[str]) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(marker in lower for marker in _TOOL_NARRATION_MARKERS)

def _assistant_message_to_dict(message: Any) -> Dict[str, Any]:
    """Normalize OpenAI/Groq assistant message objects for chat history."""
    payload: Dict[str, Any] = {
        "role": "assistant",
        "content": message.content or "",
    }
    if getattr(message, "tool_calls", None):
        payload["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]
    return payload


def execute_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """Invokes database tools dynamically based on name and arguments."""
    if name == "get_fd_summary":
        return tools.get_fd_summary(arguments["start_date"], arguments["end_date"])
    elif name == "get_rd_summary":
        return tools.get_rd_summary(arguments["start_date"], arguments["end_date"])
    elif name == "get_branch_summary":
        return tools.get_branch_summary(arguments["start_date"], arguments["end_date"])
    elif name == "get_top_fd":
        limit = arguments.get("limit", 5)
        return tools.get_top_fd(limit)
    elif name == "get_monthly_trend":
        month = arguments.get("month")
        return tools.get_monthly_trend(month)
    elif name == "get_daily_summary":
        return tools.get_daily_summary(arguments["date"])
    else:
        raise ValueError(f"Tool {name} does not exist.")

def build_frontend_tables_and_charts(executed_tools: List[Tuple[str, Dict[str, Any], Any]]) -> Tuple[Optional[List[Dict[str, Any]]], Optional[List[Dict[str, Any]]]]:
    """
    Parses executed tools to build structural table and chart representations 
    that the React frontend can easily render.
    """
    table_data = None
    chart_data = None

    for name, args, result in executed_tools:
        # 1. Branch Summary -> Table + Double dataset Bar Chart
        if name == "get_branch_summary":
            table_data = []
            branches = []
            fd_totals = []
            rd_totals = []
            for row in result:
                table_data.append({
                    "Branch": row["branch"],
                    "FD Count": row["fd_count"],
                    "FD Volume": f"${row['fd_total']:,.2f}",
                    "RD Count": row["rd_count"],
                    "RD Volume (Monthly)": f"${row['rd_total']:,.2f}"
                })
                branches.append(row["branch"])
                fd_totals.append(row["fd_total"])
                rd_totals.append(row["rd_total"])
            
            chart_data = [{
                "type": "bar",
                "title": f"Deposit Volume by Branch ({args.get('start_date')} to {args.get('end_date')})",
                "labels": branches,
                "datasets": [
                    {"label": "FD Total Volume", "data": fd_totals},
                    {"label": "RD Monthly Volume", "data": rd_totals}
                ]
            }]

        # 2. Top FDs -> Table + Bar Chart of amounts
        elif name == "get_top_fd":
            table_data = []
            names = []
            amounts = []
            for row in result:
                table_data.append({
                    "FD Number": row["fd_number"],
                    "Customer Name": row["customer_name"],
                    "Amount": f"${row['amount']:,.2f}",
                    "Interest Rate": f"{row['interest_rate']}%",
                    "Tenure (M)": row["tenure_months"],
                    "Booking Date": row["booking_date"],
                    "Branch": row["branch"]
                })
                names.append(f"{row['customer_name']} ({row['fd_number']})")
                amounts.append(row["amount"])
            
            chart_data = [{
                "type": "bar",
                "title": f"Top Fixed Deposits (Limit: {args.get('limit', 5)})",
                "labels": names,
                "datasets": [
                    {"label": "Booking Amount", "data": amounts}
                ]
            }]

        # 3. Monthly/Daily Trend -> Table + Line Chart of FD and RD volumes
        elif name == "get_monthly_trend":
            table_data = []
            labels = []
            fd_volumes = []
            rd_volumes = []
            
            for row in result:
                table_data.append({
                    "Period": row["label"],
                    "FD Bookings": row["fd_count"],
                    "FD Volume": f"${row['fd_total']:,.2f}",
                    "RD Bookings": row["rd_count"],
                    "RD Volume": f"${row['rd_total']:,.2f}"
                })
                labels.append(row["label"])
                fd_volumes.append(row["fd_total"])
                rd_volumes.append(row["rd_total"])
                
            chart_data = [{
                "type": "line",
                "title": "Booking Trend Volume" if args.get("month") else "Last 12 Months Booking Trend",
                "labels": labels,
                "datasets": [
                    {"label": "FD Volume", "data": fd_volumes},
                    {"label": "RD Monthly/Daily Volume", "data": rd_volumes}
                ]
            }]

        # 4. FD/RD Summaries -> Aggregated KPI Table
        elif name == "get_fd_summary" and not table_data:
            table_data = [{
                "Metric": "Fixed Deposits Volume",
                "Value": f"${result['total_amount']:,.2f}"
            }, {
                "Metric": "Fixed Deposits Booked",
                "Value": f"{result['count']:,}"
            }, {
                "Metric": "Average Booking Size",
                "Value": f"${result['average_amount']:,.2f}"
            }, {
                "Metric": "Average Interest Rate",
                "Value": f"{result['average_interest_rate']}%"
            }]

        elif name == "get_rd_summary" and not table_data:
            table_data = [{
                "Metric": "Recurring Deposits Monthly Volume",
                "Value": f"${result['total_monthly_amount']:,.2f}"
            }, {
                "Metric": "Recurring Deposits Booked",
                "Value": f"{result['count']:,}"
            }, {
                "Metric": "Average Monthly Deposit Size",
                "Value": f"${result['average_monthly_amount']:,.2f}"
            }]
            
        elif name == "get_daily_summary" and not table_data:
            table_data = [{
                "Metric": "FD Bookings Created",
                "Value": f"{result['fd_count']}"
            }, {
                "Metric": "FD Booking Volume",
                "Value": f"${result['fd_total']:,.2f}"
            }, {
                "Metric": "RD Bookings Created",
                "Value": f"{result['rd_count']}"
            }, {
                "Metric": "RD Booking Volume (Monthly)",
                "Value": f"${result['rd_total']:,.2f}"
            }, {
                "Metric": "Total Combined Bookings",
                "Value": f"{result['total_bookings']}"
            }, {
                "Metric": "Total Volume",
                "Value": f"${result['total_volume']:,.2f}"
            }]

    return table_data, chart_data

def check_and_generate_pdf(
    message: str,
    ai_answer: str,
    executed_tools: List[Tuple[str, Dict[str, Any], Any]]
) -> bool:
    """
    Checks if the user requested a PDF report.
    If so, gathers all required statistics, generates the PDF, and saves it.
    """
    msg_lower = message.lower()
    pdf_triggers = ["pdf", "download", "export", "report"]
    should_generate = any(trigger in msg_lower for trigger in pdf_triggers)
    
    if not should_generate:
        return False
        
    try:
        # Determine the target date range.
        # Check executed tools first to grab dates.
        start_date = CURRENT_DATE
        end_date = CURRENT_DATE
        
        for name, args, result in executed_tools:
            if "start_date" in args and "end_date" in args:
                start_date = args["start_date"]
                end_date = args["end_date"]
                break
            elif name == "get_daily_summary" and "date" in args:
                start_date = args["date"]
                end_date = args["date"]
                break
                
        # If no dates found, check if a trend was queried.
        # Fallback: if we need to query statistics, we execute them now.
        fd_stats = None
        rd_stats = None
        branch_stats = None
        
        for name, args, result in executed_tools:
            if name == "get_fd_summary":
                fd_stats = result
            elif name == "get_rd_summary":
                rd_stats = result
            elif name == "get_branch_summary":
                branch_stats = result
                
        # Run queries behind the scenes if missing
        if not fd_stats:
            fd_stats = tools.get_fd_summary(start_date, end_date)
        if not rd_stats:
            rd_stats = tools.get_rd_summary(start_date, end_date)
        if not branch_stats:
            branch_stats = tools.get_branch_summary(start_date, end_date)
            
        # Format statistics for PDF service
        statistics = {
            "fd_count": fd_stats.get("count", 0),
            "fd_total_volume": fd_stats.get("total_amount", 0.0),
            "rd_count": rd_stats.get("count", 0),
            "rd_total_monthly": rd_stats.get("total_monthly_amount", 0.0)
        }
        
        # Call PDF generation service
        generate_pdf_report(
            output_path=PDF_OUTPUT_PATH,
            original_question=message,
            summary_text=ai_answer,
            statistics=statistics,
            branch_data=branch_stats
        )
        return True
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return False

def process_chat_message(message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Full conversation orchestration loop:
    1. Parse history.
    2. Add user message.
    3. Run agent with Groq LLM tools.
    4. Call tool functions.
    5. Handle responses.
    6. Generate tabular/chart/PDF data.
    7. Return payload.
    """
    client = get_groq_client()
    session_id, history = get_session_history(session_id)
    
    # Initialize history with system prompt if empty
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
        
    # Append user message
    history.append({"role": "user", "content": message})
    
    # Call Groq API — force tools when the question clearly needs DB data
    tool_choice: Any = "required" if _is_analytics_question(message) else "auto"
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=history,
            tools=LLM_TOOLS,
            tool_choice=tool_choice,
        )
    except Exception as e:
        # Clean history in case it got corrupted
        if len(history) > 1:
            history.pop()
        raise e

    response_message = response.choices[0].message

    # Some models narrate tool use instead of emitting tool_calls — retry forced
    if (
        not response_message.tool_calls
        and (
            _is_analytics_question(message)
            or _looks_like_tool_narration(response_message.content)
        )
    ):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=history,
                tools=LLM_TOOLS,
                tool_choice="required",
            )
            response_message = response.choices[0].message
        except Exception as e:
            if len(history) > 1:
                history.pop()
            raise e

    executed_tools = []

    # Check for tool calls
    if response_message.tool_calls:
        history.append(_assistant_message_to_dict(response_message))

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            try:
                tool_result = execute_tool_call(function_name, function_args)
                executed_tools.append((function_name, function_args, tool_result))
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result),
                })
            except Exception as e:
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps({"error": str(e)}),
                })

        # Final answer grounded in tool outputs
        try:
            second_response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=history,
            )
            final_message = second_response.choices[0].message
            answer_text = final_message.content or ""
            history.append({"role": "assistant", "content": answer_text})
        except Exception as e:
            raise e
    else:
        history.append({"role": "assistant", "content": response_message.content or ""})
        answer_text = response_message.content or ""

    # Parse executed tools to build structural frontend representation (tables, charts)
    table_data, chart_data = build_frontend_tables_and_charts(executed_tools)
    
    # Check if a PDF needs to be generated
    pdf_avail = check_and_generate_pdf(message, answer_text, executed_tools)
    
    # If the user asked for a PDF, make sure the LLM response lets them know it's ready.
    # (If the LLM didn't already state this, we can optionally append a short notice).
    if pdf_avail and "pdf" not in answer_text.lower() and "report" not in answer_text.lower():
        answer_text += "\n\nI have generated the PDF report. You can download it using the download button below."
        # Update history with the modified answer text
        if history and history[-1]["role"] == "assistant":
            history[-1]["content"] = answer_text

    return {
        "answer": answer_text,
        "table": table_data,
        "charts": chart_data,
        "pdf_available": pdf_avail,
        "session_id": session_id
    }
