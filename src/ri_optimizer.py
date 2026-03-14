"""
RI/Savings Plans Optimizer
Analyzes EC2 usage patterns and recommends optimal commitment-based discounts
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class RIOptimizer:
    """Analyzes EC2 usage and recommends RI/Savings Plans coverage"""

    def __init__(self, usage_file, inventory_file, pricing_file):
        """Load EC2 usage data"""
        self.usage_df = pd.read_csv(usage_file)
        self.inventory_df = pd.read_csv(inventory_file)
        self.pricing_df = pd.read_csv(pricing_file)

        # Convert date column to datetime
        self.usage_df['date'] = pd.to_datetime(self.usage_df['date'])

    def analyze_baseline_usage(self):
        """
        Identify stable baseline workloads vs variable usage
        Baseline = instances running consistently for 90+ days
        """

        # Calculate average daily hours per instance
        instance_avg = self.usage_df.groupby('instance_id').agg({
            'hours_used': ['mean', 'std', 'min', 'max'],
            'daily_cost': 'sum'
        }).reset_index()

        instance_avg.columns = ['instance_id', 'avg_hours',
                                'std_hours', 'min_hours', 'max_hours', 'total_cost_90d']

        # Merge with inventory to get instance details
        analysis = instance_avg.merge(
            self.inventory_df[['instance_id', 'instance_type',
                               'environment', 'team', 'usage_pattern']],
            on='instance_id'
        )

        # Classify stability: stable if runs >20 hours/day consistently
        analysis['is_stable_baseline'] = analysis['avg_hours'] >= 20
        analysis['consistency_score'] = 1 - \
            (analysis['std_hours'] / analysis['avg_hours'])
        analysis['consistency_score'] = analysis['consistency_score'].clip(
            0, 1)

        # Calculate monthly cost (90 days = 3 months)
        analysis['monthly_cost'] = analysis['total_cost_90d'] / 3

        return analysis

    def calculate_ri_recommendations(self, baseline_analysis, target_coverage=0.65):
        """
        Calculate RI/SP recommendations for stable baseline workloads

        Args:
            baseline_analysis: DataFrame from analyze_baseline_usage()
            target_coverage: % of stable workloads to cover (default 65%)

        Returns:
            dict with recommendations for Standard RI, Convertible RI, Savings Plans
        """

        # Filter to stable instances only
        stable_instances = baseline_analysis[baseline_analysis['is_stable_baseline']].copy(
        )

        if len(stable_instances) == 0:
            return {
                'error': 'No stable baseline workloads found',
                'stable_count': 0
            }

        # Calculate current monthly on-demand cost
        total_monthly_cost = baseline_analysis['monthly_cost'].sum()
        stable_monthly_cost = stable_instances['monthly_cost'].sum()
        variable_monthly_cost = total_monthly_cost - stable_monthly_cost

        # Sort by monthly cost (cover most expensive instances first)
        stable_instances = stable_instances.sort_values(
            'monthly_cost', ascending=False)

        # Calculate cumulative coverage
        stable_instances['cumulative_cost'] = stable_instances['monthly_cost'].cumsum(
        )
        stable_instances['coverage_pct'] = stable_instances['cumulative_cost'] / \
            stable_monthly_cost

        # Instances to cover with RIs (top instances up to target coverage)
        ri_candidates = stable_instances[stable_instances['coverage_pct'] <= target_coverage].copy(
        )

        # If we have no candidates after filtering, take at least the top instance
        if len(ri_candidates) == 0 and len(stable_instances) > 0:
            ri_candidates = stable_instances.head(1).copy()

        ri_monthly_cost = ri_candidates['monthly_cost'].sum()
        actual_coverage = ri_monthly_cost / \
            stable_monthly_cost if stable_monthly_cost > 0 else 0

        # Calculate savings for each option
        recommendations = {}

        # Merge with pricing data to get discount rates
        ri_candidates_with_pricing = ri_candidates.merge(
            self.pricing_df[['instance_type', 'on_demand_hourly', 'standard_ri_1yr_hourly',
                             'convertible_ri_1yr_hourly', 'savings_plan_hourly']],
            on='instance_type'
        )

        # Calculate monthly hours (assume 730 hours/month)
        monthly_hours = 730

        # Standard RI calculation
        standard_ri_monthly = (
            ri_candidates_with_pricing['standard_ri_1yr_hourly'] * monthly_hours).sum()
        standard_savings_monthly = ri_monthly_cost - standard_ri_monthly
        standard_savings_annual = standard_savings_monthly * 12
        standard_upfront = standard_ri_monthly * 12  # 1-year all-upfront
        standard_payback = standard_upfront / \
            standard_savings_monthly if standard_savings_monthly > 0 else 0

        recommendations['standard_ri'] = {
            'name': 'Standard Reserved Instances (1-Year)',
            'coverage_pct': round(actual_coverage * 100, 1),
            'instances_covered': len(ri_candidates),
            'monthly_cost_before': round(ri_monthly_cost, 2),
            'monthly_cost_after': round(standard_ri_monthly, 2),
            'monthly_savings': round(standard_savings_monthly, 2),
            'annual_savings': round(standard_savings_annual, 2),
            'savings_pct': round((standard_savings_monthly / ri_monthly_cost * 100), 1) if ri_monthly_cost > 0 else 0,
            'upfront_commitment': round(standard_upfront, 2),
            'payback_months': round(standard_payback, 1),
            'risk_level': 'Medium',
            'flexibility': 'Low - locked to instance type and region'
        }

        # Convertible RI calculation
        convertible_ri_monthly = (
            ri_candidates_with_pricing['convertible_ri_1yr_hourly'] * monthly_hours).sum()
        convertible_savings_monthly = ri_monthly_cost - convertible_ri_monthly
        convertible_savings_annual = convertible_savings_monthly * 12
        convertible_upfront = convertible_ri_monthly * 12
        convertible_payback = convertible_upfront / \
            convertible_savings_monthly if convertible_savings_monthly > 0 else 0

        recommendations['convertible_ri'] = {
            'name': 'Convertible Reserved Instances (1-Year)',
            'coverage_pct': round(actual_coverage * 100, 1),
            'instances_covered': len(ri_candidates),
            'monthly_cost_before': round(ri_monthly_cost, 2),
            'monthly_cost_after': round(convertible_ri_monthly, 2),
            'monthly_savings': round(convertible_savings_monthly, 2),
            'annual_savings': round(convertible_savings_annual, 2),
            'savings_pct': round((convertible_savings_monthly / ri_monthly_cost * 100), 1) if ri_monthly_cost > 0 else 0,
            'upfront_commitment': round(convertible_upfront, 2),
            'payback_months': round(convertible_payback, 1),
            'risk_level': 'Low',
            'flexibility': 'Medium - can exchange for different instance types'
        }

        # Savings Plans calculation (compute savings plans)
        # Savings Plans cover more usage flexibly, so calculate for 70% coverage
        # Slightly higher coverage due to flexibility
        sp_coverage = min(target_coverage * 1.1, 0.70)
        sp_candidates = stable_instances[stable_instances['coverage_pct'] <= sp_coverage]

        if len(sp_candidates) == 0:
            sp_candidates = stable_instances.head(1)

        sp_monthly_cost = sp_candidates['monthly_cost'].sum()
        sp_actual_coverage = sp_monthly_cost / \
            stable_monthly_cost if stable_monthly_cost > 0 else 0

        sp_candidates_with_pricing = sp_candidates.merge(
            self.pricing_df[['instance_type',
                             'on_demand_hourly', 'savings_plan_hourly']],
            on='instance_type'
        )

        sp_monthly = (
            sp_candidates_with_pricing['savings_plan_hourly'] * monthly_hours).sum()
        sp_savings_monthly = sp_monthly_cost - sp_monthly
        sp_savings_annual = sp_savings_monthly * 12
        sp_hourly_commitment = sp_monthly / monthly_hours
        sp_payback = (sp_monthly * 12) / \
            sp_savings_monthly if sp_savings_monthly > 0 else 0

        recommendations['savings_plan'] = {
            'name': 'Compute Savings Plans (1-Year)',
            'coverage_pct': round(sp_actual_coverage * 100, 1),
            'instances_covered': len(sp_candidates),
            'monthly_cost_before': round(sp_monthly_cost, 2),
            'monthly_cost_after': round(sp_monthly, 2),
            'monthly_savings': round(sp_savings_monthly, 2),
            'annual_savings': round(sp_savings_annual, 2),
            'savings_pct': round((sp_savings_monthly / sp_monthly_cost * 100), 1) if sp_monthly_cost > 0 else 0,
            'hourly_commitment': round(sp_hourly_commitment, 2),
            'payback_months': round(sp_payback, 1),
            'risk_level': 'Very Low',
            'flexibility': 'High - applies across instance families, sizes, regions, and compute services'
        }

        # Add summary
        recommendations['summary'] = {
            'total_monthly_cost': round(total_monthly_cost, 2),
            'stable_monthly_cost': round(stable_monthly_cost, 2),
            'variable_monthly_cost': round(variable_monthly_cost, 2),
            'stable_instances_count': len(stable_instances),
            'variable_instances_count': len(baseline_analysis) - len(stable_instances),
            'recommended_option': self._get_best_recommendation(recommendations)
        }

        # Add instance details for recommendations
        recommendations['instance_details'] = {
            'standard_ri_instances': ri_candidates[['instance_id', 'instance_type', 'environment', 'monthly_cost']].to_dict('records'),
            'savings_plan_instances': sp_candidates[['instance_id', 'instance_type', 'environment', 'monthly_cost']].to_dict('records')
        }

        return recommendations

    def _get_best_recommendation(self, recommendations):
        """Determine best recommendation based on savings and flexibility"""

        # Compare annual savings and risk
        options = []

        if 'standard_ri' in recommendations:
            options.append({
                'name': 'Standard RI',
                'annual_savings': recommendations['standard_ri']['annual_savings'],
                'flexibility_score': 1,  # Low flexibility
                'payback': recommendations['standard_ri']['payback_months']
            })

        if 'convertible_ri' in recommendations:
            options.append({
                'name': 'Convertible RI',
                'annual_savings': recommendations['convertible_ri']['annual_savings'],
                'flexibility_score': 2,  # Medium flexibility
                'payback': recommendations['convertible_ri']['payback_months']
            })

        if 'savings_plan' in recommendations:
            options.append({
                'name': 'Savings Plan',
                'annual_savings': recommendations['savings_plan']['annual_savings'],
                'flexibility_score': 3,  # High flexibility
                'payback': recommendations['savings_plan']['payback_months']
            })

        # Weight: 60% savings, 40% flexibility
        for opt in options:
            opt['score'] = (opt['annual_savings'] * 0.6) + \
                (opt['flexibility_score'] * opt['annual_savings'] * 0.1)

        # Sort by score
        best = sorted(options, key=lambda x: x['score'], reverse=True)[0]

        return best['name']

    def generate_report(self, recommendations):
        """Generate a human-readable recommendation report"""

        if 'error' in recommendations:
            return recommendations['error']

        summary = recommendations['summary']
        best = summary['recommended_option']

        report = f"""
