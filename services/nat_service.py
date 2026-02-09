import logging

class NATCalculatorService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Industry Benchmark Costs (Placeholder values for Demo)
        # In a real enterprise product, these would be configurable via Admin panel
        self.benchmarks = {
            "cgnat_hardware_cost_per_gbps": 15000,  # USD per Gbps capacity
            "maintenance_overhead_pct": 0.15,       # 15% annual maintenance
            "latency_penalty_ms_per_hop": 12,       # Average added latency due to NAT
            "support_ticket_cost": 45,              # USD per ticket related to NAT/Port issues
            "ipv4_market_price": 45                 # Current market price per IPv4 address
        }

    def calculate_impact(self, users, traffic_gbps):
        """
        Estimates the operational and financial impact of maintaining IPv4 NAT 
        vs migrating to IPv6.
        """
        try:
            users = int(users)
            traffic_gbps = float(traffic_gbps)

            # 1. Hardware/CapEx Impact
            cgnat_capex = traffic_gbps * self.benchmarks["cgnat_hardware_cost_per_gbps"]
            
            # 2. OpEx (Annual)
            cgnat_opex = cgnat_capex * self.benchmarks["maintenance_overhead_pct"]
            
            # 3. User Experience Impact
            # High NAT load creates port exhaustion failure rates (estimated 0.5% of users/year)
            # and latency overhead.
            estimated_tickets = users * 0.005 
            support_cost = estimated_tickets * self.benchmarks["support_ticket_cost"]
            
            total_annual_cost_usd = cgnat_opex + support_cost
            
            # 4. Strategic Assets (IPv4 Value)
            # If migrating to IPv6 allows reclaiming 50% of public IPv4 addresses
            # Assuming 1 public IP serves 64 users in CGNAT
            public_ips_used = users / 64
            asset_value_reclaimable = (public_ips_used * 0.5) * self.benchmarks["ipv4_market_price"]

            return {
                "status": "success",
                "annual_cost_usd": round(total_annual_cost_usd, 2),
                "capex_avoidance_usd": round(cgnat_capex, 2),
                "performance_penalty": {
                    "latency_added_ms": self.benchmarks["latency_penalty_ms_per_hop"],
                    "failure_risk_pct": "0.5%"
                },
                "asset_value_usd": round(asset_value_reclaimable, 2),
                "roi_months": round((cgnat_capex / (total_annual_cost_usd/12)), 1) if total_annual_cost_usd > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"NAT Calculation error: {e}")
            return {"status": "error", "message": str(e)}

nat_service = NATCalculatorService()
