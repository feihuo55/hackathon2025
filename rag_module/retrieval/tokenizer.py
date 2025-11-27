"""
中文分词和同义词扩展
"""
from typing import Optional
import re

# 延迟导入jieba
_jieba = None

def _get_jieba():
    """延迟加载jieba"""
    global _jieba
    if _jieba is None:
        try:
            import jieba
            jieba.setLogLevel(20)  # 关闭jieba日志
            _jieba = jieba
        except ImportError:
            pass
    return _jieba


# 金融领域同义词表（中英双语）
SYNONYMS = {
    # 净值相关 (NAV)
    "净值": ["NAV", "nav", "单位净值", "累计净值", "基金净值", "net value"],
    "NAV": ["净值", "单位净值", "累计净值", "net asset value"],
    "net value": ["净值", "NAV", "nav"],

    # 分红相关 (Dividend)
    "分红": ["派息", "红利", "分配", "派发", "dividend", "distribution"],
    "派息": ["分红", "红利", "分配", "dividend"],
    "红利": ["分红", "派息", "分配", "dividend"],
    "dividend": ["分红", "派息", "红利", "distribution"],
    "distribution": ["分红", "dividend", "派发"],

    # 查询相关 (Query)
    "查询": ["查看", "获取", "搜索", "检索", "查", "看", "query", "search", "check"],
    "获取": ["查询", "查看", "得到", "get", "fetch"],
    "query": ["查询", "搜索", "检索", "search"],
    "search": ["查询", "搜索", "query", "find"],
    "check": ["查看", "查询", "检查"],

    # 处理相关 (Process)
    "处理": ["执行", "运行", "操作", "办理", "process", "handle"],
    "执行": ["处理", "运行", "操作", "execute", "run"],
    "process": ["处理", "执行", "handle"],
    "handle": ["处理", "process"],

    # 基金相关 (Fund)
    "基金": ["fund", "产品", "理财"],
    "fund": ["基金", "产品"],
    "funds": ["基金", "fund", "基金列表"],

    # 列表相关 (List)
    "列表": ["清单", "名单", "全部", "所有", "list", "all"],
    "所有": ["全部", "列表", "清单", "all"],
    "list": ["列表", "清单", "all"],
    "all": ["所有", "全部", "list"],

    # 历史相关 (History)
    "历史": ["记录", "过往", "以前", "history", "record"],
    "记录": ["历史", "日志", "record", "history"],
    "history": ["历史", "记录", "past"],
    "record": ["记录", "历史", "history"],

    # 持仓相关 (Holdings)
    "持仓": ["holdings", "持有", "仓位", "positions"],
    "holdings": ["持仓", "持有", "positions"],
    "positions": ["持仓", "holdings", "仓位"],

    # 风险相关 (Risk)
    "风险": ["risk", "波动", "风险指标"],
    "risk": ["风险", "波动"],
    "volatility": ["波动", "波动率", "风险"],

    # 收益相关 (Return)
    "收益": ["return", "回报", "盈利", "profit"],
    "return": ["收益", "回报", "profit"],
    "profit": ["收益", "盈利", "return"],

    # 经理相关 (Manager)
    "经理": ["manager", "管理人", "基金经理"],
    "manager": ["经理", "基金经理", "管理人"],

    # 对比相关 (Compare)
    "对比": ["compare", "比较", "PK"],
    "compare": ["对比", "比较", "comparison"],
    "comparison": ["对比", "compare"],

    # 订阅相关 (Subscribe)
    "订阅": ["subscribe", "提醒", "通知"],
    "subscribe": ["订阅", "alert"],
    "alert": ["提醒", "通知", "预警"],
    "notification": ["通知", "提醒", "alert"],

    # 显示相关 (Show)
    "显示": ["show", "展示", "display"],
    "show": ["显示", "展示", "display"],
    "display": ["显示", "show"],
}

