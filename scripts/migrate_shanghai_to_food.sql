-- 将 shanghai.restaurant_info 迁移到 shanghai_food.restaurant_info
-- 运行方式: mysql -h 127.0.0.1 -u root -p123456 < scripts/migrate_shanghai_to_food.sql

USE shanghai_food;

INSERT INTO restaurant_info (
    restaurant_id,
    restaurant_name,
    address,
    phone,
    avg_price,
    rating_overall,
    review_count,
    cuisine_type,
    district,
    business_area,
    data_source,
    crawl_time
)
SELECT
    CONCAT('dp_', `店铺id`) AS restaurant_id,
    `店铺名` AS restaurant_name,

    -- 地址："-" 视为 NULL
    NULLIF(TRIM(`店铺地址`), '-') AS address,

    -- 电话
    NULLIF(TRIM(`店铺电话`), '') AS phone,

    -- 人均价格：去掉 ￥ 符号，转数字，无效值置 0
    CASE
        WHEN `人均价格` REGEXP '^￥[0-9]+$'
            THEN CAST(REPLACE(`人均价格`, '￥', '') AS DECIMAL(10,2))
        ELSE 0
    END AS avg_price,

    -- 评分：转 decimal，无效值置 0
    CASE
        WHEN `店铺总分` REGEXP '^[0-9]+(\\.[0-9]+)?$'
            THEN CAST(`店铺总分` AS DECIMAL(3,1))
        ELSE 0.0
    END AS rating_overall,

    -- 评论数：去掉"条评价"，转 int
    CASE
        WHEN `评论总数` REGEXP '^[0-9]+'
            THEN CAST(REGEXP_REPLACE(`评论总数`, '[^0-9]', '') AS UNSIGNED)
        ELSE 0
    END AS review_count,

    -- 菜系类型
    NULLIF(TRIM(`标签1`), '') AS cuisine_type,

    -- 按商圈推断所属区
    CASE `标签2`
        WHEN '五角场/大学路'     THEN '杨浦区'
        WHEN '新江湾城商圈'      THEN '杨浦区'
        WHEN '陆家嘴商圈'        THEN '浦东新区'
        WHEN '洋泾商圈'          THEN '浦东新区'
        WHEN '世纪大道'          THEN '浦东新区'
        WHEN '金桥商圈'          THEN '浦东新区'
        WHEN '八佰伴'            THEN '浦东新区'
        WHEN '人民广场/南京路'   THEN '黄浦区'
        WHEN '南京东路商圈'      THEN '黄浦区'
        WHEN '莲花路/南方商城'   THEN '闵行区'
        WHEN '七宝商圈'          THEN '闵行区'
        WHEN '虹桥枢纽'          THEN '闵行区'
        WHEN '中山公园/江苏路'   THEN '长宁区'
        WHEN '真如商圈'          THEN '普陀区'
        WHEN '闸北公园'          THEN '静安区'
        WHEN '临平路/和平公园'   THEN '虹口区'
        WHEN '江桥万达广场'      THEN '嘉定区'
        WHEN '南翔商圈'          THEN '嘉定区'
        WHEN '金汇镇商圈'        THEN '奉贤区'
        WHEN '徐家汇商圈'        THEN '徐汇区'
        WHEN '漕河泾/田林'       THEN '徐汇区'
        WHEN '万体馆'            THEN '徐汇区'
        WHEN '外滩商圈'          THEN '黄浦区'
        WHEN '老西门/陆家浜路'   THEN '黄浦区'
        WHEN '静安寺商圈'        THEN '静安区'
        WHEN '月星环球港'        THEN '普陀区'
        WHEN '真北中环'          THEN '普陀区'
        WHEN '大柏树'            THEN '虹口区'
        WHEN '虹口龙之梦'        THEN '虹口区'
        WHEN '北新泾/淞虹路'     THEN '长宁区'
        WHEN '龙柏地区'          THEN '长宁区'
        WHEN '虹桥镇商圈'        THEN '闵行区'
        WHEN '莘庄商圈'          THEN '闵行区'
        WHEN '华漕商圈'          THEN '闵行区'
        WHEN '浦江镇商圈'        THEN '闵行区'
        WHEN '张江商圈'          THEN '浦东新区'
        WHEN '世博园'            THEN '浦东新区'
        WHEN '康桥/周浦'         THEN '浦东新区'
        WHEN '御桥'              THEN '浦东新区'
        WHEN '滴水湖临港地区'    THEN '浦东新区'
        WHEN '嘉定新城'          THEN '嘉定区'
        WHEN '宝山万达广场'      THEN '宝山区'
        WHEN '宝山区'            THEN '宝山区'
        WHEN '宝山城区/吴淞'     THEN '宝山区'
        WHEN '松江万达广场'      THEN '松江区'
        WHEN '泗泾镇商圈'        THEN '松江区'
        WHEN '南桥商圈'          THEN '奉贤区'
        WHEN '金山万达'          THEN '金山区'
        WHEN '金山区'            THEN '金山区'
        WHEN '长风公园/华师大'   THEN '普陀区'
        ELSE NULL
    END AS district,

    -- 商圈
    NULLIF(TRIM(`标签2`), '') AS business_area,

    'dianping' AS data_source,
    NOW() AS crawl_time

FROM shanghai.restaurant_info

-- 跳过已存在的记录（以 restaurant_id 为准）
ON DUPLICATE KEY UPDATE
    update_time = update_time;  -- 不覆盖，仅忽略重复

SELECT
    CONCAT('迁移完成，当前 restaurant_info 总行数: ', COUNT(*)) AS result
FROM restaurant_info;
