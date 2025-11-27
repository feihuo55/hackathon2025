"""
RAG模块演示数据
包含丰富的模拟服务、基金、知识库数据
"""

# ============================================================
# 模拟基金数据
# ============================================================

MOCK_FUNDS = [
    {
        "fund_code": "161005",
        "name": "富国天惠成长混合",
        "short_name": "富国天惠",
        "type": "混合型",
        "manager": "朱少醒",
        "company": "富国基金",
        "nav": 3.2156,
        "acc_nav": 6.8234,
        "change_pct": 2.35,
        "size": "158.23亿",
        "establish_date": "2005-11-16",
        "risk_level": "中高风险",
    },
    {
        "fund_code": "110011",
        "name": "易方达消费行业股票",
        "short_name": "易方达消费",
        "type": "股票型",
        "manager": "萧楠",
        "company": "易方达基金",
        "nav": 4.1523,
        "acc_nav": 4.1523,
        "change_pct": -0.82,
        "size": "245.67亿",
        "establish_date": "2010-08-20",
        "risk_level": "高风险",
    },
    {
        "fund_code": "000001",
        "name": "华夏成长混合",
        "short_name": "华夏成长",
        "type": "混合型",
        "manager": "王泽实",
        "company": "华夏基金",
        "nav": 1.2340,
        "acc_nav": 3.8900,
        "change_pct": 0.56,
        "size": "89.45亿",
        "establish_date": "2001-12-18",
        "risk_level": "中高风险",
    },
    {
        "fund_code": "519068",
        "name": "汇添富成长焦点混合",
        "short_name": "汇添富成长",
        "type": "混合型",
        "manager": "雷鸣",
        "company": "汇添富基金",
        "nav": 2.8765,
        "acc_nav": 5.4321,
        "change_pct": 1.23,
        "size": "112.34亿",
        "establish_date": "2007-03-12",
        "risk_level": "中高风险",
    },
    {
        "fund_code": "270002",
        "name": "广发稳健增长混合",
        "short_name": "广发稳健",
        "type": "混合型",
        "manager": "傅友兴",
        "company": "广发基金",
        "nav": 1.9876,
        "acc_nav": 4.5678,
        "change_pct": -0.34,
        "size": "76.89亿",
        "establish_date": "2006-07-26",
        "risk_level": "中风险",
    },
    {
        "fund_code": "163402",
        "name": "兴全趋势投资混合",
        "short_name": "兴全趋势",
        "type": "混合型",
        "manager": "董承非",
        "company": "兴全基金",
        "nav": 0.9823,
        "acc_nav": 8.9012,
        "change_pct": 0.89,
        "size": "198.56亿",
        "establish_date": "2005-11-03",
        "risk_level": "中高风险",
    },
    {
        "fund_code": "005827",
        "name": "易方达蓝筹精选混合",
        "short_name": "易方达蓝筹",
        "type": "混合型",
        "manager": "张坤",
        "company": "易方达基金",
        "nav": 1.8934,
        "acc_nav": 1.8934,
        "change_pct": -1.56,
        "size": "567.89亿",
        "establish_date": "2018-09-05",
        "risk_level": "中高风险",
    },
    {
        "fund_code": "260108",
        "name": "景顺长城新兴成长混合",
        "short_name": "景顺新兴",
        "type": "混合型",
        "manager": "刘彦春",
        "company": "景顺长城基金",
        "nav": 3.4567,
        "acc_nav": 5.6789,
        "change_pct": 0.45,
        "size": "234.56亿",
        "establish_date": "2008-04-17",
        "risk_level": "中高风险",
    },
]

# ============================================================
# 模拟分红记录
# ============================================================

MOCK_DIVIDENDS = {
    "161005": [
        {"date": "2024-01-15", "amount": 0.50, "type": "现金分红"},
        {"date": "2023-06-20", "amount": 0.35, "type": "现金分红"},
        {"date": "2022-12-10", "amount": 0.42, "type": "现金分红"},
        {"date": "2022-06-15", "amount": 0.28, "type": "现金分红"},
    ],
    "110011": [
        {"date": "2023-12-05", "amount": 0.80, "type": "现金分红"},
        {"date": "2023-06-10", "amount": 0.65, "type": "现金分红"},
    ],
    "000001": [
        {"date": "2024-02-20", "amount": 0.15, "type": "现金分红"},
        {"date": "2023-08-15", "amount": 0.12, "type": "现金分红"},
        {"date": "2023-02-10", "amount": 0.18, "type": "现金分红"},
    ],
    "519068": [
        {"date": "2024-01-08", "amount": 0.45, "type": "现金分红"},
    ],
    "163402": [
        {"date": "2023-11-20", "amount": 1.20, "type": "现金分红"},
        {"date": "2023-05-15", "amount": 0.95, "type": "现金分红"},
        {"date": "2022-11-10", "amount": 0.88, "type": "现金分红"},
    ],
}

