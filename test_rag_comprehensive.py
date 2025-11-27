"""
RAG模块综合测试
使用丰富的模拟数据进行全面测试
"""
import asyncio
import sys
import io

# 修复Windows控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from rag_module.retrieval.service_matcher import ServiceMatcher
from rag_module.memory import MemoryManager, SemanticMemory, ProceduralMemory, SummaryMemory
from rag_module.demo_data import (
    DEMO_SERVICES, MOCK_FUNDS, MOCK_DIVIDENDS, MOCK_HOLDINGS,
    KNOWLEDGE_BASE, SAMPLE_CONVERSATIONS, TEST_QUERIES,
    get_fund_by_code, get_dividends, get_holdings, search_knowledge
)


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title: str):
    print(f"\n--- {title} ---")


def print_result(label: str, value, indent=2):
    prefix = " " * indent
    print(f"{prefix}{label}: {value}")


async def test_service_matching_comprehensive():
    """综合服务匹配测试"""
    print_header("综合服务匹配测试 (10个服务, 30+查询)")

    matcher = ServiceMatcher()
    matcher.index_services(DEMO_SERVICES)

    print(f"\n已索引 {len(DEMO_SERVICES)} 个服务:")
    for svc in DEMO_SERVICES:
        print(f"  - {svc['service_id']}: {svc['name']}")

    # 按类别分组测试
    categories = {
        "净值查询": [q for q in TEST_QUERIES if q[1] == "getFundNAV"],
        "分红查询": [q for q in TEST_QUERIES if q[1] == "getFundDividend"],
        "基金列表": [q for q in TEST_QUERIES if q[1] == "getAllFunds"],
        "持仓查询": [q for q in TEST_QUERIES if q[1] == "getFundHoldings"],
        "基金经理": [q for q in TEST_QUERIES if q[1] == "getFundManager"],
        "基金对比": [q for q in TEST_QUERIES if q[1] == "compareFunds"],
        "分红处理": [q for q in TEST_QUERIES if q[1] == "processDividend"],
        "收益计算": [q for q in TEST_QUERIES if q[1] == "calculateReturn"],
        "风险指标": [q for q in TEST_QUERIES if q[1] == "getRiskMetrics"],
        "订阅提醒": [q for q in TEST_QUERIES if q[1] == "subscribeAlert"],
    }

    total_tests = 0
    correct_matches = 0

    for category, queries in categories.items():
        if not queries:
            continue

        print_subheader(f"{category} ({len(queries)}个测试)")

        for query, expected_service in queries:
            total_tests += 1
            matches = await matcher.match_service(query, top_k=1)

            if matches:
                matched_service = matches[0]["service_id"]
                score = matches[0]["relevance_score"]
                is_correct = matched_service == expected_service

                if is_correct:
                    correct_matches += 1
                    status = "✓"
                else:
                    status = "✗"

                print(f"  {status} \"{query}\"")
                print(f"      期望: {expected_service}, 匹配: {matched_service} (score: {score:.3f})")
            else:
                print(f"  ✗ \"{query}\" - 未找到匹配")

    accuracy = correct_matches / total_tests * 100 if total_tests > 0 else 0
    print(f"\n匹配准确率: {correct_matches}/{total_tests} ({accuracy:.1f}%)")

    return accuracy >= 50  # 至少50%准确率


async def test_memory_with_conversations():
    """使用对话数据测试记忆系统"""
    print_header("对话记忆测试 (3组对话, 11轮交互)")

    memory = MemoryManager()

    for conv_idx, conversation in enumerate(SAMPLE_CONVERSATIONS, 1):
        print_subheader(f"对话 {conv_idx} ({len(conversation)//2}轮)")

        for i in range(0, len(conversation), 2):
            user_msg = conversation[i]
            assistant_msg = conversation[i + 1] if i + 1 < len(conversation) else None

            # 存储用户输入
            user_input = user_msg["content"]
            print(f"  用户: {user_input[:40]}...")

            if assistant_msg:
                result = {
                    "success": True,
                    "message": assistant_msg["content"],
                }
                await memory.store_interaction(user_input, result)
                print(f"  助手: {assistant_msg['content'][:40]}...")

    # 测试上下文获取
    print_subheader("上下文检索")
    context = memory.get_context(max_turns=5)
    print(f"  最近5轮上下文:\n{context[:200]}...")

    # 测试统计
    print_subheader("记忆统计")
    stats = memory.get_statistics()
    print_result("总事件数", stats['episodic']['total_memories'])
    print_result("用户输入", stats['episodic']['user_inputs'])
    print_result("助手响应", stats['episodic']['total_memories'] - stats['episodic']['user_inputs'])

    return True


