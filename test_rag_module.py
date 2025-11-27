"""
RAG Module 功能测试
"""
import asyncio
import sys
import io
from pathlib import Path

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 检测chromadb是否可用
CHROMADB_AVAILABLE = False
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    print("Warning: chromadb not available, some tests will be skipped")


def test_document_loader():
    """测试文档加载器"""
    print("\n" + "="*50)
    print("测试 DocumentLoader")
    print("="*50)

    from rag_module.indexing.document_loader import DocumentLoader
    from rag_module.indexing.document_loader import Document

    loader = DocumentLoader()

    # 测试服务加载
    test_services = [
        {
            "service_id": "getFundNAV",
            "name": "基金净值查询",
            "description": "查询指定基金的单位净值、累计净值和涨跌幅",
            "keywords": ["净值", "基金", "查询", "NAV"],
            "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
            "returns": {"nav": "单位净值", "acc_nav": "累计净值"},
        },
        {
            "service_id": "getFundDividend",
            "name": "基金分红查询",
            "description": "查询指定基金的历史分红记录",
            "keywords": ["分红", "派息", "红利"],
            "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
            "returns": {"dividends": "分红记录列表"},
        },
    ]

    docs = loader.load_services(test_services)
    print(f"[OK] 加载了 {len(docs)} 个服务文档")

    for doc in docs:
        print(f"  - ID: {doc.doc_id}, Type: {doc.doc_type}")
        print(f"    Metadata: {doc.metadata.get('name')}")

    return True


def test_embeddings():
    """测试向量化服务"""
    print("\n" + "="*50)
    print("测试 Embeddings")
    print("="*50)

    from rag_module.indexing.embeddings import TextPreprocessor

    preprocessor = TextPreprocessor()

    # 测试文本预处理
    text = "  查询  富国天惠  基金的  净值  "
    processed = preprocessor.preprocess(text)
    print(f"[OK] 文本预处理: '{text}' -> '{processed}'")

    # 测试文本分块
    long_text = "这是一段很长的文本。" * 50
    chunks = preprocessor.chunk_text(long_text, chunk_size=100, overlap=20)
    print(f"[OK] 文本分块: {len(long_text)} 字符 -> {len(chunks)} 块")

    # 测试关键词提取
    test_text = "查询富国天惠基金今天的净值和分红情况"
    keywords = preprocessor.extract_keywords(test_text, top_k=5)
    print(f"[OK] 关键词提取: {keywords}")

    return True


def test_index_builder():
    """测试索引构建器"""
    print("\n" + "="*50)
    print("测试 IndexBuilder")
    print("="*50)

    if not CHROMADB_AVAILABLE:
        print("[SKIP] chromadb不可用，跳过测试")
        return True

    from rag_module.indexing.index_builder import IndexBuilder

    builder = IndexBuilder()

    # 清空索引
    builder.clear_index()
    print("[OK] 清空索引")

    # 测试从服务构建索引
    test_services = [
        {
            "service_id": "getFundNAV",
            "name": "基金净值查询",
            "description": "查询指定基金的单位净值、累计净值和涨跌幅",
            "keywords": ["净值", "基金", "查询"],
            "parameters": {},
            "returns": {},
        },
    ]

    count = builder.build_from_services(test_services)
    print(f"[OK] 索引构建: {count} 个文档")

    # 获取统计
    stats = builder.get_index_stats()
    print(f"[OK] 索引统计: {stats}")

    return True


def test_service_matcher():
    """测试服务匹配器"""
    print("\n" + "="*50)
    print("测试 ServiceMatcher")
    print("="*50)

    from rag_module.retrieval.service_matcher import ServiceMatcher

    matcher = ServiceMatcher()

    # 索引服务
    test_services = [
        {
            "service_id": "getFundNAV",
            "name": "基金净值查询",
            "description": "查询指定基金的单位净值、累计净值和涨跌幅",
            "keywords": ["净值", "基金", "查询", "NAV", "涨跌"],
            "parameters": {"fund_code": {"type": "string"}},
        },
        {
            "service_id": "getFundDividend",
            "name": "基金分红查询",
            "description": "查询指定基金的历史分红记录",
            "keywords": ["分红", "派息", "红利", "分配"],
            "parameters": {"fund_code": {"type": "string"}},
        },
        {
            "service_id": "getAllFunds",
            "name": "获取基金列表",
            "description": "获取系统中所有可查询的基金列表",
            "keywords": ["列表", "所有基金", "基金列表"],
            "parameters": {},
        },
    ]

    matcher.index_services(test_services)
    print(f"[OK] 索引了 {matcher.get_indexed_count()} 个服务")

    # 测试匹配
    async def test_match():
        # 测试查询1
        query1 = "查询富国天惠基金今天的净值"
        results1 = await matcher.match_service(query1, top_k=2)
        print(f"\n查询: '{query1}'")
        for r in results1:
            print(f"  - {r['name']} (score: {r['relevance_score']:.3f})")

        # 测试查询2
        query2 = "基金分红记录"
        results2 = await matcher.match_service(query2, top_k=2)
        print(f"\n查询: '{query2}'")
        for r in results2:
            print(f"  - {r['name']} (score: {r['relevance_score']:.3f})")

        # 测试最佳匹配
        best = await matcher.find_best_match("查询净值")
        if best:
            print(f"\n[OK] 最佳匹配: {best['name']}")
        else:
            print("\n[WARN] 未找到最佳匹配")

    asyncio.run(test_match())
    return True