# ============================================================
# 模拟持仓数据
# ============================================================

MOCK_HOLDINGS = {
    "161005": [
        {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 8.5},
        {"stock_code": "000858", "stock_name": "五粮液", "weight": 6.2},
        {"stock_code": "000333", "stock_name": "美的集团", "weight": 5.8},
        {"stock_code": "601318", "stock_name": "中国平安", "weight": 4.5},
        {"stock_code": "000651", "stock_name": "格力电器", "weight": 4.2},
    ],
    "110011": [
        {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 9.8},
        {"stock_code": "000568", "stock_name": "泸州老窖", "weight": 7.5},
        {"stock_code": "600887", "stock_name": "伊利股份", "weight": 6.3},
        {"stock_code": "000858", "stock_name": "五粮液", "weight": 5.9},
        {"stock_code": "603288", "stock_name": "海天味业", "weight": 4.8},
    ],
    "005827": [
        {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 14.2},
        {"stock_code": "000858", "stock_name": "五粮液", "weight": 8.6},
        {"stock_code": "000568", "stock_name": "泸州老窖", "weight": 7.8},
        {"stock_code": "600809", "stock_name": "山西汾酒", "weight": 5.4},
        {"stock_code": "000596", "stock_name": "古井贡酒", "weight": 4.2},
    ],
}

# ============================================================
# 模拟服务定义（扩展版）
# ============================================================

