#!/usr/bin/env python3
"""
RTB Real-Time Inference Example.

Demonstrates:
1. Multi-variant endpoints for A/B testing
2. Latency tracking and SLO monitoring
3. Variant weight updates (canary deployment)
4. Real-time predictions with latency awareness

RTB Context:
  - SSP needs to decide which ads to show in milliseconds
  - Every 10ms of latency matters (longer response = less ads sold)
  - Must track which model made each prediction (for attribution)
  - Progressive rollout: test new model on 1% traffic before 100% rollout
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, List
import numpy as np

# Add parent directory to path (1_sagemaker-mlops/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
from inference.realtime_optimizer import LatencyTracker, ModelOptimizer, RTBInferenceOptimizer
from inference.realtime_endpoint import MultiVariantEndpoint, RTBPredictionRouter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTBSimulator:
    """
    Simulate RTB inference workflow with latency tracking.

    In production, this would be integrated with your ad server,
    but this shows the patterns you need.
    """

    def __init__(self, endpoint_name: str, slo_ms: float = 20.0):
        self.endpoint_name = endpoint_name
        self.tracker = LatencyTracker(slo_ms=slo_ms)
        self.router = RTBPredictionRouter(endpoint_name=endpoint_name)
        self.variant_stats = {}

    def process_impression(
        self,
        impression_id: str,
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process one ad impression (bid request) through RTB.

        Timeline:
        1. Extract features (0-2ms)
        2. Fetch from feature store (8-12ms) ← Phase 2
        3. Call model (5-10ms)
        4. Post-process (0-1ms)
        Total: < 20ms SLO

        Returns:
            {
                "impression_id": "imp_123",
                "prediction": 0.45,
                "variant": "production",
                "latency_ms": 15.3,
                "slo_met": True,
            }
        """
        start = time.time()

        # Step 1: Extract features (0-2ms)
        feature_extract_start = time.time()
        # ... feature extraction happens here
        feature_extract_ms = (time.time() - feature_extract_start) * 1000

        # Step 2: Feature lookup (simulated, would be DynamoDB/Redis in Phase 2)
        feature_lookup_start = time.time()
        # For now, simulate lookup time
        simulated_lookup_ms = np.random.normal(8, 2)  # 8ms ± 2ms
        time.sleep(simulated_lookup_ms / 1000)
        feature_lookup_ms = (time.time() - feature_lookup_start) * 1000

        # Step 3: Model inference
        inference_start = time.time()
        try:
            # In production, this calls the real endpoint
            # For now, simulate inference
            simulated_inference_ms = np.random.normal(5, 1)  # 5ms ± 1ms
            time.sleep(simulated_inference_ms / 1000)

            # Simulated prediction
            prediction = float(np.random.uniform(0, 1))
            variant = np.random.choice(["production", "canary"], p=[0.9, 0.1])

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return {"error": str(e)}

        inference_ms = (time.time() - inference_start) * 1000

        # Step 4: Post-process (0-1ms)
        post_start = time.time()
        # Apply business logic (e.g., floor price checks)
        post_processing_ms = (time.time() - post_start) * 1000

        # Record latency
        total_ms = (time.time() - start) * 1000
        self.tracker.record(feature_lookup_ms, inference_ms, post_processing_ms)

        # Track stats per variant
        if variant not in self.variant_stats:
            self.variant_stats[variant] = {
                "count": 0,
                "total_latency": 0,
                "predictions": [],
            }
        self.variant_stats[variant]["count"] += 1
        self.variant_stats[variant]["total_latency"] += total_ms
        self.variant_stats[variant]["predictions"].append(prediction)

        slo_met = total_ms < self.tracker.slo_ms

        return {
            "impression_id": impression_id,
            "prediction": round(prediction, 3),
            "variant": variant,
            "latency_ms": round(total_ms, 2),
            "slo_met": slo_met,
            "breakdown": {
                "feature_lookup_ms": round(feature_lookup_ms, 2),
                "inference_ms": round(inference_ms, 2),
                "post_processing_ms": round(post_processing_ms, 2),
            }
        }

    def print_stats(self):
        """Print per-variant statistics and SLO compliance."""
        print("\n" + "="*80)
        print("RTB INFERENCE STATISTICS")
        print("="*80)

        for variant, stats in self.variant_stats.items():
            avg_latency = stats["total_latency"] / stats["count"]
            print(f"\n{variant.upper()}:")
            print(f"  Requests: {stats['count']}")
            print(f"  Avg latency: {avg_latency:.2f}ms")
            print(f"  Prediction range: {min(stats['predictions']):.3f} - {max(stats['predictions']):.3f}")

        print("\n" + "-"*80)
        print("LATENCY REPORT (across all variants):")
        print("-"*80)
        print(self.tracker.report())

    def recommend_rollout(self) -> Dict[str, Any]:
        """
        Should we increase canary traffic?

        In production RTB:
        - Monitor error rates
        - Monitor latency SLOs
        - Monitor business metrics (CTR, viewability, etc.)
        - Make rollout decision

        This is a simplified example.
        """
        print("\n" + "="*80)
        print("CANARY ROLLOUT ANALYSIS")
        print("="*80)

        if "canary" not in self.variant_stats:
            return {"recommendation": "No canary to analyze"}

        canary = self.variant_stats["canary"]
        production = self.variant_stats["production"]

        canary_latency = canary["total_latency"] / canary["count"]
        prod_latency = production["total_latency"] / production["count"]

        latency_diff = canary_latency - prod_latency

        print(f"Canary latency: {canary_latency:.2f}ms")
        print(f"Production latency: {prod_latency:.2f}ms")
        print(f"Difference: {latency_diff:+.2f}ms")

        recommendation = "INCREASE traffic"
        if latency_diff > 5:
            recommendation = "HOLD (canary too slow)"
        elif canary_latency > self.tracker.slo_ms:
            recommendation = "HOLD (violating SLO)"

        print(f"\nRecommendation: {recommendation}")

        return {
            "recommendation": recommendation,
            "canary_latency_ms": round(canary_latency, 2),
            "prod_latency_ms": round(prod_latency, 2),
            "latency_diff_ms": round(latency_diff, 2),
        }


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   RTB REAL-TIME INFERENCE EXAMPLE                            ║
║                                                                              ║
║ Scenario: SSP evaluates CTR model for ad placement decisions                 ║
║ - Production model: current model (90% traffic)                              ║
║ - Canary model: new model with better features (10% traffic)                 ║
║ - SLO: p99 latency < 20ms (RTB standard)                                     ║
║                                                                              ║
║ Key Patterns:                                                                ║
║ 1. Multi-variant endpoint: test without redeployment                         ║
║ 2. Latency tracking: identify bottlenecks (Phase 1)                          ║
║ 3. Canary analysis: safe rollout (ramping traffic)                           ║
║ 4. Feature store integration: coming in Phase 2                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Initialize simulator
    simulator = RTBSimulator(
        endpoint_name="rtb-ctr-ab-test",
        slo_ms=20.0  # 20ms SLO (p99)
    )

    print("\nSimulating 500 RTB impressions (bid requests)...\n")

    # Simulate RTB traffic
    for i in range(500):
        impression_id = f"imp_{i:06d}"

        # Simulate features (in Phase 2, these come from feature store)
        features = {
            "user_id": f"user_{np.random.randint(0, 10000)}",
            "ad_slot": np.random.choice([1, 2, 3, 4]),
            "inventory_type": np.random.choice(["banner", "video", "native"]),
            "user_segment": np.random.choice(["high_value", "medium", "low"]),
        }

        result = simulator.process_impression(impression_id, features)

        # Print sample results
        if i < 5 or i % 100 == 0:
            print(f"  {result['impression_id']}: "
                  f"CTR={result['prediction']:.3f} | "
                  f"variant={result['variant']} | "
                  f"latency={result['latency_ms']}ms | "
                  f"SLO={'✓' if result['slo_met'] else '✗ VIOLATED'}")

    # Print final statistics
    simulator.print_stats()

    # Analyze canary performance
    rollout_rec = simulator.recommend_rollout()

    # Show optimization recommendations
    print("\n" + "="*80)
    print("OPTIMIZATION OPPORTUNITIES")
    print("="*80)

    optimizer = ModelOptimizer()
    recs = optimizer.get_optimization_recommendations(
        current_latency_ms=13.5,
        target_latency_ms=20.0,
        num_trees=100,
        tree_depth=5
    )

    print(f"\nCurrent latency: {recs['current_latency_ms']:.1f}ms (within SLO ✓)")
    print(f"Target latency: {recs['target_latency_ms']:.1f}ms")
    print("\nIf you needed to optimize further:")
    for opt in recs["optimizations"]:
        if isinstance(opt, dict):
            print(f"  • {opt.get('technique', opt)}")


if __name__ == "__main__":
    main()