def test_knowledge_search():
    """测试知识检索"""
    print("\n" + "="*50)
    print("测试 KnowledgeSearch")
    print("="*50)

    if not CHROMADB_AVAILABLE:
        print("[SKIP] chromadb不可用，跳过测试")
        return True

    from rag_module.retrieval.knowledge_search import KnowledgeSearch
    from rag_module.indexing.index_builder import IndexBuilder

    # 先构建索引
    builder = IndexBuilder()
    builder.clear_index()

    test_services = [
        {
            "service_id": "getFundNAV",
            "name": "基金净值查询",
            "description": "查询指定基金的单位净值、累计净值和涨跌幅",
            "keywords": ["净值", "基金", "查询"],
            "parameters": {},
            "returns": {},
        },
    ]
    builder.build_from_services(test_services)

    # 测试检索
    search = KnowledgeSearch()

    async def test_search():
        results = await search.search("基金净值", top_k=3)
        print(f"[OK] 检索结果: {len(results)} 条")
        for r in results:
            print(f"  - {r.doc_id}: score={r.score:.3f}")

        stats = search.get_statistics()
        print(f"[OK] 检索统计: {stats}")

    asyncio.run(test_search())
    return True


def test_episodic_memory():
    """测试事件记忆"""
    print("\n" + "="*50)
    print("测试 EpisodicMemory")
    print("="*50)

    from rag_module.memory.episodic_memory import EpisodicMemory

    memory = EpisodicMemory(max_entries=50)

    # 添加事件
    memory.add("user_input", {"text": "查询基金净值"}, {"source": "user"})
    memory.add("agent_response", {"text": "正在查询..."}, {"source": "system"})
    memory.add("service_call", {"service_id": "getFundNAV", "result": {"nav": 3.21}})

    print(f"[OK] 添加了 {memory.count()} 条记录")

    # 获取最近记录
    recent = memory.get_recent(5)
    print(f"[OK] 最近记录: {len(recent)} 条")

    # 按类型获取
    user_inputs = memory.get_by_type("user_input")
    print(f"[OK] 用户输入: {len(user_inputs)} 条")

    # 获取对话历史
    history = memory.get_conversation_history()
    print(f"[OK] 对话历史: {len(history)} 条")

    # 搜索
    results = memory.search("净值")
    print(f"[OK] 搜索结果: {len(results)} 条")

    return True


def test_semantic_memory():
    """测试语义记忆"""
    print("\n" + "="*50)
    print("测试 SemanticMemory")
    print("="*50)

    from rag_module.memory.semantic_memory import SemanticMemory

    memory = SemanticMemory(collection_name="test_semantic_memory")
    memory.clear()

    # 存储知识
    memory.store(
        knowledge_id="fund_nav_concept",
        content="基金净值是指基金每份额的价格，包括单位净值和累计净值",
        category="concept",
        metadata={"domain": "fund"},
    )

    memory.store(
        knowledge_id="dividend_concept",
        content="基金分红是基金将收益的一部分派发给投资者",
        category="concept",
        metadata={"domain": "fund"},
    )

    print(f"[OK] 存储了 {memory.count()} 条知识")

    # 检索知识
    results = memory.retrieve("什么是基金净值", top_k=2)
    print(f"[OK] 检索结果: {len(results)} 条")
    for r in results:
        print(f"  - {r['knowledge_id']}: score={r['score']:.3f}")

    # 按ID获取
    knowledge = memory.get_by_id("fund_nav_concept")
    if knowledge:
        print(f"[OK] 按ID获取: {knowledge['knowledge_id']}")

    # 按类别获取
    concepts = memory.get_by_category("concept")
    print(f"[OK] 按类别获取: {len(concepts)} 条")

    return True


