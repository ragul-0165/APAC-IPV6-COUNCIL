import os
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')  # Force non-GUI backend for thread-safe operation
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create output directory
output_dir = "static/output"
os.makedirs(output_dir, exist_ok=True)

def setup_recon_style():
    """Sets a futuristic, high-contrast reconnaissance aesthetic."""
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.facecolor'] = '#0f172a' # Slate 900
    plt.rcParams['figure.facecolor'] = '#0f172a'
    plt.rcParams['axes.labelcolor'] = '#94a3b8'
    plt.rcParams['text.color'] = '#f8fafc'
    plt.rcParams['xtick.color'] = '#475569'
    plt.rcParams['ytick.color'] = '#475569'
    plt.rcParams['axes.edgecolor'] = '#1e293b'
    plt.rcParams['grid.color'] = '#1e293b'

def generate_visualizations(domain_data):
    """
    Generates 4 unique, 'Intelligence-Grade' visualizations for domain reconnaissance.
    """
    try:
        setup_recon_style()
        df = pd.DataFrame(domain_data)

        if df.empty:
            logging.warning("No data to visualize.")
            return

        # 1. Infrastructure Relationship Map (Radial Tree Simulation)
        # Shows derived relationships: Root -> Domains -> Endpoints
        try:
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111, polar=True)
            
            # Root at center
            ax.plot([0], [0], marker='h', markersize=15, color='#3b82f6', label='Scan Root')
            
            num_domains = len(df)
            angles = np.linspace(0, 2 * np.pi, num_domains, endpoint=False)
            
            for i, (angle, row) in enumerate(zip(angles, df.iloc)):
                # Domain node
                ax.plot([angle, angle], [0, 0.6], color='#1e293b', linewidth=1, zorder=1)
                ax.plot([angle], [0.6], marker='o', markersize=10, color='#6366f1', zorder=2)
                ax.text(angle, 0.7, row['domain'], ha='center', va='center', fontsize=8, fontweight='bold', rotation=np.degrees(angle)-90 if angle < np.pi else np.degrees(angle)+90)
                
                # Protocol children
                v4_ready = row['ipv4'] != 'None'
                v6_ready = row['ipv6'] != 'None'
                
                if v4_ready:
                    ax.plot([angle, angle-0.1], [0.6, 0.9], color='#3b82f6', alpha=0.3)
                    ax.plot([angle-0.1], [0.9], marker='.', markersize=5, color='#3b82f6')
                if v6_ready:
                    ax.plot([angle, angle+0.1], [0.6, 0.9], color='#10b981', alpha=0.5)
                    ax.plot([angle+0.1], [0.9], marker='s', markersize=5, color='#10b981')

            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.grid(False)
            plt.title('Derived Infrastructure Relationships', fontsize=14, fontweight='black', pad=30, color='#f8fafc')
            plt.savefig(os.path.join(output_dir, "relationship_map.png"), bbox_inches='tight', dpi=150)
            plt.close()
        except Exception as e:
            logging.error(f"Error in Relationship Map: {str(e)}")

        # 2. Recon Flow Analytics (Visualizing conversion from Input to Success)
        try:
            plt.figure(figsize=(10, 6))
            total = len(df)
            v6 = (df['ipv6'] != 'None').sum()
            secure = (df['dnssec'] == 'signed').sum()
            
            x = ['Input Fleet', 'IPv6 Enabled', 'DNSSEC Integrity']
            y = [total, v6, secure]
            
            # Create a custom flow-like bar
            plt.fill_between(x, y, color='#3b82f6', alpha=0.1)
            plt.plot(x, y, marker='h', markersize=12, color='#3b82f6', linewidth=3, markerfacecolor='#0f172a', markeredgewidth=2)
            
            for i, val in enumerate(y):
                plt.text(i, val + (total*0.05), f"{val} ({int(val/total*100) if total > 0 else 0}%)", ha='center', fontweight='black', color='#f8fafc')

            plt.title('Recon Flow Analytics', fontsize=14, fontweight='black', pad=20)
            plt.ylim(0, total * 1.2)
            plt.grid(axis='y', alpha=0.1)
            plt.savefig(os.path.join(output_dir, "recon_flow.png"), bbox_inches='tight', dpi=150)
            plt.close()
        except Exception as e:
            logging.error(f"Error in Recon Flow: {str(e)}")

        # 3. Security Fleet Profile (Radar Evaluation)
        try:
            # Metrics: IPv6%, DNSSEC%, TLS%, Global%, ISP Diverse%
            v6_pct = (df['ipv6'] != 'None').mean() * 100
            dnssec_pct = (df['dnssec'] == 'signed').mean() * 100
            tls_pct = (df['tls_issuer'] != 'Unknown').mean() * 100
            isp_diverse = (df['hosting_company'].nunique() / len(df)) * 100 if len(df) > 0 else 0
            geo_diverse = (df['hosting_location'].nunique() / len(df)) * 100 if len(df) > 0 else 0
            
            labels = ['IPv6 Matrix', 'DNSSEC Integrity', 'TLS Cryptography', 'Host Diversity', 'Geo Resilience']
            values = [v6_pct, dnssec_pct, tls_pct, isp_diverse, geo_diverse]
            num_vars = len(labels)

            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            ax.fill(angles, values, color='#10b981', alpha=0.2)
            ax.plot(angles, values, color='#10b981', linewidth=3, marker='h', markersize=8, markerfacecolor='#0f172a')
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, fontweight='bold', color='#94a3b8')
            ax.set_yticklabels([]) # Hide radii
            
            plt.title('Security Fleet Profile', fontsize=14, fontweight='black', pad=30)
            plt.savefig(os.path.join(output_dir, "fleet_profile.png"), bbox_inches='tight', dpi=150)
            plt.close()
        except Exception as e:
            logging.error(f"Error in Fleet Profile: {str(e)}")

        # 4. Global Infrastructure Density (Hexagonal Heatmap Simulation)
        try:
            plt.figure(figsize=(10, 6))
            loc_counts = df['hosting_location'].value_counts()
            
            # Map country codes to arbitrary coordinates for a hive-like display
            # This is a stylized representation of "infrastructure density"
            coord_map = {
                'US': (10, 10), 'IN': (15, 5), 'AU': (20, 0), 'JP': (18, 8), 
                'SG': (16, 2), 'HK': (17, 4), 'CN': (16, 7), 'KR': (18, 7),
                'VN': (15, 3), 'TH': (14, 2), 'MY': (15, 1), 'ID': (16, -1),
                'PH': (18, 3), 'N/A': (0, 0), 'Unknown': (0, 0)
            }
            
            x, y, s = [], [], []
            for country, count in loc_counts.items():
                cx, cy = coord_map.get(country, (np.random.randint(0, 25), np.random.randint(-5, 15)))
                x.append(cx)
                y.append(cy)
                s.append(count * 500)
                plt.text(cx, cy, f"{country}\n({count})", ha='center', va='center', color='#f8fafc', fontsize=8, fontweight='black')

            plt.scatter(x, y, s=s, c=s, cmap='magma', alpha=0.3, edgecolors='#f43f5e', linewidth=2)
            plt.axis('off')
            plt.title('Global Infrastructure Density', fontsize=14, fontweight='black', pad=20)
            plt.savefig(os.path.join(output_dir, "infrastructure_density.png"), bbox_inches='tight', dpi=150)
            plt.close()
        except Exception as e:
            logging.error(f"Error in Infrastructure Density: {str(e)}")

        logging.info("Intelligence-Grade visualizations generated.")
    except Exception as e:
        logging.error(f"Error in generate_visualizations: {str(e)}", exc_info=True)

def generate_lab_visualizations():
    """Custom bar for Lab - keeping it readable as it's a data index."""
    try:
        setup_recon_style()
        normalized_file = 'static/data/apac_ipv6_normalized.json'
        if not os.path.exists(normalized_file): return
        with open(normalized_file, 'r') as f: data = json.load(f)
        stats = data.get('stats', {})
        records = [{'Country': v.get('country', cc), 'Adoption': v.get('ipv6_adoption', 0)} for cc, v in stats.items()]
        df = pd.DataFrame(records).sort_values(by='Adoption', ascending=False).head(15)

        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='Adoption', y='Country', data=df, palette="magma")
        plt.title('APAC IPv6 Macro Adoption Index', fontsize=16, fontweight='black', pad=20)
        plt.xlabel('Adoption Rate (%)', fontweight='bold')
        for i, v in enumerate(df['Adoption']):
            ax.text(v + 0.5, i + .25, f"{v:.1f}%", color='#f8fafc', fontweight='black')
        plt.savefig(os.path.join(output_dir, "lab_apac_adoption_bar.png"), bbox_inches='tight', dpi=150)
        plt.close()
        return "lab_apac_adoption_bar.png"
    except Exception: return None
