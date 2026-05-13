"""
Dashboard Cache Service — Pre-computes all heavy dashboard metrics in the background.

Instead of computing Health Index, Momentum Leaderboard, Forecast, and Strategic Horizon
on every user request (which causes 50+ DB queries and AI inference loops), this service
runs periodically and stores the final result in a single MongoDB document.

The dashboard route then simply reads this one document = instant page load.
"""

import logging
from datetime import datetime, timedelta
from services.database_service import db_service
from services.inference_service import inference_service

logger = logging.getLogger(__name__)

# Approximate populations (in millions) for major APAC countries
POPULATIONS = {
    'IN': 1428, 'CN': 1411, 'ID': 277, 'PK': 240, 'BD': 173, 'JP': 123,
    'PH': 117, 'VN': 98, 'IR': 89, 'TH': 71, 'MM': 54, 'KR': 51,
    'MY': 34, 'NP': 31, 'AF': 42, 'AU': 26, 'KP': 26, 'TW': 23,
    'LK': 21, 'KZ': 19, 'KH': 16, 'NZ': 5, 'SG': 5, 'LA': 7,
    'MN': 3, 'BN': 0.4, 'MV': 0.5, 'BT': 0.7, 'TL': 1.3
}

COUNTRY_NAMES = {
    "AF": "Afghanistan", "AS": "American Samoa", "AU": "Australia", "BD": "Bangladesh",
    "BT": "Bhutan", "BN": "Brunei Darussalam", "KH": "Cambodia", "CN": "China",
    "CK": "Cook Islands", "FJ": "Fiji", "GU": "Guam", "HK": "Hong Kong", "IN": "India",
    "ID": "Indonesia", "JP": "Japan", "KR": "Korea, Republic of", "LA": "Lao PDR",
    "MO": "Macau", "MY": "Malaysia", "MV": "Maldives", "MN": "Mongolia", "MM": "Myanmar",
    "NP": "Nepal", "NC": "New Caledonia", "NZ": "New Zealand", "PK": "Pakistan",
    "PG": "Papua New Guinea", "PH": "Philippines", "WS": "Samoa", "SG": "Singapore",
    "SB": "Solomon Islands", "LK": "Sri Lanka", "TW": "Taiwan", "TH": "Thailand",
    "TL": "Timor-Leste", "TO": "Tonga", "VU": "Vanuatu", "VN": "Vietnam", "KZ": "Kazakhstan",
    "UZ": "Uzbekistan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", "PF": "French Polynesia",
    "KI": "Kiribati", "MH": "Marshall Islands", "FM": "Micronesia", "NR": "Nauru",
    "PW": "Palau", "TV": "Tuvalu", "KP": "Korea, DPR", "MP": "N. Mariana Islands",
    "NU": "Niue", "WF": "Wallis and Futuna", "CX": "Christmas Island", "CC": "Cocos Islands",
    "NF": "Norfolk Island", "IO": "British Indian Ocean Territory", "TK": "Tokelau", "PN": "Pitcairn",
    "TF": "French Southern Territories"
}

CACHE_KEY = "dashboard_snapshot"