RI/SAVINGS PLANS OPTIMIZATION REPORT
=====================================

Current State (100% On-Demand)
------------------------------
Total Monthly Cost: ${summary['total_monthly_cost']:,.2f}
  - Stable Workloads: ${summary['stable_monthly_cost']:,.2f} ({summary['stable_instances_count']} instances)
  - Variable Workloads: ${summary['variable_monthly_cost']:,.2f} ({summary['variable_instances_count']} instances)

Optimization Potential
----------------------
{summary['stable_instances_count']} instances running 24/7 are excellent RI/SP candidates
Target: Cover 60-70% of stable workloads with commitment-based discounts

RECOMMENDATIONS
===============
"""

        # Add each option
        for option_name, option_key in [
            ('Option 1: Standard Reserved Instances', 'standard_ri'),
            ('Option 2: Convertible Reserved Instances', 'convertible_ri'),
            ('Option 3: Compute Savings Plans', 'savings_plan')
        ]:
            if option_key in recommendations:
                opt = recommendations[option_key]
                is_recommended = best in option_name

                report += f"""
{option_name} {'[RECOMMENDED]' if is_recommended else ''}
-----------------------------------------
Coverage: {opt['coverage_pct']}% of stable workloads ({opt['instances_covered']} instances)
Monthly Savings: ${opt['monthly_savings']:,.2f} ({opt['savings_pct']}% reduction)
Annual Savings: ${opt['annual_savings']:,.2f}
{'Upfront Commitment: $' + f"{opt['upfront_commitment']:,.2f}" if 'upfront_commitment' in opt else 'Hourly Commitment: $' + f"{opt['hourly_commitment']:.2f}/hour"}
Payback Period: {opt['payback_months']} months
Risk: {opt['risk_level']}
Flexibility: {opt['flexibility']}
"""

        return report


def main():
    """Test the RI optimizer"""

    print("RI/Savings Plans Optimizer\n")

    # Initialize
    optimizer = RIOptimizer(
        usage_file='../data/simulated_ec2_usage.csv',
        inventory_file='../data/ec2_inventory.csv',
        pricing_file='../data/ri_sp_pricing.csv'
    )

    # Analyze baseline
    print("Analyzing EC2 usage patterns...")
    baseline = optimizer.analyze_baseline_usage()

    stable_count = baseline['is_stable_baseline'].sum()
    print(f"   Found {stable_count} stable baseline instances (RI candidates)")
    print(
        f"   Found {len(baseline) - stable_count} variable instances (keep On-Demand)")

    # Generate recommendations
    print("\nCalculating RI/Savings Plans recommendations...")
    recommendations = optimizer.calculate_ri_recommendations(
        baseline, target_coverage=0.65)

    # Print report
    print("\n" + optimizer.generate_report(recommendations))

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
