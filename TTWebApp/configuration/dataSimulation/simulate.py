import os
import json
import random
import numpy as np
from datetime import datetime, timedelta

# Create the output directory
output_dir = "dataSimulation"
os.makedirs(output_dir, exist_ok=True)

# Load existing data if available
def load_existing_data():
    if os.path.exists(os.path.join(output_dir, 'usage_history.json')):
        with open(os.path.join(output_dir, 'usage_history.json'), 'r') as file:
            usage_history = json.load(file)
    else:
        usage_history = []
    
    if os.path.exists(os.path.join(output_dir, 'recharge_history.json')):
        with open(os.path.join(output_dir, 'recharge_history.json'), 'r') as file:
            recharge_history = json.load(file)
    else:
        recharge_history = []

    if os.path.exists(os.path.join(output_dir, 'balances.json')):
        with open(os.path.join(output_dir, 'balances.json'), 'r') as file:
            balances_list = json.load(file)
            # Convert list of balances into a dictionary using userId as the key
            balances = {balance["userId"]: balance for balance in balances_list}
    else:
        balances = {}

    return usage_history, recharge_history, balances

# User data for bonus plan
users = [
    {"bonusPlan": 2, "id": 1, "phoneNumber": "90000000", "username": "asma"},
    {"bonusPlan": 3, "id": 2, "phoneNumber": "90000001", "username": "behe"},
    {"bonusPlan": 5, "id": 3, "phoneNumber": "91234567", "username": None},
    {"bonusPlan": 2, "id": 4, "phoneNumber": "90123456", "username": None},
    {"bonusPlan": 10, "id": 5, "phoneNumber": "90012345", "username": None},
    {"bonusPlan": 7, "id": 6, "phoneNumber": "90001234", "username": None},
    {"bonusPlan": 2, "id": 7, "phoneNumber": "90000123", "username": None},
    {"bonusPlan": 4, "id": 8, "phoneNumber": "90000012", "username": None},
    {"bonusPlan": 5, "id": 9, "phoneNumber": "98765432", "username": None},
    {"bonusPlan": 6, "id": 10, "phoneNumber": "98765430", "username": None},
]

# Recharge plans data (provided by you)
recharge_plans = [
    {"bonusExpDays": 1, "id": 1, "price": 1.0, "rechargeAmount": 0.95, "rechargeExpDays": 3},
    {"bonusExpDays": 3, "id": 2, "price": 2.0, "rechargeAmount": 1.8, "rechargeExpDays": 6},
    {"bonusExpDays": 7, "id": 3, "price": 5.0, "rechargeAmount": 4.385, "rechargeExpDays": 15},
    {"bonusExpDays": 15, "id": 4, "price": 10.0, "rechargeAmount": 8.77, "rechargeExpDays": 30},
    {"bonusExpDays": 32, "id": 5, "price": 25.0, "rechargeAmount": 21.925, "rechargeExpDays": 75},
    {"bonusExpDays": 75, "id": 6, "price": 50.0, "rechargeAmount": 43.85, "rechargeExpDays": 150},
    {"bonusExpDays": 125, "id": 7, "price": 75.0, "rechargeAmount": 65.775, "rechargeExpDays": 250},
    {"bonusExpDays": 150, "id": 8, "price": 99.0, "rechargeAmount": 86.823, "rechargeExpDays": 300}
]

# Mobile data plans data (as you provided)
mobile_data_plans = [
    {"dataAmountMB": 75.0, "expDays": 1, "id": 1, "price": 0.35},
    {"dataAmountMB": 220.0, "expDays": 1, "id": 2, "price": 1.0},
    {"dataAmountMB": 500.0, "expDays": 7, "id": 3, "price": 2.3},
    {"dataAmountMB": 800.0, "expDays": 20, "id": 4, "price": 4.0},
    {"dataAmountMB": 1250.0, "expDays": 30, "id": 5, "price": 5.0},
    {"dataAmountMB": 2800.0, "expDays": 30, "id": 6, "price": 10.0},
    {"dataAmountMB": 6000.0, "expDays": 30, "id": 7, "price": 15.0},
    {"dataAmountMB": 10000.0, "expDays": 30, "id": 8, "price": 20.0}
]

# Parameters
start_date = datetime(2024, 12, 1)

# Set the end date to yesterday
end_date = datetime.today() - timedelta(days=1)

# User segments for data usage and recharge
user_segments = {
    'light_user': {'avg_data': 200, 'avg_recharge': 5, 'std_dev_data': 50, 'std_dev_recharge': 2},
    'heavy_user': {'avg_data': 2000, 'avg_recharge': 15, 'std_dev_data': 500, 'std_dev_recharge': 5},
}

