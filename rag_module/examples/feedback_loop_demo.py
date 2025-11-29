"""
反馈闭环系统使用示例
演示完整的用户反馈收集→学习→优化流程

运行方式：
    cd C:/Code/hackathon2025
    python -m rag_module.examples.feedback_loop_demo
"""
import asyncio
from typing import List, Dict

# 导入反馈闭环系统组件
from ..memory.feedback_memory import FeedbackMemory, FeedbackType
from ..learning.relevance_learner import RelevanceLearner
from ..learning.knowledge_refiner import KnowledgeRefiner
from ..feedback.feedback_collector import FeedbackCollector
from ..retrieval.feedback_reranker import FeedbackReranker


async def demo_feedback_collection():
    """演示反馈收集"""
    print("=" * 60)
    print("1. 反馈收集演示")
    print("=" * 60)

    # 创建反馈收集器
    collector = FeedbackCollector()

    # 模拟用户交互
    interactions = [
        {
            "query": "查询基金161005的净值",
            "response": "基金161005的最新净值是1.2345元",
            "doc_ids": ["fund_nav_001", "fund_info_161005"],
            "feedback": "positive",
        },
        {
            "query": "如何处理基金分红",
            "response": "基金分红处理流程：1. 确认分红日期 2. 计算分红金额",
            "doc_ids": ["dividend_process_001"],
            "feedback": "negative",
        },
        {
            "query": "查询基金161005的净值",
            "response": "基金161005的最新净值是1.2345元",
            "doc_ids": ["fund_nav_001", "fund_info_161005"],
            "feedback": "correction",
            "correction_text": "最新净值应该是1.2567元，数据已更新",
        },
    ]

    for i, interaction in enumerate(interactions):
        print(f"\n交互 {i + 1}:")
        print(f"  查询: {interaction['query']}")
        print(f"  回复: {interaction['response'][:50]}...")

        # 设置上下文
        collector.set_context(
            query=interaction["query"],
            response=interaction["response"],
            retrieved_doc_ids=interaction["doc_ids"],
        )

        # 收集反馈
        if interaction["feedback"] == "positive":
            feedback = await collector.thumbs_up()
            print(f"  反馈: 👍 正面反馈")
        elif interaction["feedback"] == "negative":
            feedback = await collector.thumbs_down()
            print(f"  反馈: 👎 负面反馈")
        elif interaction["feedback"] == "correction":
            feedback = await collector.submit_correction(
                interaction["correction_text"]
            )
            print(f"  反馈: ✏️ 纠正 - {interaction['correction_text'][:30]}...")

    # 显示统计
    print("\n反馈统计:")
    stats = collector.get_statistics()
    fb_stats = stats["feedback_memory"]
    print(f"  总反馈数: {fb_stats['total_feedbacks']}")
    print(f"  满意度: {fb_stats['satisfaction_rate']:.1%}")
    print(f"  纠正数: {fb_stats.get('corrections_count', 0)}")

    return collector


