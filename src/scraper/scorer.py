import re
from typing import List, Dict

# ---------- 关键词库 ----------

# 匹配标题/岗位描述中可能出现的关键词
KEYWORDS_TITLE: Dict[str, List[str]] = {
    # 信息安全合规（重点方向，权重最高）
    "compliance": [
        "compliance",
        "合规",
        "信息安全合规",
        "数据合规",
        "网络安全合规",
        "security compliance",
        "data compliance",
        "it compliance",
        "grc",
        "等保",
        "等级保护",
        "合规专员",
        "合规经理",
        "合规总监",
        "合规岗",
        "iso 27001",
        "soc 2",
    ],
    # 数据隐私 / 个人信息保护（信息安全合规核心）
    "privacy": [
        "privacy",
        "个人信息保护",
        "数据隐私",
        "gdpr",
        "privacy officer",
        "数据安全",
        "隐私官",
        "dpo",
        "data protection officer",
        "个保法",
        "隐私合规",
    ],
    # 安全技术（保留核心，降权）
    "security": [
        "security",
        "信息安全",
        "网络安全",
        "cyber",
        "risk",
        "risk management",
        "信息安全工程师",
        "information security officer",
        "information security manager",
        "security analyst",
        "infosec",
        "网络安全工程师",
    ],
}

# 标题关键词分值（信息安全合规 > 隐私 > 安全技术）
TITLE_POINTS: Dict[str, int] = {
    "compliance": 3,
    "privacy": 2,
    "security": 1,
}

# 护栏：非 IT 信息安全方向的岗位（法务/律师/审计会计/财务税务等），
# 命中则标题不加分，防止"合规"漂移成法务、律师、财务合规等非技术岗位。
EXCLUDE_TITLE: List[str] = [
    "lawyer",
    "attorney",
    "legal counsel",
    "律师",
    "法务",
    "法律顾问",
    "auditor",
    "accountant",
    "会计",
    "审计",
    "税务",
    "tax",
    "财务合规",
    r"(?<![a-z])hr(?![a-z])",
    "human resource",
    "human resources",
    "人力资源",
    "招聘",
    r"\brecruit",
    "薪酬",
    "薪资福利",
    "payroll",
    r"\bsales\b",
    "销售",
    "marketing",
    "市场营销",
]

# "合规/compliance" 极易漂移到各行业（质量/环保/贸易/医疗/金融/生产…）。
# 只有标题同时含以下 IT 信息安全限定词时，compliance 命中才算 IT 方向而加分；
# 否则视为非 IT 合规，不加分。一条白名单规则覆盖所有行业变体，无需逐个枚举。
INFOSEC_QUALIFIERS: List[str] = [
    "信息安全",
    "网络安全",
    "数据",
    "隐私",
    "网安",
    "infosec",
    "cyber",
    "information security",
    "data ",
    "it compliance",
    "it security",
    "privacy",
    "gdpr",
    "等保",
    "等级保护",
    "iso 27001",
    "soc 2",
    "grc",
]


# 匹配目标公司的权重，按层级划分
# 层级分值：foreign_tech / cn_tech_giant = 4，foreign_traditional = 3，
#           state_owned = 2，unicorn = 1（见 score_job 中的 COMPANY_TIER_POINTS）
KEYWORDS_COMPANY: Dict[str, List[str]] = {
    # 外企 500 强科技行业 + 中国民营科技巨头（最高档）
    "foreign_tech": [
        "Microsoft",
        "Google",
        "Amazon",
        "Apple",
        "Intel",
        "NVIDIA",
        "IBM",
        "Oracle",
        "Cisco",
        "SAP",
        "Adobe",
        "Salesforce",
        "Tencent",
        "Alibaba",
        "ByteDance",
        "Huawei",
        "Ant Group",
        "ZTE",
    ],
    # 外企 500 强传统行业
    "foreign_traditional": [
        "Siemens",
        "BOSCH",
    ],
    # 央企
    "state_owned": [
        "China Mobile",
        "China Telecom",
        "China Unicom",
        "ICBC",
        "CCB",
        "Bank of China",
        "CICC",
        "Ping An",
    ],
    # 独角兽企业
    "unicorn": [
        "SpaceX",
        "SHEIN",
        "Stripe",
        "Klarna",
        "Canva",
        "Databricks",
        "Epic Games",
        "Chime",
        "Instacart",
        "Gusto",
        "HashiCorp",
        "Discord",
        "Reddit",
        "Palantir",
    ],
}

# 公司层级 -> 分值（按用户权重：外企科技/民营科技巨头 > 外企传统 > 央企 > 独角兽）
COMPANY_TIER_POINTS: Dict[str, int] = {
    "foreign_tech": 4,
    "foreign_traditional": 3,
    "state_owned": 2,
    "unicorn": 1,
}