# Data structures
usage_history, recharge_history, balances = load_existing_data()

# Simulate data
for user in users:
    user_id = user["id"]
    bonus_plan = user["bonusPlan"]
    current_balance = balances.get(user_id, {
        "monetaryBalance": 0,
        "bonusBalance": 0,
        "dataBalanceMB": 0,
        "monetaryExpiryDate": None,
        "bonusExpiryDate": None,
        "dataExpiryDate": None,
    })

    # Assign a segment to the user (light or heavy user)
    segment = random.choice(['light_user', 'heavy_user'])
    user_data = user_segments[segment]

    # Simulate recharges (Poisson distribution for recharge frequency)
    num_recharges = np.random.poisson(user_data['avg_recharge'])  # Recharge frequency
    for _ in range(num_recharges):
        recharge_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        recharge_amount = np.random.normal(user_data['avg_recharge'], user_data['std_dev_recharge'])

        recharge_type = random.choice(["money", "data"])

        if recharge_type == "money":
            # Select a recharge plan (pick the recharge amount from a random plan)
            recharge_plan = random.choice(recharge_plans)
            
            # Apply the multiplier based on bonusPlan
            bonus_added = recharge_amount * bonus_plan
            monetary_expiry_date = (recharge_date + timedelta(days=recharge_plan["rechargeExpDays"])).strftime("%Y-%m-%d")
            bonus_expiry_date = (recharge_date + timedelta(days=recharge_plan["bonusExpDays"])).strftime("%Y-%m-%d")
            data_added_mb = None
            data_expiry_date = None

            # Update balance
            current_balance["monetaryBalance"] += recharge_amount
            current_balance["bonusBalance"] += bonus_added
            current_balance["monetaryExpiryDate"] = monetary_expiry_date
            current_balance["bonusExpiryDate"] = bonus_expiry_date
        else:
            data_added_mb = np.random.normal(user_data['avg_data'], user_data['std_dev_data'])
            data_expiry_days = random.choice([1, 7, 15, 30])  # Different expiration days for data plans
            data_expiry_date = (recharge_date + timedelta(days=data_expiry_days)).strftime("%Y-%m-%d")
            bonus_added = None
            monetary_expiry_date = None
            bonus_expiry_date = None

            # Update balance
            current_balance["dataBalanceMB"] += data_added_mb
            current_balance["dataExpiryDate"] = data_expiry_date

        recharge_history.append({
            "userId": user_id,
            "rechargeAmount": recharge_amount if recharge_type == "money" else 0,
            "bonusAdded": bonus_added if bonus_added is not None else 0,
            "dataAddedMB": data_added_mb if data_added_mb is not None else 0,
            "rechargeDate": recharge_date.strftime("%Y-%m-%d"),
            "monetaryExpiryDate": monetary_expiry_date,
            "bonusExpiryDate": bonus_expiry_date,
            "dataExpiryDate": data_expiry_date,
        })

    # Simulate usage history based on normal distribution
    num_usages = random.randint(50, 100)  # Random number of usage events
    for _ in range(num_usages):
        usage_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        calls_minutes = random.randint(0, 30)
        sms_count = random.randint(0, 10)
        data_usage_mb = np.random.normal(100, 50)  # Normal distribution for data usage

        # Deduct from balance
        cost = calls_minutes * 0.035 + sms_count * 0.025
        if current_balance["bonusBalance"] >= cost:
            current_balance["bonusBalance"] -= cost
        elif current_balance["bonusBalance"] + current_balance["monetaryBalance"] >= cost:
            remaining_cost = cost - current_balance["bonusBalance"]
            current_balance["bonusBalance"] = 0
            current_balance["monetaryBalance"] -= remaining_cost
        else:
            continue  # Skip if no sufficient balance (bonus + monetary)

        usage_history.append({
            "userId": user_id,
            "usageTimestamp": usage_date.strftime("%Y-%m-%d"),
            "callsMinutes": calls_minutes,
            "smsCount": sms_count,
            "dataUsageMB": round(data_usage_mb, 2),
        })

    # Update balance data
    balances[user_id] = current_balance

# Save files
with open(os.path.join(output_dir, 'usage_history.json'), 'w') as usage_file:
    json.dump(usage_history, usage_file, indent=4)

with open(os.path.join(output_dir, 'recharge_history.json'), 'w') as recharge_file:
    json.dump(recharge_history, recharge_file, indent=4)

with open(os.path.join(output_dir, 'balances.json'), 'w') as balance_file:
    json.dump([
        {"userId": user_id, **balances[user_id]}
        for user_id in balances
    ], balance_file, indent=4)

print(f"Simulation completed. Data saved in the '{output_dir}' folder.")
