#!/bin/bash
# 部署脚本
# 功能：
# - 检查 Docker 和 Docker Compose 是否安装
# - 复制 .env 为 .env（如不存在）
# - 复制 config/config.example.yaml 为 config/config.yaml（如不存在）
# - 构建并启动所有服务：docker compose up -d --build
# - 等待 MySQL 就绪后执行数据库初始化：scripts/init_db.sql
# - 输出服务访问地址
# 用法：bash scripts/deploy.sh
