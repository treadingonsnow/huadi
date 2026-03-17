# MySQL 远程连接指南

> 操作人：组员（非服务器端）| 前提：许嘉赫已完成服务器搭建

---

## 你需要的信息

向许嘉赫确认以下信息后再操作：

| 项目 | 内容 |
|------|------|
| 服务器 IP | 许嘉赫 Windows 主机的局域网 IP |
| 端口 | 3306 |
| 用户名 | team |
| 密码 | team123456 |
| 数据库名 | shanghai_food |

---

## 第一步：测试网络连通性

```bash
# 替换为实际 IP
ping 192.168.x.x

# 测试 3306 端口是否开放，这个指令需要下载netcat
nc -zv 192.168.x.x 3306
# 看到 "succeeded" 才能继续
```

如果 ping 不通或端口不通，让许嘉赫检查服务器配置。

---

## 第二步：安装 MySQL 客户端（只需要客户端，不需要服务器）

```bash
# macOS
brew install mysql-client
echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Linux / WSL
sudo apt install -y mysql-client
```

---

## 第三步：连接测试

```bash
mysql -h 192.168.x.x -P 3306 -u team -p
# 输入密码：team123456
```

连接成功后验证：
```sql
SHOW DATABASES;
USE shanghai_food;
SHOW TABLES;
EXIT;
```

看到 `restaurant_info`、`sys_user` 等表说明连接正常。

---

## 第四步：配置 .env 文件

在项目根目录复制配置文件：
```bash
cp .env.example .env
nano .env
```

编辑 `.env`，只需修改 MySQL 相关的几行：
```env
MYSQL_HOST=192.168.x.x
MYSQL_PORT=3306
MYSQL_USER=team
MYSQL_PASSWORD=team123456
MYSQL_DATABASE=shanghai_food
```

其余配置保持默认即可。

---

## 常见问题

**`Connection refused` / 连接被拒绝**
→ 许嘉赫的 MySQL 服务没启动，让他执行 `sudo service mysql start`


**`Can't connect to MySQL server` / 超时**
→ 端口转发失效（WSL IP 变了），让许嘉赫更新转发规则后重试

**连接时断时续**
→ WSL 可能休眠了，让许嘉赫检查 WSL 是否还在运行
