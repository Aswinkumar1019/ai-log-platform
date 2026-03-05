#!/bin/bash

echo "============================================"
echo "🚀 AI Log Platform - Restore Script"
echo "============================================"

# Step 1 - Set kubeconfig
echo ""
echo "📁 Step 1 - Setting kubeconfig..."
export KUBECONFIG=$HOME/.kube/config
echo 'export KUBECONFIG=$HOME/.kube/config' >> ~/.bashrc

# Step 2 - Start Kind cluster
echo ""
echo "☸️  Step 2 - Creating Kind cluster..."
kind create cluster --config /home/ubuntu/ai-log-platform/kind-cluster-config.yaml
echo "✅ Cluster created!"

# Step 3 - Wait for node to be ready
echo ""
echo "⏳ Step 3 - Waiting for node to be Ready..."
kubectl wait --for=condition=Ready node --all --timeout=120s
echo "✅ Node is Ready!"

# Step 4 - Deploy microservices
echo ""
echo "🔧 Step 4 - Deploying microservices..."
kubectl create namespace microservices
kubectl apply -f /home/ubuntu/ai-log-platform/k8s/microservices/
echo "✅ Microservices deployed!"

# Step 5 - Deploy logging stack
echo ""
echo "📊 Step 5 - Deploying logging stack..."
kubectl create namespace logging
kubectl apply -f /home/ubuntu/ai-log-platform/k8s/logging/
echo "✅ Logging stack deployed!"

# Step 6 - Wait for Elasticsearch
echo ""
echo "⏳ Step 6 - Waiting for Elasticsearch to be ready..."
kubectl wait --for=condition=Ready pod -l app=elasticsearch -n logging --timeout=120s
echo "✅ Elasticsearch is Ready!"

# Step 7 - Port forward Elasticsearch
echo ""
echo "🔌 Step 7 - Setting up port forward..."
pkill -f "port-forward" 2>/dev/null
sleep 3
kubectl port-forward -n logging svc/elasticsearch 9200:9200 &
sleep 5
echo "✅ Port forward active!"

# Step 8 - Verify everything
echo ""
echo "🔍 Step 8 - Verifying everything..."
echo ""
echo "--- Cluster Nodes ---"
kubectl get nodes
echo ""
echo "--- Microservices ---"
kubectl get pods -n microservices
echo ""
echo "--- Logging Stack ---"
kubectl get pods -n logging
echo ""
echo "--- Elasticsearch Health ---"
curl -s http://localhost:9200/_cluster/health | python3 -m json.tool

echo ""
echo "============================================"
echo "✅ Platform Restored Successfully!"
echo "============================================"
echo ""
echo "To run AI analyzer:"
echo "  cd /home/ubuntu/ai-log-platform/ai-analyzer"
echo "  python3 analyzer.py"
echo ""
echo "To watch logs:"
echo "  kubectl logs -f deployment/api-service -n microservices"
echo "============================================"
