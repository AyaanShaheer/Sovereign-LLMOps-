# Field Incident Runbook: Sovereign Edge LLM Serving

Target Environment: Air-Gapped K3s Single-Node Cluster (CentOS-VM-1, 4 vCPU, 8 GB RAM)
Model Stack: llama-server (Qwen2.5-1.5B-Instruct-Q4_K_M.gguf), NodePort 30800
Observability: Prometheus (:30900), Grafana (:30400), Local Registry (:30500), Gitea (:30300)

## 1. Rapid Triage Checklist (Run First)
    kubectl get pods -A
    curl -s http://localhost:30800/health
    curl -s http://localhost:30900/api/v1/targets | grep -o '"health":"[^"]*"'

## 2. Playbook A: High Latency or Queue Saturation (LLMQueueSaturation)
- Symptom: llamacpp:requests_deferred > 0 or generation throughput < 5 tok/s.
- Root Cause: Concurrent requests exceeding single-slot KV cache capacity or CPU throttling.
- Remediation:
    curl -s http://localhost:30800/metrics | grep -E "llamacpp:(requests_processing|requests_deferred)"
    ./harnesses/deploy_with_gate.sh

## 3. Playbook B: Pod OOMKilled (Exit Code 137)
- Symptom: kubectl get pods -n sovereign-ai shows OOMKilled or CrashLoopBackOff.
- Root Cause: Context window (--ctx-size) or model weights exceeded the 2200Mi memory limit.
- Remediation:
    kubectl describe pod -l app=qwen-edge-llm -n sovereign-ai | grep -A 5 "Last State:"
    # Reduce --ctx-size from 2048 to 1024 in manifests/llm-serving.yaml, then run:
    ./harnesses/deploy_with_gate.sh

## 4. Playbook C: Failed Evaluation Gate / Emergency Rollback
- Symptom: Model update fails accuracy (< 75%) or latency (> 8.0s) SLA gate.
- Manual Override (if needed in field):
    kubectl rollout undo deployment/qwen-edge-llm -n sovereign-ai
    kubectl rollout status deployment/qwen-edge-llm -n sovereign-ai
    python3 harnesses/eval_gate.py