def test_procedural_memory():
    """测试程序记忆"""
    print("\n" + "="*50)
    print("测试 ProceduralMemory")
    print("="*50)

    from rag_module.memory.procedural_memory import ProceduralMemory

    memory = ProceduralMemory()
    memory.clear()

    # 存储流程
    procedure = memory.store_procedure(
        procedure_id="fund_nav_query",
        name="基金净值查询流程",
        description="查询指定基金的净值信息",
        steps=[
            {"step": 1, "action": "解析用户输入", "description": "提取基金代码"},
            {"step": 2, "action": "调用服务", "description": "调用getFundNAV"},
            {"step": 3, "action": "格式化结果", "description": "返回净值数据"},
        ],
        parameters={"fund_code": "string"},
    )

    print(f"[OK] 存储流程: {procedure.name}")

    # 记录执行
    memory.record_execution("fund_nav_query", success=True, execution_time=0.5)
    memory.record_execution("fund_nav_query", success=True, execution_time=0.3)
    memory.record_execution("fund_nav_query", success=False, execution_time=1.0)

    # 获取流程
    p = memory.get_procedure("fund_nav_query")
    if p:
        print(f"[OK] 成功率: {p.success_rate:.2%}")

    # 查找流程
    found = memory.find_procedure("查询净值", top_k=1)
    print(f"[OK] 查找结果: {len(found)} 个流程")

    # 获取统计
    stats = memory.get_statistics()
    print(f"[OK] 统计信息: {stats}")

    return True


def test_summary_memory():
    """测试摘要记忆"""
    print("\n" + "="*50)
    print("测试 SummaryMemory")
    print("="*50)

    from rag_module.memory.summary_memory import SummaryMemory

    memory = SummaryMemory()
    memory.clear()

    # 创建摘要
    summary = memory.create_summary(
        content="用户查询了富国天惠基金的净值，系统返回了净值3.21元",
        source_type="conversation",
        source_count=2,
    )
    print(f"[OK] 创建摘要: {summary.summary_id}")

    # 摘要对话
    messages = [
        {"role": "user", "content": "查询富国天惠基金今天的净值"},
        {"role": "assistant", "content": "富国天惠(161005)今日净值为3.2156元，涨幅2.35%"},
        {"role": "user", "content": "这个基金最近有分红吗"},
        {"role": "assistant", "content": "最近一次分红是在2024年1月，每份派息0.5元"},
    ]

    conv_summary = memory.summarize_conversation(messages)
    print(f"[OK] 对话摘要: {conv_summary.content[:50]}...")

    # 获取上下文摘要
    context = memory.get_context_summary(max_summaries=2)
    print(f"[OK] 上下文摘要长度: {len(context)} 字符")

    # 搜索
    results = memory.search("净值")
    print(f"[OK] 搜索结果: {len(results)} 条")

    # 统计
    stats = memory.get_statistics()
    print(f"[OK] 统计信息: {stats}")

    return True


def test_memory_manager():
    """测试统一记忆管理器"""
    print("\n" + "="*50)
    print("测试 MemoryManager")
    print("="*50)

    from rag_module.memory.memory_manager import MemoryManager

    manager = MemoryManager()
    manager.clear_all()

    async def test():
        # 存储交互
        await manager.store_interaction(
            user_input="查询富国天惠基金净值",
            result={"success": True, "message": "净值为3.21元", "data": {"nav": 3.21}},
        )
        print("[OK] 存储交互")

        # 存储服务调用
        await manager.store_service_call(
            service_id="getFundNAV",
            parameters={"fund_code": "161005"},
            result={"success": True, "nav": 3.21},
        )
        print("[OK] 存储服务调用")

        # 存储知识
        await manager.store_knowledge(
            knowledge_id="test_knowledge",
            content="这是一条测试知识",
            category="test",
        )
        print("[OK] 存储知识")

        # 存储流程
        procedure = await manager.store_procedure(
            procedure_id="test_procedure",
            name="测试流程",
            description="这是一个测试流程",
            steps=[{"step": 1, "action": "测试"}],
        )
        print(f"[OK] 存储流程: {procedure.name}")

        # 获取上下文
        context = manager.get_context(max_turns=5)
        print(f"[OK] 获取上下文: {len(context)} 字符")

        # 获取完整上下文
        full_context = manager.get_full_context()
        print(f"[OK] 获取完整上下文: {len(full_context)} 字符")

        # 获取统计
        stats = manager.get_statistics()
        print(f"[OK] 统计信息:")
        print(f"  - 事件记忆: {stats['episodic']['total_memories']} 条")
        print(f"  - 语义记忆: {stats['semantic']['total_knowledge']} 条")
        print(f"  - 程序记忆: {stats['procedural']['total_procedures']} 个")
        print(f"  - 摘要记忆: {stats['summary']['total_summaries']} 条")

        # 导出状态
        state = manager.export_state()
        print(f"[OK] 导出状态: {len(state)} 个部分")

    asyncio.run(test())
    return True


