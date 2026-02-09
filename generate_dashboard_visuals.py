from services.stats_service import StatsService
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.makedirs('static/images/dashboard', exist_ok=True)
service = StatsService(cache_dir='.cache')

def generate_map():
    logging.info("Generating adoption map from real data...")
    # Real data for key regional economies
    economies = ['IN', 'AU', 'JP', 'MY', 'VN', 'TH']
    economy_names = ['India', 'Australia', 'Japan', 'Malaysia', 'Vietnam', 'Thailand']
    
    adoption_values = []
    for ec in economies:
        metrics = service.get_latest_metrics(ec)
        if metrics:
            adoption_values.append(metrics['capable_pc'])
        else:
            adoption_values.append(0)
    
    plt.figure(figsize=(10, 6), facecolor='#f8fafc')
    colors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#a5f3fc', '#cbd5e1']
    
    bars = plt.bar(economy_names, adoption_values, color=colors[:len(economies)])
    
    # Add percentage labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.title('Real-Time IPv6 Adoption in APAC (%)', fontsize=16, fontweight='bold', color='#1e293b', pad=25)
    plt.ylabel('Adoption Percentage', fontsize=12, color='#64748b')
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('static/images/dashboard/adoption_map.png', dpi=100)
    plt.close()
    logging.info("Adoption map saved.")

def generate_trend():
    logging.info("Generating growth trend from historical data...")
    # Historical data for India (IN)
    series = service.get_time_series('IN', days=90)
    if not series:
        logging.warning("No time series data available for trend chart.")
        return

    dates = [d['date'] for d in series]
    # Extract capable_pc from the 'raw' object if it exists, otherwise use '10' bucket
    capable = [d.get('raw', {}).get('capable_pc', d.get('10', {}).get('capable_pc', 0)) for d in series]
    preferred = [d.get('raw', {}).get('preferred_pc', d.get('10', {}).get('preferred_pc', 0)) for d in series]

    plt.figure(figsize=(12, 6), facecolor='#f8fafc')
    
    # Plotting Every 15th date for readability
    plt.plot(dates, capable, label='IPv6 Capable', color='#2563eb', linewidth=3)
    plt.plot(dates, preferred, label='IPv6 Preferred', color='#10b981', linewidth=2, linestyle='--')
    
    plt.fill_between(dates, capable, alpha=0.1, color='#2563eb')
    
    # Fix x-axis ticks
    step = max(1, len(dates) // 6)
    plt.xticks(dates[::step], dates[::step], rotation=15)
    
    plt.title('90-Day IPv6 Growth Trajectory (India)', fontsize=16, fontweight='bold', color='#1e293b', pad=20)
    plt.xlabel('Date (Recent 3 Months)', fontsize=12, color='#64748b')
    plt.ylabel('Percentage (%)', fontsize=12, color='#64748b')
    plt.legend(frameon=False)
    plt.grid(linestyle='--', alpha=0.3)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('static/images/dashboard/growth_trend.png', dpi=100)
    plt.close()
    logging.info("Growth trend saved.")

if __name__ == "__main__":
    generate_map()
    generate_trend()
    print("Real-world dashboard visuals generated successfully.")
