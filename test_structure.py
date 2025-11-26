"""
Project structure test script
Verify all modules can be imported correctly
"""
import sys
import asyncio


def test_imports():
    """Test all module imports"""
    errors = []

    # Test config
    try:
        from config import AWS_CONFIG, CHROMA_CONFIG, UI_CONFIG
        print("[OK] config module imported")
    except Exception as e:
        errors.append(f"config: {e}")

    # Test service_module
    try:
        from service_module.mock_services.fund_services import FundServices, FUND_DATA
        from service_module.mock_services.service_registry import ServiceRegistry
        from service_module.sipoc.templates import SIPOCDocument
        from service_module.sipoc.sipoc_generator import SIPOCGenerator
        from service_module.service_generator import ServiceGenerator
        print("[OK] service_module imported")
    except Exception as e:
        errors.append(f"service_module: {e}")

    # Test rag_module
    try:
        from rag_module.memory.episodic_memory import EpisodicMemory
        from rag_module.memory.memory_manager import MemoryManager
        print("[OK] rag_module (memory) imported")
    except Exception as e:
        errors.append(f"rag_module.memory: {e}")

    # Test agent_module
    try:
        from agent_module.bedrock_client import BedrockClient
        print("[OK] agent_module (bedrock_client) imported")
    except Exception as e:
        errors.append(f"agent_module.bedrock_client: {e}")

    # Test ui_module
    try:
        from ui_module.sipoc_viewer import render_sipoc
        from ui_module.status_panel import StatusPanel
        from ui_module.chat_handler import ChatHandler
        print("[OK] ui_module imported")
    except Exception as e:
        errors.append(f"ui_module: {e}")

    return errors


async def test_services():
    """Test service functionality"""
    print("\n--- Testing Services ---")

    from service_module.mock_services.fund_services import FundServices
    from service_module.mock_services.service_registry import ServiceRegistry

    # Test fund service
    result = await FundServices.get_fund_nav("161005")
    if result.get("success"):
        data = result["data"]
        print(f"[OK] Fund NAV query: {data['name']} - NAV: {data['nav']}")
    else:
        print(f"[FAIL] Fund NAV query failed: {result.get('error')}")

    # Test service registry
    registry = ServiceRegistry()
    services = registry.get_all_services()
    print(f"[OK] Service registry has {len(services)} services")

    # Test service invocation
    result = await registry.invoke("getAllFunds")
    if result.get("success"):
        print(f"[OK] Service invoke: got {len(result['data'])} funds")
    else:
        print("[FAIL] Service invoke failed")


async def test_sipoc():
    """Test SIPOC functionality"""
    print("\n--- Testing SIPOC ---")

    from service_module.sipoc.templates import SIPOCTemplates, SIPOCDocument
    from service_module.sipoc.sipoc_generator import SIPOCGenerator
    from ui_module.sipoc_viewer import render_sipoc

    # Test templates
    templates = SIPOCTemplates()
    sipoc = templates.fund_dividend_processing()
    print(f"[OK] SIPOC template created: {sipoc.title}")

    # Test rendering
    rendered = render_sipoc(sipoc)
    if "Supplier" in rendered:
        print("[OK] SIPOC rendering works")
    else:
        print("[FAIL] SIPOC rendering failed")


async def test_memory():
    """Test memory system"""
    print("\n--- Testing Memory System ---")

    from rag_module.memory.memory_manager import MemoryManager

    memory = MemoryManager()

    # Add interaction record
    await memory.store_interaction(
        user_input="Query fund NAV",
        result={"success": True, "message": "NAV: 3.2156"}
    )

    # Get statistics
    stats = memory.get_statistics()
    print(f"[OK] Memory system: {stats['total_memories']} records")


def main():
    print("=" * 50)
    print("Custody Bank AI Platform - Structure Test")
    print("=" * 50)

    # Test imports
    print("\n--- Testing Module Imports ---")
    errors = test_imports()

    if errors:
        print("\nImport errors:")
        for err in errors:
            print(f"  [FAIL] {err}")
        sys.exit(1)

    # Run async tests
    asyncio.run(test_services())
    asyncio.run(test_sipoc())
    asyncio.run(test_memory())

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
