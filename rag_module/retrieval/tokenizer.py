"""
Bilingual Tokenizer and Synonym Expansion
中英双语分词器和同义词扩展

This module provides:
- BilingualTokenizer: Enhanced tokenizer supporting both Chinese and English
- Synonym expansion for financial domain terms
- Language detection and automatic handling
- Text similarity calculation

本模块提供：
- 双语分词器：支持中英文的增强分词器
- 金融领域同义词扩展
- 语言检测和自动处理
- 文本相似度计算
"""
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

# Lazy import jieba / 延迟导入jieba
_jieba = None


def _get_jieba():
    """Lazy load jieba tokenizer / 延迟加载jieba分词器"""
    global _jieba
    if _jieba is None:
        try:
            import jieba
            jieba.setLogLevel(20)
            _jieba = jieba
        except ImportError:
            logger.warning("jieba not installed, using simple tokenizer fallback")
    return _jieba


# Financial domain synonyms (Chinese-English bilingual) / 金融领域同义词表
SYNONYMS = {
    # NAV / 净值相关
    "净值": ["NAV", "nav", "单位净值", "累计净值", "基金净值", "net value", "net asset value"],
    "NAV": ["净值", "单位净值", "累计净值", "net asset value", "net value"],
    "net value": ["净值", "NAV", "nav", "net asset value"],
    "net asset value": ["NAV", "净值", "net value"],

    # Dividend / 分红相关
    "分红": ["派息", "红利", "分配", "派发", "dividend", "distribution", "payout"],
    "派息": ["分红", "红利", "分配", "dividend", "coupon"],
    "dividend": ["分红", "派息", "红利", "distribution", "payout"],
    "distribution": ["分红", "dividend", "派发", "payout"],

    # Query / 查询相关
    "查询": ["查看", "获取", "搜索", "检索", "query", "search", "check", "lookup", "find", "retrieve"],
    "获取": ["查询", "查看", "得到", "get", "fetch", "retrieve", "obtain"],
    "query": ["查询", "搜索", "检索", "search", "lookup", "find"],
    "search": ["查询", "搜索", "query", "find", "lookup"],
    "check": ["查看", "查询", "检查", "verify", "inspect"],
    "find": ["查找", "查询", "search", "lookup", "locate"],
    "get": ["获取", "得到", "查询", "fetch", "retrieve"],

    # Process / 处理相关
    "处理": ["执行", "运行", "操作", "办理", "process", "handle", "execute", "perform"],
    "执行": ["处理", "运行", "操作", "execute", "run", "perform"],
    "process": ["处理", "执行", "handle", "execute"],
    "handle": ["处理", "process", "manage"],
    "execute": ["执行", "运行", "process", "run", "perform"],

    # Fund / 基金相关
    "基金": ["fund", "产品", "理财", "investment fund", "mutual fund"],
    "fund": ["基金", "产品", "funds"],
    "funds": ["基金", "fund", "基金列表", "fund list"],
    "mutual fund": ["共同基金", "基金", "fund"],
    "portfolio": ["投资组合", "组合", "持仓"],

    # List / 列表相关
    "列表": ["清单", "名单", "全部", "所有", "list", "all", "catalog"],
    "所有": ["全部", "列表", "清单", "all", "entire", "complete"],
    "list": ["列表", "清单", "all", "catalog"],
    "all": ["所有", "全部", "list", "entire", "complete"],

    # History / 历史相关
    "历史": ["记录", "过往", "以前", "history", "record", "past", "historical"],
    "记录": ["历史", "日志", "record", "history", "log"],
    "history": ["历史", "记录", "past", "historical"],
    "record": ["记录", "历史", "history", "log", "entry"],

    # Holdings / 持仓相关
    "持仓": ["holdings", "持有", "仓位", "positions", "portfolio"],
    "holdings": ["持仓", "持有", "positions", "assets"],
    "positions": ["持仓", "holdings", "仓位"],
    "assets": ["资产", "holdings", "持仓"],

    # Risk / 风险相关
    "风险": ["risk", "波动", "风险指标"],
    "risk": ["风险", "波动", "exposure"],
    "volatility": ["波动", "波动率", "风险", "fluctuation"],
    "风险评估": ["risk assessment", "risk analysis"],
    "drawdown": ["回撤", "最大回撤", "跌幅"],

    # Return / 收益相关
    "收益": ["return", "回报", "盈利", "profit", "yield", "income", "gain"],
    "return": ["收益", "回报", "profit", "yield"],
    "profit": ["收益", "盈利", "return", "gain"],
    "yield": ["收益率", "回报率", "return"],
    "performance": ["业绩", "表现", "收益"],

    # Manager / 经理相关
    "经理": ["manager", "管理人", "基金经理"],
    "manager": ["经理", "基金经理", "管理人", "fund manager"],
    "fund manager": ["基金经理", "经理", "portfolio manager"],

    # Compare / 对比相关
    "对比": ["compare", "比较", "PK", "contrast"],
    "compare": ["对比", "比较", "comparison", "versus"],
    "benchmark": ["基准", "对标", "参照"],

    # Subscribe / 订阅相关
    "订阅": ["subscribe", "提醒", "通知", "follow"],
    "subscribe": ["订阅", "alert", "follow"],
    "alert": ["提醒", "通知", "预警", "warning", "notification"],
    "notification": ["通知", "提醒", "alert", "notice"],

    # Show / 显示相关
    "显示": ["show", "展示", "display", "present"],
    "show": ["显示", "展示", "display", "present", "view"],
    "display": ["显示", "show", "展示"],
    "view": ["查看", "显示", "show", "see"],

    # Analysis / 分析相关
    "分析": ["analysis", "analyze", "研究", "评估"],
    "analysis": ["分析", "analyze", "研究"],
    "evaluate": ["评估", "评价", "analysis"],

    # Report / 报告相关
    "报告": ["report", "报表", "statement"],
    "report": ["报告", "报表", "statement"],

    # Transaction / 交易相关
    "交易": ["transaction", "trade", "买卖"],
    "transaction": ["交易", "trade", "deal"],
    "purchase": ["购买", "申购", "buy"],
    "申购": ["purchase", "subscription", "买入"],
    "赎回": ["redemption", "redeem", "卖出"],
    "buy": ["买入", "购买", "purchase"],
    "sell": ["卖出", "赎回", "redeem"],

    # Account / 账户相关
    "账户": ["account", "户头", "账号"],
    "account": ["账户", "账号"],
    "balance": ["余额", "结余", "账户余额"],

    # Status / 状态相关
    "状态": ["status", "state", "情况"],
    "status": ["状态", "state"],
    "pending": ["待处理", "等待", "挂起"],
    "completed": ["已完成", "完成", "结束"],

    # Amount / 金额相关
    "金额": ["amount", "数额", "款项"],
    "amount": ["金额", "数额", "quantity"],
    "total": ["总额", "总计", "合计"],
}

