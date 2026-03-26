#!/usr/bin/env python3
"""
从 hot-pot notebook 提取可用数据并补充生成 749 条测试数据，写入 MySQL
运行：python3 scripts/import_hotpot.py
"""
import hashlib
import random
import sys
import os

# 允许直接在项目根目录运行
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text

# ── 配置 ──────────────────────────────────────────────────
MYSQL_URL = "mysql+pymysql://team:team123456@192.168.54.48:3306/shanghai_food?charset=utf8mb4"

# ── 数据：从 notebook 输出提取的真实餐厅名 ─────────────────
REAL_NAMES = [
    "蜀城巷子老成都火锅(宜山路店)", "旬野菜日本料理和牛寿喜锅专门店(浦东店)",
    "小肥羊(光启城时尚购物中心店)", "薪火重庆本味火锅", "蜀大侠(江宁路店)",
    "三生小馆", "觅香·老成都串串香", "年糕李(静安店)", "韩式年糕火锅",
    "亦锅亦笼塔吉锅料理", "辉哥海鲜火锅(洛克外滩源店)", "洋房火锅(新天地店)",
    "季悦火锅(锦江店)", "洋房火锅(岳阳路店)", "季悦火锅(虹桥迎宾馆店)",
    "宙司汇英式宫廷Hotpot&Dessert(香港直営店)", "曹疯子老火锅", "港氽港式海鲜火锅",
    "玲姐·海鲜火锅", "三人行骨头王火锅(徐汇总店)", "哥老官重庆美蛙鱼头(日月光店)",
    "哥老官重庆美蛙鱼头(人民广场店)", "上上谦串串香火锅(虹口龙之梦店)",
    "上上谦串串香火锅(新梅联合广场店)", "川溢香老成都火锅(普陀店)",
    "呷哺呷哺(白玉兰广场店)", "红魔重庆美蛙火锅(宝山龙湖天街店)",
    "鼎尊锅物料理(斜土路店)", "云蜀哥鲜牛肉美蛙鱼火锅", "协乐海鲜火锅",
    "花马天堂古道火锅", "蟹逅港式海鲜火锅",
]

# ── 模板：用于批量生成餐厅名 ───────────────────────────────
BRAND_PREFIXES = [
    "海底捞", "小龙坎", "大龙燚", "巴奴毛肚", "蜀大侠", "老四川", "重庆胖子",
    "鱼火锅", "老成都", "串串香", "鸳鸯锅", "牛蛙火锅", "美蛙鱼头",
    "椰子鸡", "猪肚鸡", "港式火锅", "日式涮涮锅", "韩式年糕锅",
    "天府红", "辣府", "蜀九香", "袁记火锅", "德庄重庆", "小辉哥",
    "大渔铁锅", "筷牛烧烤火锅", "九宫格老火锅", "冒菜锅", "麻辣香锅",
    "鱼你在一起", "三汁焖锅", "沸点小串", "围炉煮茶火锅", "浓情骨汤锅",
]

BRANCH_SUFFIXES = [
    "(浦东店)", "(静安店)", "(黄浦店)", "(徐汇店)", "(长宁店)", "(普陀店)",
    "(虹口店)", "(杨浦店)", "(闵行店)", "(宝山店)", "(嘉定店)", "(松江店)",
    "(青浦店)", "(奉贤店)", "(新天地店)", "(陆家嘴店)", "(南京西路店)",
    "(淮海路店)", "(徐家汇店)", "(中山公园店)", "(五角场店)", "(莘庄店)",
    "(七宝店)", "(虹桥店)", "(张江店)", "(漕宝路店)", "(大宁店)", "(杨浦大学城店)",
    "(宝山万达店)", "(嘉定新城店)", "(松江万达店)", "(金山店)", "(崇明店)",
    "(奉贤南桥店)", "(青浦万达店)",
]

# ── 上海各区分布（按真实餐饮密度加权）──────────────────────
DISTRICTS = [
    ("浦东新区", 0.20), ("黄浦区", 0.12), ("静安区", 0.12), ("徐汇区", 0.11),
    ("长宁区", 0.07), ("普陀区", 0.07), ("虹口区", 0.06), ("杨浦区", 0.06),
    ("闵行区", 0.07), ("宝山区", 0.04), ("嘉定区", 0.03), ("松江区", 0.02),
    ("青浦区", 0.01), ("奉贤区", 0.01), ("金山区", 0.005), ("崇明区", 0.005),
]
DISTRICT_NAMES, DISTRICT_WEIGHTS = zip(*DISTRICTS)

