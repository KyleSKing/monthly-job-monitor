import csv
from dataclasses import dataclass, field
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

@dataclass
class Fortune500Company:
    """表示Fortune 500公司的结构"""
    rank: int
    name: str
    website: str
    career_url: Optional[str] = None  # 自动生成的招聘页面URL
    keywords: List[str] = field(default_factory=lambda: ["information security", "data compliance", "cybersecurity"])

    def to_dict(self) -> dict:
        return {
            "Rank": self.rank,
            "Company": self.name,
            "Website": self.website,
            "Career_URL": self.career_url or self._guess_career_url(),
            "Keywords": ",".join(self.keywords)  # 逗号分隔的关键词字符串
        }

    def _guess_career_url(self) -> str:
        """根据常见模式推测招聘页面URL"""
        website = self.website.rstrip('/')
        # 常见的招聘页面模式
        patterns = [
            f"{website}/careers",
            f"{website}/jobs",
            f"{website}/en-us/careers",
            f"{website}/en/careers",
        ]
        # 默认返回第一个模式
        return patterns[0]

class Fortune500Scraper:
    """从 Wikipedia 自动抓取 Fortune 500 公司列表"""
    
    def __init__(self):
        self.wiki_url = "https://en.wikipedia.org/wiki/List_of_Fortune_500_companies"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_fortune500(self) -> List[Fortune500Company]:
        """
        从 Wikipedia 抓取 Fortune 500 公司列表
        
        Returns:
            List[Fortune500Company]: 排名、公司名称、官网
        """
        try:
            response = self.session.get(self.wiki_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到包含公司数据的表格
            table = soup.find('table', {'class': 'wikitable'})
            if not table:
                raise ValueError("未找到 Fortune 500 表格")
            
            companies = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:  # 确保有足够的列
                    try:
                        rank = int(cells[0].get_text(strip=True))
                        name = cells[1].get_text(strip=True)
                        
                        # 提取网站URL
                        website_link = cells[3].find('a')
                        website = website_link.get('href') if website_link else ""
                        
                        # 清理URL，转换为完整域名
                        if website and not website.startswith('http'):
                            if website.startswith('//'):
                                website = f'https:{website}'
                            elif website.startswith('/'):
                                website = f'https://en.wikipedia.org{website}'
                            else:
                                website = f'https://{website}'
                        
                        if website and self._is_valid_website(website):
                            companies.append(Fortune500Company(
                                rank=rank,
                                name=name,
                                website=website
                            ))
                    except (ValueError, AttributeError) as e:
                        print(f"解析行时出错: {e}")
                        continue
            
            print(f"成功抓取 {len(companies)} 家 Fortune 500 公司")
            return companies
            
        except requests.RequestException as e:
            print(f"网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"解析失败: {e}")
            return []
    
    def _is_valid_website(self, url: str) -> bool:
        """验证URL是否是有效的公司网站"""
        # 过掉某些无效的链接
        invalid_patterns = [
            'wikipedia.org',
            'fortune.com',
            'forbes.com',
            'businessinsider.com'
        ]
        return not any(pattern in url.lower() for pattern in invalid_patterns)
    
    def generate_career_urls(self, companies: List[Fortune500Company]) -> List[Fortune500Company]:
        """为所有公司生成招聘页面URL"""
        for company in companies:
            company.career_url = company._guess_career_url()
        return companies
    
    def save_to_csv(self, companies: List[Fortune500Company], output_path: str = "fortune500.csv"):
        """将公司列表保存为CSV文件"""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Company", "Website", "Keywords"])
            for comp in companies:
                writer.writerow([comp.name, comp.website, ",".join(comp.keywords)])
        print(f"已保存 {len(companies)} 家公司到 {output_path}")