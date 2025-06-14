// SwarmChemistry Railway部署服务器
// 用于接收网页端数据并提供给Unity获取

const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000; // Railway会自动设置PORT环境变量

// 中间件
app.use(cors()); // 允许跨域请求
app.use(express.json({ limit: '10mb' })); // 解析JSON数据

// 数据存储（Railway环境使用内存存储）
let swarmDataStore = [];
const MAX_STORED_DATA = 50; // 限制存储数量以节省内存

// 🌐 接收网页端发送的粒子参数
app.post('/api/swarm-data', async (req, res) => {
    try {
        const swarmData = req.body;
        
        // 添加服务器接收时间
        swarmData.serverTimestamp = new Date().toISOString();
        swarmData.id = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // 存储数据
        swarmDataStore.unshift(swarmData); // 最新数据在前
        
        // 保持最近数据
        if (swarmDataStore.length > MAX_STORED_DATA) {
            swarmDataStore = swarmDataStore.slice(0, MAX_STORED_DATA);
        }
        
        console.log(`📨 收到来自 ${getClientInfo(req)} 的粒子数据:`);
        console.log(`   • 会话ID: ${swarmData.sessionId}`);
        console.log(`   • 种群数量: ${swarmData.populations.length}`);
        console.log(`   • 总粒子数: ${swarmData.totalIndividuals}`);
        console.log(`   • 用户位置: ${swarmData.userAgent ? (swarmData.userAgent.includes('Mobile') ? '移动端' : '桌面端') : '未知'}`);
        
        res.json({
            success: true,
            message: '数据接收成功',
            dataId: swarmData.id,
            timestamp: swarmData.serverTimestamp,
            serverInfo: {
                environment: 'Railway',
                region: process.env.RAILWAY_REGION || 'unknown',
                storedCount: swarmDataStore.length
            }
        });
        
    } catch (error) {
        console.error('❌ 处理数据失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误: ' + error.message
        });
    }
});

// 🎮 Unity获取最新粒子参数
app.get('/api/swarm-data/latest', (req, res) => {
    try {
        if (swarmDataStore.length === 0) {
            return res.json({
                success: false,
                message: '暂无数据',
                data: null
            });
        }
        
        const latestData = swarmDataStore[0];
        
        // 转换为Unity友好的格式
        const unityData = {
            success: true,
            timestamp: latestData.serverTimestamp,
            sessionId: latestData.sessionId,
            totalParticles: latestData.totalIndividuals,
            populations: latestData.populations.map(pop => ({
                count: pop.count,
                neighborhoodRadius: pop.parameters.neighborhoodRadius,
                normalSpeed: pop.parameters.normalSpeed,
                maxSpeed: pop.parameters.maxSpeed,
                cohesion: pop.parameters.c1,      // 聚集力
                alignment: pop.parameters.c2,     // 对齐力
                separation: pop.parameters.c3,    // 分离力
                randomness: pop.parameters.c4,    // 随机性
                speedControl: pop.parameters.c5,  // 速度调节
                color: pop.parameters.color
            }))
        };
        
        console.log(`🎮 Unity请求最新数据 - 返回 ${unityData.populations.length} 个种群`);
        res.json(unityData);
        
    } catch (error) {
        console.error('❌ 获取数据失败:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误: ' + error.message
        });
    }
});

// 📊 获取所有历史数据（可选）
app.get('/api/swarm-data/history', (req, res) => {
    const limit = parseInt(req.query.limit) || 10;
    const history = swarmDataStore.slice(0, Math.min(limit, swarmDataStore.length));
    
    res.json({
        success: true,
        count: history.length,
        total: swarmDataStore.length,
        data: history
    });
});

// 📈 获取统计信息
app.get('/api/stats', (req, res) => {
    const stats = {
        serverInfo: {
            environment: 'Railway',
            region: process.env.RAILWAY_REGION || 'unknown',
            uptime: process.uptime(),
            memory: process.memoryUsage()
        },
        dataStats: {
            totalSubmissions: swarmDataStore.length,
            latestSubmission: swarmDataStore.length > 0 ? swarmDataStore[0].serverTimestamp : null,
            uniqueSessions: new Set(swarmDataStore.map(d => d.sessionId)).size,
            totalParticles: swarmDataStore.reduce((sum, d) => sum + d.totalIndividuals, 0),
            averageParticles: swarmDataStore.length > 0 ? 
                Math.round(swarmDataStore.reduce((sum, d) => sum + d.totalIndividuals, 0) / swarmDataStore.length) : 0
        }
    };
    
    res.json(stats);
});

// 🏠 主页
app.get('/', (req, res) => {
    res.send(`
        <h1>🐝 SwarmChemistry Railway服务器</h1>
        <p>服务器运行正常！</p>
        <h3>📊 当前状态:</h3>
        <ul>
            <li>环境: Railway Cloud</li>
            <li>存储数据: ${swarmDataStore.length} 条</li>
            <li>服务器时间: ${new Date().toLocaleString('zh-CN')}</li>
            <li>运行时间: ${Math.floor(process.uptime())} 秒</li>
        </ul>
        <h3>🔗 API端点:</h3>
        <ul>
            <li><a href="/api/swarm-data/latest">GET /api/swarm-data/latest</a> - Unity获取最新数据</li>
            <li><a href="/api/swarm-data/history">GET /api/swarm-data/history</a> - 获取历史数据</li>
            <li><a href="/api/stats">GET /api/stats</a> - 获取统计信息</li>
            <li>POST /api/swarm-data - 网页端提交数据</li>
        </ul>
        <h3>🎮 Unity配置:</h3>
        <p>在Unity中设置服务器地址为: <code>${req.protocol}://${req.get('host')}</code></p>
    `);
});

// 健康检查端点（Railway推荐）
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: 'Railway',
        dataCount: swarmDataStore.length
    });
});

// 获取客户端信息
function getClientInfo(req) {
    const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
    const userAgent = req.headers['user-agent'] || 'Unknown';
    return `${ip} (${userAgent.includes('Mobile') ? '移动端' : '桌面端'})`;
}

// 启动服务器
app.listen(PORT, () => {
    console.log(`🚀 SwarmChemistry Railway服务器启动成功!`);
    console.log(`📡 监听端口: ${PORT}`);
    console.log(`🌐 环境: ${process.env.NODE_ENV || 'development'}`);
    console.log(`🎮 Unity API: /api/swarm-data/latest`);
    console.log(`📊 统计信息: /api/stats`);
});

// 优雅关闭
process.on('SIGTERM', () => {
    console.log('🛑 收到SIGTERM信号，正在关闭服务器...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('🛑 收到SIGINT信号，正在关闭服务器...');
    process.exit(0);
}); 