async def test_semantic_memory_with_knowledge():
    """使用知识库测试语义记忆"""
    print_header("知识库语义记忆测试 (8条知识)")

    memory = SemanticMemory(collection_name="test_knowledge_base")
    memory.clear()

    # 存储知识
    print_subheader("存储知识库")
    for kb in KNOWLEDGE_BASE:
        memory.store(
            knowledge_id=kb["knowledge_id"],
            content=f"{kb['title']}\n{kb['content']}",
            category=kb["category"],
            metadata={"title": kb["title"], "tags": ",".join(kb.get("tags", []))},
        )
        print(f"  + {kb['knowledge_id']}: {kb['title']}")

    print(f"\n  共存储 {memory.count()} 条知识")

    # 测试检索
    print_subheader("知识检索测试")
    test_queries = [
        ("什么是基金净值", "concept"),
        ("分红有哪几种方式", "concept"),
        ("基金有哪些费用", "faq"),
        ("风险指标怎么看", "concept"),
        ("分红派息流程", "process"),
    ]

    for query, expected_category in test_queries:
        results = memory.retrieve(query, top_k=2)
        print(f"\n  查询: \"{query}\"")
        if results:
            for r in results:
                title = r['metadata'].get('title', r['knowledge_id'])
                print(f"    - {title} (score: {r['score']:.3f})")
        else:
            print("    - 未找到相关知识")

    return True


async def test_procedural_memory_with_workflows():
    """测试程序记忆与业务流程"""
    print_header("业务流程程序记忆测试")

    memory = ProceduralMemory(enable_persistence=False)

    # 定义业务流程
    workflows = [
        {
            "id": "wf_nav_query",
            "name": "基金净值查询流程",
            "description": "查询指定基金的实时净值信息",
            "steps": [
                {"step": 1, "action": "解析用户输入", "description": "提取基金代码或名称"},
                {"step": 2, "action": "匹配基金", "description": "在基金库中匹配对应基金"},
                {"step": 3, "action": "获取净值", "description": "调用净值查询服务"},
                {"step": 4, "action": "格式化返回", "description": "组装返回消息"},
            ],
        },
        {
            "id": "wf_dividend_process",
            "name": "分红派息处理流程",
            "description": "批量处理基金分红派息业务",
            "steps": [
                {"step": 1, "action": "获取分红列表", "description": "查询待处理的分红记录"},
                {"step": 2, "action": "权益确认", "description": "确认持有人权益"},
                {"step": 3, "action": "计算金额", "description": "计算各持有人分红金额"},
                {"step": 4, "action": "派息处理", "description": "执行派息或红利再投"},
                {"step": 5, "action": "记录结果", "description": "记录处理结果"},
            ],
        },
        {
            "id": "wf_fund_compare",
            "name": "基金对比分析流程",
            "description": "对比多只基金的各项指标",
            "steps": [
                {"step": 1, "action": "解析基金列表", "description": "提取要对比的基金"},
                {"step": 2, "action": "获取基金数据", "description": "查询各基金详细信息"},
                {"step": 3, "action": "指标计算", "description": "计算收益、风险等指标"},
                {"step": 4, "action": "生成对比报告", "description": "格式化对比结果"},
            ],
        },
    ]

    print_subheader("注册业务流程")
    for wf in workflows:
        procedure = memory.store_procedure(
            procedure_id=wf["id"],
            name=wf["name"],
            description=wf["description"],
            steps=wf["steps"],
        )
        print(f"  + {wf['name']} ({len(wf['steps'])}步骤)")

    # 模拟执行记录
    print_subheader("模拟执行记录")
    execution_logs = [
        ("wf_nav_query", True, 0.15),
        ("wf_nav_query", True, 0.12),
        ("wf_nav_query", True, 0.18),
        ("wf_nav_query", False, 0.25),  # 一次失败
        ("wf_nav_query", True, 0.14),
        ("wf_dividend_process", True, 2.5),
        ("wf_dividend_process", True, 2.8),
        ("wf_dividend_process", False, 3.2),  # 一次失败
        ("wf_fund_compare", True, 0.8),
        ("wf_fund_compare", True, 0.75),
    ]

    for proc_id, success, exec_time in execution_logs:
        memory.record_execution(proc_id, success=success, execution_time=exec_time)

    print(f"  记录了 {len(execution_logs)} 次执行")

    # 查看统计
    print_subheader("流程执行统计")
    for wf in workflows:
        proc = memory.get_procedure(wf["id"])
        if proc:
            total = proc.success_count + proc.failure_count
            print(f"  {proc.name}:")
            print(f"    执行次数: {total}, 成功: {proc.success_count}, 失败: {proc.failure_count}")
            print(f"    成功率: {proc.success_rate:.1%}")

    # 查找流程
    print_subheader("流程查找测试")
    search_queries = ["查询净值", "分红处理", "对比基金"]
    for query in search_queries:
        found = memory.find_procedure(query, top_k=1)
        if found:
            print(f"  \"{query}\" -> {found[0].name}")
        else:
            print(f"  \"{query}\" -> 未找到")

    return True


