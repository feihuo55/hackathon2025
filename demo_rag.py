"""
RAG Module 独立演示脚本
可以单独运行测试 RAG 模块的各项功能
"""
import asyncio
import sys
import io

# 修复Windows控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from rag_module.retrieval.service_matcher import ServiceMatcher
from rag_module.memory import MemoryManager, ProceduralMemory, SummaryMemory


# 模拟的基金服务定义
DEMO_SERVICES = [
    {
        "service_id": "getFundNAV",
        "name": "基金净值查询",
        "description": "查询指定基金的单位净值、累计净值和涨跌幅",
        "keywords": ["净值", "基金", "查询", "NAV", "涨跌", "单位净值"],
        "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
    },
    {
        "service_id": "getFundDividend",
        "name": "基金分红查询",
        "description": "查询指定基金的历史分红记录",
        "keywords": ["分红", "派息", "红利", "历史", "记录"],
        "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
    },
    {
        "service_id": "getAllFunds",
        "name": "获取基金列表",
        "description": "获取系统中所有可查询的基金产品列表",
        "keywords": ["列表", "所有基金", "全部", "基金列表", "产品"],
        "parameters": {},
    },
    {
        "service_id": "processDividend",
        "name": "基金分红处理",
        "description": "批量处理基金分红派息业务",
        "keywords": ["分红处理", "派息", "批量", "处理", "业务"],
        "parameters": {"fund_codes": {"type": "list", "description": "基金代码列表"}},
    },
    {
        "service_id": "getFundHoldings",
        "name": "基金持仓查询",
        "description": "查询基金的持仓明细和资产配置",
        "keywords": ["持仓", "资产", "配置", "明细", "股票"],
        "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
    },
]


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value):
    """打印结果"""
    print(f"  {label}: {value}")


async def demo_service_matching():
    """演示服务匹配功能"""
    print_header("服务匹配演示 (ServiceMatcher)")

    matcher = ServiceMatcher()
    matcher.index_services(DEMO_SERVICES)
    print(f"\n已索引 {matcher.get_indexed_count()} 个服务")

    # 测试查询
    test_queries = [
        "查询富国天惠基金今天的净值",
        "基金分红记录",
        "显示所有基金",
        "处理本月分红",
        "查看基金持仓情况",
        "NAV是多少",
        "派息历史",
    ]

    print("\n服务匹配测试:")
    print("-" * 50)

    for query in test_queries:
        result = await matcher.match_with_explanation(query, top_k=2)
        print(f"\n查询: \"{query}\"")
        print(f"分词结果: {result['query_tokens'][:5]}...")

        if result['matches']:
            for i, match in enumerate(result['matches'], 1):
                print(f"  [{i}] {match['name']} (score: {match['relevance_score']:.3f})")
                if match.get('matched_keywords'):
                    print(f"      匹配关键词: {match['matched_keywords']}")
        else:
            print("  未找到匹配的服务")


async def demo_memory_system():
    """演示记忆系统功能"""
    print_header("记忆系统演示 (MemoryManager)")

    memory = MemoryManager()

    # 模拟用户交互
    interactions = [
        ("查询基金161005的净值", {"success": True, "message": "富国天惠(161005)今日净值为3.2156元", "data": {"nav": 3.2156}}),
        ("这个基金最近有分红吗", {"success": True, "message": "最近一次分红是2024年1月，每份派息0.5元", "data": {"dividend": 0.5}}),
        ("显示所有可用的基金", {"success": True, "message": "共有5只基金可供查询", "data": {"count": 5}}),
    ]

    print("\n存储交互记录:")
    print("-" * 50)
    for user_input, result in interactions:
        await memory.store_interaction(user_input, result)
        print(f"  用户: {user_input}")
        print(f"  响应: {result['message'][:40]}...")

    # 获取上下文
    print("\n\n对话上下文:")
    print("-" * 50)
    context = memory.get_context(max_turns=5)
    print(context if context else "  (无上下文)")

    # 统计信息
    print("\n\n记忆统计:")
    print("-" * 50)
    stats = memory.get_statistics()
    print_result("事件记忆条数", stats['episodic']['total_memories'])
    print_result("用户输入数", stats['episodic']['user_inputs'])
    print_result("服务调用数", stats['episodic']['service_calls'])


