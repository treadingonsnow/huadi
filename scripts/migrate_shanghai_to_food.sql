-- 将 shanghai.restaurant_info 迁移到 shanghai_food.restaurant_info
-- 运行方式: mysql -h 127.0.0.1 -u root -p123456 < scripts/migrate_shanghai_to_food.sql
-- 功能：
--   1. 菜系归并：80+ 原始标签 → 16 个大类
--   2. 行政区推断：优先匹配商圈，其次从地址关键词推断，不确定默认浦东新区

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

    -- 人均价格：去掉非数字字符，转数字，无效值置 0
    CASE
        WHEN `人均价格` REGEXP '^[0-9]+$'
            THEN CAST(`人均价格` AS DECIMAL(10,2))
        ELSE 0
    END AS avg_price,

    -- 评分：转 decimal，无效值置 0
    CASE
        WHEN `店铺总分` REGEXP '^[0-9]+(\\.[0-9]+)?$'
            THEN CAST(`店铺总分` AS DECIMAL(3,1))
        ELSE 0.0
    END AS rating_overall,

    -- 评论数：去掉"条评价"等文字，转 int
    CASE
        WHEN `评论总数` REGEXP '^[0-9]+'
            THEN CAST(REGEXP_REPLACE(`评论总数`, '[^0-9]', '') AS UNSIGNED)
        ELSE 0
    END AS review_count,

    -- =========================================================
    -- 菜系归并：80+ 原始标签 → 16 个大类（不超过 18 个）
    -- =========================================================
    CASE TRIM(`标签1`)
        -- 1. 本帮菜（上海本地菜及创意私房菜）
        WHEN '本帮菜'       THEN '本帮菜'
        WHEN '特色菜'       THEN '本帮菜'
        WHEN '私房菜'       THEN '本帮菜'
        WHEN '创意菜'       THEN '本帮菜'
        WHEN '美食'         THEN '本帮菜'
        WHEN '地方菜系'     THEN '本帮菜'

        -- 2. 粤菜/港式（粤菜、潮汕、港式茶餐厅）
        WHEN '粤菜馆'       THEN '粤菜/港式'
        WHEN '粤菜'         THEN '粤菜/港式'
        WHEN '广州菜'       THEN '粤菜/港式'
        WHEN '粤式茶点'     THEN '粤菜/港式'
        WHEN '茶餐厅'       THEN '粤菜/港式'
        WHEN '潮汕菜'       THEN '粤菜/港式'
        WHEN '打边炉/港式火锅' THEN '粤菜/港式'

        -- 3. 川湘菜（四川、湖南菜系）
        WHEN '湘菜'         THEN '川湘菜'
        WHEN '川菜馆'       THEN '川湘菜'
        WHEN '川菜'         THEN '川湘菜'

        -- 4. 江浙菜（江苏、浙江、安徽、淮扬）
        WHEN '浙菜'         THEN '江浙菜'
        WHEN '苏浙菜'       THEN '江浙菜'
        WHEN '淮扬菜'       THEN '江浙菜'
        WHEN '苏帮菜'       THEN '江浙菜'
        WHEN '江浙菜'       THEN '江浙菜'
        WHEN '徽菜'         THEN '江浙菜'

        -- 5. 北方菜（鲁菜、东北菜、其他北方菜系）
        WHEN '鲁菜'         THEN '北方菜'
        WHEN '东北菜'       THEN '北方菜'
        WHEN '江西菜'       THEN '北方菜'

        -- 6. 火锅（各类火锅）
        WHEN '重庆火锅'         THEN '火锅'
        WHEN '四川火锅'         THEN '火锅'
        WHEN '潮汕牛肉火锅'     THEN '火锅'
        WHEN '火锅'             THEN '火锅'
        WHEN '海鲜火锅'         THEN '火锅'
        WHEN '小火锅'           THEN '火锅'
        WHEN '云南火锅'         THEN '火锅'
        WHEN '老北京火锅'       THEN '火锅'
        WHEN '日式火锅'         THEN '火锅'
        WHEN '鱼火锅'           THEN '火锅'

        -- 7. 烧烤/烤肉（各类烧烤串烤）
        WHEN '烤串'             THEN '烧烤/烤肉'
        WHEN '日式烧烤/烤肉'    THEN '烧烤/烤肉'
        WHEN '融合烤肉'         THEN '烧烤/烤肉'
        WHEN '烧烤烤串'         THEN '烧烤/烤肉'
        WHEN '烤羊腿'           THEN '烧烤/烤肉'
        WHEN '烤鱼'             THEN '烧烤/烤肉'

        -- 8. 日本料理（日料、寿司、铁板烧）
        WHEN '日本料理'         THEN '日本料理'
        WHEN '寿司'             THEN '日本料理'
        WHEN '日式铁板烧'       THEN '日本料理'

        -- 9. 韩国料理（韩餐、韩式烤肉）
        WHEN '韩式料理'         THEN '韩国料理'
        WHEN '韩式烤肉'         THEN '韩国料理'
        WHEN '韩式小吃'         THEN '韩国料理'

        -- 10. 东南亚菜（泰、越、新加坡、南洋）
        WHEN '泰国菜'           THEN '东南亚菜'
        WHEN '越南菜'           THEN '东南亚菜'
        WHEN '东南亚菜'         THEN '东南亚菜'
        WHEN '新加坡菜'         THEN '东南亚菜'
        WHEN '南洋中菜'         THEN '东南亚菜'

        -- 11. 西餐（欧美菜系、牛排、印度菜）
        WHEN '西餐'             THEN '西餐'
        WHEN '意大利菜'         THEN '西餐'
        WHEN '法国菜'           THEN '西餐'
        WHEN '牛排'             THEN '西餐'
        WHEN '西班牙菜'         THEN '西餐'
        WHEN '印度菜'           THEN '西餐'

        -- 12. 海鲜（海鲜、小龙虾）
        WHEN '海鲜'             THEN '海鲜'
        WHEN '小龙虾'           THEN '海鲜'

        -- 13. 自助餐（各类自助）
        WHEN '自助餐'           THEN '自助餐'
        WHEN '海鲜自助'         THEN '自助餐'
        WHEN '烤肉自助'         THEN '自助餐'
        WHEN '烤涮一体自助'     THEN '自助餐'
        WHEN '寿喜锅/烧自助'    THEN '自助餐'

        -- 14. 面食/小吃（面馆、包子、快餐）
        WHEN '面馆'             THEN '面食/小吃'
        WHEN '小吃快餐'         THEN '面食/小吃'
        WHEN '快餐简餐'         THEN '面食/小吃'
        WHEN '小笼'             THEN '面食/小吃'
        WHEN '包子'             THEN '面食/小吃'
        WHEN '生煎'             THEN '面食/小吃'

        -- 15. 甜品/饮品（甜品、茶饮、咖啡、烘焙）
        WHEN '甜品'             THEN '甜品/饮品'
        WHEN '茶饮果汁'         THEN '甜品/饮品'
        WHEN '面包蛋糕'         THEN '甜品/饮品'
        WHEN '面包蛋糕甜品'     THEN '甜品/饮品'
        WHEN '咖啡'             THEN '甜品/饮品'
        WHEN '饮品'             THEN '甜品/饮品'
        WHEN '冰淇淋'           THEN '甜品/饮品'

        -- 16. 素食
        WHEN '素食'             THEN '素食'
        WHEN '素食自助'         THEN '素食'

        -- 其余未知/非餐饮分类置 NULL
        ELSE NULL
    END AS cuisine_type,

    -- =========================================================
    -- 行政区推断：
    --   第一优先：商圈（标签2）精确匹配
    --   第二优先：地址字符串关键词匹配
    --   兜底：浦东新区
    -- =========================================================
    CASE
        -- ---- 第一优先：商圈精确匹配 ----
        WHEN TRIM(`标签2`) IN ('五角场/大学路','新江湾城商圈','中原地区','平凉路/东外滩','控江地区','黄兴公园','杨浦区') THEN '杨浦区'
        WHEN TRIM(`标签2`) IN ('陆家嘴商圈','洋泾商圈','世纪大道','金桥商圈','八佰伴','张江商圈','世博园','康桥/周浦','御桥','滴水湖临港地区','曹路商圈','前滩','迪士尼','川沙','高行商圈','上南地区','塘桥商圈','金杨地区','唐镇商圈','外高桥','惠南镇商圈','源深体育中心','世博源','蒙山路','世纪公园/科技馆','联洋','花木商圈','北蔡商圈','南汇新城','三林地区','新场商圈','碧云社区','航头商圈','浦东机场/机场镇','浦东新区','泥城','江镇','卫清路','绿地风尚/万达广场','飞航广场','环城东路') THEN '浦东新区'
        WHEN TRIM(`标签2`) IN ('人民广场/南京路','南京东路商圈','外滩商圈','老西门/陆家浜路','新天地/马当路','打浦桥/田子坊','日月光中心广场','西藏南路/世博会馆','光启城','城隍庙/豫园','黄浦区') THEN '黄浦区'
        WHEN TRIM(`标签2`) IN ('南京西路商圈','静安寺商圈','闸北公园','大宁地区','苏河湾','同乐坊/江宁路','曹家渡商圈','彭浦新村商圈','彭浦镇商圈','市北工业园/汶水路') THEN '静安区'
        WHEN TRIM(`标签2`) IN ('徐家汇商圈','漕河泾/田林','万体馆','龙华/西岸','衡山路/复兴西路','肇嘉浜路/中山医院','音乐学院/五官科医院','上海南站') THEN '徐汇区'
        WHEN TRIM(`标签2`) IN ('中山公园/江苏路','北新泾/淞虹路','龙柏地区','虹桥/古北','天山','古北/仙霞新村','上海影城/新华路','长宁区','复兴西路/丁香花园') THEN '长宁区'
        WHEN TRIM(`标签2`) IN ('真如商圈','月星环球港','真北中环','长风公园/华师大','长寿路商圈','武宁地区','曹杨地区','丰庄','中山北路/甘泉地区','普陀区') THEN '普陀区'
        WHEN TRIM(`标签2`) IN ('临平路/和平公园','大柏树','虹口龙之梦','北外滩/外白渡桥','海宁路/七浦路','四川北路/海伦路','曲阳地区','凉城/江湾镇','虹口足球场/鲁迅公园','大连路地铁站','赤峰路') THEN '虹口区'
        WHEN TRIM(`标签2`) IN ('莲花路/南方商城','七宝商圈','虹桥枢纽','虹桥镇商圈','莘庄商圈','华漕商圈','浦江镇商圈','春申地区','老闵行/交大师大','虹桥火车站/国展中心','虹桥火车站/机场','万源城/东兰路','虹梅路商圈','闵浦','颛桥/北桥','交大闵行校区','合川路','闵行开发区') THEN '闵行区'
        WHEN TRIM(`标签2`) IN ('江桥万达广场','南翔商圈','嘉定新城','江桥','嘉定镇','外冈镇商圈','安亭黄渡镇','马陆镇商圈','安亭镇商圈','安亭新源路','嘉定区') THEN '嘉定区'
        WHEN TRIM(`标签2`) IN ('宝山万达广场','宝山区','宝山城区/吴淞','庙行/共康','大华地区','高境商圈','上海大学','美兰湖') THEN '宝山区'
        WHEN TRIM(`标签2`) IN ('松江万达广场','泗泾镇商圈','九亭商圈','松江镇','松江大学城','新桥商圈','松江区') THEN '松江区'
        WHEN TRIM(`标签2`) IN ('金汇镇商圈','南桥商圈','南桥百联购物中心','奉城镇商圈','海湾旅游区商圈','西渡街道商圈','青村','唐湾镇/曹行镇','奉贤区') THEN '奉贤区'
        WHEN TRIM(`标签2`) IN ('金山万达','金山区','枫泾镇商圈','金山卫商圈','石化商圈','朱泾镇商圈','廊下商圈','百联金山购物中心') THEN '金山区'
        WHEN TRIM(`标签2`) IN ('青浦区','青浦城区','国家会展中心','华新镇商圈','赵巷镇商圈','凤溪','重固镇商圈','徐泾商圈') THEN '青浦区'
        WHEN TRIM(`标签2`) IN ('长兴岛','陈家镇商圈','崇明区','堡镇商圈') THEN '崇明区'
        WHEN TRIM(`标签2`) IN ('淮海路') THEN '黄浦区'
        WHEN TRIM(`标签2`) IN ('易买得','万达广场') THEN '浦东新区'

        -- ---- 第二优先：从地址关键词推断 ----
        WHEN `店铺地址` LIKE '%杨浦%'   THEN '杨浦区'
        WHEN `店铺地址` LIKE '%浦东%'   THEN '浦东新区'
        WHEN `店铺地址` LIKE '%黄浦%'   THEN '黄浦区'
        WHEN `店铺地址` LIKE '%静安%'   THEN '静安区'
        WHEN `店铺地址` LIKE '%徐汇%'   THEN '徐汇区'
        WHEN `店铺地址` LIKE '%长宁%'   THEN '长宁区'
        WHEN `店铺地址` LIKE '%普陀%'   THEN '普陀区'
        WHEN `店铺地址` LIKE '%虹口%'   THEN '虹口区'
        WHEN `店铺地址` LIKE '%闵行%'   THEN '闵行区'
        WHEN `店铺地址` LIKE '%嘉定%'   THEN '嘉定区'
        WHEN `店铺地址` LIKE '%宝山%'   THEN '宝山区'
        WHEN `店铺地址` LIKE '%松江%'   THEN '松江区'
        WHEN `店铺地址` LIKE '%奉贤%'   THEN '奉贤区'
        WHEN `店铺地址` LIKE '%金山%'   THEN '金山区'
        WHEN `店铺地址` LIKE '%青浦%'   THEN '青浦区'
        WHEN `店铺地址` LIKE '%崇明%'   THEN '崇明区'

        -- ---- 兜底：不确定一律写浦东新区 ----
        ELSE '浦东新区'
    END AS district,

    -- 商圈
    NULLIF(TRIM(`标签2`), '') AS business_area,

    'dianping' AS data_source,
    NOW() AS crawl_time

FROM shanghai.restaurant_info
-- 过滤掉明显非餐饮数据（如洗浴中心）
WHERE `标签1` NOT IN ('洗浴中心')

-- 跳过已存在的记录（以 restaurant_id 为准）
ON DUPLICATE KEY UPDATE
    update_time = update_time;  -- 不覆盖，仅忽略重复

-- 迁移结果统计
SELECT
    CONCAT('迁移完成，当前 restaurant_info 总行数: ', COUNT(*)) AS result
FROM restaurant_info;

SELECT
    district,
    COUNT(*) AS cnt
FROM restaurant_info
WHERE data_source = 'dianping'
GROUP BY district
ORDER BY cnt DESC;

SELECT
    cuisine_type,
    COUNT(*) AS cnt
FROM restaurant_info
WHERE data_source = 'dianping'
GROUP BY cuisine_type
ORDER BY cnt DESC;
