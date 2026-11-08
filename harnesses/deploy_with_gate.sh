#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Applying Kubernetes manifest from Git..."
kubectl apply -f manifests/llm-serving.yaml

echo "[2/3] Waiting for rollout readiness..."
if ! kubectl rollout status deployment/qwen-edge-llm -n sovereign-ai --timeout=90s; then
    echo "[ALERT] Pod failed readiness probe! Rolling back immediately..."
    kubectl rollout undo deployment/qwen-edge-llm -n sovereign-ai
    exit 1
fi

echo "[3/3] Running Evaluation Gate against live model..."
if python3 harnesses/eval_gate.py; then
    echo "[SUCCESS] Model passed accuracy and latency SLAs. Deployment locked in."
else
    echo "[CRITICAL] Evaluation Gate REJECTED model update! Executing automatic rollback..."
    kubectl rollout undo deployment/qwen-edge-llm -n sovereign-ai
    kubectl rollout status deployment/qwen-edge-llm -n sovereign-ai --timeout=60s
    echo "[ROLLED BACK] Previous healthy revision restored."
    exit 1
fi

