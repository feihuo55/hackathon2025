"""
Custody Bank AI Automation Platform - Chainlit Main Entry
"""
import asyncio
import chainlit as cl
from config import UI_CONFIG
from agent_module.crews import QueryCrew, CreationCrew
from agent_module.agents import IntentAgent
from rag_module.retrieval import ServiceMatcher
from rag_module.memory import MemoryManager
from service_module.mock_services import ServiceRegistry
from utils.language_detector import detect_language, get_message


# Suggestion questions based on context
SUGGESTIONS = {
    "en": {
        "default": [
            ("Show all available funds", "Show me all available funds"),
            ("Query fund NAV", "What is the NAV of fund 161005?"),
            ("Check dividend history", "Show dividend history for China AMC Select"),
        ],
        "fund_nav": [
            ("Check another fund", "What is the NAV of fund 110011?"),
            ("View dividend history", "Show dividend history for this fund"),
            ("Compare with other funds", "Show me all available funds"),
        ],
        "fund_dividend": [
            ("Query fund NAV", "What is the current NAV?"),
            ("View other fund dividends", "Show dividend history for fund 110011"),
            ("List all funds", "Show me all available funds"),
        ],
        "fund_list": [
            ("Query specific fund NAV", "What is the NAV of fund 161005?"),
            ("Check dividend records", "Show dividend history for China AMC Select"),
            ("Process dividends", "Process dividend distribution"),
        ],
        "creation": [
            ("View process status", "Show the process status"),
            ("Query fund information", "What is the NAV of fund 161005?"),
            ("List all funds", "Show me all available funds"),
        ],
    },
    "zh": {
        "default": [
            ("查看所有基金", "显示所有可用的基金"),
            ("查询基金净值", "基金161005的净值是多少?"),
            ("查看分红记录", "显示华夏优势的分红历史"),
        ],
        "fund_nav": [
            ("查询其他基金", "基金110011的净值是多少?"),
            ("查看分红历史", "显示该基金的分红记录"),
            ("对比其他基金", "显示所有可用的基金"),
        ],
        "fund_dividend": [
            ("查询基金净值", "当前净值是多少?"),
            ("查看其他基金分红", "显示基金110011的分红历史"),
            ("列出所有基金", "显示所有可用的基金"),
        ],
        "fund_list": [
            ("查询特定基金净值", "基金161005的净值是多少?"),
            ("查看分红记录", "显示华夏优势的分红历史"),
            ("处理分红", "处理分红派息"),
        ],
        "creation": [
            ("查看流程状态", "显示流程状态"),
            ("查询基金信息", "基金161005的净值是多少?"),
            ("列出所有基金", "显示所有可用的基金"),
        ],
    },
}


def get_suggestions(lang: str, context: str = "default") -> list:
    """Get suggestion questions based on language and context"""
    lang_suggestions = SUGGESTIONS.get(lang, SUGGESTIONS["en"])
    return lang_suggestions.get(context, lang_suggestions["default"])


# Initialize global components
service_registry = ServiceRegistry()
service_matcher = ServiceMatcher()
memory_manager = MemoryManager()
intent_agent = IntentAgent()
query_crew = QueryCrew(service_registry, service_matcher, memory_manager)
creation_crew = CreationCrew(service_registry, memory_manager)


# Loading animation frames
LOADING_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']