DEMO_SERVICES = [
    # 基金查询类服务 (Fund Query Services)
    {
        "service_id": "getFundNAV",
        "name": "基金净值查询",
        "name_en": "Fund NAV Query",
        "description": "查询指定基金的单位净值、累计净值和涨跌幅，支持按基金代码或名称查询",
        "description_en": "Query fund NAV, accumulated NAV and change percentage by fund code or name",
        "keywords": ["净值", "NAV", "涨跌", "单位净值", "累计净值", "今日净值", "净值查询",
                     "net value", "net asset value", "fund value", "check NAV", "query NAV"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
        },
        "returns": {"nav": "单位净值", "acc_nav": "累计净值", "change_pct": "涨跌幅"},
        "examples": ["查询基金161005的净值", "What is the NAV of fund 161005"],
    },
    {
        "service_id": "getFundDividend",
        "name": "基金分红查询",
        "name_en": "Fund Dividend Query",
        "description": "查询指定基金的历史分红派息记录，包括分红日期、金额和类型",
        "description_en": "Query fund dividend history including date, amount and type",
        "keywords": ["分红", "派息", "红利", "分红记录", "分红历史", "有分红",
                     "dividend", "distribution", "dividend history", "dividend record"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
            "start_date": {"type": "string", "description": "起始日期", "required": False},
            "end_date": {"type": "string", "description": "结束日期", "required": False},
        },
        "returns": {"dividends": "分红记录列表"},
        "examples": ["查询分红记录", "Show dividend history"],
    },
    {
        "service_id": "getAllFunds",
        "name": "获取基金列表",
        "name_en": "Get All Funds",
        "description": "获取系统中所有可查询的基金产品列表，支持按类型筛选",
        "description_en": "Get all available funds in the system, support filter by type",
        "keywords": ["列表", "所有基金", "全部基金", "基金列表", "显示基金", "有哪些基金",
                     "list", "all funds", "show funds", "available funds", "fund list"],
        "parameters": {
            "fund_type": {"type": "string", "description": "基金类型", "required": False},
        },
        "returns": {"funds": "基金列表"},
        "examples": ["显示所有基金", "Show all funds"],
    },
    {
        "service_id": "getFundHoldings",
        "name": "基金持仓查询",
        "name_en": "Fund Holdings Query",
        "description": "查询基金的持仓明细和资产配置情况，包括重仓股票",
        "description_en": "Query fund holdings and asset allocation including top stocks",
        "keywords": ["持仓", "重仓", "持有股票", "资产配置", "重仓股", "仓位",
                     "holdings", "positions", "stocks", "portfolio", "top holdings"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
        },
        "returns": {"holdings": "持仓明细"},
        "examples": ["查询持仓", "Show fund holdings"],
    },
    {
        "service_id": "getFundManager",
        "name": "基金经理查询",
        "name_en": "Fund Manager Query",
        "description": "查询基金经理信息，包括管理基金、从业年限、历史业绩",
        "description_en": "Query fund manager info including managed funds and performance",
        "keywords": ["基金经理", "经理", "管理人", "谁管理", "经理是谁",
                     "manager", "fund manager", "who manages", "portfolio manager"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": False},
            "manager_name": {"type": "string", "description": "经理姓名", "required": False},
        },
        "returns": {"manager": "基金经理信息"},
        "examples": ["基金经理是谁", "Who is the fund manager"],
    },
    {
        "service_id": "compareFunds",
        "name": "基金对比",
        "name_en": "Fund Comparison",
        "description": "对比多只基金的收益、风险、持仓等指标",
        "description_en": "Compare multiple funds on return, risk and holdings",
        "keywords": ["对比", "比较", "PK", "哪个好", "选哪个", "对比分析",
                     "compare", "comparison", "versus", "which better", "vs"],
        "parameters": {
            "fund_codes": {"type": "list", "description": "基金代码列表", "required": True},
        },
        "returns": {"comparison": "对比结果"},
        "examples": ["对比两只基金", "Compare two funds"],
    },

    # 业务处理类服务 (Business Processing Services)
    {
        "service_id": "processDividend",
        "name": "基金分红处理",
        "name_en": "Process Dividend",
        "description": "批量处理基金分红派息业务，支持现金分红和红利再投",
        "description_en": "Batch process fund dividend distribution, support cash or reinvestment",
        "keywords": ["分红处理", "处理分红", "批量处理", "派息处理", "执行分红",
                     "process dividend", "handle dividend", "dividend processing", "execute distribution"],
        "parameters": {
            "fund_codes": {"type": "list", "description": "基金代码列表", "required": True},
            "dividend_type": {"type": "string", "description": "分红方式", "required": False},
        },
        "returns": {"processed_count": "处理数量", "total_amount": "总金额"},
        "examples": ["处理分红", "Process dividend distribution"],
    },
    {
        "service_id": "calculateReturn",
        "name": "收益计算",
        "name_en": "Calculate Return",
        "description": "计算基金投资的收益率，支持区间收益和年化收益",
        "description_en": "Calculate fund investment return including period and annualized return",
        "keywords": ["收益", "回报", "计算收益", "赚了多少", "年化收益", "收益率", "盈亏",
                     "return", "profit", "calculate return", "annualized", "earnings", "gain"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
            "start_date": {"type": "string", "description": "起始日期", "required": True},
            "end_date": {"type": "string", "description": "结束日期", "required": False},
        },
        "returns": {"return_rate": "收益率", "annualized_return": "年化收益"},
        "examples": ["计算收益率", "Calculate return rate"],
    },
    {
        "service_id": "getRiskMetrics",
        "name": "风险指标查询",
        "name_en": "Risk Metrics Query",
        "description": "查询基金的风险指标，包括波动率、最大回撤、夏普比率",
        "description_en": "Query fund risk metrics including volatility, max drawdown and Sharpe ratio",
        "keywords": ["风险", "波动率", "回撤", "夏普比率", "风险指标", "风险大",
                     "risk", "volatility", "drawdown", "sharpe", "risk metrics", "risk level"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
        },
        "returns": {"volatility": "波动率", "max_drawdown": "最大回撤", "sharpe_ratio": "夏普比率"},
        "examples": ["风险指标查询", "What is the risk level"],
    },
    {
        "service_id": "subscribeAlert",
        "name": "订阅提醒",
        "name_en": "Subscribe Alert",
        "description": "订阅基金净值变动、分红等事件的提醒通知",
        "description_en": "Subscribe to NAV change, dividend and other event alerts",
        "keywords": ["订阅", "提醒", "通知", "预警", "监控", "提醒我", "通知我",
                     "subscribe", "alert", "notify", "notification", "reminder"],
        "parameters": {
            "fund_code": {"type": "string", "description": "基金代码", "required": True},
            "alert_type": {"type": "string", "description": "提醒类型", "required": True},
        },
        "returns": {"subscription_id": "订阅ID"},
        "examples": ["订阅净值提醒", "Subscribe to NAV alerts"],
    },
]

# ============================================================
# 知识库内容
# ============================================================

