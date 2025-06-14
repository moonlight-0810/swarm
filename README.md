# 🐝 SwarmChemistry Railway服务器

这是SwarmChemistry项目的云端同步服务器，部署在Railway平台上。

## 🚀 功能

- 接收网页端用户发送的粒子参数
- 为Unity本地端提供实时数据API
- 支持全球用户同步
- 自动扩展和高可用性

## 📡 API端点

### 网页端使用
- `POST /api/swarm-data` - 提交粒子参数

### Unity端使用
- `GET /api/swarm-data/latest` - 获取最新参数
- `GET /api/stats` - 获取统计信息

### 监控
- `GET /health` - 健康检查
- `GET /` - 服务器状态页面

## 🛠️ 本地开发

```bash
npm install
npm start
```

## 🌐 部署到Railway

1. 连接GitHub仓库到Railway
2. Railway会自动检测并部署
3. 获取部署URL并配置到网页端

## 📊 环境变量

Railway会自动设置以下变量：
- `PORT` - 服务器端口
- `RAILWAY_REGION` - 部署区域
- `NODE_ENV` - 运行环境 