# -*- coding:utf-8 -*-
import json
import sys

from utils.logger import logger
from utils.spider_config import spider_config


CREATE_INFO_SQL = """
CREATE TABLE IF NOT EXISTS `restaurant_info` (
    `店铺id`   VARCHAR(64)  NOT NULL,
    `店铺名`   VARCHAR(255) DEFAULT NULL,
    `评论总数` VARCHAR(64)  DEFAULT NULL,
    `人均价格` VARCHAR(64)  DEFAULT NULL,
    `标签1`    VARCHAR(128) DEFAULT NULL,
    `标签2`    VARCHAR(128) DEFAULT NULL,
    `店铺地址` VARCHAR(512) DEFAULT NULL,
    `详情链接` VARCHAR(512) DEFAULT NULL,
    `图片链接` VARCHAR(512) DEFAULT NULL,
    `店铺均分` TEXT         DEFAULT NULL,
    `推荐菜`   TEXT         DEFAULT NULL,
    `店铺总分` VARCHAR(64)  DEFAULT NULL,
    `店铺电话` VARCHAR(128) DEFAULT NULL,
    `其他信息` TEXT         DEFAULT NULL,
    PRIMARY KEY (`店铺id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_REVIEW_SQL = """
CREATE TABLE IF NOT EXISTS `restaurant_review` (
    `店铺id`       VARCHAR(64) NOT NULL,
    `评论摘要`     JSON        DEFAULT NULL,
    `评论总数`     VARCHAR(64) DEFAULT NULL,
    `好评个数`     VARCHAR(64) DEFAULT NULL,
    `中评个数`     VARCHAR(64) DEFAULT NULL,
    `差评个数`     VARCHAR(64) DEFAULT NULL,
    `带图评论个数` VARCHAR(64) DEFAULT NULL,
    `精选评论`     JSON        DEFAULT NULL,
    PRIMARY KEY (`店铺id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def _to_json(value):
    """将 list/dict 序列化为 JSON 字符串，其他类型原样返回字符串。"""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value) if value is not None else None


class MySQLSaver:
    def __init__(self):
        cfg = spider_config.MYSQL_CONFIG
        try:
            import pymysql
            # 先不指定数据库，确保数据库存在
            conn_no_db = pymysql.connect(
                host=cfg['host'],
                port=int(cfg['port']),
                user=cfg['user'],
                password=cfg['password'],
                charset='utf8mb4',
                autocommit=True,
            )
            with conn_no_db.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn_no_db.close()

            self.conn = pymysql.connect(
                host=cfg['host'],
                port=int(cfg['port']),
                user=cfg['user'],
                password=cfg['password'],
                database=cfg['database'],
                charset='utf8mb4',
                autocommit=True,
            )
            self._init_tables()
        except Exception as e:
            logger.warning(f'MySQL 连接失败，请检查配置或确认 MySQL 已启动：{e}')
            sys.exit()

    def _init_tables(self):
        with self.conn.cursor() as cur:
            cur.execute(CREATE_INFO_SQL)
            cur.execute(CREATE_REVIEW_SQL)

    def save_data(self, data, data_type):
        assert data_type in ['search', 'detail', 'review']
        if data_type == 'search':
            self._save_search(data)
        elif data_type == 'detail':
            self._save_detail(data)
        elif data_type == 'review':
            self._save_review(data)

    def _save_search(self, data):
        sql = """
        INSERT INTO `restaurant_info`
            (`店铺id`,`店铺名`,`评论总数`,`人均价格`,`标签1`,`标签2`,
             `店铺地址`,`详情链接`,`图片链接`,`店铺均分`,`推荐菜`,`店铺总分`,
             `店铺电话`,`其他信息`)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            `店铺名`=VALUES(`店铺名`), `评论总数`=VALUES(`评论总数`),
            `人均价格`=VALUES(`人均价格`), `标签1`=VALUES(`标签1`),
            `标签2`=VALUES(`标签2`), `店铺地址`=VALUES(`店铺地址`),
            `详情链接`=VALUES(`详情链接`), `图片链接`=VALUES(`图片链接`),
            `店铺均分`=VALUES(`店铺均分`), `推荐菜`=VALUES(`推荐菜`),
            `店铺总分`=VALUES(`店铺总分`), `店铺电话`=VALUES(`店铺电话`),
            `其他信息`=VALUES(`其他信息`)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                data.get('店铺id'),
                data.get('店铺名'),
                data.get('评论总数'),
                data.get('人均价格'),
                data.get('标签1'),
                data.get('标签2'),
                data.get('店铺地址'),
                data.get('详情链接'),
                data.get('图片链接'),
                _to_json(data.get('店铺均分')),
                data.get('推荐菜'),
                data.get('店铺总分'),
                data.get('店铺电话'),
                data.get('其他信息'),
            ))

    def _save_detail(self, data):
        sql = """
        INSERT INTO `restaurant_info`
            (`店铺id`,`店铺名`,`评论总数`,`人均价格`,`店铺地址`,`店铺电话`,`其他信息`)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            `店铺名`=VALUES(`店铺名`), `评论总数`=VALUES(`评论总数`),
            `人均价格`=VALUES(`人均价格`), `店铺地址`=VALUES(`店铺地址`),
            `店铺电话`=VALUES(`店铺电话`), `其他信息`=VALUES(`其他信息`)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                data.get('店铺id'),
                data.get('店铺名'),
                data.get('评论总数'),
                data.get('人均价格'),
                data.get('店铺地址'),
                data.get('店铺电话'),
                data.get('其他信息'),
            ))

    def _save_review(self, data):
        sql = """
        INSERT INTO `restaurant_review`
            (`店铺id`,`评论摘要`,`评论总数`,`好评个数`,`中评个数`,
             `差评个数`,`带图评论个数`,`精选评论`)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            `评论摘要`=VALUES(`评论摘要`), `评论总数`=VALUES(`评论总数`),
            `好评个数`=VALUES(`好评个数`), `中评个数`=VALUES(`中评个数`),
            `差评个数`=VALUES(`差评个数`), `带图评论个数`=VALUES(`带图评论个数`),
            `精选评论`=VALUES(`精选评论`)
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                data.get('店铺id'),
                _to_json(data.get('评论摘要')),
                str(data.get('评论总数', '')),
                data.get('好评个数'),
                data.get('中评个数'),
                data.get('差评个数'),
                data.get('带图评论个数'),
                _to_json(data.get('精选评论')),
            ))