class DashboardCacheService:
    """Singleton service that pre-computes and caches all dashboard metrics."""

    def rebuild_cache(self):
        """
        Performs all the heavy computation that was previously done in
        visualizations.py index() on every request. Stores the result
        in a single MongoDB document for instant retrieval.
        """
        if not db_service.connect():
            logger.error("Cannot rebuild dashboard cache: DB not connected")
            return False

        logger.info("[CACHE] Starting dashboard cache rebuild...")
        start_time = datetime.now()

        try:
            db = db_service._db

            # ============================================================
            # 1. FETCH ALL DATA UPFRONT (batch queries, not per-country)
            # ============================================================

            # 1a. All APAC stats (one query)
            all_stats_raw = list(db['apac_ipv6_normalized'].find({}))

            # 1b. All benchmarks (one query)
            from services.external_data_service import external_data_service
            all_benchmarks = external_data_service.get_benchmarks('ALL')

            # 1c. All history logs for regional aggregate (one query)
            all_reg_logs = list(db['history_logs'].find(
                {"sector": "government", "type": "regional_aggregate"}
            ).sort("date", -1))

            # 1d. Historical data for momentum/growth (one aggregation)
            target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            hist_pipeline = [
                {"$match": {"date": {"$lte": target_date}, "sector": "government"}},
                {"$sort": {"date": -1}},
                {"$group": {
                    "_id": "$country",
                    "historical_rate": {"$first": "$rate"}
                }}
            ]
            historical_stats = {
                h['_id']: h['historical_rate']
                for h in db['history_logs'].aggregate(hist_pipeline)
            }

            # ============================================================
            # 2. AI INFERENCE — run once per country, cache results
            # ============================================================
            inference_service.clear_cache()

            stats_list = []
            country_current = {}
            for s in all_stats_raw:
                cc = s.get('country_code', 'UNKNOWN')
                raw_v6 = s.get('ipv6_adoption', 0)
                optimized = inference_service.get_optimized_adoption(cc, raw_v6)
                s['ipv6_adoption'] = optimized
                stats_list.append(s)
                country_current[cc] = optimized

            # ============================================================
            # 3. HEALTH INDEX (population-weighted average)
            # ============================================================
            total_population = 0
            weighted_sum = 0
            for s in stats_list:
                cc = s.get('country_code', 'UNKNOWN')
                adoption = s.get('ipv6_adoption', 0)
                pop = POPULATIONS.get(cc, 1)
                weighted_sum += (adoption * pop)
                total_population += pop

            avg_adoption = weighted_sum / total_population if total_population > 0 else 0

            # YoY growth from regional aggregate history logs
            yoy_growth = 3.4  # fallback
            if all_reg_logs:
                latest_log = all_reg_logs[0]
                old_val = next((log for log in all_reg_logs if log['date'] <= target_date), None)
                if old_val:
                    yoy_growth = latest_log.get('rate', 0) - old_val.get('rate', 0)

            health_data = {
                "score": int(avg_adoption),
                "status": "Moderate Acceleration" if avg_adoption > 30 else "Steady Progress",
                "yoy_growth": round(yoy_growth, 1)
            }

            # ============================================================
            # 4. MOMENTUM LEADERBOARD
            # ============================================================
            fastest_country = "India"
            fastest_rate = 0.8
            current_adoption_fastest = inference_service.get_optimized_adoption("IN", 78.18)

            if country_current and historical_stats:
                growth_list = []
                for country_code, hist_rate in historical_stats.items():
                    if country_code in country_current:
                        growth = country_current[country_code] - hist_rate
                        growth_list.append({
                            "country": country_code,
                            "rate": round(growth, 1),
                            "current": country_current[country_code]
                        })

                if growth_list:
                    top_growth = max(growth_list, key=lambda x: x['rate'])
                    country_name_map = {
                        s.get('country_code'): s.get('country_name')
                        for s in stats_list if s.get('country_name')
                    }
                    # Fallback to internal mapping if DB name is missing
                    code = top_growth['country']
                    fastest_country = country_name_map.get(code) or COUNTRY_NAMES.get(code, code)
                    fastest_rate = top_growth['rate']
                    current_adoption_fastest = top_growth['current']

            # Most Resilient ASN
            resilient_asn = "AS55836 (Reliance Jio)"
            try:
                all_readiness = list(db['asn_ipv6_readiness'].find().sort("sample_count", -1).limit(50))
                valid_resilience = [r for r in all_readiness
                                   if isinstance(r.get('ipv6_capable'), (int, float))
                                   and r.get('ipv6_capable') <= 100.0]
                if valid_resilience:
                    top_asn_doc = valid_resilience[0]
                    asn_id = top_asn_doc['asn']
                    org_info = db['asn_organizations'].find_one({"asn": asn_id})
                    org_name = org_info.get('org_name', 'Global Provider') if org_info else 'Global Infrastructure'
                    resilient_asn = f"AS{asn_id} ({org_name})"
            except Exception as e:
                logger.error(f"Error fetching resilient ASN: {e}")

            # At Risk (lowest adoption)
            at_risk = "Afghanistan"
            if stats_list:
                lowest = min(stats_list, key=lambda x: x.get('ipv6_adoption', 100))
                risk_code = lowest.get('country_code', 'AF')
                at_risk = COUNTRY_NAMES.get(risk_code, risk_code)

            momentum_data = {
                "fastest_growth_country": fastest_country,
                "fastest_growth_rate": fastest_rate,
                "current_adoption": current_adoption_fastest,
                "most_resilient_asn": resilient_asn,
                "at_risk_country": at_risk
            }

            # ============================================================
            # 5. TRAJECTORY FORECAST
            # ============================================================
            real_growth_rate_annual = 0
            if all_reg_logs:
                reg_latest = all_reg_logs[0]
                old_forecast_val = next(
                    (log for log in all_reg_logs if log['date'] <= target_date), None
                )
                if old_forecast_val:
                    reg_curr = reg_latest.get('rate', 0)
                    reg_prev = old_forecast_val.get('rate', 0)
                    real_growth_rate_annual = round(reg_curr - reg_prev, 2)

            if real_growth_rate_annual <= 0:
                real_growth_rate_annual = max(yoy_growth, 1.0)

            growth_rate = real_growth_rate_annual / 365  # daily

            current_rate = avg_adoption
            days_to_80 = (80 - current_rate) / growth_rate if current_rate < 80 and growth_rate > 0 else 0
            days_to_95 = (95 - current_rate) / growth_rate if current_rate < 95 and growth_rate > 0 else 0

            target_80 = (datetime.now() + timedelta(days=days_to_80)).year
            target_95 = (datetime.now() + timedelta(days=days_to_95)).year

            forecast_data = {
                "current_pace": round(growth_rate * 365, 1),
                "target_80_date": target_80,
                "target_95_date": target_95
            }

            # ============================================================
            # 6. STRATEGIC HORIZON DATA
            # ============================================================
            horizon_data = self._compute_horizon_data(
                stats_list, country_current, historical_stats, all_benchmarks
            )

            # ============================================================
            # 7. WRITE CACHE DOCUMENT (upsert = atomic replace)
            # ============================================================
            elapsed = (datetime.now() - start_time).total_seconds()

            cache_doc = {
                "key": CACHE_KEY,
                "health": health_data,
                "momentum": momentum_data,
                "forecast": forecast_data,
                "horizon": horizon_data,
                "avg_adoption": round(avg_adoption, 2),
                "computed_at": datetime.now().isoformat(),
                "computation_time_seconds": round(elapsed, 2)
            }

            db['dashboard_cache'].update_one(
                {"key": CACHE_KEY},
                {"$set": cache_doc},
                upsert=True
            )

            logger.info(f"[CACHE] Dashboard cache rebuilt in {elapsed:.2f}s")
            return True

        except Exception as e:
            logger.error(f"[CACHE] Dashboard cache rebuild failed: {e}")
            return False

    def get_cached_dashboard(self):
        """Read the pre-computed dashboard snapshot. Returns None if not available."""
        if not db_service.connect():
            return None
        try:
            doc = db_service._db['dashboard_cache'].find_one({"key": CACHE_KEY})
            if doc:
                doc.pop('_id', None)
            return doc
        except Exception as e:
            logger.error(f"[CACHE] Failed to read dashboard cache: {e}")
            return None

    def _compute_horizon_data(self, stats_list, country_current, historical_stats, all_benchmarks):
        """
        Computes Strategic Horizon quadrant classification.
        Same logic as intelligence_service.get_strategic_horizon_data() but using
        pre-fetched data instead of per-country DB queries.
        """
        try:
            if len(stats_list) < 2:
                return []

            data_points = []
            total_adoption = 0
            total_growth = 0
            valid_countries = 0

            for stat in stats_list:
                country_code = stat.get('country_code', 'Unknown')
                adoption = stat.get('ipv6_adoption', 0)
                raw_adoption = stat.get('_original_adoption', adoption)

                # Get benchmarks from pre-fetched batch (no per-country query)
                benchmarks_for_cc = {
                    'apnic': raw_adoption,
                    'google': all_benchmarks.get("Google", {}).get(country_code, raw_adoption),
                    'cloudflare': all_benchmarks.get("Cloudflare", {}).get(country_code, raw_adoption),
                    'pulse': all_benchmarks.get("IPv6_Pulse", {}).get(country_code, 0)
                }

                prev_adoption = historical_stats.get(country_code)
                if prev_adoption is not None:
                    growth = adoption - prev_adoption
                else:
                    growth = stat.get('yoy_growth', 0)

                data_points.append({
                    'country': country_code,
                    'full_name': stat.get('country_name', country_code),
                    'adoption': float(adoption),
                    'growth': float(growth),
                    'benchmarks': benchmarks_for_cc
                })

                total_adoption += adoption
                total_growth += growth
                valid_countries += 1

            if valid_countries == 0:
                return []

            avg_adoption = total_adoption / valid_countries
            avg_growth = total_growth / valid_countries

            # Classification
            for p in data_points:
                if p['adoption'] >= avg_adoption:
                    if p['growth'] >= avg_growth:
                        p['classification'] = "Champion"
                        p['color_class'] = "emerald"
                    else:
                        p['classification'] = "Stagnant Giant"
                        p['color_class'] = "amber"
                else:
                    if p['growth'] >= avg_growth:
                        p['classification'] = "Fast Climber"
                        p['color_class'] = "blue"
                    else:
                        p['classification'] = "Risk Zone"
                        p['color_class'] = "rose"

            return {
                'points': data_points,
                'thresholds': {
                    'adoption': round(avg_adoption, 2),
                    'growth': round(avg_growth, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error computing Strategic Horizon: {e}")
            return []


# Global singleton
dashboard_cache_service = DashboardCacheService()
