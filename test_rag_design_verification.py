"""
RAG模块设计符合性验证测试
验证RAG模块是否符合设计要求
"""
import asyncio
import sys
import io
import json
import os
from datetime import datetime

# 修复Windows控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DesignVerificationReport:
    """设计验证报告"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_result(self, category: str, test_name: str, passed: bool, details: str = "", warning: bool = False):
        status = "PASS" if passed else ("WARN" if warning else "FAIL")
        self.results.append({
            "category": category,
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        elif warning:
            self.warnings += 1
        else:
            self.failed += 1

    def print_report(self):
        print("\n" + "=" * 80)
        print("   RAG模块设计符合性验证报告")
        print("=" * 80)

        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        for cat, tests in categories.items():
            print(f"\n{'─' * 40}")
            print(f"  {cat}")
            print(f"{'─' * 40}")
            for t in tests:
                icon = "✓" if t["status"] == "PASS" else ("⚠" if t["status"] == "WARN" else "✗")
                print(f"  {icon} {t['test']}: {t['status']}")
                if t["details"]:
                    print(f"      {t['details']}")

        print("\n" + "=" * 80)
        total = self.passed + self.failed + self.warnings
        print(f"  总计: {total} 项测试")
        print(f"  通过: {self.passed} | 失败: {self.failed} | 警告: {self.warnings}")
        print(f"  符合率: {self.passed / total * 100:.1f}%" if total > 0 else "  无测试")
        print("=" * 80)


async def verify_module_structure(report: DesignVerificationReport):
    """验证模块结构"""
    print("\n>>> 验证模块结构...")

    # 检查核心模块是否存在
    try:
        from rag_module import (
            ServiceMatcher,
            MemoryManager,
            EpisodicMemory,
            SemanticMemory,
            ProceduralMemory,
            SummaryMemory,
        )
        report.add_result("模块结构", "核心类导入", True, "ServiceMatcher, MemoryManager, 四层记忆系统")
    except ImportError as e:
        report.add_result("模块结构", "核心类导入", False, str(e))

    # 检查工具模块
    try:
        from rag_module import (
            RetryConfig,
            with_retry,
            with_async_retry,
            CircuitBreaker,
            RAGError,
        )
        report.add_result("模块结构", "工具类导入", True, "重试机制, 熔断器, 异常类")
    except ImportError as e:
        report.add_result("模块结构", "工具类导入", False, str(e))

    # 检查分词器
    try:
        from rag_module.retrieval.tokenizer import ChineseTokenizer, expand_synonyms, SYNONYMS
        report.add_result("模块结构", "中文分词器", True, f"同义词表: {len(SYNONYMS)} 条")
    except ImportError as e:
        report.add_result("模块结构", "中文分词器", False, str(e))


async def verify_service_matcher(report: DesignVerificationReport):
    """验证服务匹配器"""
    print("\n>>> 验证服务匹配器...")

    from rag_module.retrieval.service_matcher import ServiceMatcher
    from rag_module.demo_data import DEMO_SERVICES, TEST_QUERIES

    matcher = ServiceMatcher()
    matcher.index_services(DEMO_SERVICES)

    # 验证索引功能
    indexed_count = matcher.get_indexed_count()
    report.add_result("服务匹配", "服务索引", indexed_count > 0, f"索引了 {indexed_count} 个服务")

    # 验证中文查询
    chinese_queries = [q for q in TEST_QUERIES if any('\u4e00' <= c <= '\u9fff' for c in q[0])]
    chinese_correct = 0
    for query, expected in chinese_queries[:10]:
        matches = await matcher.match_service(query, top_k=1)
        if matches and matches[0]["service_id"] == expected:
            chinese_correct += 1
    chinese_accuracy = chinese_correct / min(10, len(chinese_queries)) * 100
    report.add_result("服务匹配", "中文查询匹配", chinese_accuracy >= 40,
                      f"准确率: {chinese_accuracy:.1f}%", warning=(chinese_accuracy < 50))

    # 验证英文查询
    english_queries = [q for q in TEST_QUERIES if not any('\u4e00' <= c <= '\u9fff' for c in q[0])]
    english_correct = 0
    for query, expected in english_queries[:10]:
        matches = await matcher.match_service(query, top_k=1)
        if matches and matches[0]["service_id"] == expected:
            english_correct += 1
    english_accuracy = english_correct / min(10, len(english_queries)) * 100
    report.add_result("服务匹配", "英文查询匹配", english_accuracy >= 50,
                      f"准确率: {english_accuracy:.1f}%", warning=(english_accuracy < 70))

    # 验证匹配解释功能
    result = await matcher.match_with_explanation("查询基金净值", top_k=3)
    has_explanation = "query_tokens" in result and "matches" in result
    report.add_result("服务匹配", "匹配解释功能", has_explanation,
                      f"分词数: {len(result.get('query_tokens', []))}")

    # 验证阈值过滤
    best = await matcher.find_best_match("这是一个无关的查询xyz", threshold=0.5)
    report.add_result("服务匹配", "阈值过滤", best is None,
                      "无关查询正确返回None" if best is None else f"错误匹配: {best}")


async def verify_four_layer_memory(report: DesignVerificationReport):
    """验证四层记忆系统"""
    print("\n>>> 验证四层记忆系统...")

    from rag_module import MemoryManager, EpisodicMemory, SemanticMemory, ProceduralMemory, SummaryMemory

    # ===== 1. 事件记忆 (Episodic Memory) =====
    episodic = EpisodicMemory(max_entries=100)

    # 测试添加和获取
    episodic.add("user_input", {"text": "测试输入"}, {"source": "test"})
    episodic.add("agent_response", {"text": "测试响应"}, {"source": "test"})
    report.add_result("事件记忆", "添加/获取事件", episodic.count() == 2, f"事件数: {episodic.count()}")

    # 测试按类型获取
    user_inputs = episodic.get_by_type("user_input")
    report.add_result("事件记忆", "按类型筛选", len(user_inputs) == 1, f"用户输入数: {len(user_inputs)}")

    # 测试对话历史
    history = episodic.get_conversation_history()
    report.add_result("事件记忆", "对话历史转换", len(history) == 2,
                      f"历史条数: {len(history)}, 角色: {[h['role'] for h in history]}")

    # 测试搜索
    search_results = episodic.search("测试")
    report.add_result("事件记忆", "关键词搜索", len(search_results) == 2, f"搜索结果: {len(search_results)}")

    # ===== 2. 语义记忆 (Semantic Memory) =====
    semantic = SemanticMemory(collection_name="test_verification")
    semantic.clear()

    # 测试存储知识
    semantic.store("kb_001", "基金净值是基金资产净值的简称", "concept", {"tags": "净值,基金"})
    semantic.store("kb_002", "分红是基金将收益分配给投资者", "concept", {"tags": "分红,收益"})
    report.add_result("语义记忆", "知识存储", semantic.count() == 2, f"知识条数: {semantic.count()}")

    # 测试检索
    results = semantic.retrieve("什么是基金净值", top_k=2)
    report.add_result("语义记忆", "语义检索", len(results) > 0,
                      f"检索结果数: {len(results)}" + (f", 最佳: {results[0]['knowledge_id']}" if results else ""))

    # ===== 3. 程序记忆 (Procedural Memory) =====
    procedural = ProceduralMemory(enable_persistence=False)

    # 测试存储流程
    proc = procedural.store_procedure(
        procedure_id="test_proc",
        name="测试流程",
        description="用于验证的测试流程",
        steps=[
            {"step": 1, "action": "步骤一"},
            {"step": 2, "action": "步骤二"},
        ]
    )
    report.add_result("程序记忆", "流程存储", proc is not None, f"流程: {proc.name}, 步骤数: {len(proc.steps)}")

    # 测试执行记录
    procedural.record_execution("test_proc", success=True, execution_time=0.5)
    procedural.record_execution("test_proc", success=True, execution_time=0.3)
    procedural.record_execution("test_proc", success=False, execution_time=0.8)
    proc = procedural.get_procedure("test_proc")
    report.add_result("程序记忆", "执行统计", proc.success_count == 2 and proc.failure_count == 1,
                      f"成功: {proc.success_count}, 失败: {proc.failure_count}, 成功率: {proc.success_rate:.1%}")

    # ===== 4. 摘要记忆 (Summary Memory) =====
    summary = SummaryMemory(enable_persistence=False)

    # 测试对话摘要
    conversation = [
        {"role": "user", "content": "查询基金净值"},
        {"role": "assistant", "content": "富国天惠今日净值3.21元"},
        {"role": "user", "content": "有分红吗"},
        {"role": "assistant", "content": "最近一次分红0.5元"},
    ]
    s = summary.summarize_conversation(conversation)
    report.add_result("摘要记忆", "对话摘要生成", s is not None and s.source_count == 4,
                      f"摘要ID: {s.summary_id}, 来源数: {s.source_count}")

    # 测试摘要搜索
    search = summary.search("净值")
    report.add_result("摘要记忆", "摘要搜索", len(search) > 0, f"搜索到: {len(search)} 条摘要")

    # ===== 5. 统一记忆管理器 =====
    manager = MemoryManager()

    # 测试交互存储
    await manager.store_interaction("用户查询测试", {"success": True, "message": "测试响应"})
    stats = manager.get_statistics()
    report.add_result("记忆管理器", "交互存储", stats["episodic"]["total_memories"] >= 2,
                      f"事件数: {stats['episodic']['total_memories']}")

    # 测试上下文获取
    context = manager.get_context(max_turns=5)
    report.add_result("记忆管理器", "上下文获取", len(context) > 0, f"上下文长度: {len(context)} 字符")

    # 测试状态导出
    state = manager.export_state()
    has_keys = all(k in state for k in ["episodic", "procedural", "summary", "session_data"])
    report.add_result("记忆管理器", "状态导出", has_keys, f"包含键: {list(state.keys())}")


async def verify_bilingual_support(report: DesignVerificationReport):
    """验证中英文双语支持"""
    print("\n>>> 验证中英文双语支持...")

    from rag_module.retrieval.tokenizer import ChineseTokenizer, expand_synonyms, SYNONYMS

    tokenizer = ChineseTokenizer()

    # 验证同义词表双语覆盖
    chinese_keys = [k for k in SYNONYMS.keys() if any('\u4e00' <= c <= '\u9fff' for c in k)]
    english_keys = [k for k in SYNONYMS.keys() if k.isascii()]
    report.add_result("双语支持", "同义词表", len(chinese_keys) > 10 and len(english_keys) > 10,
                      f"中文词: {len(chinese_keys)}, 英文词: {len(english_keys)}")

    # 验证中文分词
    cn_tokens = tokenizer.tokenize("查询基金净值")
    report.add_result("双语支持", "中文分词", len(cn_tokens) > 0, f"分词结果: {cn_tokens}")

    # 验证英文分词
    en_tokens = tokenizer.tokenize("Query fund NAV")
    report.add_result("双语支持", "英文分词", len(en_tokens) > 0, f"分词结果: {en_tokens}")

    # 验证同义词扩展 - 中文
    cn_synonyms = expand_synonyms("净值")
    has_english = any(s.isascii() for s in cn_synonyms if s)
    report.add_result("双语支持", "中文→英文同义词", has_english,
                      f"'净值' 扩展: {[s for s in cn_synonyms if s.isascii()][:5]}")

    # 验证同义词扩展 - 英文
    en_synonyms = expand_synonyms("dividend")
    def is_chinese(s):
        return any('\u4e00' <= c <= '\u9fff' for c in s)
    has_chinese = any(is_chinese(s) for s in en_synonyms if s)
    chinese_syns = [s for s in en_synonyms if s and is_chinese(s)][:5]
    report.add_result("双语支持", "英文→中文同义词", has_chinese,
                      f"'dividend' 扩展: {chinese_syns}")

    # 验证搜索分词扩展
    search_tokens = set(tokenizer.tokenize_for_search("NAV"))
    has_cross_lingual = "净值" in search_tokens or "net value" in search_tokens
    report.add_result("双语支持", "搜索词跨语言扩展", has_cross_lingual,
                      f"'NAV' 扩展后包含: {list(search_tokens)[:8]}")


async def verify_persistence(report: DesignVerificationReport):
    """验证持久化功能"""
    print("\n>>> 验证持久化功能...")

    from rag_module import ProceduralMemory, SummaryMemory, MemoryPersistence, get_persistence

    # 验证持久化管理器
    persistence = get_persistence()
    report.add_result("持久化", "持久化管理器", persistence is not None,
                      f"存储路径: {persistence.storage_dir if persistence else 'N/A'}")

    # 验证程序记忆持久化
    proc_memory = ProceduralMemory(enable_persistence=True)
    proc_memory.store_procedure(
        procedure_id="persist_test",
        name="持久化测试流程",
        description="测试持久化",
        steps=[{"step": 1, "action": "test"}]
    )
    proc_memory.record_execution("persist_test", success=True)

    # 导出和恢复
    exported = proc_memory.to_dict()
    new_proc = ProceduralMemory(enable_persistence=False)
    new_proc.from_dict(exported)
    recovered = new_proc.get_procedure("persist_test")
    report.add_result("持久化", "程序记忆导出/恢复",
                      recovered is not None and recovered.success_count == 1,
                      f"恢复流程: {recovered.name if recovered else 'None'}")

    # 验证摘要记忆持久化
    sum_memory = SummaryMemory(enable_persistence=True)
    sum_memory.summarize_conversation([
        {"role": "user", "content": "测试"},
        {"role": "assistant", "content": "响应"},
    ])

    exported_sum = sum_memory.to_list()
    report.add_result("持久化", "摘要记忆导出", len(exported_sum) > 0,
                      f"导出摘要数: {len(exported_sum)}")


async def verify_error_handling(report: DesignVerificationReport):
    """验证错误处理"""
    print("\n>>> 验证错误处理...")

    from rag_module import RAGError, IndexingError, RetrievalError, ServiceMatchError
    from rag_module import RetryConfig, CircuitBreaker

    # 验证异常类层次
    is_hierarchy = (
        issubclass(IndexingError, RAGError) and
        issubclass(RetrievalError, RAGError) and
        issubclass(ServiceMatchError, RAGError)
    )
    report.add_result("错误处理", "异常类层次", is_hierarchy,
                      "RAGError <- IndexingError, RetrievalError, ServiceMatchError")

    # 验证重试配置 (使用正确的参数名: max_attempts, exponential_base)
    config = RetryConfig(max_attempts=3, initial_delay=0.1, max_delay=1.0, exponential_base=2.0)
    report.add_result("错误处理", "重试配置",
                      config.max_attempts == 3 and config.exponential_base == 2.0,
                      f"最大重试: {config.max_attempts}, 退避因子: {config.exponential_base}")

    # 验证熔断器
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)
    breaker.record_failure()
    breaker.record_failure()
    report.add_result("错误处理", "熔断器", breaker._failure_count == 2,
                      f"失败计数: {breaker._failure_count}, 阈值: {breaker.failure_threshold}")


async def verify_integration(report: DesignVerificationReport):
    """验证集成场景"""
    print("\n>>> 验证集成场景...")

    from rag_module import ServiceMatcher, MemoryManager
    from rag_module.demo_data import DEMO_SERVICES

    # 模拟完整交互流程
    matcher = ServiceMatcher()
    matcher.index_services(DEMO_SERVICES)
    memory = MemoryManager()

    # 场景1: 用户查询 -> 服务匹配 -> 存储交互
    user_query = "查询基金161005的净值"
    matches = await matcher.match_service(user_query, top_k=1)

    if matches:
        # 模拟服务调用
        result = {
            "success": True,
            "message": f"基金161005净值为3.21元",
            "data": {"nav": 3.21}
        }
        await memory.store_interaction(user_query, result)
        await memory.store_service_call(
            service_id=matches[0]["service_id"],
            parameters={"fund_code": "161005"},
            result=result
        )

    # 验证流程完整性
    stats = memory.get_statistics()
    integration_ok = (
        stats["episodic"]["total_memories"] >= 2 and
        len(matches) > 0
    )
    report.add_result("集成测试", "完整交互流程", integration_ok,
                      f"匹配服务: {matches[0]['name'] if matches else 'None'}, " +
                      f"记忆数: {stats['episodic']['total_memories']}")

    # 场景2: 多轮对话上下文
    queries = [
        ("这个基金有分红吗", {"success": True, "message": "最近分红0.5元"}),
        ("基金经理是谁", {"success": True, "message": "朱少醒"}),
    ]
    for q, r in queries:
        await memory.store_interaction(q, r)

    context = memory.get_context(max_turns=5)
    report.add_result("集成测试", "多轮对话上下文", len(context) > 50,
                      f"上下文长度: {len(context)} 字符")

    # 场景3: 统计信息完整性
    final_stats = memory.get_statistics()
    stats_complete = all(k in final_stats for k in ["episodic", "semantic", "procedural", "summary"])
    report.add_result("集成测试", "统计信息完整", stats_complete,
                      f"事件: {final_stats['episodic']['total_memories']}, " +
                      f"服务调用: {final_stats['episodic']['service_calls']}")


async def main():
    """运行所有验证测试"""
    print("\n" + "=" * 80)
    print("   托管银行AI自动化平台 - RAG模块设计符合性验证")
    print("=" * 80)
    print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    report = DesignVerificationReport()

    # 执行所有验证
    test_funcs = [
        ("模块结构验证", verify_module_structure),
        ("服务匹配器验证", verify_service_matcher),
        ("四层记忆系统验证", verify_four_layer_memory),
        ("中英文双语支持验证", verify_bilingual_support),
        ("持久化功能验证", verify_persistence),
        ("错误处理验证", verify_error_handling),
        ("集成场景验证", verify_integration),
    ]

    for name, func in test_funcs:
        try:
            await func(report)
        except Exception as e:
            report.add_result(name, "执行异常", False, str(e))
            import traceback
            traceback.print_exc()

    # 打印报告
    report.print_report()

    # 返回结果
    return report.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
