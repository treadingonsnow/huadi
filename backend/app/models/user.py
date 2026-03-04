# 用户 ORM 模型
# 对应数据表：sys_user
# 字段：
# - user_id       INT PK AUTO_INCREMENT  用户ID
# - username      VARCHAR(50) UNIQUE      用户名
# - password_hash VARCHAR(128)            密码哈希（BCrypt）
# - phone         VARCHAR(20)             手机号
# - email         VARCHAR(100)            邮箱
# - role          VARCHAR(20)             角色（admin/analyst/editor/user）
# - is_active     BOOLEAN                 是否启用
# - create_time   DATETIME                创建时间
# - last_login    DATETIME                最后登录时间
#
# 关联表：user_favorites（用户收藏）
# - user_id, restaurant_id, create_time