# 构建反向同义词映射
REVERSE_SYNONYMS = {}
for key, values in SYNONYMS.items():
    for v in values:
        if v not in REVERSE_SYNONYMS:
            REVERSE_SYNONYMS[v] = set()
        REVERSE_SYNONYMS[v].add(key)
        REVERSE_SYNONYMS[v].update(values)


class ChineseTokenizer:
    """中文分词器"""

    def __init__(self, use_jieba: bool = True):
        """
        初始化分词器

        Args:
            use_jieba: 是否使用jieba分词
        """
        self.use_jieba = use_jieba
        self._jieba = None

        # 金融领域专有词汇
        self.custom_words = [
            "基金净值", "单位净值", "累计净值", "分红派息",
            "富国天惠", "易方达", "华夏回报", "南方绩优", "博时主题",
            "基金代码", "涨跌幅", "分红处理", "批量处理",
        ]

    def _ensure_jieba(self):
        """确保jieba已加载"""
        if self._jieba is None and self.use_jieba:
            self._jieba = _get_jieba()
            if self._jieba:
                # 添加自定义词汇
                for word in self.custom_words:
                    self._jieba.add_word(word)
        return self._jieba

    def tokenize(self, text: str) -> list[str]:
        """
        分词

        Args:
            text: 输入文本

        Returns:
            分词结果列表
        """
        if not text:
            return []

        jieba = self._ensure_jieba()

        if jieba:
            # 使用jieba精确模式分词
            tokens = list(jieba.cut(text, cut_all=False))
        else:
            # 回退到简单分词
            tokens = self._simple_tokenize(text)

        # 过滤空白和标点
        tokens = [t.strip() for t in tokens if t.strip() and len(t.strip()) > 0]

        return tokens

    def _simple_tokenize(self, text: str) -> list[str]:
        """简单分词（不使用jieba时的回退方案）"""
        # 按空格、标点分割
        tokens = re.split(r'[\s,，。！？!?\-_/\\]+', text)

        # 对中文进行字符级分割（简化处理）
        result = []
        for token in tokens:
            if re.match(r'^[\u4e00-\u9fa5]+$', token):
                # 纯中文，尝试按2-4字符分割
                if len(token) <= 4:
                    result.append(token)
                else:
                    # 分割成2-3字符的词
                    for i in range(0, len(token), 2):
                        result.append(token[i:i+2])
            else:
                result.append(token)

        return result

    def tokenize_for_search(self, text: str) -> list[str]:
        """
        为搜索优化的分词（包含同义词扩展）

        Args:
            text: 输入文本

        Returns:
            扩展后的词列表
        """
        tokens = self.tokenize(text)
        expanded = set(tokens)

        # 添加同义词
        for token in tokens:
            token_lower = token.lower()
            if token_lower in REVERSE_SYNONYMS:
                expanded.update(REVERSE_SYNONYMS[token_lower])
            if token in SYNONYMS:
                expanded.update(SYNONYMS[token])

        return list(expanded)


def expand_synonyms(word: str) -> list[str]:
    """
    扩展同义词

    Args:
        word: 原词

    Returns:
        同义词列表（包含原词）
    """
    result = {word, word.lower()}

    word_lower = word.lower()
    if word_lower in REVERSE_SYNONYMS:
        result.update(REVERSE_SYNONYMS[word_lower])
    if word in SYNONYMS:
        result.update(SYNONYMS[word])

    return list(result)


def calculate_text_similarity(text1: str, text2: str, tokenizer: Optional[ChineseTokenizer] = None) -> float:
    """
    计算两段文本的相似度

    Args:
        text1: 文本1
        text2: 文本2
        tokenizer: 分词器

    Returns:
        相似度分数 (0-1)
    """
    if not tokenizer:
        tokenizer = ChineseTokenizer()

    tokens1 = set(tokenizer.tokenize_for_search(text1.lower()))
    tokens2 = set(tokenizer.tokenize_for_search(text2.lower()))

    if not tokens1 or not tokens2:
        return 0.0

    # Jaccard相似度
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


# 全局分词器实例
chinese_tokenizer = ChineseTokenizer()