KNOWLEDGE_BASE = [
    # 基金基础知识
    {
        "knowledge_id": "kb_fund_types",
        "title": "基金类型介绍",
        "category": "concept",
        "content": """基金按投资标的可分为以下类型：
1. 股票型基金：80%以上资产投资于股票，风险较高，收益潜力大
2. 混合型基金：同时投资股票和债券，风险收益适中
3. 债券型基金：80%以上资产投资于债券，风险较低，收益稳定
4. 货币型基金：投资于短期货币工具，风险最低，流动性好
5. 指数型基金：跟踪特定指数，被动投资，费率较低""",
        "tags": ["基金类型", "股票型", "混合型", "债券型", "货币型"],
    },
    {
        "knowledge_id": "kb_nav_concept",
        "title": "基金净值概念",
        "category": "concept",
        "content": """基金净值相关概念：
1. 单位净值(NAV)：基金每份额的价格，等于基金总资产除以总份额
2. 累计净值：单位净值加上历史分红金额，反映基金成立以来的总回报
3. 估算净值：根据持仓股票实时价格估算的净值，仅供参考
4. 净值更新时间：通常在交易日晚间8-10点更新""",
        "tags": ["净值", "NAV", "单位净值", "累计净值"],
    },
    {
        "knowledge_id": "kb_dividend_types",
        "title": "基金分红方式",
        "category": "concept",
        "content": """基金分红的两种方式：
1. 现金分红：直接将红利发放到投资者账户，适合需要现金流的投资者
2. 红利再投：将红利自动转换为基金份额，适合长期投资者，可享受复利效应
注意：分红不会增加投资者的实际收益，只是将部分资产从基金中提取出来""",
        "tags": ["分红", "现金分红", "红利再投", "派息"],
    },
    {
        "knowledge_id": "kb_risk_metrics",
        "title": "基金风险指标",
        "category": "concept",
        "content": """评估基金风险的主要指标：
1. 波动率：衡量净值波动程度，越高风险越大
2. 最大回撤：从最高点到最低点的最大跌幅，反映极端风险
3. 夏普比率：每承担一单位风险获得的超额收益，越高越好
4. 贝塔系数：相对于市场的波动程度，大于1表示波动大于市场""",
        "tags": ["风险", "波动率", "回撤", "夏普比率"],
    },

    # 业务流程知识
    {
        "knowledge_id": "kb_dividend_process",
        "title": "分红派息流程",
        "category": "process",
        "content": """基金分红派息的标准流程：
1. 权益登记日：确定享有分红权益的持有人
2. 除息日：基金净值会相应下调
3. 红利发放日：现金分红到账或份额增加
4. 分红确认：投资者可在账户中查看分红记录
处理时间通常为T+1到T+3个工作日""",
        "tags": ["分红流程", "派息", "权益登记", "除息"],
    },
    {
        "knowledge_id": "kb_nav_calculation",
        "title": "净值计算方法",
        "category": "process",
        "content": """基金净值的计算公式：
单位净值 = (基金总资产 - 基金总负债) / 基金总份额
其中：
- 总资产包括：股票、债券、现金等投资品的市值
- 总负债包括：管理费、托管费等应付款项
- 净值精确到小数点后4位""",
        "tags": ["净值计算", "资产", "负债", "份额"],
    },

    # 常见问题
    {
        "knowledge_id": "kb_faq_buy_time",
        "title": "基金买入时机",
        "category": "faq",
        "content": """关于基金买入时间的常见问题：
Q: 什么时候买基金合适？
A: 基金是长期投资工具，定投策略可以平滑买入成本。避免追涨杀跌。

Q: 交易日几点前买入算当天？
A: 交易日15:00前提交的申购按当天净值成交，之后按下一交易日净值。""",
        "tags": ["买入", "时机", "定投", "交易时间"],
    },
    {
        "knowledge_id": "kb_faq_fees",
        "title": "基金费用说明",
        "category": "faq",
        "content": """基金相关费用说明：
1. 申购费：买入时收取，一般0.1%-1.5%，持有时间越长费率越低
2. 赎回费：卖出时收取，持有7天以内通常1.5%，长期持有可免
3. 管理费：每年从基金资产中扣除，一般0.5%-1.5%
4. 托管费：支付给托管银行，一般0.1%-0.25%""",
        "tags": ["费用", "申购费", "赎回费", "管理费"],
    },
]

# ============================================================
# 模拟对话历史
# ============================================================

