#!/usr/bin/env python3
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "http://localhost:30800/v1/chat/completions"
METRICS_URL = "http://localhost:30800/metrics"

# SLA Thresholds for Constrained 4-Core Edge Node
MAX_AVG_LATENCY_SEC = 8.0
MIN_ACCURACY_SCORE = 0.75

# Golden Test Suite for Strategic/Sovereign Deployment Verification
TEST_CASES = [
    {
        "id": "airgap-net-01",
        "prompt": "Answer in one word: Which protocol uses port 22 for secure remote shell access, SSH or HTTP?",
        "expected_keywords": ["ssh"]
    },
    {
        "id": "k8s-ops-02",
        "prompt": "Answer in one word: In Kubernetes, what is the smallest deployable compute unit, a Pod or a Cluster?",
        "expected_keywords": ["pod"]
    },
    {
        "id": "india-sov-03",
        "prompt": "What is the capital city of India? Reply with the city name only.",
        "expected_keywords": ["delhi", "new delhi"]
    },
    {
        "id": "quant-ml-04",
        "prompt": "Does 4-bit quantization (Q4_K_M) increase or decrease model memory usage compared to FP16? Reply with increase or decrease.",
        "expected_keywords": ["decrease", "reduces", "lower"]
    }
]

def run_inference(prompt):
    payload = json.dumps({
        "model": "qwen2.5-1.5b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 32,
        "temperature": 0.0
    }).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=payload, headers={"Content-Type": "application/json"})
    start = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency = time.time() - start
    text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    return text, latency, usage.get("completion_tokens", 0)

def fetch_prometheus_metrics():
    metrics = {}
    with urllib.request.urlopen(METRICS_URL, timeout=10) as resp:
        for line in resp.read().decode("utf-8").splitlines():
            if line.startswith("llamacpp:") and not line.startswith("#"):
                parts = line.split()
                if len(parts) == 2:
                    metrics[parts[0]] = float(parts[1])
    return metrics

def main():
    print("=== SOVEREIGN EDGE EVALUATION HARNESS ===")
    passed = 0
    latencies = []
    total_tokens = 0
    results = []

    for tc in TEST_CASES:
        try:
            reply, latency, comp_tokens = run_inference(tc["prompt"])
            latencies.append(latency)
            total_tokens += comp_tokens
            hit = any(kw in reply.lower() for kw in tc["expected_keywords"])
            if hit:
                passed += 1
            status = "PASS" if hit else "FAIL"
            print(f"[{status}] {tc['id']} | Latency: {latency:.2f}s | Output: {reply!r}")
            results.append({"id": tc["id"], "status": status, "latency_sec": round(latency, 3), "output": reply})
        except Exception as e:
            print(f"[ERROR] {tc['id']} failed: {e}")
            results.append({"id": tc["id"], "status": "ERROR", "error": str(e)})

    accuracy = passed / len(TEST_CASES)
    avg_latency = sum(latencies) / len(latencies) if latencies else 999.0
    tps = total_tokens / sum(latencies) if sum(latencies) > 0 else 0.0
    prom_snapshot = fetch_prometheus_metrics()

    verdict = "APPROVED" if (accuracy >= MIN_ACCURACY_SCORE and avg_latency <= MAX_AVG_LATENCY_SEC) else "REJECTED"

    audit_record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "summary": {
            "accuracy": accuracy,
            "avg_latency_sec": round(avg_latency, 3),
            "throughput_tokens_per_sec": round(tps, 2),
            "sla_max_latency_sec": MAX_AVG_LATENCY_SEC,
            "sla_min_accuracy": MIN_ACCURACY_SCORE
        },
        "prometheus_telemetry": prom_snapshot,
        "test_results": results
    }

    with open("audit-logs/latest_eval_audit.json", "w") as f:
        json.dump(audit_record, f, indent=2)

    print("-----------------------------------------")
    print(f"Accuracy: {accuracy*100:.1f}% (SLA >= {MIN_ACCURACY_SCORE*100:.0f}%)")
    print(f"Avg Latency: {avg_latency:.2f}s (SLA <= {MAX_AVG_LATENCY_SEC:.1f}s) | Throughput: {tps:.2f} tok/s")
    print(f"Gate Verdict: {verdict}")
    sys.exit(0 if verdict == "APPROVED" else 1)

if __name__ == "__main__":
    main()

