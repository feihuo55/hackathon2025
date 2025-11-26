"""
Language Detection Utility
Detects user input language and provides bilingual responses
"""
import re


def detect_language(text: str) -> str:
    """
    Detect if the input text is Chinese or English

    Args:
        text: Input text

    Returns:
        'zh' for Chinese, 'en' for English
    """
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.replace(' ', ''))

    if total_chars == 0:
        return 'en'

    # If more than 20% Chinese characters, consider it Chinese
    if chinese_chars / total_chars > 0.2:
        return 'zh'

    return 'en'


# Bilingual message templates
MESSAGES = {
    'welcome': {
        'en': """**Welcome to Custody Bank AI Platform**

I'm your intelligent assistant for fund management. Here's what I can help you with:

**Fund Queries**
- Query fund NAV: `Query fund 161005`
- View all funds: `Show all funds`
- Check dividends: `Query dividend for 161005`

**Process Automation**
- Process dividends: `Process dividend for all funds`
- Create workflows: `Create a new business process`

How can I assist you today?""",
        'zh': """**欢迎使用托管银行AI平台**

我是您的智能基金管理助手。以下是我可以帮您做的事情：

**基金查询**
- 查询基金净值：`查询161005净值`
- 查看所有基金：`显示所有基金`
- 查询分红：`查询161005分红`

**流程自动化**
- 处理分红：`处理所有基金分红`
- 创建流程：`创建新业务流程`

请问有什么可以帮您？"""
    },
    'analyzing': {
        'en': 'Analyzing your request...',
        'zh': '正在分析您的请求...'
    },
    'intent_detected': {
        'en': 'Intent detected: {intent}, processing...',
        'zh': '识别到意图: {intent}，正在处理...'
    },
    'searching': {
        'en': 'Searching for relevant information...',
        'zh': '正在搜索相关信息...'
    },
    'processing': {
        'en': 'Processing your request...',
        'zh': '正在处理您的请求...'
    },
    'generating': {
        'en': 'Generating response...',
        'zh': '正在生成回复...'
    },
    'unknown_intent': {
        'en': """Sorry, I couldn't understand your request. Please try:
- Query fund NAV: `Query fund 161005`
- View all funds: `Show all funds`
- Process dividends: `Process dividend for all funds`""",
        'zh': """抱歉，我无法理解您的请求。请尝试：
- 查询基金净值：`查询161005净值`
- 查看所有基金：`显示所有基金`
- 处理分红：`处理所有基金分红`"""
    },
    'no_service_match': {
        'en': """Sorry, I couldn't find a matching service. Please try:
- Query fund NAV: `Query fund 161005`
- Check dividend history: `Query dividend for 161005`
- View all funds: `Show all funds`""",
        'zh': """抱歉，未找到匹配的服务。请尝试：
- 查询基金净值：`查询161005净值`
- 查询分红记录：`查询161005分红`
- 查看所有基金：`显示所有基金`"""
    },
    'service_error': {
        'en': 'Service execution failed: {error}',
        'zh': '服务执行失败: {error}'
    },
    'process_error': {
        'en': 'Error processing request: {error}',
        'zh': '处理请求时发生错误: {error}'
    },
    'service_success': {
        'en': 'Service executed successfully. Data: {data}',
        'zh': '服务执行成功，返回数据：{data}'
    },
    'no_service_id': {
        'en': 'No service ID specified',
        'zh': '未指定服务ID'
    },
    'confirm_operation': {
        'en': 'Please confirm to execute this operation',
        'zh': '请确认是否执行此操作'
    },
    'missing_sipoc': {
        'en': 'Missing SIPOC document, cannot build service',
        'zh': '缺少SIPOC文档，无法构建服务'
    },
    'service_created': {
        'en': """**Service Created and Executed Successfully!**

Results:
- Funds processed: {count}
- Total dividend amount: ${amount:,.2f}

Details have been recorded in the system.""",
        'zh': """**服务创建并执行成功！**

处理结果：
- 处理基金数量: {count}
- 分红总金额: ¥{amount:,.2f}

详细信息已记录到系统中。"""
    },
    'nav_result': {
        'en': {
            'header': '**{name}** ({code})',
            'nav_label': 'Unit NAV',
            'acc_nav_label': 'Accumulated NAV',
            'change_label': 'Change',
            'date_label': 'Update Date'
        },
        'zh': {
            'header': '**{name}** ({code})',
            'nav_label': '单位净值',
            'acc_nav_label': '累计净值',
            'change_label': '涨跌幅',
            'date_label': '更新日期'
        }
    },
    'dividend_result': {
        'en': {
            'header': '**{name}** Dividend History',
            'total': 'Total Dividends: **{amount:.2f}** per share',
            'date_col': 'Date',
            'amount_col': 'Amount',
            'type_col': 'Type'
        },
        'zh': {
            'header': '**{name}** 分红记录',
            'total': '累计分红: **{amount:.2f}** 元/份',
            'date_col': '分红日期',
            'amount_col': '分红金额',
            'type_col': '分红类型'
        }
    },
    'fund_list': {
        'en': {
            'header': '**Available Funds**',
            'code_col': 'Code',
            'name_col': 'Name',
            'type_col': 'Type'
        },
        'zh': {
            'header': '**可查询基金列表**',
            'code_col': '代码',
            'name_col': '名称',
            'type_col': '类型'
        }
    },
    'dividend_processing': {
        'en': {
            'header': '**Dividend Processing Complete**',
            'count': 'Funds Processed',
            'total': 'Total Amount',
            'fund_col': 'Fund',
            'amount_col': 'Amount',
            'method_col': 'Method',
            'status_col': 'Status'
        },
        'zh': {
            'header': '**分红处理完成**',
            'count': '处理基金数量',
            'total': '分红总金额',
            'fund_col': '基金',
            'amount_col': '分红金额',
            'method_col': '方式',
            'status_col': '状态'
        }
    }
}


def get_message(key: str, lang: str, **kwargs) -> str:
    """
    Get a message in the specified language

    Args:
        key: Message key
        lang: Language code ('en' or 'zh')
        **kwargs: Format arguments

    Returns:
        Formatted message string
    """
    if key not in MESSAGES:
        return key

    msg = MESSAGES[key].get(lang, MESSAGES[key].get('en', key))

    if isinstance(msg, str) and kwargs:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg

    return msg


def get_template(key: str, lang: str) -> dict:
    """
    Get a template dictionary in the specified language

    Args:
        key: Template key
        lang: Language code

    Returns:
        Template dictionary
    """
    if key not in MESSAGES:
        return {}

    return MESSAGES[key].get(lang, MESSAGES[key].get('en', {}))