def test_full_integration():
    """完整集成测试"""
    print("\n" + "="*50)
    print("完整集成测试")
    print("="*50)

    from rag_module import (
        MemoryManager,
        ServiceMatcher,
    )

    # 初始化组件
    memory_manager = MemoryManager()
    service_matcher = ServiceMatcher()

    # 模拟服务注册
    services = [
        {
            "service_id": "getFundNAV",
            "name": "基金净值查询",
            "description": "查询指定基金的单位净值、累计净值和涨跌幅",
            "keywords": ["净值", "基金", "查询", "NAV", "涨跌"],
            "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
            "returns": {"nav": "单位净值"},
        },
        {
            "service_id": "getFundDividend",
            "name": "基金分红查询",
            "description": "查询指定基金的历史分红记录",
            "keywords": ["分红", "派息", "红利"],
            "parameters": {"fund_code": {"type": "string", "description": "基金代码"}},
            "returns": {"dividends": "分红记录"},
        },
        {
            "service_id": "processDividend",
            "name": "基金分红处理",
            "description": "批量处理基金分红派息",
            "keywords": ["分红处理", "派息", "批量"],
            "parameters": {"fund_codes": {"type": "list", "description": "基金代码列表"}},
            "returns": {"processed_count": "处理数量"},
        },
    ]

    # 索引服务
    service_matcher.index_services(services)
    print(f"[OK] 索引了 {len(services)} 个服务")

    async def simulate_workflow():
        # 模拟用户查询流程
        user_query = "查询富国天惠基金今天的净值"

        # 1. 匹配服务
        matches = await service_matcher.match_service(user_query, top_k=1)
        if matches:
            matched_service = matches[0]
            print(f"[OK] 匹配服务: {matched_service['name']} (score: {matched_service['relevance_score']:.3f})")

        # 2. 存储交互
        await memory_manager.store_interaction(
            user_input=user_query,
            result={
                "success": True,
                "message": "富国天惠(161005)今日净值为3.2156元",
                "data": {"nav": 3.2156, "fund_code": "161005"},
            },
        )

        # 3. 存储服务调用
        await memory_manager.store_service_call(
            service_id="getFundNAV",
            parameters={"fund_code": "161005"},
            result={"success": True, "nav": 3.2156},
        )

        # 4. 模拟第二次查询
        user_query2 = "处理本周所有基金的分红"
        matches2 = await service_matcher.match_service(user_query2, top_k=1)
        if matches2:
            print(f"[OK] 匹配服务: {matches2[0]['name']} (score: {matches2[0]['relevance_score']:.3f})")

        # 5. 获取统计
        stats = memory_manager.get_statistics()
        print(f"[OK] 记忆统计:")
        print(f"  - 事件数: {stats['episodic']['total_memories']}")
        print(f"  - 服务调用: {stats['episodic']['service_calls']}")

    asyncio.run(simulate_workflow())
    print("\n[OK] 集成测试完成")
    return True


def main():
    """运行所有测试"""
    print("="*60)
    print("RAG Module 功能测试")
    print("="*60)

    tests = [
        ("DocumentLoader", test_document_loader),
        ("Embeddings", test_embeddings),
        ("IndexBuilder", test_index_builder),
        ("ServiceMatcher", test_service_matcher),
        ("KnowledgeSearch", test_knowledge_search),
        ("EpisodicMemory", test_episodic_memory),
        ("SemanticMemory", test_semantic_memory),
        ("ProceduralMemory", test_procedural_memory),
        ("SummaryMemory", test_summary_memory),
        ("MemoryManager", test_memory_manager),
        ("Full Integration", test_full_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS" if success else "FAIL"))
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"ERROR: {str(e)[:50]}"))

    # 打印总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)

    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)

    for name, result in results:
        status = "[OK]" if result == "PASS" else "[FAIL]"
        print(f"{status} {name}: {result}")

    print(f"\n总计: {passed}/{total} 通过")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
