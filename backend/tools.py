import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Customer, FDBooking, RDBooking

def parse_date(date_str: str) -> datetime.date:
    """Helper to parse YYYY-MM-DD string to date object."""
    try:
        return datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}. Must be YYYY-MM-DD. Error: {str(e)}")

def serialize_decimal(val: Any) -> Any:
    """Convert Decimal values to float for JSON compatibility."""
    if isinstance(val, Decimal):
        return float(val)
    return val

def get_fd_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Get summary of Fixed Deposits (FD) booked between start_date and end_date (inclusive).
    Dates must be in 'YYYY-MM-DD' format.
    """
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)

    with SessionLocal() as session:
        # Aggregations
        q = session.query(
            func.count(FDBooking.fd_id).label("count"),
            func.sum(FDBooking.amount).label("total_amount"),
            func.avg(FDBooking.amount).label("avg_amount"),
            func.avg(FDBooking.interest_rate).label("avg_interest_rate")
        ).filter(
            and_(FDBooking.booking_date >= s_date, FDBooking.booking_date <= e_date)
        ).one()

        count = q.count or 0
        total_amount = serialize_decimal(q.total_amount) or 0.0
        avg_amount = serialize_decimal(q.avg_amount) or 0.0
        avg_rate = serialize_decimal(q.avg_interest_rate) or 0.0

        # Status breakdown
        status_q = session.query(
            FDBooking.status,
            func.count(FDBooking.fd_id)
        ).filter(
            and_(FDBooking.booking_date >= s_date, FDBooking.booking_date <= e_date)
        ).group_by(FDBooking.status).all()

        status_breakdown = {status: cnt for status, cnt in status_q}

        return {
            "start_date": start_date,
            "end_date": end_date,
            "count": count,
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "average_interest_rate": round(avg_rate, 2),
            "status_breakdown": status_breakdown
        }

def get_rd_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Get summary of Recurring Deposits (RD) booked between start_date and end_date (inclusive).
    Dates must be in 'YYYY-MM-DD' format.
    """
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)

    with SessionLocal() as session:
        # Aggregations
        q = session.query(
            func.count(RDBooking.rd_id).label("count"),
            func.sum(RDBooking.monthly_amount).label("total_monthly_amount"),
            func.avg(RDBooking.monthly_amount).label("avg_monthly_amount")
        ).filter(
            and_(RDBooking.booking_date >= s_date, RDBooking.booking_date <= e_date)
        ).one()

        count = q.count or 0
        total_monthly = serialize_decimal(q.total_monthly_amount) or 0.0
        avg_monthly = serialize_decimal(q.avg_monthly_amount) or 0.0

        # Status breakdown
        status_q = session.query(
            RDBooking.status,
            func.count(RDBooking.rd_id)
        ).filter(
            and_(RDBooking.booking_date >= s_date, RDBooking.booking_date <= e_date)
        ).group_by(RDBooking.status).all()

        status_breakdown = {status: cnt for status, cnt in status_q}

        return {
            "start_date": start_date,
            "end_date": end_date,
            "count": count,
            "total_monthly_amount": total_monthly,
            "average_monthly_amount": avg_monthly,
            "status_breakdown": status_breakdown
        }