# ── 星级 → 评分映射 ────────────────────────────────────────
STAR_MAP = {
    "五星商户":   (4.6, 5.0),
    "准五星商户": (4.2, 4.7),
    "四星商户":   (3.8, 4.3),
    "准四星商户": (3.4, 3.9),
    "三星商户":   (3.0, 3.6),
}
# notebook 中的分布：约 47% 五星，47% 准五星，5% 四星，<1% 其他
STAR_DIST = ["五星商户"] * 352 + ["准五星商户"] * 352 + ["四星商户"] * 38 + ["准四星商户"] * 5 + ["三星商户"] * 2
random.shuffle(STAR_DIST)


def _rid(name: str) -> str:
    return "hotpot_" + hashlib.md5(name.encode()).hexdigest()[:12]


def _rating(star: str, rng: random.Random) -> float:
    lo, hi = STAR_MAP[star]
    return round(rng.uniform(lo, hi), 1)


def _price(rng: random.Random) -> int:
    """上海火锅人均：50-1000，集中在 80-250"""
    weights = [5, 30, 35, 20, 7, 2, 1]
    ranges  = [(50, 80), (80, 150), (150, 250), (250, 400), (400, 600), (600, 800), (800, 1073)]
    bucket  = rng.choices(ranges, weights=weights)[0]
    return rng.randint(*bucket)


def _comment(rng: random.Random) -> int:
    """评论数：53-41585，大多数在 200-5000"""
    weights = [10, 40, 30, 15, 4, 1]
    ranges  = [(53, 200), (200, 2000), (2000, 8000), (8000, 15000), (15000, 30000), (30000, 42000)]
    bucket  = rng.choices(ranges, weights=weights)[0]
    return rng.randint(*bucket)


def build_records(n: int = 749) -> list[dict]:
    rng = random.Random(42)  # 固定种子，每次生成一致
    records = []

    # 先插入 notebook 中的真实餐厅名
    used_names = set()
    for i, name in enumerate(REAL_NAMES):
        star = STAR_DIST[i % len(STAR_DIST)]
        district = rng.choices(DISTRICT_NAMES, weights=DISTRICT_WEIGHTS)[0]
        records.append({
            "restaurant_id":   _rid(name),
            "restaurant_name": name,
            "cuisine_type":    "火锅",
            "district":        district,
            "avg_price":       _price(rng),
            "rating_overall":  _rating(star, rng),
            "review_count":    _comment(rng),
            "data_source":     "dianping",
            "address":         f"上海市{district}（详细地址待补充）",
        })
        used_names.add(name)

    # 生成剩余数量
    idx = len(records)
    while len(records) < n:
        prefix = rng.choice(BRAND_PREFIXES)
        suffix = rng.choice(BRANCH_SUFFIXES)
        name = prefix + suffix
        if name in used_names:
            continue
        used_names.add(name)
        star = STAR_DIST[idx % len(STAR_DIST)]
        district = rng.choices(DISTRICT_NAMES, weights=DISTRICT_WEIGHTS)[0]
        records.append({
            "restaurant_id":   _rid(name),
            "restaurant_name": name,
            "cuisine_type":    "火锅",
            "district":        district,
            "avg_price":       _price(rng),
            "rating_overall":  _rating(star, rng),
            "review_count":    _comment(rng),
            "data_source":     "dianping",
            "address":         f"上海市{district}（详细地址待补充）",
        })
        idx += 1

    return records


def import_to_mysql(records: list[dict]) -> tuple[int, int]:
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    inserted = skipped = 0

    insert_sql = text("""
        INSERT IGNORE INTO restaurant_info
            (restaurant_id, restaurant_name, address, cuisine_type,
             district, avg_price, rating_overall, review_count, data_source)
        VALUES
            (:restaurant_id, :restaurant_name, :address, :cuisine_type,
             :district, :avg_price, :rating_overall, :review_count, :data_source)
    """)

    with engine.begin() as conn:
        for i, rec in enumerate(records, 1):
            result = conn.execute(insert_sql, rec)
            if result.rowcount:
                inserted += 1
            else:
                skipped += 1
            if i % 100 == 0:
                print(f"  进度：{i}/{len(records)}")

    return inserted, skipped


if __name__ == "__main__":
    print("生成测试数据…")
    records = build_records(749)
    print(f"共生成 {len(records)} 条上海火锅餐厅记录")

    print("连接 MySQL，写入数据…")
    try:
        inserted, skipped = import_to_mysql(records)
        print(f"\n完成！新增 {inserted} 条，跳过已存在 {skipped} 条")
        print("✅ 数据库已有测试数据，可以启动项目演示了")
    except Exception as e:
        print(f"❌ 导入失败：{e}")
        sys.exit(1)
