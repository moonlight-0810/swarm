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
app.use(express.text({ limit: '10mb' })); // 解析文本数据

// 🌐 静态文件服务 - 提供网页界面
app.use('/static', express.static(path.join(__dirname, 'public')));

// 数据存储（Railway环境使用内存存储）
let swarmDataStore = [];
const MAX_STORED_DATA = 50; // 限制存储数量以节省内存

// 🌐 接收网页端发送的粒子参数
app.post('/api/swarm-data', async (req, res) => {
    try {
        let swarmData;
        
        // 检查数据格式：JSON格式 vs 标准文本格式
        if (typeof req.body === 'string') {
            // 标准文本格式处理
            swarmData = parseStandardFormat(req.body);
        } else {
            // JSON格式处理（现有格式）
            swarmData = req.body;
        }
        
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
        console.log(`   • 数据格式: ${typeof req.body === 'string' ? '标准文本格式' : 'JSON格式'}`);
        console.log(`   • 用户位置: ${swarmData.userAgent ? (swarmData.userAgent.includes('Mobile') ? '移动端' : '桌面端') : '未知'}`);
        
        res.json({
            success: true,
            message: '数据接收成功',
            dataId: swarmData.id,
            timestamp: swarmData.serverTimestamp,
            format: typeof req.body === 'string' ? 'standard' : 'json',
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

// 🎯 Unity获取标准格式数据（新增端点）
app.get('/api/swarm-data/standard', (req, res) => {
    try {
        if (swarmDataStore.length === 0) {
            return res.json({
                success: false,
                message: '暂无数据',
                data: null
            });
        }
        
        const latestData = swarmDataStore[0];
        
        // 转换为标准文本格式
        const standardFormat = convertToStandardFormat(latestData);
        
        res.json({
            success: true,
            timestamp: latestData.serverTimestamp,
            sessionId: latestData.sessionId,
            totalParticles: latestData.totalIndividuals,
            standardFormat: standardFormat,
            populationCount: latestData.populations.length
        });
        
        console.log(`🎯 Unity请求标准格式数据 - 返回 ${latestData.populations.length} 个种群`);
        
    } catch (error) {
        console.error('❌ 获取标准格式数据失败:', error);
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

// 🏠 主页 - 提供完整的网页界面
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 📊 状态页面 - 原有的状态信息
app.get('/status', (req, res) => {
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
            <li><a href="/api/swarm-data/latest">GET /api/swarm-data/latest</a> - Unity获取最新数据(JSON格式)</li>
            <li><a href="/api/swarm-data/standard">GET /api/swarm-data/standard</a> - Unity获取标准格式数据</li>
            <li><a href="/api/swarm-data/history">GET /api/swarm-data/history</a> - 获取历史数据</li>
            <li><a href="/api/stats">GET /api/stats</a> - 获取统计信息</li>
            <li>POST /api/swarm-data - 网页端提交数据(支持JSON和标准文本格式)</li>
        </ul>
        <h3>🎮 Unity配置:</h3>
        <p>在Unity中设置服务器地址为: <code>${req.protocol}://${req.get('host')}</code></p>
        <h3>🌐 网页界面:</h3>
        <p><a href="/">返回主页面</a> - 完整的SwarmChemistry网页界面</p>
        <h3>📝 支持的数据格式:</h3>
        <pre>标准格式示例:
102 * (293.86, 17.06, 38.3, 0.81, 0.05, 0.83, 0.2, 0.9)
124 * (226.18, 19.27, 24.57, 0.95, 0.84, 13.09, 0.07, 0.8)</pre>
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

// 🔧 辅助函数：解析标准文本格式
function parseStandardFormat(textData) {
    const lines = textData.trim().split('\n').filter(line => line.trim());
    const populations = [];
    let totalIndividuals = 0;
    
    lines.forEach(line => {
        // 匹配格式: count * (param1, param2, param3, param4, param5, param6, param7, param8)
        const match = line.match(/(\d+)\s*\*\s*\(([^)]+)\)/);
        if (match) {
            const count = parseInt(match[1]);
            const params = match[2].split(',').map(p => parseFloat(p.trim()));
            
            if (params.length === 8) {
                populations.push({
                    count: count,
                    parameters: {
                        neighborhoodRadius: params[0],
                        normalSpeed: params[1],
                        maxSpeed: params[2],
                        c1: params[3],
                        c2: params[4],
                        c3: params[5],
                        c4: params[6],
                        c5: params[7],
                        color: generateRandomColor()
                    }
                });
                totalIndividuals += count;
            }
        }
    });
    
    return {
        sessionId: 'standard_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString(),
        populations: populations,
        totalIndividuals: totalIndividuals,
        userAgent: 'Standard Format Parser',
        format: 'standard'
    };
}

// 🔧 辅助函数：转换为标准格式
function convertToStandardFormat(data) {
    if (!data.populations) return '';
    
    return data.populations.map(pop => {
        const params = pop.parameters;
        return `${pop.count} * (${params.neighborhoodRadius.toFixed(2)}, ${params.normalSpeed.toFixed(2)}, ${params.maxSpeed.toFixed(2)}, ${params.c1.toFixed(2)}, ${params.c2.toFixed(2)}, ${params.c3.toFixed(2)}, ${params.c4.toFixed(2)}, ${params.c5.toFixed(2)})`;
    }).join('\n');
}

// 🔧 辅助函数：生成随机颜色
function generateRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = Math.floor(Math.random() * 40) + 60; // 60-100%
    const lightness = Math.floor(Math.random() * 30) + 50;  // 50-80%
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

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
    console.log(`🎮 Unity API: /api/swarm-data/latest (JSON格式)`);
    console.log(`🎯 Unity API: /api/swarm-data/standard (标准格式)`);
    console.log(`📊 统计信息: /api/stats`);
    console.log(`📝 支持格式: JSON + 标准文本格式`);
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