# 公司环境、福利关键词（描述中出现的福利/环境词）
COMPANY_ENV_KEYWORDS: Dict[str, List[str]] = {
    "culture": [
        "great culture",
        "amazing culture",
        "inclusive",
        "diverse",
        "work-life balance",
        "flexible hours",
        "flat hierarchy",
        "扁平管理",
        "年轻团队",
        "学习氛围",
    ],
    "benefits": [
        "stock options",
        " equity",
        "rsu",
        "bonus",
        "奖金",
        "health insurance",
        "medical insurance",
        "五险一金",
        "housing fund",
        "补充医疗",
        "商业保险",
        "paid leave",
        "remote work",
        "弹性工作",
        "免费午餐",
        "下午茶",
        "gym",
        "健身房",
        "education allowance",
        "培训补贴",
    ],
    "growth": [
        "career growth",
        "career advancement",
        "learning budget",
        "job training",
        "professional development",
        "技术培训",
        "晋升空间",
        "发展机会",
    ],
}

# ---------- 辅助函数 ----------


def _match_keywords(text: str, patterns: List[str]) -> bool:
    """检查文本中是否匹配任意关键词（不区分大小写）"""
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def _salary_to_wan_per_month(salary: str) -> float | None:
    """将 salary 字段归一化为「万元/月」。

    salary 字段来自 main.py 的 _extract_salary，形如 "6000-12000元"、
    "14-28万/年"、"3 w"、"25000"、"N/A"。尽力解析，无法可靠解析时返回 None。
    区间取下限（保守估计）。
    """
    if not salary or "N/A" in salary:
        return None

    text = salary.replace(",", "").lower()
    nums = re.findall(r"\d+\.?\d*", text)
    if not nums:
        return None
    try:
        low = float(nums[0])
    except ValueError:
        return None

    is_yearly = "/年" in text or "年薪" in salary
    if "万" in text or "w" in text:
        wan = low
    elif "元" in text or low >= 1000:
        # 以「元」计的月薪（或裸数字如 25000）
        wan = low / 10000.0
    elif "k" in text or "千" in text:
        wan = low / 10.0
    else:
        # 无单位的小数字，无法可靠判断
        return None

    if is_yearly:
        wan = wan / 12.0
    return wan


def _score_salary_points(salary: str) -> int:
    """按「万元/月」分档给分（0-4 分）。

    >=5 万 -> 4；3.5-5 万 -> 3；2-3.5 万 -> 2；1-2 万 -> 1；其余/无法解析 -> 0。
    """
    wan = _salary_to_wan_per_month(salary)
    if wan is None:
        return 0
    if wan >= 5:
        return 4
    if wan >= 3.5:
        return 3
    if wan >= 2:
        return 2
    if wan >= 1:
        return 1
    return 0


def _score_company_env(description: str) -> int:
    """
    根据公司环境、福利关键词给予额外分数（0-2 分）。
    - 具备优秀福利（stock options, 完整保险等）：+1 分
    - 具备成长机会或文化氛围：+1 分
    """
    score = 0
    text = description.lower()

    # 福利关键词匹配
    if _match_keywords(text, COMPANY_ENV_KEYWORDS["benefits"]):
        score += 1

    # 成长/环境关键词匹配
    if _match_keywords(text, COMPANY_ENV_KEYWORDS["culture"]) or _match_keywords(
        text, COMPANY_ENV_KEYWORDS["growth"]
    ):
        score += 1

    return score


# ---------- 评分核心 ----------


def score_job(job: dict) -> int:
    """
    综合评分（最高 10 分）：

    1) 标题关键词（安全相关加权更高）
    2) 公司是否为重点/ unicorn 企业
    3) 地点是否为北京或远程
    4) 薪资水平（从描述中提取）
    5) 公司环境与福利

    输出分数在 0-10 范围内，后续用于排序取 Top-N。
    """
    score = 0

    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    description = job.get("description", "")
    salary = job.get("salary", "")

    # ---- 1. 标题关键词 ----
    # 命中非 IT 信息安全方向的排除词（法务/审计/HR/销售等）则标题不加分。
    # 此外 compliance 类只有在标题含 IT 信息安全限定词时才加分，
    # 防止"质量合规/环保合规/医疗合规"等各行业合规岗漂移进来。
    if not _match_keywords(title, EXCLUDE_TITLE):
        has_infosec = _match_keywords(title, INFOSEC_QUALIFIERS)
        for cat, patterns in KEYWORDS_TITLE.items():
            if cat == "compliance" and not has_infosec:
                continue
            if _match_keywords(title, patterns):
                score += TITLE_POINTS[cat]

    # ---- 2. 公司匹配（按层级取最高档，不叠加）----
    for tier, points in COMPANY_TIER_POINTS.items():
        if _match_keywords(company, KEYWORDS_COMPANY[tier]):
            score += points
            break

    # ---- 3. 地点匹配 ----
    if _match_keywords(location, ["beijing", "北京", "remote", "远程", "线上", "异地"]):
        score += 1

    # ---- 4. 薪资加分 ----
    salary_points = _score_salary_points(salary)
    score += salary_points

    # ---- 5. 公司环境与福利 ----
    env_score = _score_company_env(description)
    score += env_score

    # 确保不超过上限
    return min(score, 10)