SAMPLE_CONVERSATIONS = [
    # 对话1：基金净值查询
    [
        {"role": "user", "content": "帮我查一下富国天惠基金今天的净值"},
        {"role": "assistant", "content": "富国天惠成长混合(161005)今日净值为3.2156元，累计净值6.8234元，较昨日上涨2.35%。该基金由知名基金经理朱少醒管理，是一只优秀的混合型基金。"},
        {"role": "user", "content": "这个基金最近有分红吗"},
        {"role": "assistant", "content": "富国天惠最近一次分红是在2024年1月15日，每份派息0.50元。2023年还有两次分红，分别是6月20日派息0.35元和12月10日派息0.42元。"},
        {"role": "user", "content": "这个基金持有哪些股票"},
        {"role": "assistant", "content": "富国天惠的前五大重仓股为：1.贵州茅台(8.5%) 2.五粮液(6.2%) 3.美的集团(5.8%) 4.中国平安(4.5%) 5.格力电器(4.2%)。主要配置在消费和金融板块。"},
    ],
    # 对话2：基金对比
    [
        {"role": "user", "content": "易方达消费和易方达蓝筹哪个好"},
        {"role": "assistant", "content": "这两只基金各有特点：\n易方达消费(110011)：专注消费行业，净值4.1523，今日-0.82%\n易方达蓝筹(005827)：张坤管理，持仓更集中在白酒，净值1.8934，今日-1.56%\n易方达消费历史更长、规模更大，但近期蓝筹回调较多。"},
        {"role": "user", "content": "张坤管理的基金业绩怎么样"},
        {"role": "assistant", "content": "张坤是易方达的明星基金经理，管理易方达蓝筹精选等多只基金，规模超过500亿。他的投资风格偏向价值投资，重仓白酒消费股。2021年后由于白酒板块调整，基金净值有所回撤，但长期业绩优秀。"},
    ],
    # 对话3：业务处理
    [
        {"role": "user", "content": "帮我处理一下本月的基金分红"},
        {"role": "assistant", "content": "好的，我来帮您处理本月的分红。系统中有3只基金在本月有分红记录：\n1. 富国天惠(161005) - 派息0.50元/份\n2. 汇添富成长(519068) - 派息0.45元/份\n3. 华夏成长(000001) - 派息0.15元/份\n请确认是否开始处理？"},
        {"role": "user", "content": "确认处理"},
        {"role": "assistant", "content": "分红处理已完成！\n处理结果：\n- 成功处理3只基金的分红派息\n- 总派息金额：1.10元/份\n- 处理方式：现金分红\n- 预计到账时间：T+2个工作日\n您可以在账户中查看详细的分红记录。"},
    ],
]

# ============================================================
# 用于测试的查询样本（中英双语）
# ============================================================

