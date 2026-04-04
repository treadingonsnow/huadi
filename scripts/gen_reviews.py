"""为每个餐厅生成 10 条模拟评论数据并插入 restaurant_review 表"""
import random
import uuid
from datetime import datetime, timedelta
import pymysql

# 数据库配置
DB = dict(host="localhost", port=3306, user="team", password="team123456",
          database="shanghai_food", charset="utf8mb4")

# 评论模板（正面/中性/负面）
POSITIVE = [
    "味道非常好，食材新鲜，下次还会来！",
    "环境很舒适，服务态度好，菜品口味地道。",
    "性价比超高，分量足，强烈推荐！",
    "朋友聚餐首选，菜品丰富，口感一流。",
    "厨师手艺很棒，每道菜都很用心，赞！",
    "上菜速度快，服务员很热情，体验很好。",
    "食材新鲜，调味恰到好处，非常满意。",
    "装修精致，氛围好，适合约会或家庭聚餐。",
    "招牌菜真的很好吃，下次还要带朋友来。",
    "口味正宗，价格实惠，附近最好吃的一家。",
    "菜量很足，味道鲜美，服务周到，五星好评！",
    "环境干净整洁，菜品色香味俱全，非常推荐。",
]

NEUTRAL = [
    "味道还可以，中规中矩，价格偏贵一点。",
    "整体还行，但等位时间有点长。",
    "菜品口味一般，环境不错，服务还好。",
    "性价比一般，味道说得过去，不会特意再来。",
    "口味偏淡，可能不太适合重口味的朋友。",
    "服务一般，菜品还行，位置比较方便。",
    "味道中等，没有特别惊艳，但也不差。",
]

NEGATIVE = [
    "等了很久才上菜，味道也一般，有点失望。",
    "菜品偏咸，服务态度有待改善。",
    "性价比不高，分量少，不太推荐。",
    "环境嘈杂，菜品口味不稳定，体验较差。",
    "上菜慢，服务员态度冷淡，不会再来了。",
]

def random_review(rating: float) -> str:
    if rating >= 4.5:
        return random.choice(POSITIVE)
    elif rating >= 3.5:
        return random.choice(POSITIVE + NEUTRAL)
    elif rating >= 3.0:
        return random.choice(NEUTRAL)
    else:
        return random.choice(NEGATIVE + NEUTRAL)

def random_rating(base: float) -> float:
    """在基础评分附近随机浮动"""
    r = base + random.uniform(-0.8, 0.8)
    return round(max(1.0, min(5.0, r)), 1)

def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()

    # 获取所有餐厅
    cur.execute("SELECT restaurant_id, rating_overall FROM restaurant_info")
    restaurants = cur.fetchall()
    print(f"共 {len(restaurants)} 家餐厅，开始生成评论...")

    rows = []
    now = datetime.now()
    for rid, base_rating in restaurants:
        base = float(base_rating) if base_rating else 4.0
        for _ in range(10):
            rating = random_rating(base)
            sub_rating = random_rating(base)
            review_time = now - timedelta(days=random.randint(1, 365))
            sentiment = round(min(1.0, max(-1.0, (rating - 3) / 2 + random.uniform(-0.1, 0.1))), 2)
            rows.append((
                str(uuid.uuid4()),          # review_id
                rid,                         # restaurant_id
                f"user_{random.randint(10000, 99999)}",  # user_id
                rating,                      # rating_overall
                sub_rating,                  # rating_taste
                random_rating(base),         # rating_environment
                random_rating(base),         # rating_service
                random_review(rating),       # review_content
                review_time.strftime("%Y-%m-%d %H:%M:%S"),  # review_time
                random.randint(0, 50),       # like_count
                sentiment,                   # sentiment_score
                "meituan",                   # data_source
            ))

    sql = """INSERT INTO restaurant_review
        (review_id, restaurant_id, user_id, rating_overall, rating_taste,
         rating_environment, rating_service, review_content, review_time,
         like_count, sentiment_score, data_source)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

    # 分批插入
    batch = 500
    for i in range(0, len(rows), batch):
        cur.executemany(sql, rows[i:i+batch])
        conn.commit()
        print(f"  已插入 {min(i+batch, len(rows))}/{len(rows)} 条")

    cur.execute("SELECT COUNT(*) FROM restaurant_review")
    total = cur.fetchone()[0]
    print(f"完成！restaurant_review 表现有 {total} 条评论。")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
