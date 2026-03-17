# MySQL 共享服务器搭建指南

> 操作人：许嘉赫（服务器端）| 环境：WSL2 Ubuntu 24.04

---

## 第一步：安装 MySQL

```bash
sudo apt update
sudo apt install -y mysql-server
```

验证安装成功：
```bash
mysql --version
# 输出类似：mysql  Ver 8.x.x
```

---

## 第二步：启动 MySQL

WSL 不支持 systemctl，用 service 命令：
```bash
sudo service mysql start
sudo service mysql status   # 确认显示 running
```

---

## 第三步：初始化数据库

```bash
sudo mysql < /home/xjh01/ShangHaiFoodData/scripts/init_db.sql
```

验证：
```bash
sudo mysql -e "USE shanghai_food; SHOW TABLES; SELECT username, role FROM sys_user;"
# 应看到 4 张表，以及 admin 和 analyst 两个账号
```

---

## 第四步：允许远程连接

### 4.1 修改 MySQL 配置

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

找到这行并修改：
```
# 改前
bind-address = 127.0.0.1

# 改后
bind-address = 0.0.0.0
```

保存：Ctrl+O → Enter → Ctrl+X

重启 MySQL：
```bash
sudo service mysql restart
```

### 4.2 创建远程账号

```bash
sudo mysql
```

```sql
CREATE USER 'team'@'%' IDENTIFIED BY 'team123456';
GRANT ALL PRIVILEGES ON shanghai_food.* TO 'team'@'%';
FLUSH PRIVILEGES;
EXIT;
```

---

## 第五步：Windows 端口转发（让局域网组员能访问）

**在 Windows 上以管理员身份打开 PowerShell**，执行：

```powershell
# 1. 查当前 WSL 的 IP
wsl hostname -I
# 记下输出的 IP，例如 172.26.x.x

# 2. 设置端口转发（把 Windows:3306 转发到 WSL:3306）
#    把下面的 172.26.x.x 换成上一步查到的实际 IP
netsh interface portproxy add v4tov4 listenport=3306 listenaddress=0.0.0.0 connectport=3306 connectaddress=172.26.x.x

# 3. 防火墙放行 3306 端口
netsh advfirewall firewall add rule name="MySQL WSL" dir=in action=allow protocol=TCP localport=3306
```

### 查 Windows 本机局域网 IP（告诉组员）

```powershell
ipconfig | findstr "IPv4"
# 找到类似 192.168.x.x 的地址，这个 IP 告诉组员
```

---

## 每次重启 WSL 后需要做的事

WSL 重启后 MySQL 停止、IP 可能变化，每次执行：

```bash
# 1. 在 WSL 里启动 MySQL
sudo service mysql start

# 2. 查新的 WSL IP
hostname -I
```

如果 WSL IP 变了，在 **Windows 管理员 PowerShell** 里更新转发规则：

```powershell
# 删除旧规则
netsh interface portproxy delete v4tov4 listenport=3306 listenaddress=0.0.0.0

# 添加新规则（换成新 IP）
netsh interface portproxy add v4tov4 listenport=3306 listenaddress=0.0.0.0 connectport=3306 connectaddress=<新WSL IP>
```

**建议**：把上面两条命令保存为 `update_mysql_proxy.ps1`，每次右键"以管理员身份运行"即可。

---

## 账号信息汇总（告诉组员）

| 项目 | 内容 |
|------|------|
| 服务器 IP | Windows 主机局域网 IP（用 `ipconfig` 查） |
| 端口 | 3306 |
| 用户名 | team |
| 密码 | team123456 |
| 数据库名 | shanghai_food |

预置登录账号：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| analyst | analyst123 | 普通用户 |
