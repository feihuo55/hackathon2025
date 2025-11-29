"""
Language Detection Utility
Provides message templates (English only)
"""
import re


def detect_language(text: str) -> str:
    """
    Detect if the input text is Chinese or English
    Always returns 'en' for English-only mode

    Args:
        text: Input text

    Returns:
        'en' for English
    """
    return 'en'


# Message templates (English only)
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

How can I assist you today?"""
    },
    'analyzing': {
        'en': 'Analyzing your request...'
    },
    'intent_detected': {
        'en': 'Intent detected: {intent}, processing...'
    },
    'searching': {
        'en': 'Searching for relevant information...'
    },
    'processing': {
        'en': 'Processing your request...'
    },
    'generating': {
        'en': 'Generating response...'
    },
    'unknown_intent': {
        'en': """Sorry, I couldn't understand your request. Please try:
- Query fund NAV: `Query fund 161005`
- View all funds: `Show all funds`
- Process dividends: `Process dividend for all funds`"""
    },
    'no_service_match': {
        'en': """Sorry, I couldn't find a matching service. Please try:
- Query fund NAV: `Query fund 161005`
- Check dividend history: `Query dividend for 161005`
- View all funds: `Show all funds`"""
    },
    'service_error': {
        'en': 'Service execution failed: {error}'
    },
    'process_error': {
        'en': 'Error processing request: {error}'
    },
    'service_success': {
        'en': 'Service executed successfully. Data: {data}'
    },
    'no_service_id': {
        'en': 'No service ID specified'
    },
    'confirm_operation': {
        'en': 'Please confirm to execute this operation'
    },
    'missing_sipoc': {
        'en': 'Missing SIPOC document, cannot build service'
    },
    'service_created': {
        'en': """**Service Created and Executed Successfully!**

Results:
- Funds processed: {count}
- Total dividend amount: ${amount:,.2f}

Details have been recorded in the system."""
    },
    'nav_result': {
        'en': {
            'header': '**{name}** ({code})',
            'nav_label': 'Unit NAV',
            'acc_nav_label': 'Accumulated NAV',
            'change_label': 'Change',
            'date_label': 'Update Date'
        }
    },
    'dividend_result': {
        'en': {
            'header': '**{name}** Dividend History',
            'total': 'Total Dividends: **{amount:.2f}** per share',
            'date_col': 'Date',
            'amount_col': 'Amount',
            'type_col': 'Type'
        }
    },
    'fund_list': {
        'en': {
            'header': '**Available Funds**',
            'code_col': 'Code',
            'name_col': 'Name',
            'type_col': 'Type'
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
        }
    }
}


def get_message(key: str, lang: str = 'en', **kwargs) -> str:
    """
    Get a message in English

    Args:
        key: Message key
        lang: Language code (ignored, always uses English)
        **kwargs: Format arguments

    Returns:
        Formatted message string
    """
    if key not in MESSAGES:
        return key

    msg = MESSAGES[key].get('en', key)

    if isinstance(msg, str) and kwargs:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg

    return msg


def get_template(key: str, lang: str = 'en') -> dict:
    """
    Get a template dictionary in English

    Args:
        key: Template key
        lang: Language code (ignored, always uses English)

    Returns:
        Template dictionary
    """
    if key not in MESSAGES:
        return {}

    return MESSAGES[key].get('en', {})