async def animate_loading(msg: cl.Message, text: str, duration: float = 0.5):
    """Show loading animation"""
    frames = LOADING_FRAMES
    end_time = asyncio.get_event_loop().time() + duration
    frame_idx = 0

    while asyncio.get_event_loop().time() < end_time:
        msg.content = f"{frames[frame_idx]} {text}"
        await msg.update()
        frame_idx = (frame_idx + 1) % len(frames)
        await asyncio.sleep(0.1)


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    # Initialize session state
    cl.user_session.set("history", [])
    cl.user_session.set("context", {})
    cl.user_session.set("lang", "en")  # Default language

    # Send welcome message with AI author
    welcome_msg = cl.Message(content=get_message('welcome', 'en'), author="Custody Bank AI")
    await welcome_msg.send()

    # Send initial suggestions
    lang = "en"
    suggestions = get_suggestions(lang, "default")
    actions = []
    for i, (label, query) in enumerate(suggestions):
        actions.append(
            cl.Action(
                name=f"suggestion_{i}",
                label=label,
                payload={"query": query},
                description=query,
            )
        )

    suggestion_label = "Try asking:"
    await cl.Message(
        content=f"**{suggestion_label}**",
        author="Custody Bank AI",
        actions=actions,
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages"""
    user_input = message.content
    history = cl.user_session.get("history", [])

    # Detect language from user input
    lang = detect_language(user_input)
    cl.user_session.set("lang", lang)

    # Add to history
    history.append({"role": "user", "content": user_input})

    # Create response message with streaming (AI author)
    response_msg = cl.Message(content="", author="Custody Bank AI")
    await response_msg.send()

    try:
        # Step 1: Analyzing - with animation
        await animate_loading(response_msg, get_message('analyzing', lang), 0.5)

        # Intent recognition
        intent_result = await intent_agent.analyze(user_input)
        intent_type = intent_result.get("type", "unknown")

        # Step 2: Show intent detected
        response_msg.content = f"✓ {get_message('intent_detected', lang, intent=intent_type)}"
        await response_msg.update()
        await asyncio.sleep(0.3)

        # Step 3: Processing - with animation
        await animate_loading(response_msg, get_message('processing', lang), 0.5)

        # Route to appropriate handler based on intent
        if intent_type == "query":
            # Flow 1: Query existing services
            result = await query_crew.execute(user_input, intent_result)
        elif intent_type == "creation":
            # Flow 2: Create new service flow
            result = await creation_crew.execute(user_input, intent_result)
        else:
            result = {
                "success": False,
                "message": get_message('unknown_intent', lang)
            }

        # Step 4: Generating response - with animation
        await animate_loading(response_msg, get_message('generating', lang), 0.3)

        # Store to memory system
        await memory_manager.store_interaction(user_input, result)

        # Update message with final result
        response_msg.content = result.get("message", "Done")
        await response_msg.update()

        # If SIPOC document exists, display visualization
        if result.get("sipoc"):
            from ui_module.sipoc_viewer import render_sipoc
            sipoc_content = render_sipoc(result["sipoc"])
            await cl.Message(content=sipoc_content, author="Custody Bank AI").send()

        # Determine suggestion context based on query type
        suggestion_context = "default"
        if intent_type == "query":
            query_type = intent_result.get("query_type", "")
            suggestion_context = query_type if query_type else "default"
        elif intent_type == "creation":
            suggestion_context = "creation"

        # Add suggestion buttons
        suggestions = get_suggestions(lang, suggestion_context)
        actions = []
        for i, (label, query) in enumerate(suggestions):
            actions.append(
                cl.Action(
                    name=f"suggestion_{i}",
                    label=label,
                    payload={"query": query},
                    description=query,
                )
            )

        # Send suggestions as a separate message with actions
        suggestion_label = "Try asking:" if lang == "en" else "试试问:"
        await cl.Message(
            content=f"**{suggestion_label}**",
            author="Custody Bank AI",
            actions=actions,
        ).send()

        # Update history
        history.append({"role": "assistant", "content": result.get("message", "")})
        cl.user_session.set("history", history)

    except Exception as e:
        error_msg = get_message('process_error', lang, error=str(e))
        response_msg.content = f"❌ {error_msg}"
        await response_msg.update()
        history.append({"role": "assistant", "content": error_msg})
        cl.user_session.set("history", history)


@cl.action_callback("suggestion_0")
@cl.action_callback("suggestion_1")
@cl.action_callback("suggestion_2")
async def on_suggestion_click(action: cl.Action):
    """Handle suggestion button clicks"""
    # Get the query from the action payload
    query = action.payload.get("query", "")

    # Create a fake message with the suggestion query
    fake_message = cl.Message(content=query)

    # Process the suggestion as if it was typed by the user
    await on_message(fake_message)


@cl.on_chat_end
async def on_chat_end():
    """Cleanup on chat end"""
    # Save session memory
    history = cl.user_session.get("history", [])
    if history:
        await memory_manager.save_session(history)


if __name__ == "__main__":
    cl.run()
