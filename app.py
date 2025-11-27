"""
Custody Bank AI Automation Platform - Chainlit Main Entry
Using MainCrew as unified orchestrator
"""
import asyncio
import chainlit as cl
from config import UI_CONFIG
from agent_module.crews import MainCrew
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
        "fund_dividend_query": [
            ("Query fund NAV", "What is the current NAV?"),
            ("View other fund dividends", "Show dividend history for fund 110011"),
            ("List all funds", "Show me all available funds"),
        ],
        "fund_list": [
            ("Query specific fund NAV", "What is the NAV of fund 161005?"),
            ("Check dividend records", "Show dividend history for China AMC Select"),
            ("Process dividends", "Process dividend distribution"),
        ],
        "dividend_process": [
            ("View process status", "Show the process status"),
            ("Query fund information", "What is the NAV of fund 161005?"),
            ("List all funds", "Show me all available funds"),
        ],
        "confirming": [
            ("Confirm execution", "confirm"),
            ("Cancel operation", "cancel"),
            ("Modify requirements", "Please modify the process"),
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
        "fund_dividend_query": [
            ("查询基金净值", "当前净值是多少?"),
            ("查看其他基金分红", "显示基金110011的分红历史"),
            ("列出所有基金", "显示所有可用的基金"),
        ],
        "fund_list": [
            ("查询特定基金净值", "基金161005的净值是多少?"),
            ("查看分红记录", "显示华夏优势的分红历史"),
            ("处理分红", "处理分红派息"),
        ],
        "dividend_process": [
            ("查看流程状态", "显示流程状态"),
            ("查询基金信息", "基金161005的净值是多少?"),
            ("列出所有基金", "显示所有可用的基金"),
        ],
        "confirming": [
            ("确认执行", "确认"),
            ("取消操作", "取消"),
            ("修改需求", "请修改流程"),
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

# Initialize MainCrew - unified orchestrator
main_crew = MainCrew(
    service_registry=service_registry,
    service_matcher=service_matcher,
    memory_manager=memory_manager,
)


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
    cl.user_session.set("session_id", str(id(cl.user_session)))  # Unique session ID

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


async def animate_step(msg: cl.Message, base_content: str, step_text: str, duration: float = 0.4):
    """Animate a step with spinner"""
    frames = LOADING_FRAMES
    end_time = asyncio.get_event_loop().time() + duration
    frame_idx = 0

    while asyncio.get_event_loop().time() < end_time:
        msg.content = f"{base_content}{frames[frame_idx]} {step_text}"
        await msg.update()
        frame_idx = (frame_idx + 1) % len(frames)
        await asyncio.sleep(0.1)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages"""
    user_input = message.content
    history = cl.user_session.get("history", [])
    session_id = cl.user_session.get("session_id", "default")

    # Detect language from user input
    lang = detect_language(user_input)
    cl.user_session.set("lang", lang)

    # Add to history
    history.append({"role": "user", "content": user_input})

    # Create response message (all content in one message)
    response_msg = cl.Message(content="", author="Custody Bank AI")
    await response_msg.send()

    # Accumulated content for unified display
    accumulated_content = ""

    # Define thinking callback
    async def on_thinking(steps):
        nonlocal accumulated_content
        # Show thinking animation
        await animate_step(response_msg, accumulated_content, "🤔 Analyzing...", 0.5)

        # Display thinking steps
        accumulated_content += "🤔 **Analyzing**\n"
        for step in steps:
            accumulated_content += f"> {step}\n"
            response_msg.content = accumulated_content
            await response_msg.update()
            await asyncio.sleep(0.25)

        accumulated_content += "✅ Done\n\n"
        response_msg.content = accumulated_content
        await response_msg.update()

    # Define expert speak callback (subtle, in same message)
    async def on_expert_speak(name, emoji, speech):
        nonlocal accumulated_content
        # Show spinner animation
        await animate_step(response_msg, accumulated_content, f"{emoji} {name}...", 0.3)

        # Add expert speech (one line)
        accumulated_content += f"{emoji} **{name}**: {speech}\n"
        response_msg.content = accumulated_content
        await response_msg.update()

    try:
        # Use MainCrew with callbacks
        result = await main_crew.process(
            user_input=user_input,
            session_id=session_id,
            lang=lang,
            on_thinking=on_thinking,
            on_expert_speak=on_expert_speak,
        )

        # Store to memory system
        await memory_manager.store_interaction(user_input, result)

        # Display final result
        status = result.get("status")
        if status in ["rag_not_found", "sipoc_confirming"]:
            # Flow 2 stages: append message to accumulated content
            accumulated_content += "\n" + result.get("message", "")
            response_msg.content = accumulated_content
        else:
            # Other cases: show final result
            response_msg.content = result.get("message", "Done")

        await response_msg.update()

        # Determine suggestion context based on result status
        suggestion_context = "default"
        if status in ["rag_not_found", "sipoc_confirming"]:
            suggestion_context = "confirming"
        elif result.get("data"):
            # Try to determine context from the data
            data = result.get("data", {})
            if "nav" in str(data).lower():
                suggestion_context = "fund_nav"
            elif "dividend" in str(data).lower():
                suggestion_context = "fund_dividend_query"
            elif isinstance(data, list):
                suggestion_context = "fund_list"

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
    session_id = cl.user_session.get("session_id", "default")

    if history:
        await memory_manager.save_session(history)

    # Clear session state in MainCrew
    main_crew.clear_session(session_id)


if __name__ == "__main__":
    cl.run()