def get_branch_summary(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get branch-wise summary of Fixed Deposits (FD) and Recurring Deposits (RD) bookings 
    created between start_date and end_date (inclusive).
    Dates must be in 'YYYY-MM-DD' format.
    """
    s_date = parse_date(start_date)
    e_date = parse_date(end_date)

    with SessionLocal() as session:
        # FD Branch totals
        fd_branch_q = session.query(
            FDBooking.branch,
            func.count(FDBooking.fd_id).label("fd_count"),
            func.sum(FDBooking.amount).label("fd_total")
        ).filter(
            and_(FDBooking.booking_date >= s_date, FDBooking.booking_date <= e_date)
        ).group_by(FDBooking.branch).all()

        # RD Branch totals
        rd_branch_q = session.query(
            RDBooking.branch,
            func.count(RDBooking.rd_id).label("rd_count"),
            func.sum(RDBooking.monthly_amount).label("rd_total")
        ).filter(
            and_(RDBooking.booking_date >= s_date, RDBooking.booking_date <= e_date)
        ).group_by(RDBooking.branch).all()

        # Merge branches
        branch_map = {}
        for branch, count, total in fd_branch_q:
            branch_map[branch] = {
                "branch": branch,
                "fd_count": count,
                "fd_total": serialize_decimal(total) or 0.0,
                "rd_count": 0,
                "rd_total": 0.0
            }

        for branch, count, total in rd_branch_q:
            if branch in branch_map:
                branch_map[branch]["rd_count"] = count
                branch_map[branch]["rd_total"] = serialize_decimal(total) or 0.0
            else:
                branch_map[branch] = {
                    "branch": branch,
                    "fd_count": 0,
                    "fd_total": 0.0,
                    "rd_count": count,
                    "rd_total": serialize_decimal(total) or 0.0
                }

        # Return sorted by total FD volume descending
        return sorted(branch_map.values(), key=lambda x: x["fd_total"], reverse=True)

def get_top_fd(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get top N Fixed Deposits (FD) by booking amount.
    Returns details of customer name, branch, booking amount, interest rate, tenure, and booking date.
    """
    with SessionLocal() as session:
        top_fds = session.query(
            FDBooking.fd_number,
            Customer.customer_name,
            FDBooking.amount,
            FDBooking.interest_rate,
            FDBooking.tenure_months,
            FDBooking.booking_date,
            FDBooking.branch,
            FDBooking.status
        ).join(
            Customer, Customer.customer_id == FDBooking.customer_id
        ).order_by(
            FDBooking.amount.desc()
        ).limit(limit).all()

        return [
            {
                "fd_number": fd_number,
                "customer_name": name,
                "amount": serialize_decimal(amount),
                "interest_rate": serialize_decimal(rate),
                "tenure_months": tenure,
                "booking_date": booking_date.strftime("%Y-%m-%d"),
                "branch": branch,
                "status": status
            }
            for fd_number, name, amount, rate, tenure, booking_date, branch, status in top_fds
        ]

def get_monthly_trend(month: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get trend of FD and RD bookings.
    If 'month' is provided in YYYY-MM format (e.g. '2026-07'), returns the daily trend for that month.
    If 'month' is not provided, returns the monthly trend for the last 12 months.
    """
    with SessionLocal() as session:
        if month:
            # Parse month
            try:
                year_part, month_part = map(int, month.split("-"))
                start_date = datetime.date(year_part, month_part, 1)
                if month_part == 12:
                    end_date = datetime.date(year_part + 1, 1, 1) - datetime.timedelta(days=1)
                else:
                    end_date = datetime.date(year_part, month_part + 1, 1) - datetime.timedelta(days=1)
            except Exception:
                raise ValueError(f"Invalid month format: {month}. Must be YYYY-MM.")

            # Daily breakdown within the month
            fd_trend = session.query(
                FDBooking.booking_date.label("date"),
                func.count(FDBooking.fd_id).label("fd_count"),
                func.sum(FDBooking.amount).label("fd_total")
            ).filter(
                and_(FDBooking.booking_date >= start_date, FDBooking.booking_date <= end_date)
            ).group_by(FDBooking.booking_date).all()

            rd_trend = session.query(
                RDBooking.booking_date.label("date"),
                func.count(RDBooking.rd_id).label("rd_count"),
                func.sum(RDBooking.monthly_amount).label("rd_total")
            ).filter(
                and_(RDBooking.booking_date >= start_date, RDBooking.booking_date <= end_date)
            ).group_by(RDBooking.booking_date).all()

            # Merge daily data
            trend_map = {}
            # Initialize all days of the month to 0.0 to ensure a continuous line chart
            curr = start_date
            while curr <= end_date:
                date_str = curr.strftime("%Y-%m-%d")
                trend_map[date_str] = {
                    "label": date_str,
                    "fd_count": 0,
                    "fd_total": 0.0,
                    "rd_count": 0,
                    "rd_total": 0.0
                }
                curr += datetime.timedelta(days=1)

            for date_val, count, total in fd_trend:
                d_str = date_val.strftime("%Y-%m-%d")
                if d_str in trend_map:
                    trend_map[d_str]["fd_count"] = count
                    trend_map[d_str]["fd_total"] = serialize_decimal(total) or 0.0

            for date_val, count, total in rd_trend:
                d_str = date_val.strftime("%Y-%m-%d")
                if d_str in trend_map:
                    trend_map[d_str]["rd_count"] = count
                    trend_map[d_str]["rd_total"] = serialize_decimal(total) or 0.0

            return sorted(trend_map.values(), key=lambda x: x["label"])
        
        else:
            # Monthly breakdown for the last 12 months.
            # We can calculate based on today being 2026-07-22. Let's make it cover the past 12 months.
            # Specifically, from 12 months ago to the current date.
            today = datetime.date(2026, 7, 22)
            # 12 months ago would be starting 2025-07-01
            start_date = datetime.date(2025, 7, 1)
            
            # Fetch FDs grouped by year & month
            fd_trend = session.query(
                extract('year', FDBooking.booking_date).label('year'),
                extract('month', FDBooking.booking_date).label('month'),
                func.count(FDBooking.fd_id).label("fd_count"),
                func.sum(FDBooking.amount).label("fd_total")
            ).filter(
                FDBooking.booking_date >= start_date
            ).group_by(
                extract('year', FDBooking.booking_date),
                extract('month', FDBooking.booking_date)
            ).all()

            # Fetch RDs grouped by year & month
            rd_trend = session.query(
                extract('year', RDBooking.booking_date).label('year'),
                extract('month', RDBooking.booking_date).label('month'),
                func.count(RDBooking.rd_id).label("rd_count"),
                func.sum(RDBooking.monthly_amount).label("rd_total")
            ).filter(
                RDBooking.booking_date >= start_date
            ).group_by(
                extract('year', RDBooking.booking_date),
                extract('month', RDBooking.booking_date)
            ).all()

            # Merge trends
            trend_map = {}
            # Initialize past 12 months
            for i in range(13):
                # Calculate year and month for (12 - i) months ago
                # e.g., if i=0, we look at July 2025
                year_offset = (start_date.month + i - 1) // 12
                target_month = (start_date.month + i - 1) % 12 + 1
                target_year = start_date.year + year_offset
                month_key = f"{target_year}-{target_month:02d}"
                trend_map[month_key] = {
                    "label": month_key,
                    "fd_count": 0,
                    "fd_total": 0.0,
                    "rd_count": 0,
                    "rd_total": 0.0
                }

            for yr, mn, count, total in fd_trend:
                # Convert to int as extract can return floats/decimals depending on DB driver
                y_key = f"{int(yr)}-{int(mn):02d}"
                if y_key in trend_map:
                    trend_map[y_key]["fd_count"] = count
                    trend_map[y_key]["fd_total"] = serialize_decimal(total) or 0.0

            for yr, mn, count, total in rd_trend:
                y_key = f"{int(yr)}-{int(mn):02d}"
                if y_key in trend_map:
                    trend_map[y_key]["rd_count"] = count
                    trend_map[y_key]["rd_total"] = serialize_decimal(total) or 0.0

            return sorted(trend_map.values(), key=lambda x: x["label"])

def get_daily_summary(date: str) -> Dict[str, Any]:
    """
    Get a summary of all Fixed Deposits (FD) and Recurring Deposits (RD) booked on a specific date.
    Date must be in 'YYYY-MM-DD' format.
    """
    target_date = parse_date(date)

    with SessionLocal() as session:
        # FD summary
        fd_q = session.query(
            func.count(FDBooking.fd_id).label("count"),
            func.sum(FDBooking.amount).label("total_amount")
        ).filter(FDBooking.booking_date == target_date).one()

        # RD summary
        rd_q = session.query(
            func.count(RDBooking.rd_id).label("count"),
            func.sum(RDBooking.monthly_amount).label("total_amount")
        ).filter(RDBooking.booking_date == target_date).one()

        fd_count = fd_q.count or 0
        fd_total = serialize_decimal(fd_q.total_amount) or 0.0
        rd_count = rd_q.count or 0
        rd_total = serialize_decimal(rd_q.total_amount) or 0.0

        return {
            "date": date,
            "fd_count": fd_count,
            "fd_total": fd_total,
            "rd_count": rd_count,
            "rd_total": rd_total,
            "total_bookings": fd_count + rd_count,
            "total_volume": fd_total + rd_total
        }
