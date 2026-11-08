# Sovereign Edge: Air-Gapped LLM Serving, GitOps & Observability Pipeline

End-to-end MLOps platform for deploying, evaluating, monitoring, and rolling back quantized LLMs in disconnected, resource-constrained edge environments.

## Architecture & Stack
- Edge Cluster: Air-gapped K3s single-node cluster on CentOS Stream 9 (4 vCPU, 8 GB RAM)
- Air-Gap Artifact Ingestion: Daemonless OCI image bundling via crane and local Docker Registry (:30500)
- Local GitOps Source of Truth: Self-hosted Gitea (:30300) managing declarative Kubernetes manifests
- Inference Engine: llama.cpp HTTP server (:30800) serving 4-bit quantized Qwen2.5-1.5B-Instruct (Q4_K_M GGUF)
- Evaluation & Rollback Gate: Zero-dependency Python harness (harnesses/eval_gate.py) and automated rollback wrapper (harnesses/deploy_with_gate.sh)
- Observability & Alerting: Prometheus (:30900) and auto-provisioned Grafana dashboards (:30400)

## Measured Edge Benchmarks (4 vCPU, 8 GB RAM CPU-Only Node)
- Golden Set Accuracy: 100%
- Average End-to-End Request Latency: 0.36s - 0.44s
- Prompt Prefill Throughput: 102.05 tokens/sec
- Token Generation Throughput: 15.24 tokens/sec
- Container Memory Footprint: < 2.2 GB RAM
