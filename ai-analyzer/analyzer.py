import os
import requests
from datetime import datetime
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ES_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ES_PORT = os.getenv("ELASTICSEARCH_PORT", "9200")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")

def fetch_recent_logs(minutes=5):
    print(f"\n📥 Fetching logs from last {minutes} minutes...")
    query = {
        "query": {
            "bool": {
                "must": [{"range": {"@timestamp": {"gte": f"now-{minutes}m", "lte": "now"}}}],
                "should": [
                    {"match": {"message": "ERROR"}},
                    {"match": {"message": "WARNING"}},
                    {"match": {"message": "WARN"}},
                    {"match": {"message": "error"}},
                    {"match": {"message": "warning"}}
                ],
                "minimum_should_match": 1
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": 50
    }
    today = datetime.now().strftime("%Y.%m.%d")
    index = f"fluentd-{today}"
    try:
        response = es.search(index=index, body=query)
        logs = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            logs.append({
                'timestamp': source.get('@timestamp', ''),
                'log': source.get('message', ''),
                'pod': source.get('kubernetes', {}).get('pod_name', 'unknown'),
                'namespace': source.get('kubernetes', {}).get('namespace_name', 'unknown')
            })
        print(f"✅ Found {len(logs)} warning/error logs")
        return logs
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")
        return []

def analyze_with_ai(logs):
    if not logs:
        print("⚠️  No logs to analyze")
        return None
    print(f"\n🤖 Sending {len(logs)} logs to AI for analysis...")
    log_text = "\n".join([
        f"[{log['timestamp']}] POD:{log['pod']} - {log['log'].strip()}"
        for log in logs[:30]
    ])
    prompt = f"""You are a DevOps expert analyzing Kubernetes pod logs.
Analyze these logs and provide:
1. SUMMARY: Brief summary (2-3 sentences)
2. CRITICAL ISSUES: List critical errors
3. WARNINGS: List warnings
4. ROOT CAUSE: Most likely root cause
5. RECOMMENDATIONS: Top 3 action items

Logs:
{log_text}

Be concise and actionable."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
        )
        response.raise_for_status()
        analysis = response.json()['choices'][0]['message']['content']
        print("✅ AI analysis complete!")
        return analysis
    except Exception as e:
        print(f"❌ Error calling Groq API: {e}")
        return None

def send_discord_alert(analysis, log_count):
    if not DISCORD_WEBHOOK:
        print("\n⚠️  Discord webhook not configured - printing to console only")
        return False
    print("\n📤 Sending alert to Discord...")
    
    # Truncate to fit Discord 2000 char limit
    if len(analysis) > 1500:
        analysis = analysis[:1500] + "...(truncated)"
    
    message = f"🚨 **AI Log Analysis Alert**\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📊 **Logs Analyzed:** {log_count}\n\n🤖 **AI Analysis:**\n{analysis}"
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": message})
        response.raise_for_status()
        print("✅ Discord alert sent!")
        return True
    except Exception as e:
        print(f"❌ Error sending Discord alert: {e}")
        return False

def run_analysis():
    print("=" * 60)
    print("🔍 AI LOG ANALYZER v2.0 - Starting Analysis")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    logs = fetch_recent_logs(minutes=5)
    if not logs:
        print("\n✅ No warnings or errors found in last 5 minutes!")
        return
    analysis = analyze_with_ai(logs)
    if not analysis:
        print("❌ AI analysis failed")
        return
    print("\n" + "=" * 60)
    print("🤖 AI ANALYSIS RESULT:")
    print("=" * 60)
    print(analysis)
    send_discord_alert(analysis, len(logs))
    print("\n" + "=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_analysis()
