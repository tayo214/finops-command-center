"""
RI/Savings Plans Optimizer Dashboard
Interactive visualization for EC2 commitment-based discount recommendations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ri_optimizer import RIOptimizer

# Page config
st.set_page_config(page_title="RI/SP Optimizer", layout="wide")

# Title
st.title("💰 Reserved Instance & Savings Plans Optimizer")
st.markdown(
    "Analyze EC2 usage patterns and optimize commitment-based discount coverage")

# Load data and initialize optimizer


@st.cache_data
def load_optimizer():
    """Initialize the RI optimizer with data"""
    optimizer = RIOptimizer(
        usage_file='../data/simulated_ec2_usage.csv',
        inventory_file='../data/ec2_inventory.csv',
        pricing_file='../data/ri_sp_pricing.csv'
    )
    return optimizer


optimizer = load_optimizer()

# Analyze baseline usage
baseline = optimizer.analyze_baseline_usage()

# Sidebar - Configuration
st.sidebar.header("Configuration")
target_coverage = st.sidebar.slider(
    "Target RI/SP Coverage %",
    min_value=40,
    max_value=90,
    value=65,
    step=5,
    help="Percentage of stable workloads to cover with commitment-based discounts"
) / 100

# Generate recommendations
recommendations = optimizer.calculate_ri_recommendations(
    baseline, target_coverage=target_coverage)
summary = recommendations['summary']

# --- CURRENT STATE SECTION ---
st.header("📊 Current State Analysis")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Monthly Cost",
        value=f"${summary['total_monthly_cost']:,.0f}",
        delta="100% On-Demand"
    )

with col2:
    st.metric(
        label="Stable Workloads",
        value=f"${summary['stable_monthly_cost']:,.0f}",
        delta=f"{summary['stable_instances_count']} instances"
    )

with col3:
    st.metric(
        label="Variable Workloads",
        value=f"${summary['variable_monthly_cost']:,.0f}",
        delta=f"{summary['variable_instances_count']} instances"
    )

with col4:
    st.metric(
        label="RI Candidates",
        value=f"{summary['stable_instances_count']}",
        delta="Running 24/7"
    )

# --- RECOMMENDATIONS SECTION ---
st.header("💡 Optimization Recommendations")

# Create three columns for recommendations
rec_col1, rec_col2, rec_col3 = st.columns(3)

# Option 1: Standard RI
with rec_col1:
    opt = recommendations['standard_ri']
    is_best = summary['recommended_option'] == 'Standard RI'

    st.markdown(f"### {'🏆 ' if is_best else ''}Option 1: Standard RI")
    st.markdown(f"**Coverage:** {opt['coverage_pct']}%")
    st.markdown(f"**Monthly Savings:** ${opt['monthly_savings']:,.0f}")
    st.markdown(f"**Annual Savings:** ${opt['annual_savings']:,.0f}")
    st.markdown(f"**Payback:** {opt['payback_months']} months")
    st.markdown(f"**Risk:** {opt['risk_level']}")

    if is_best:
        st.success("Recommended Option")

    with st.expander("Details"):
        st.write(f"**Instances Covered:** {opt['instances_covered']}")
        st.write(f"**Upfront Cost:** ${opt['upfront_commitment']:,.0f}")
        st.write(f"**Discount:** {opt['savings_pct']}%")
        st.write(f"**Flexibility:** {opt['flexibility']}")

# Option 2: Convertible RI
with rec_col2:
    opt = recommendations['convertible_ri']
    is_best = summary['recommended_option'] == 'Convertible RI'

    st.markdown(f"### {'🏆 ' if is_best else ''}Option 2: Convertible RI")
    st.markdown(f"**Coverage:** {opt['coverage_pct']}%")
    st.markdown(f"**Monthly Savings:** ${opt['monthly_savings']:,.0f}")
    st.markdown(f"**Annual Savings:** ${opt['annual_savings']:,.0f}")
    st.markdown(f"**Payback:** {opt['payback_months']} months")
    st.markdown(f"**Risk:** {opt['risk_level']}")

    if is_best:
        st.success("Recommended Option")

    with st.expander("Details"):
        st.write(f"**Instances Covered:** {opt['instances_covered']}")
        st.write(f"**Upfront Cost:** ${opt['upfront_commitment']:,.0f}")
        st.write(f"**Discount:** {opt['savings_pct']}%")
        st.write(f"**Flexibility:** {opt['flexibility']}")

# Option 3: Savings Plan
with rec_col3:
    opt = recommendations['savings_plan']
    is_best = summary['recommended_option'] == 'Savings Plan'

    st.markdown(f"### {'🏆 ' if is_best else ''}Option 3: Savings Plan")
    st.markdown(f"**Coverage:** {opt['coverage_pct']}%")
    st.markdown(f"**Monthly Savings:** ${opt['monthly_savings']:,.0f}")
    st.markdown(f"**Annual Savings:** ${opt['annual_savings']:,.0f}")
    st.markdown(f"**Payback:** {opt['payback_months']} months")
    st.markdown(f"**Risk:** {opt['risk_level']}")

    if is_best:
        st.success("Recommended Option")

    with st.expander("Details"):
        st.write(f"**Instances Covered:** {opt['instances_covered']}")
        st.write(
            f"**Hourly Commitment:** ${opt['hourly_commitment']:.2f}/hour")
        st.write(f"**Discount:** {opt['savings_pct']}%")
        st.write(f"**Flexibility:** {opt['flexibility']}")

# --- SAVINGS VISUALIZATION ---
st.header("📈 Savings Impact")

# Get the recommended option details
best_option = summary['recommended_option']
if best_option == 'Standard RI':
    best_rec = recommendations['standard_ri']
elif best_option == 'Convertible RI':
    best_rec = recommendations['convertible_ri']
else:
    best_rec = recommendations['savings_plan']

# Create before/after comparison chart
fig_savings = go.Figure()

fig_savings.add_trace(go.Bar(
    name='Current (On-Demand)',
    x=['Monthly Cost'],
    y=[summary['total_monthly_cost']],
    marker_color='#ff6b6b',
    text=[f"${summary['total_monthly_cost']:,.0f}"],
    textposition='auto',
))

optimized_cost = summary['total_monthly_cost'] - best_rec['monthly_savings']
fig_savings.add_trace(go.Bar(
    name=f'Optimized ({best_option})',
    x=['Monthly Cost'],
    y=[optimized_cost],
    marker_color='#51cf66',
    text=[f"${optimized_cost:,.0f}"],
    textposition='auto',
))

fig_savings.update_layout(
    title="Monthly Cost: Current vs Optimized",
    yaxis_title="Cost ($)",
    barmode='group',
    height=400,
    showlegend=True
)

st.plotly_chart(fig_savings, use_container_width=True)

# Savings breakdown
col1, col2 = st.columns(2)

with col1:
    # Pie chart: Stable vs Variable workloads
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Stable Workloads (RI Candidates)',
                'Variable Workloads (On-Demand)'],
        values=[summary['stable_monthly_cost'],
                summary['variable_monthly_cost']],
        marker_colors=['#4dabf7', '#ffd43b'],
        hole=0.3
    )])
    fig_pie.update_layout(title="Workload Distribution", height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Bar chart: Savings comparison across all options
    options_data = {
        'Option': ['Standard RI', 'Convertible RI', 'Savings Plan'],
        'Annual Savings': [
            recommendations['standard_ri']['annual_savings'],
            recommendations['convertible_ri']['annual_savings'],
            recommendations['savings_plan']['annual_savings']
        ]
    }

    fig_comparison = px.bar(
        options_data,
        x='Option',
        y='Annual Savings',
        title='Annual Savings Comparison',
        color='Annual Savings',
        color_continuous_scale='greens',
        text='Annual Savings'
    )
    fig_comparison.update_traces(
        texttemplate='$%{text:,.0f}', textposition='outside')
    fig_comparison.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_comparison, use_container_width=True)

# --- INSTANCE DETAILS ---
st.header("🖥️ Instance Coverage Details")

# Show which instances would be covered
instance_details = pd.DataFrame(
    recommendations['instance_details']['savings_plan_instances'])
instance_details['monthly_cost'] = instance_details['monthly_cost'].round(2)

st.markdown(
    f"**{len(instance_details)} instances recommended for {best_option} coverage:**")

# Format the table nicely
st.dataframe(
    instance_details,
    column_config={
        "instance_id": "Instance ID",
        "instance_type": "Instance Type",
        "environment": "Environment",
        "monthly_cost": st.column_config.NumberColumn(
            "Monthly Cost",
            format="$%.2f"
        )
    },
    hide_index=True,
    use_container_width=True
)

# --- USAGE PATTERNS ANALYSIS ---
st.header("📊 Usage Pattern Analysis")

# Show baseline usage analysis
baseline_display = baseline[['instance_id', 'instance_type', 'environment', 'avg_hours',
                             'is_stable_baseline', 'monthly_cost']].copy()
baseline_display['avg_hours'] = baseline_display['avg_hours'].round(1)
baseline_display['monthly_cost'] = baseline_display['monthly_cost'].round(2)
baseline_display['is_stable_baseline'] = baseline_display['is_stable_baseline'].map({
                                                                                    True: 'Yes', False: 'No'})

st.dataframe(
    baseline_display,
    column_config={
        "instance_id": "Instance ID",
        "instance_type": "Type",
        "environment": "Environment",
        "avg_hours": "Avg Daily Hours",
        "is_stable_baseline": "RI Candidate?",
        "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f")
    },
    hide_index=True,
    use_container_width=True
)

# --- KEY INSIGHTS ---
st.header("💡 Key Insights")

col1, col2 = st.columns(2)

with col1:
    st.info(f"""
    **Optimization Strategy**
    
    - Target coverage: {int(target_coverage * 100)}% of stable workloads
    - Recommended: {best_option}
    - Instances to cover: {best_rec['instances_covered']} out of {summary['stable_instances_count']}
    - Keep {summary['variable_instances_count']} variable instances on On-Demand
    """)

with col2:
    st.success(f"""
    **Financial Impact**
    
    - Monthly savings: ${best_rec['monthly_savings']:,.0f} ({best_rec['savings_pct']}%)
    - Annual savings: ${best_rec['annual_savings']:,.0f}
    - Payback period: {best_rec['payback_months']} months
    - 3-year savings: ${best_rec['annual_savings'] * 3:,.0f}
    """)

# Footer
st.markdown("---")
st.markdown(
    "*Recommendations based on 90-day usage analysis. Adjust coverage slider to see different scenarios.*")