# Build reverse synonym mapping / 构建反向同义词映射
REVERSE_SYNONYMS = {}
for key, values in SYNONYMS.items():
    key_lower = key.lower()
    if key_lower not in REVERSE_SYNONYMS:
        REVERSE_SYNONYMS[key_lower] = set()
    REVERSE_SYNONYMS[key_lower].add(key)
    for v in values:
        v_lower = v.lower()
        if v_lower not in REVERSE_SYNONYMS:
            REVERSE_SYNONYMS[v_lower] = set()
        REVERSE_SYNONYMS[v_lower].add(key)
        REVERSE_SYNONYMS[v_lower].update(values)

# English stop words / 英文停用词
ENGLISH_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "in", "out", "on", "off", "over", "under", "again",
    "here", "there", "where", "why", "how", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "should", "now", "i", "me", "my", "we", "our", "you", "your",
    "he", "him", "his", "she", "her", "it", "its", "they", "them", "their",
    "what", "which", "who", "this", "that", "these", "those", "am", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "would", "could", "might", "must", "shall", "of",
}

# Chinese stop words / 中文停用词
CHINESE_STOP_WORDS = {
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "着",
    "或", "一个", "没有", "我们", "你们", "他们", "这个", "那个",
    "之", "以", "于", "为", "则", "等", "但", "并", "从", "在",
    "到", "把", "被", "让", "向", "往", "由", "给", "跟", "同",
    "比", "对", "当", "如", "若", "使", "因", "所", "又", "也",
    "且", "不", "很", "太", "更", "最", "还", "只", "已", "曾",
    "将", "要", "会", "能", "可", "可以", "应", "该", "这", "那",
    "什么", "怎么", "哪", "哪个", "为什么", "如何", "多少", "几",
    "谁", "吗", "呢", "吧", "啊", "呀", "嘛", "哦", "嗯",
}


