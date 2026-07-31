import os
import random
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import Customer, FDBooking, RDBooking

# Configuration lists for realistic mock data
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
               "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
CITIES = ["New York", "Chicago", "Los Angeles", "Houston", "San Francisco", "Seattle", "Boston", "Austin", "Miami", "Denver"]
BRANCHES = ["Main Branch", "Downtown", "West End", "Northside", "East Gate", "Metro Center", "Valley View", "Southside", "Harbor Point", "Financial District"]
STATUSES = ["ACTIVE", "CLOSED", "MATURED"]

def get_maturity_date(booking_date: datetime.date, tenure_months: int) -> datetime.date:
    """Helper to calculate maturity date by adding months to booking date."""
    month = booking_date.month - 1 + tenure_months
    year = booking_date.year + month // 12
    month = month % 12 + 1
    day = min(booking_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)

def seed_database():
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("Generating 1,000 customers...")
        customers = []
        for i in range(1, 1001):
            cif = f"CIF{100000 + i}"
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            city = random.choice(CITIES)
            branch = random.choice(BRANCHES)
            customers.append({
                "cif": cif,
                "customer_name": name,
                "city": city,
                "branch": branch
            })
        
        # Bulk insert customers and retrieve primary keys
        session.bulk_insert_mappings(Customer, customers)
        session.commit()
        
        # Get customer IDs
        db_customers = session.query(Customer.customer_id, Customer.branch).all()
        cust_ids = [c[0] for c in db_customers]
        cust_branches = {c[0]: c[1] for c in db_customers}

        # Date parameters
        # Current system date in mock environment: 2026-07-22
        today = datetime.date(2026, 7, 22)
        yesterday = today - datetime.timedelta(days=1)
        start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
        
        print("Generating ~10,000 realistic bookings...")
        fd_bookings = []
        rd_bookings = []
        
        # Total counts we want
        total_fds = 6000
        total_rds = 4000
        
        # Keep track of sequential booking numbers
        fd_counter = 1
        rd_counter = 1

        # We will distribute bookings:
        # - High density on 'today' (2026-07-22) to make sure queries work
        # - High density on 'yesterday'
        # - High density in 'this week'
        # - Rest spread across the past 12 months (2025-07-22 to 2026-07-21)
        
        # Predefined dates for density
        special_dates = {
            "today": [today] * 150,
            "yesterday": [yesterday] * 120,
            "this_week": [start_of_week + datetime.timedelta(days=d) for d in range(today.weekday()) for _ in range(30)]
        }
        
        # Combine special dates
        all_special_dates = special_dates["today"] + special_dates["yesterday"] + special_dates["this_week"]
        
        # 1. FD Booking Generation
        for i in range(total_fds):
            # Select booking date
            if i < len(all_special_dates) * 0.6:  # 60% of special dates allocated to FDs
                booking_date = random.choice(all_special_dates)
            else:
                # Random date between 12 months ago and yesterday
                days_ago = random.randint(1, 365)
                booking_date = today - datetime.timedelta(days=days_ago)
                
            cust_id = random.choice(cust_ids)
            branch = cust_branches[cust_id]  # Keep customer home branch for simplicity
            
            amount = round(random.uniform(5000, 500000), 2)
            interest_rate = round(random.uniform(4.5, 8.2), 2)
            tenure_months = random.choice([3, 6, 12, 24, 36, 60])
            maturity_date = get_maturity_date(booking_date, tenure_months)
            
            # Status determination based on maturity date relative to 'today' (2026-07-22)
            if maturity_date <= today:
                status = random.choice(["MATURED", "CLOSED"])
            else:
                status = "ACTIVE"
                
            fd_number = f"FD{2026000000 + fd_counter}"
            fd_counter += 1
            
            fd_bookings.append({
                "customer_id": cust_id,
                "fd_number": fd_number,
                "amount": Decimal(str(amount)),
                "interest_rate": Decimal(str(interest_rate)),
                "tenure_months": tenure_months,
                "booking_date": booking_date,
                "maturity_date": maturity_date,
                "status": status,
                "branch": branch
            })

        # 2. RD Booking Generation
        for i in range(total_rds):
            # Select booking date
            if i < len(all_special_dates) * 0.4:  # 40% of special dates allocated to RDs
                booking_date = random.choice(all_special_dates)
            else:
                # Random date between 12 months ago and yesterday
                days_ago = random.randint(1, 365)
                booking_date = today - datetime.timedelta(days=days_ago)
                
            cust_id = random.choice(cust_ids)
            branch = cust_branches[cust_id]
            
            monthly_amount = round(random.uniform(500, 25000), 2)
            tenure_months = random.choice([6, 12, 24, 36, 60])
            maturity_date = get_maturity_date(booking_date, tenure_months)
            
            # Status determination based on maturity date relative to 'today' (2026-07-22)
            if maturity_date <= today:
                status = random.choice(["MATURED", "CLOSED"])
            else:
                status = "ACTIVE"
                
            rd_number = f"RD{2026000000 + rd_counter}"
            rd_counter += 1
            
            rd_bookings.append({
                "customer_id": cust_id,
                "rd_number": rd_number,
                "monthly_amount": Decimal(str(monthly_amount)),
                "tenure_months": tenure_months,
                "booking_date": booking_date,
                "maturity_date": maturity_date,
                "status": status,
                "branch": branch
            })

        print(f"Bulk inserting {len(fd_bookings)} Fixed Deposits...")
        session.bulk_insert_mappings(FDBooking, fd_bookings)
        
        print(f"Bulk inserting {len(rd_bookings)} Recurring Deposits...")
        session.bulk_insert_mappings(RDBooking, rd_bookings)
        
        session.commit()
        print("Database seeding completed successfully!")
        
        # Verify counts
        fd_count = session.query(FDBooking).count()
        rd_count = session.query(RDBooking).count()
        cust_count = session.query(Customer).count()
        print(f"Seeded totals -> Customers: {cust_count}, FDs: {fd_count}, RDs: {rd_count}")

    except Exception as e:
        session.rollback()
        print(f"Seeding failed: {str(e)}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