async def demo_relevance_learning():
    """演示相关性学习"""
    print("\n" + "=" * 60)
    print("2. 相关性学习演示")
    print("=" * 60)

    learner = RelevanceLearner()

    # 模拟学习信号
    print("\n添加学习信号...")

    # 正面反馈
    learner.add_positive_feedback(
        "查询基金净值",
        ["fund_nav_001", "fund_info_161005"]
    )
    print("  ✅ 添加正面反馈: 基金净值查询 -> fund_nav_001, fund_info_161005")

    # 负面反馈
    learner.add_negative_feedback(
        "查询基金净值",
        ["irrelevant_doc_001"]
    )
    print("  ❌ 添加负面反馈: 基金净值查询 -> irrelevant_doc_001")

    # 点击信号
    learner.add_click_signal("查询基金净值", "fund_nav_001", rank=1)
    learner.add_click_signal("查询基金净值", "fund_info_161005", rank=3)
    print("  🖱️ 添加点击信号")

    # 检查学习效果
    print("\n学习效果:")
    score1, conf1 = learner.get_relevance_score("查询基金净值", "fund_nav_001")
    score2, conf2 = learner.get_relevance_score("查询基金净值", "irrelevant_doc_001")

    print(f"  fund_nav_001: 分数={score1:.3f}, 置信度={conf1:.3f}")
    print(f"  irrelevant_doc_001: 分数={score2:.3f}, 置信度={conf2:.3f}")

    # 演示重排序
    print("\n重排序演示:")
    mock_results = [
        {"doc_id": "irrelevant_doc_001", "content": "不相关文档", "score": 0.9},
        {"doc_id": "fund_nav_001", "content": "基金净值查询服务", "score": 0.7},
        {"doc_id": "fund_info_161005", "content": "基金161005信息", "score": 0.6},
    ]

    print("  原始排序:")
    for r in mock_results:
        print(f"    {r['doc_id']}: {r['score']:.2f}")

    reranked = learner.rerank_results("查询基金净值", mock_results)

    print("  重排序后:")
    for r in reranked:
        print(f"    {r['doc_id']}: {r['final_score']:.2f} (原={r['original_score']:.2f})")

    return learner


async def demo_knowledge_refinement():
    """演示知识修正"""
    print("\n" + "=" * 60)
    print("3. 知识修正演示")
    print("=" * 60)

    refiner = KnowledgeRefiner()

    # 创建纠正动作
    print("\n创建纠正动作...")
    action = refiner.create_correction_action(
        query="查询基金161005的净值",
        original_response="基金161005的最新净值是1.2345元",
        correction_text="最新净值应该是1.2567元",
        target_doc_id="fund_nav_001",
        feedback_ids=["fb_001"],
    )

    print(f"  动作ID: {action.action_id}")
    print(f"  类型: {action.refinement_type.value}")
    print(f"  置信度: {action.confidence:.2f}")
    print(f"  优先级: {action.priority}")
    print(f"  状态: {action.status.value}")

    # 创建知识添加动作
    print("\n创建知识添加动作...")
    add_action = refiner.create_knowledge_addition(
        query="查询ETF申购费率",
        new_knowledge="ETF申购费率通常为0.1%-0.5%，具体以基金公告为准",
        category="fund_fee",
        feedback_ids=["fb_002"],
    )

    print(f"  动作ID: {add_action.action_id}")
    print(f"  类型: {add_action.refinement_type.value}")

    # 获取待审核动作
    print("\n待审核动作:")
    pending = refiner.get_pending_actions()
    for p in pending:
        print(f"  - {p.action_id}: {p.change_description[:40]}...")

    # 统计
    print("\n修正器统计:")
    stats = refiner.get_statistics()
    print(f"  总动作数: {stats['total_actions']}")
    print(f"  待审核: {stats['pending_count']}")

    return refiner


async def demo_feedback_reranking():
    """演示反馈重排序"""
    print("\n" + "=" * 60)
    print("4. 反馈重排序演示")
    print("=" * 60)

    # 创建重排序器（使用预训练的学习器）
    learner = RelevanceLearner()

    # 预先添加一些学习信号
    for _ in range(5):
        learner.add_positive_feedback("基金净值", ["doc_good_001", "doc_good_002"])
        learner.add_negative_feedback("基金净值", ["doc_bad_001"])

    reranker = FeedbackReranker(relevance_learner=learner)

    # 模拟检索结果
    mock_results = [
        {"doc_id": "doc_bad_001", "content": "不相关内容", "score": 0.95, "metadata": {}},
        {"doc_id": "doc_good_001", "content": "基金净值查询", "score": 0.80, "metadata": {}},
        {"doc_id": "doc_new_001", "content": "新文档", "score": 0.75, "metadata": {}},
        {"doc_id": "doc_good_002", "content": "净值计算方法", "score": 0.70, "metadata": {}},
    ]

    print("\n原始检索结果:")
    for r in mock_results:
        print(f"  {r['doc_id']}: score={r['score']:.2f}")

    # 重排序
    reranked = reranker.rerank("基金净值", mock_results)

    print("\n重排序后:")
    for r in reranked:
        boost_info = ""
        if r.confidence > 0:
            boost_info = f" [学习分数={r.learned_score:.2f}, 置信度={r.confidence:.2f}]"
        print(f"  {r.doc_id}: score={r.final_score:.2f}{boost_info}")

    # 获取推荐文档
    print("\n基于反馈的推荐文档:")
    recommendations = reranker.get_recommendations("基金净值", top_k=3)
    for doc_id, score in recommendations:
        print(f"  {doc_id}: {score:.2f}")

    return reranker


