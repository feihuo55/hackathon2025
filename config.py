"""
全局配置文件
托管银行AI自动化平台
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.resolve()

# AWS Bedrock 配置
AWS_CONFIG = {
    "bearer_token": os.environ.get("AWS_BEARER_TOKEN_BEDROCK", ""),
    "region": os.environ.get("AWS_REGION", "us-east-1"),
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "max_tokens": 4096,
    "temperature": 0.7,
}

# Chroma 向量数据库配置
CHROMA_CONFIG = {
    "persist_directory": str(BASE_DIR / "data" / "chroma_db"),
    "collection_name": "services",
}

# 记忆系统配置
MEMORY_CONFIG = {
    "max_episodic_entries": 100,
    "max_summary_length": 500,
}

# Chainlit UI 配置
UI_CONFIG = {
    "app_name": "Custody Bank AI",
    "welcome_message": """**Welcome to Custody Bank AI Platform**

I'm your intelligent assistant for fund management. Here's what I can help you with:

**Fund Queries**
- Query fund NAV: `Query fund 161005`
- View all funds: `Show all funds`
- Check dividends: `Query dividend history for 161005`

**Process Automation**
- Process dividends: `Process dividend for all funds`
- Create workflows: `Create a new business process`

How can I assist you today?""",
}

# 服务配置
SERVICE_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
}

# 日志配置
LOG_CONFIG = {
    "level": os.environ.get("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
