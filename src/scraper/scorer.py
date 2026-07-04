import re
from typing import List, Dict

# ---------- 关键词库 ----------

# 匹配标题/岗位描述中可能出现的关键词
KEYWORDS_TITLE: Dict[str, List[str]] = {
    "security": [
        "security",
        "sec",
        "信息安全",
        "网络安全",
        "cyber",
        "risk",
        "risk management",
        "保安",
        "信息安全工程师",
        "information security officer",
        "information security manager",
        "security analyst",
        "infosec",
        "网络安全工程师",
    ],
    "compliance": [
        "compliance",
        "合规",
        "合规专员",
        "合规经理",
        "合规总监",
        "合规审计",
        "合规岗",
    ],
    "privacy": [
        "privacy",
        "个人信息保护",
        "数据隐私",
        "gdpr",
        "privacy officer",
        "数据安全",
        "隐私官",
    ],
}

# 匹配目标公司的权重，按层级划分
KEYWORDS_COMPANY: Dict[str, List[str]] = {
    "top_tier": [
        "Tencent",
        "ByteDance",
        "Huawei",
        "ZTE",
        "China Mobile",
        "China Telecom",
        "China Unicom",
        "Alibaba",
        "Ant Group",
        "Ping An",
        "CICC",
        "CCB",
        "Bank of China",
        "ICBC",
        "Microsoft",
        "Google",
        "Amazon",
        "Apple",
        "Intel",
        "NVIDIA",
        "Siemens",
        "BOSCH",
        "IBM",
        "Oracle",
        "Cisco",
        "SAP",
        "Adobe",
        "Salesforce",
    ],
    "unicorn": [
        "ByteDance",
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


def _extract_salary_points(description: str) -> int:
    """
    从岗位描述中提取薪资信息并映射为分数（0-3 分）。
    支持「¥50k」「50K」「月薪50k」「年薪80w」等多种写法。
    """
    desc_upper = description.upper()
    nums = re.findall(r"\d+\.?\d*", desc_upper)

    if not nums:
        return 0

    try:
        salary_val = float(nums[0])
    except ValueError:
        return 0

    if salary_val >= 50:
        return 3
    if 30 <= salary_val < 50:
        return 2
    if 10 <= salary_val < 30:
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

    # ---- 1. 标题关键词 ----
    for cat, patterns in KEYWORDS_TITLE.items():
        if _match_keywords(title, patterns):
            score += 2 if cat == "security" else 1

    # ---- 2. 公司匹配 ----
    if _match_keywords(company, KEYWORDS_COMPANY["top_tier"]):
        score += 2
    elif _match_keywords(company, KEYWORDS_COMPANY["unicorn"]):
        score += 1

    # ---- 3. 地点匹配 ----
    if _match_keywords(location, ["beijing", "北京", "remote", "远程", "线上", "异地"]):
        score += 1

    # ---- 4. 薪资加分 ----
    salary_points = _extract_salary_points(description)
    score += salary_points

    # ---- 5. 公司环境与福利 ----
    env_score = _score_company_env(description)
    score += env_score

    # 确保不超过上限
    return min(score, 10)