async def demo_full_loop():
    """演示完整闭环"""
    print("\n" + "=" * 60)
    print("5. 完整闭环演示")
    print("=" * 60)

    # 初始化所有组件
    feedback_memory = FeedbackMemory()
    relevance_learner = RelevanceLearner()
    knowledge_refiner = KnowledgeRefiner()

    collector = FeedbackCollector(
        feedback_memory=feedback_memory,
        relevance_learner=relevance_learner,
        knowledge_refiner=knowledge_refiner,
    )

    reranker = FeedbackReranker(
        relevance_learner=relevance_learner,
        feedback_memory=feedback_memory,
    )

    print("\n模拟多轮交互...")

    # 第一轮：用户查询，给出负面反馈
    print("\n[轮次1] 用户查询基金净值")
    collector.set_context(
        query="查询基金净值",
        response="基金净值为1.00",
        retrieved_doc_ids=["doc_001", "doc_002"],
    )
    await collector.thumbs_down()
    print("  用户反馈: 👎 (回复不准确)")

    # 第二轮：系统改进后，用户给出正面反馈
    print("\n[轮次2] 系统改进后再次查询")
    collector.set_context(
        query="查询基金净值",
        response="基金161005的最新净值是1.2567元，更新时间2024-01-15",
        retrieved_doc_ids=["doc_003", "doc_004"],
    )
    await collector.thumbs_up()
    print("  用户反馈: 👍 (回复准确)")

    # 第三轮：用户提供纠正
    print("\n[轮次3] 用户提供纠正信息")
    collector.set_context(
        query="查询基金分红日期",
        response="基金分红日期为每月15日",
        retrieved_doc_ids=["doc_005"],
    )
    await collector.submit_correction("分红日期应该是每季度末")
    print("  用户反馈: ✏️ 纠正 (分红日期应该是每季度末)")

    # 显示学习效果
    print("\n学习效果:")
    score1, conf1 = relevance_learner.get_relevance_score("查询基金净值", "doc_001")
    score2, conf2 = relevance_learner.get_relevance_score("查询基金净值", "doc_003")
    print(f"  doc_001 (第一轮): 分数={score1:.3f}, 置信度={conf1:.3f}")
    print(f"  doc_003 (第二轮): 分数={score2:.3f}, 置信度={conf2:.3f}")

    # 显示改进建议
    print("\n系统改进建议:")
    suggestions = collector.get_improvement_suggestions()
    for s in suggestions:
        print(f"  - [{s['priority']}] {s['description'][:50]}...")

    # 显示待处理纠正
    print("\n待处理的知识纠正:")
    corrections = collector.get_pending_corrections()
    for c in corrections:
        print(f"  - {c['description'][:50]}...")

    print("\n闭环演示完成!")


async def main():
    """主函数"""
    print("=" * 60)
    print("RAG 用户反馈闭环系统演示")
    print("=" * 60)

    await demo_feedback_collection()
    await demo_relevance_learning()
    await demo_knowledge_refinement()
    await demo_feedback_reranking()
    await demo_full_loop()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
