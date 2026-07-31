import sys
import os
import json

# Add current dir to path
sys.path.append(os.path.dirname(__file__))

import tools

def run_tests():
    print("=== STARTING BACKEND DATABASE TOOLS VERIFICATION ===")
    
    # Target date is 2026-07-22 (today in mock environment)
    target_date = "2026-07-22"
    start_date = "2026-07-01"
    end_date = "2026-07-22"
    
    print("\n1. Testing get_daily_summary(date)...")
    try:
        res = tools.get_daily_summary(target_date)
        print("Success! Result:")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")
        
    print("\n2. Testing get_fd_summary(start_date, end_date)...")
    try:
        res = tools.get_fd_summary(start_date, end_date)
        print("Success! Result (truncated keys):")
        # print first few keys
        truncated = {k: v for k, v in res.items() if k != "status_breakdown"}
        print(json.dumps(truncated, indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")
        
    print("\n3. Testing get_rd_summary(start_date, end_date)...")
    try:
        res = tools.get_rd_summary(start_date, end_date)
        print("Success! Result (truncated keys):")
        truncated = {k: v for k, v in res.items() if k != "status_breakdown"}
        print(json.dumps(truncated, indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")

    print("\n4. Testing get_branch_summary(start_date, end_date)...")
    try:
        res = tools.get_branch_summary(start_date, end_date)
        print(f"Success! Retrieved {len(res)} branches. Top branch:")
        if res:
            print(json.dumps(res[0], indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")

    print("\n5. Testing get_top_fd(limit)...")
    try:
        res = tools.get_top_fd(3)
        print(f"Success! Retrieved top {len(res)} deposits. Top 1:")
        if res:
            print(json.dumps(res[0], indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")

    print("\n6. Testing get_monthly_trend(month=None)...")
    try:
        res = tools.get_monthly_trend()
        print(f"Success! Retrieved trend covering {len(res)} months. First period:")
        if res:
            print(json.dumps(res[0], indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")

    print("\n7. Testing get_monthly_trend(month='2026-07')...")
    try:
        res = tools.get_monthly_trend("2026-07")
        print(f"Success! Retrieved daily trend for July 2026 covering {len(res)} days. First day:")
        if res:
            print(json.dumps(res[0], indent=2))
    except Exception as e:
        print(f"FAILED: {str(e)}")

    print("\n=== VERIFICATION COMPLETED ===")

if __name__ == "__main__":
    run_tests()