TEST_QUERIES = [
    # === 净值查询 (Chinese) ===
    ("查询富国天惠基金今天的净值", "getFundNAV"),
    ("161005净值多少", "getFundNAV"),
    ("NAV是多少", "getFundNAV"),
    ("基金净值查询", "getFundNAV"),

    # === 净值查询 (English) ===
    ("What is the NAV of fund 161005", "getFundNAV"),
    ("Query fund net value", "getFundNAV"),
    ("Check the NAV", "getFundNAV"),
    ("Show me the net asset value", "getFundNAV"),

    # === 分红查询 (Chinese) ===
    ("基金分红记录", "getFundDividend"),
    ("派息历史", "getFundDividend"),
    ("有没有分红", "getFundDividend"),
    ("红利发放情况", "getFundDividend"),

    # === 分红查询 (English) ===
    ("Show dividend history", "getFundDividend"),
    ("Any dividend distribution", "getFundDividend"),
    ("Check dividend records", "getFundDividend"),

    # === 基金列表 (Chinese) ===
    ("显示所有基金", "getAllFunds"),
    ("有哪些基金可以查", "getAllFunds"),
    ("基金产品列表", "getAllFunds"),

    # === 基金列表 (English) ===
    ("Show all funds", "getAllFunds"),
    ("List available funds", "getAllFunds"),
    ("What funds can I query", "getAllFunds"),

    # === 持仓查询 (Chinese) ===
    ("查看基金持仓", "getFundHoldings"),
    ("持有哪些股票", "getFundHoldings"),
    ("重仓股是什么", "getFundHoldings"),

    # === 持仓查询 (English) ===
    ("Show fund holdings", "getFundHoldings"),
    ("What stocks does it hold", "getFundHoldings"),
    ("Check positions", "getFundHoldings"),

    # === 基金经理 (Chinese) ===
    ("基金经理是谁", "getFundManager"),
    ("谁管理这只基金", "getFundManager"),

    # === 基金经理 (English) ===
    ("Who is the fund manager", "getFundManager"),
    ("Who manages this fund", "getFundManager"),

    # === 基金对比 (Chinese) ===
    ("对比两只基金", "compareFunds"),
    ("哪个基金更好", "compareFunds"),
    ("PK一下", "compareFunds"),

    # === 基金对比 (English) ===
    ("Compare two funds", "compareFunds"),
    ("Which fund is better", "compareFunds"),

    # === 分红处理 (Chinese) ===
    ("处理分红派息", "processDividend"),
    ("批量分红处理", "processDividend"),

    # === 分红处理 (English) ===
    ("Process dividend distribution", "processDividend"),
    ("Handle dividend payment", "processDividend"),

    # === 收益计算 (Chinese) ===
    ("计算收益率", "calculateReturn"),
    ("赚了多少钱", "calculateReturn"),
    ("年化收益", "calculateReturn"),

    # === 收益计算 (English) ===
    ("Calculate return rate", "calculateReturn"),
    ("How much profit", "calculateReturn"),
    ("Annualized return", "calculateReturn"),

    # === 风险指标 (Chinese) ===
    ("风险大不大", "getRiskMetrics"),
    ("最大回撤多少", "getRiskMetrics"),

    # === 风险指标 (English) ===
    ("What is the risk level", "getRiskMetrics"),
    ("Show max drawdown", "getRiskMetrics"),
    ("Check volatility", "getRiskMetrics"),

    # === 订阅提醒 (Chinese) ===
    ("订阅净值提醒", "subscribeAlert"),
    ("分红时通知我", "subscribeAlert"),

    # === 订阅提醒 (English) ===
    ("Subscribe to NAV alerts", "subscribeAlert"),
    ("Notify me when dividend", "subscribeAlert"),
]

# 双语对话样本
BILINGUAL_CONVERSATIONS = [
    # 英文对话
    [
        {"role": "user", "content": "What is the NAV of fund 161005?"},
        {"role": "assistant", "content": "The NAV of Fuguo Tianhui (161005) is 3.2156 CNY, with accumulated NAV of 6.8234 CNY, up 2.35% from yesterday."},
        {"role": "user", "content": "Does this fund have any dividend?"},
        {"role": "assistant", "content": "The latest dividend was on January 15, 2024, at 0.50 CNY per share."},
    ],
    # 中英混合对话
    [
        {"role": "user", "content": "Show me the holdings of 富国天惠"},
        {"role": "assistant", "content": "富国天惠 top 5 holdings: 1.Kweichow Moutai(8.5%) 2.Wuliangye(6.2%) 3.Midea(5.8%)"},
        {"role": "user", "content": "这个基金的manager是谁?"},
        {"role": "assistant", "content": "The fund manager is Zhu Shaoxing (朱少醒), one of the most famous fund managers in China."},
    ],
]


def get_fund_by_code(fund_code: str) -> dict:
    """根据代码获取基金信息"""
    for fund in MOCK_FUNDS:
        if fund["fund_code"] == fund_code:
            return fund
    return None


def get_fund_by_name(name: str) -> dict:
    """根据名称模糊匹配基金"""
    name_lower = name.lower()
    for fund in MOCK_FUNDS:
        if name_lower in fund["name"].lower() or name_lower in fund["short_name"].lower():
            return fund
    return None


def get_dividends(fund_code: str) -> list:
    """获取基金分红记录"""
    return MOCK_DIVIDENDS.get(fund_code, [])


def get_holdings(fund_code: str) -> list:
    """获取基金持仓"""
    return MOCK_HOLDINGS.get(fund_code, [])


def get_knowledge_by_category(category: str) -> list:
    """按类别获取知识"""
    return [k for k in KNOWLEDGE_BASE if k["category"] == category]


def search_knowledge(query: str) -> list:
    """搜索知识库"""
    query_lower = query.lower()
    results = []
    for k in KNOWLEDGE_BASE:
        score = 0
        if query_lower in k["title"].lower():
            score += 3
        if query_lower in k["content"].lower():
            score += 2
        for tag in k.get("tags", []):
            if query_lower in tag.lower():
                score += 1
        if score > 0:
            results.append({"knowledge": k, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
