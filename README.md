# FinOps Command Center 💰

> **AWS cost optimization platform built by a FinOps Certified Practitioner**

Interactive dashboard for analyzing cloud spending patterns, detecting anomalies, and optimizing AWS costs. Works with both enterprise-scale data and real AWS accounts.

![Enterprise Dashboard](screenshots/enterprise_kpi_metrics.png)

---

## What This Does

This is a working FinOps platform I built to demonstrate cost management at scale. It analyzes AWS spending data and gives you the insights you actually need - where money's going, what's trending up, and when something looks off.

**Key features:**
- Real-time cost visibility across services and accounts
- Anomaly detection (flags spending spikes >20% above baseline)
- Multi-account analysis for organizational chargeback
- Toggle between enterprise-scale demo ($4.2M) and personal AWS data ($0.64)

**Why two data modes?**  
My personal AWS account has minimal spend ($0.64 over 3 months), which is great for learning but doesn't show what this platform can do at scale. So I built realistic simulated data (~$4.2M total) that follows actual AWS spending patterns - EC2-heavy, weekend dips, gradual growth. Best of both worlds: authenticity + real-world scale.

---

## Screenshots

### Enterprise Scale Analysis ($4.2M)

**Key performance indicators:**
![Enterprise KPIs](screenshots/enterprise_kpi_metrics.png)

**Daily spend tracking with trend analysis:**
![Enterprise Spend Trend](screenshots/enterprise_spend_trend.png)

**Service-level cost breakdown:**
![Enterprise Services](screenshots/enterprise_service-by-cost.png)

The enterprise view shows realistic AWS spending patterns - EC2 dominates at 42.5% (compute-heavy workload), RDS at 22.4% (database costs), then storage, networking, and caching services. Weekend dips and daily variation match real production environments.

---

### Personal AWS Account ($0.64)

**My actual AWS account metrics:**
![Personal KPIs](screenshots/personal_kpi_metrics.png)

**Real spending growth over 3 months:**
![Personal Spend Trend](screenshots/personal_daily_spend_trend.png)

**Actual service breakdown:**
![Personal Services](screenshots/personal_service-by-cost.png)

You can see exactly what I'm using - primarily Secrets Manager ($0.61) for credential storage, some AWS tax charges ($0.03), tiny amounts of S3 storage, and API Gateway usage. This is what a learning/development account actually looks like.

---

## Tech Stack

**Built with:**
- **Python** - Data processing and business logic
- **Pandas** - AWS billing data transformation
- **Streamlit** - Interactive web dashboard
- **Plotly** - Professional-grade visualizations
- **AWS Cost Explorer** - Real billing data source

**Why these tools?**  
Streamlit gets you from idea to working dashboard incredibly fast, and Plotly makes charts that actually look good. Perfect combo for a portfolio project that needed to work *and* look professional.

---

## FinOps Concepts Demonstrated

This project isn't just about making charts - it implements real FinOps principles:

**Cost Allocation & Visibility**
- Service-level and account-level spend breakdown
- Multi-account organizational analysis
- Shows exactly where dollars are going

**The Prius Effect**
- Real-time visibility changes behavior (that's the whole point!)
- Daily trend tracking with baseline averages
- Teams can't optimize what they can't see

**Anomaly Detection**
- Automated alerts when spend jumps >20% above 7-day average
- Catches issues before they become problems
- No more surprise bills at month-end

**Metric-Driven Optimization**
- KPIs: Total spend, daily average, service count, account count
- Data-driven decisions instead of gut feelings
- Track improvements over time

---

## How to Run This
```bash