async def test_summary_memory_with_conversations():
    """使用对话数据测试摘要记忆"""
    print_header("对话摘要记忆测试")

    memory = SummaryMemory(enable_persistence=False)

    print_subheader("生成对话摘要")
    for conv_idx, conversation in enumerate(SAMPLE_CONVERSATIONS, 1):
        summary = memory.summarize_conversation(conversation)
        print(f"\n  对话{conv_idx}摘要:")
        print(f"    来源消息数: {summary.source_count}")
        print(f"    主题: {summary.metadata.get('topics', [])}")
        print(f"    内容: {summary.content[:100]}...")

    # 获取合并摘要
    print_subheader("上下文摘要")
    context_summary = memory.get_context_summary(max_summaries=3)
    print(f"  合并后的上下文 ({len(context_summary)} 字符):")
    print(f"  {context_summary[:200]}...")

    # 搜索摘要
    print_subheader("摘要搜索")
    search_terms = ["净值", "分红", "基金经理"]
    for term in search_terms:
        results = memory.search(term)
        print(f"  搜索 \"{term}\": 找到 {len(results)} 条相关摘要")

    return True


async def test_full_integration():
    """完整集成测试"""
    print_header("完整集成测试 - 模拟真实场景")

    # 初始化所有组件
    service_matcher = ServiceMatcher()
    service_matcher.index_services(DEMO_SERVICES)

    memory_manager = MemoryManager()
    semantic_memory = SemanticMemory(collection_name="integration_test")
    semantic_memory.clear()

    # 加载知识库
    print_subheader("加载知识库")
    for kb in KNOWLEDGE_BASE:
        semantic_memory.store(
            knowledge_id=kb["knowledge_id"],
            content=f"{kb['title']}\n{kb['content']}",
            category=kb["category"],
        )
    print(f"  已加载 {semantic_memory.count()} 条知识")

    # 模拟用户交互场景
    print_subheader("模拟用户交互场景")

    scenarios = [
        # 场景1：查询基金净值
        {
            "user_input": "查询富国天惠基金今天的净值",
            "expected_service": "getFundNAV",
            "mock_result": lambda: {
                "success": True,
                "message": f"富国天惠({MOCK_FUNDS[0]['fund_code']})今日净值为{MOCK_FUNDS[0]['nav']}元",
                "data": {"nav": MOCK_FUNDS[0]['nav']},
            },
        },
        # 场景2：查询分红
        {
            "user_input": "这个基金有分红吗",
            "expected_service": "getFundDividend",
            "mock_result": lambda: {
                "success": True,
                "message": f"最近一次分红是{MOCK_DIVIDENDS['161005'][0]['date']}，派息{MOCK_DIVIDENDS['161005'][0]['amount']}元",
                "data": {"dividends": MOCK_DIVIDENDS['161005']},
            },
        },
        # 场景3：查询持仓
        {
            "user_input": "持有哪些股票",
            "expected_service": "getFundHoldings",
            "mock_result": lambda: {
                "success": True,
                "message": f"前5大重仓股：{', '.join([h['stock_name'] for h in MOCK_HOLDINGS['161005']])}",
                "data": {"holdings": MOCK_HOLDINGS['161005']},
            },
        },
        # 场景4：处理分红
        {
            "user_input": "帮我处理本月的分红派息",
            "expected_service": "processDividend",
            "mock_result": lambda: {
                "success": True,
                "message": "已处理3只基金的分红派息，总金额1.10元/份",
                "data": {"processed_count": 3},
            },
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n  场景{i}: {scenario['user_input']}")

        # 服务匹配
        matches = await service_matcher.match_service(scenario['user_input'], top_k=1)
        if matches:
            matched = matches[0]
            expected = scenario['expected_service']
            status = "✓" if matched['service_id'] == expected else "✗"
            print(f"    {status} 匹配服务: {matched['name']} (score: {matched['relevance_score']:.3f})")

        # 执行并存储结果
        result = scenario['mock_result']()
        await memory_manager.store_interaction(scenario['user_input'], result)
        print(f"    响应: {result['message'][:50]}...")

    # 最终统计
    print_subheader("最终统计")
    stats = memory_manager.get_statistics()
    print(f"  事件记忆: {stats['episodic']['total_memories']} 条")
    print(f"  语义记忆: {semantic_memory.count()} 条")

    # 导出上下文
    print_subheader("导出对话上下文")
    context = memory_manager.get_full_context()
    print(f"  上下文长度: {len(context)} 字符")
    print(f"  预览: {context[:150]}...")

    return True


async def main():
    """运行所有综合测试"""
    print("\n" + "=" * 70)
    print("   托管银行AI自动化平台 - RAG模块综合测试")
    print("=" * 70)

    tests = [
        ("服务匹配综合测试", test_service_matching_comprehensive),
        ("对话记忆测试", test_memory_with_conversations),
        ("知识库语义记忆测试", test_semantic_memory_with_knowledge),
        ("业务流程程序记忆测试", test_procedural_memory_with_workflows),
        ("对话摘要记忆测试", test_summary_memory_with_conversations),
        ("完整集成测试", test_full_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"ERROR: {str(e)[:30]}"))

    # 打印总结
    print("\n" + "=" * 70)
    print("  测试结果总结")
    print("=" * 70)

    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)

    for name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"  {status} {name}: {result}")

    print(f"\n  总计: {passed}/{total} 通过")
    print("=" * 70 + "\n")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