class BilingualTokenizer:
    """
    Bilingual Tokenizer supporting Chinese and English
    中英双语分词器
    """

    def __init__(self, use_jieba: bool = True, remove_stopwords: bool = False):
        """
        Initialize the tokenizer / 初始化分词器

        Args:
            use_jieba: Whether to use jieba for Chinese / 是否使用jieba中文分词
            remove_stopwords: Whether to remove stop words / 是否移除停用词
        """
        self.use_jieba = use_jieba
        self.remove_stopwords = remove_stopwords
        self._jieba = None

        # Financial domain custom words / 金融领域专有词汇
        self.chinese_custom_words = [
            "基金净值", "单位净值", "累计净值", "分红派息",
            "富国天惠", "易方达", "华夏回报", "南方绩优", "博时主题",
            "基金代码", "涨跌幅", "分红处理", "批量处理",
            "风险评估", "收益率", "投资组合", "资产配置",
            "申购赎回", "基金经理", "净值更新", "分红记录",
        ]

    def _ensure_jieba(self):
        """Ensure jieba is loaded / 确保jieba已加载"""
        if self._jieba is None and self.use_jieba:
            self._jieba = _get_jieba()
            if self._jieba:
                for word in self.chinese_custom_words:
                    self._jieba.add_word(word)
        return self._jieba

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect the primary language / 检测文本的主要语言"""
        if not text:
            return "english"

        chinese_chars = len(re.findall(r"[一-龥]", text))
        english_chars = len(re.findall(r"[a-zA-Z]", text))
        total = chinese_chars + english_chars

        if total == 0:
            return "english"

        chinese_ratio = chinese_chars / total
        if chinese_ratio > 0.7:
            return "chinese"
        elif chinese_ratio < 0.3:
            return "english"
        return "mixed"

    def tokenize(self, text: str) -> list[str]:
        """Tokenize the text / 根据文本语言进行分词"""
        if not text:
            return []

        language = self.detect_language(text)

        if language == "english":
            tokens = self._tokenize_english(text)
        elif language == "chinese":
            tokens = self._tokenize_chinese(text)
        else:
            tokens = self._tokenize_mixed(text)

        tokens = [t.strip() for t in tokens if t.strip()]

        if self.remove_stopwords:
            tokens = self._filter_stopwords(tokens)

        return tokens

    def _tokenize_english(self, text: str) -> list[str]:
        """Tokenize English text / 英文分词"""
        text = text.lower()
        tokens = re.split(r"[^a-z0-9]+", text)
        return [t for t in tokens if t]

    def _tokenize_chinese(self, text: str) -> list[str]:
        """Tokenize Chinese text / 中文分词"""
        jieba = self._ensure_jieba()
        if jieba:
            tokens = list(jieba.cut(text, cut_all=False))
        else:
            tokens = self._simple_tokenize_chinese(text)
        return tokens

    def _tokenize_mixed(self, text: str) -> list[str]:
        """Tokenize mixed Chinese-English text / 混合中英文分词"""
        tokens = []
        segments = re.split(r"([一-龥]+)", text)

        for segment in segments:
            if not segment.strip():
                continue
            if re.match(r"^[一-龥]+$", segment):
                tokens.extend(self._tokenize_chinese(segment))
            else:
                tokens.extend(self._tokenize_english(segment))
        return tokens

    def _simple_tokenize_chinese(self, text: str) -> list[str]:
        """Simple Chinese tokenization fallback / 简单中文分词回退"""
        tokens = re.split(r"[\s,，。！？!?\-_/\：:；;]+", text)
        result = []
        for token in tokens:
            if re.match(r"^[一-龥]+$", token):
                if len(token) <= 4:
                    result.append(token)
                else:
                    for i in range(0, len(token) - 1, 2):
                        result.append(token[i:i + 2])
            else:
                result.append(token)
        return result

    def _filter_stopwords(self, tokens: list[str]) -> list[str]:
        """Filter stop words / 过滤停用词"""
        return [
            t for t in tokens
            if t.lower() not in ENGLISH_STOP_WORDS
            and t not in CHINESE_STOP_WORDS
        ]

    def tokenize_for_search(self, text: str) -> list[str]:
        """Tokenize with synonym expansion / 为搜索优化的分词（包含同义词扩展）"""
        tokens = self.tokenize(text)
        expanded = set(tokens)

        for token in tokens:
            token_lower = token.lower()
            if token_lower in REVERSE_SYNONYMS:
                expanded.update(REVERSE_SYNONYMS[token_lower])
            if token in SYNONYMS:
                expanded.update(SYNONYMS[token])

        return list(expanded)

    def extract_keywords(self, text: str, top_k: int = 10) -> list[str]:
        """Extract keywords from text / 从文本中提取关键词"""
        original_setting = self.remove_stopwords
        self.remove_stopwords = True
        tokens = self.tokenize(text)
        self.remove_stopwords = original_setting

        freq = {}
        for token in tokens:
            if len(token) >= 2:
                freq[token] = freq.get(token, 0) + 1

        sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [token for token, _ in sorted_tokens[:top_k]]


# Backward compatibility alias / 向后兼容别名
ChineseTokenizer = BilingualTokenizer


def expand_synonyms(word: str) -> list[str]:
    """Expand a word to include its synonyms / 扩展同义词"""
    result = {word, word.lower()}
    word_lower = word.lower()
    if word_lower in REVERSE_SYNONYMS:
        result.update(REVERSE_SYNONYMS[word_lower])
    if word in SYNONYMS:
        result.update(SYNONYMS[word])
    return list(result)


def get_bilingual_keywords(text: str, top_k: int = 10) -> list[str]:
    """Extract bilingual keywords / 提取双语关键词"""
    tokenizer = BilingualTokenizer(remove_stopwords=True)
    return tokenizer.extract_keywords(text, top_k)


def calculate_text_similarity(
    text1: str,
    text2: str,
    tokenizer: Optional[BilingualTokenizer] = None
) -> float:
    """Calculate Jaccard similarity / 使用Jaccard系数计算相似度"""
    if not tokenizer:
        tokenizer = BilingualTokenizer()

    tokens1 = set(tokenizer.tokenize_for_search(text1.lower()))
    tokens2 = set(tokenizer.tokenize_for_search(text2.lower()))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


# Global tokenizer instances / 全局分词器实例
chinese_tokenizer = BilingualTokenizer()
bilingual_tokenizer = BilingualTokenizer()
