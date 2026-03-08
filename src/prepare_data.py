"""
Data preparation script for AWS billing data
Converts your real AWS data + creates simulated data for portfolio
"""

import pandas as pd
from datetime import datetime, timedelta
import random

print("🚀 Starting data preparation...")

# ==========================================
# PART 1: Process your REAL AWS data
# ==========================================
print("\n📊 Processing your real AWS data...")

# Read your real services CSV
real_services = pd.read_csv('data/aws_billing_services.csv', skiprows=1)
print(f"✅ Found {len(real_services)} rows in services data")

# Read your real accounts CSV
real_accounts = pd.read_csv('data/aws_billing_accounts.csv', skiprows=1)
print(f"✅ Found {len(real_accounts)} rows in accounts data")

# Save processed real data
real_services.to_csv('data/real_aws_data.csv', index=False)
print("✅ Saved: data/real_aws_data.csv")

# ==========================================
# PART 2: Create SIMULATED data for portfolio
# ==========================================
print("\n🎨 Creating simulated data for portfolio demo...")

# Generate 90 days of data
dates = pd.date_range(end=datetime.now(), periods=90, freq='D')

# Common AWS services with realistic spending patterns
services = {
    'EC2': {'base': 15000, 'variance': 3000},
    'S3': {'base': 5000, 'variance': 500},
    'RDS': {'base': 8000, 'variance': 1000},
    'Lambda': {'base': 2000, 'variance': 400},
    'CloudWatch': {'base': 1000, 'variance': 200},
    'NAT Gateway': {'base': 3000, 'variance': 300},
    'EBS': {'base': 4000, 'variance': 500},
    'CloudFront': {'base': 2500, 'variance': 300},
    'DynamoDB': {'base': 1500, 'variance': 250},
    'ElastiCache': {'base': 3500, 'variance': 400},
}

# Create simulated data
simulated_data = []

for date in dates:
    for service, params in services.items():
        # Add some realistic variation
        cost = params['base'] + \
            random.uniform(-params['variance'], params['variance'])

        # Add weekly pattern (weekends slightly lower)
        if date.weekday() >= 5:  # Weekend
            cost *= 0.85

        # Add growth trend (5% per month)
        months_from_start = (date - dates[0]).days / 30
        cost *= (1 + 0.05 * months_from_start)

        simulated_data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Service': service,
            'Cost': round(cost, 2)
        })

# Convert to DataFrame
simulated_df = pd.DataFrame(simulated_data)

# Add account information (simulating multi-account)
accounts = ['Production', 'Development', 'Staging', 'Security']
simulated_df['Account'] = [random.choice(
    accounts) for _ in range(len(simulated_df))]

# Save simulated data
simulated_df.to_csv('data/simulated_aws_data.csv', index=False)
print(f"✅ Created {len(simulated_df)} rows of simulated data")
print(
    f"   Date range: {simulated_df['Date'].min()} to {simulated_df['Date'].max()}")
print(f"   Total simulated spend: ${simulated_df['Cost'].sum():,.2f}")

print("\n✨ Data preparation complete!")
print("\n📁 Files created:")
print("   - data/real_aws_data.csv (your actual AWS data)")
print("   - data/simulated_aws_data.csv (portfolio demo data)")