async def demo_procedural_memory():
    """演示程序记忆功能"""
    print_header("程序记忆演示 (ProceduralMemory)")

    memory = ProceduralMemory(enable_persistence=False)  # 演示时不持久化

    # 存储流程
    procedure = memory.store_procedure(
        procedure_id="fund_nav_query",
        name="基金净值查询流程",
        description="查询指定基金的净值信息",
        steps=[
            {"step": 1, "action": "解析用户输入", "description": "提取基金代码"},
            {"step": 2, "action": "调用服务", "description": "调用getFundNAV服务"},
            {"step": 3, "action": "格式化结果", "description": "返回净值数据"},
        ],
    )

    print(f"\n创建流程: {procedure.name}")
    print(f"步骤数: {len(procedure.steps)}")

    # 模拟执行记录
    print("\n模拟执行记录:")
    print("-" * 50)
    for i in range(5):
        success = i != 2  # 第3次模拟失败
        memory.record_execution("fund_nav_query", success=success, execution_time=0.3 + i * 0.1)
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  执行 {i+1}: {status}")

    # 查看统计
    p = memory.get_procedure("fund_nav_query")
    print(f"\n执行统计:")
    print_result("成功次数", p.success_count)
    print_result("失败次数", p.failure_count)
    print_result("成功率", f"{p.success_rate:.1%}")


async def demo_summary_memory():
    """演示摘要记忆功能"""
    print_header("摘要记忆演示 (SummaryMemory)")

    memory = SummaryMemory(enable_persistence=False)

    # 模拟对话
    messages = [
        {"role": "user", "content": "查询富国天惠基金今天的净值"},
        {"role": "assistant", "content": "富国天惠(161005)今日净值为3.2156元，较昨日上涨2.35%"},
        {"role": "user", "content": "这个基金最近有分红吗"},
        {"role": "assistant", "content": "最近一次分红是在2024年1月，每份派息0.5元"},
        {"role": "user", "content": "帮我查一下所有基金"},
        {"role": "assistant", "content": "系统中共有5只基金可供查询：富国天惠、易方达消费、华夏回报等"},
    ]

    print("\n原始对话:")
    print("-" * 50)
    for msg in messages:
        role = "用户" if msg["role"] == "user" else "助手"
        print(f"  {role}: {msg['content'][:30]}...")

    # 生成摘要
    summary = memory.summarize_conversation(messages)

    print("\n\n生成的对话摘要:")
    print("-" * 50)
    print(f"{summary.content}")

    print(f"\n摘要统计:")
    print_result("来源消息数", summary.source_count)
    print_result("提取主题", summary.metadata.get('topics', []))


async def interactive_demo():
    """交互式演示"""
    print_header("交互式服务匹配")

    matcher = ServiceMatcher()
    matcher.index_services(DEMO_SERVICES)

    print("\n可用服务:")
    for svc in DEMO_SERVICES:
        print(f"  - {svc['name']}: {svc['description'][:30]}...")

    print("\n输入查询进行服务匹配 (输入 'quit' 退出):")
    print("-" * 50)

    while True:
        try:
            query = input("\n> 请输入查询: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("退出演示")
                break

            if not query:
                continue

            result = await matcher.match_with_explanation(query, top_k=3)

            print(f"\n分词: {result['query_tokens']}")
            print(f"\n匹配结果:")

            if result['matches']:
                for i, match in enumerate(result['matches'], 1):
                    print(f"  [{i}] {match['name']}")
                    print(f"      服务ID: {match['service_id']}")
                    print(f"      匹配度: {match['relevance_score']:.3f}")
            else:
                print("  未找到匹配的服务")

        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n退出演示")
            break


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("   托管银行 AI 自动化平台 - RAG 模块演示")
    print("=" * 60)

    print("\n选择演示模式:")
    print("  1. 服务匹配演示")
    print("  2. 记忆系统演示")
    print("  3. 程序记忆演示")
    print("  4. 摘要记忆演示")
    print("  5. 运行所有演示")
    print("  6. 交互式服务匹配")
    print("  0. 退出")

    try:
        choice = input("\n请选择 (1-6, 默认5): ").strip() or "5"

        if choice == "1":
            await demo_service_matching()
        elif choice == "2":
            await demo_memory_system()
        elif choice == "3":
            await demo_procedural_memory()
        elif choice == "4":
            await demo_summary_memory()
        elif choice == "5":
            await demo_service_matching()
            await demo_memory_system()
            await demo_procedural_memory()
            await demo_summary_memory()
        elif choice == "6":
            await interactive_demo()
        elif choice == "0":
            print("退出")
            return
        else:
            print("无效选择")
            return

    except (EOFError, KeyboardInterrupt):
        # 非交互模式，运行所有演示
        await demo_service_matching()
        await demo_memory_system()
        await demo_procedural_memory()
        await demo_summary_memory()

    print("\n" + "=" * 60)
    print("   演示完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
