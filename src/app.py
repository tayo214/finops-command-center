"""
FinOps Command Center - AWS Cost Optimization Dashboard
Built by: Tayo Salako | FinOps Certified Practitioner
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =====================
# PAGE CONFIGURATION
# =====================
st.set_page_config(
    page_title="FinOps Command Center",
    page_icon="💰",
    layout="wide"
)

# =====================
# TITLE
# =====================
st.title("💰 FinOps Command Center")
st.markdown(
    "**AWS Cost Optimization Platform** | FinOps Certified Practitioner")
st.markdown("---")

# =====================
# DATA LOADING
# =====================


@st.cache_data
def load_simulated_data():
    """Load simulated AWS data"""
    df = pd.read_csv('data/simulated_aws_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df


@st.cache_data
def load_real_data():
    """Load and process real AWS Cost Explorer data"""

    # Read the CSV skipping the first 2 rows (header info)
    df = pd.read_csv('data/aws_billing_services.csv', skiprows=2)

    # The structure now is:
    # Column 0: Date (2025-12-01, 2026-01-01, etc.)
    # Columns 1+: Service costs (Secrets Manager($), Tax($), S3($), etc.)

    # Get column names (service names from the first row of original CSV)
    header_df = pd.read_csv('data/aws_billing_services.csv', nrows=1)
    # Skip first (Service) and last (Total costs)
    service_columns = header_df.columns[1:-1].tolist()

    # Clean service names - remove "($)" suffix
    service_columns = [col.replace('($)', '').strip()
                       for col in service_columns]

    # Melt the dataframe to long format
    records = []

    for _, row in df.iterrows():
        date = pd.to_datetime(row.iloc[0])  # First column is date

        # Loop through each service column
        for i, service_name in enumerate(service_columns):
            cost_value = row.iloc[i + 1]  # +1 because first column is date

            # Convert to float, handle empty/NaN
            try:
                cost = float(cost_value) if pd.notna(
                    cost_value) and cost_value != '' else 0.0
            except (ValueError, TypeError):
                cost = 0.0

            if cost > 0:  # Only keep non-zero costs
                records.append({
                    'Date': date,
                    'Service': service_name,
                    'Cost': cost,
                    'Account': 'tayo-main (Management)'
                })

    return pd.DataFrame(records)


# =====================
# SIDEBAR
# =====================
st.sidebar.header("🎛️ Controls")

# Data source selector
data_source = st.sidebar.radio(
    "View",
    ["Enterprise Scale", "Personal Account"],
    help="Toggle between enterprise-scale analysis and personal AWS account"
)

if data_source == "Personal Account":
    df = load_real_data()
    st.sidebar.info("📊 Personal AWS Account Analysis")
else:
    df = load_simulated_data()
    st.sidebar.info("📊 Enterprise-Scale Analysis")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Key Features")
st.sidebar.success("""
**Platform Capabilities:**
✅ Cost trend analysis
✅ Real-time anomaly detection  
✅ Service-level breakdown
✅ Multi-account visibility
""")

# =====================
# KPI METRICS
# =====================
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_spend = df['Cost'].sum()
daily_avg = df.groupby('Date')['Cost'].sum().mean()
num_services = df['Service'].nunique()
num_accounts = df['Account'].nunique()

with col1:
    st.metric("💵 Total Spend", f"${total_spend:,.0f}")

with col2:
    st.metric("📅 Daily Average", f"${daily_avg:,.0f}")

with col3:
    st.metric("🔧 Active Services", num_services)

with col4:
    st.metric("🏢 AWS Accounts", num_accounts)

# =====================
# DAILY SPEND TREND
# =====================
st.markdown("---")
st.subheader("📈 Daily Spend Trend - The Prius Effect")
st.caption("*Real-time visibility enables proactive cost management*")

daily_spend = df.groupby('Date')['Cost'].sum().reset_index()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily_spend['Date'],
    y=daily_spend['Cost'],
    mode='lines+markers',
    name='Daily Spend',
    line=dict(color='#1f77b4', width=2)
))

avg_spend = daily_spend['Cost'].mean()
fig.add_hline(
    y=avg_spend,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Average: ${avg_spend:,.0f}"
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Cost ($)",
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# =====================
# SERVICE BREAKDOWN
# =====================
st.markdown("---")
st.subheader("🔧 Top Services by Cost")

# Group by service and sum costs
service_totals = df.groupby(
    'Service')['Cost'].sum().sort_values(ascending=False)

# Remove zero-cost services
service_totals = service_totals[service_totals > 0]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**All Services**")

    # Simple bar chart using Plotly Graph Objects for more control
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=service_totals.index,
        x=service_totals.values,
        orientation='h',
        text=[f'${val:.2f}' if val >=
              1 else f'${val:.4f}' for val in service_totals.values],
        textposition='outside',
        marker_color='lightblue'
    ))

    fig.update_layout(
        xaxis_title="Total Cost ($)",
        yaxis_title="",
        height=max(300, len(service_totals) * 60),
        margin=dict(l=150, r=100, t=20, b=50),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown(f"**Top {min(5, len(service_totals))} Services**")

    # Pie chart
    top_n = min(5, len(service_totals))
    top_services = service_totals.head(top_n)

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=top_services.index,
        values=top_services.values,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Cost: $%{value:.4f}<br>%{percent}<extra></extra>'
    ))

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

# Show detailed breakdown table for personal account
if data_source == "Personal Account":
    st.markdown("**Detailed Service Breakdown**")
    breakdown_df = pd.DataFrame({
        'Service': service_totals.index,
        'Total Cost': service_totals.values,
        'Percentage': (service_totals.values / service_totals.sum() * 100)
    })

    st.dataframe(
        breakdown_df.style.format({
            'Total Cost': '${:.4f}',
            'Percentage': '{:.2f}%'
        }),
        use_container_width=True,
        hide_index=True
    )
# Show detailed breakdown table for personal account
if data_source == "Personal Account":

    st.markdown("**Detailed Service Breakdown**")

# =====================
# ACCOUNT BREAKDOWN
# =====================
st.markdown("---")
st.subheader("🏢 Multi-Account Analysis")
st.caption("*Organizational cost allocation and chargeback analysis*")

account_spend = df.groupby(
    'Account')['Cost'].sum().sort_values(ascending=False)

fig = px.bar(
    x=account_spend.index,
    y=account_spend.values,
    title="Spend by AWS Account",
    labels={'x': 'Account', 'y': 'Total Cost ($)'},
    color=account_spend.values,
    color_continuous_scale='Blues'
)

st.plotly_chart(fig, use_container_width=True)

# =====================
# ANOMALY DETECTION
# =====================
st.markdown("---")
st.subheader("⚠️ Anomaly Detection")
st.caption("*Automated threshold-based alerting system*")

daily_spend['Rolling_Avg'] = daily_spend['Cost'].rolling(
    window=7, min_periods=1).mean()
daily_spend['Threshold'] = daily_spend['Rolling_Avg'] * 1.2
daily_spend['Anomaly'] = daily_spend['Cost'] > daily_spend['Threshold']

num_anomalies = daily_spend['Anomaly'].sum()

if num_anomalies > 0:
    st.warning(
        f"🚨 {num_anomalies} days with spending >20% above 7-day average detected!")
else:
    st.success("✅ No significant anomalies detected")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily_spend['Date'],
    y=daily_spend['Cost'],
    mode='lines',
    name='Daily Spend',
    line=dict(color='#1f77b4')
))

fig.add_trace(go.Scatter(
    x=daily_spend['Date'],
    y=daily_spend['Rolling_Avg'],
    mode='lines',
    name='7-Day Average',
    line=dict(color='green', dash='dash')
))

anomalies = daily_spend[daily_spend['Anomaly']]
if len(anomalies) > 0:
    fig.add_trace(go.Scatter(
        x=anomalies['Date'],
        y=anomalies['Cost'],
        mode='markers',
        name='Anomalies',
        marker=dict(color='red', size=10, symbol='x')
    ))

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Cost ($)",
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# =====================
# FOOTER
# =====================
st.markdown("---")
st.markdown(
    "**Built by:** Babatunde Salako | **Certification:** FinOps Certified Practitioner | **GitHub:** [Link] | **LinkedIn:** [Link]")
