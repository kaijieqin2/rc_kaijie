# 快速开始指南

## 系统说明

HTTP通知投递系统 - 接收业务系统提交的HTTP通知请求,异步可靠地投递到外部供应商API。

**特点:**
- 完全Mock实现,无需真实数据库/缓存/消息队列
- 开箱即用,一键启动
- 完整的API文档和演示

## 启动步骤

### 1. 安装依赖 (首次运行)

```bash
cd notification_service
pip3 install -r requirements.txt
```

### 2. 启动服务

**方式A: 使用启动脚本 (推荐)**
```bash
./start.sh
```

**方式B: 直接运行**
```bash
python3 main.py
```

服务将在 `http://localhost:8000` 启动

### 3. 查看API文档

访问: http://localhost:8000/docs

可以直接在浏览器中测试API

### 4. 运行演示 (新终端)

```bash
cd notification_service
python3 demo.py
```

演示脚本会:
- 生成10个随机业务事件
- 提交通知请求
- 等待投递完成
- 查询通知状态
- 显示统计信息和监控指标

## API使用示例

### 创建通知

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "business_system": "user-service",
    "event_type": "user_registered",
    "provider": "ad_provider_a",
    "data": {
      "user_id": "12345",
      "email": "user@example.com"
    }
  }'
```

### 查询通知

```bash
curl http://localhost:8000/api/v1/notifications/{notification_id}
```

### 获取统计

```bash
curl http://localhost:8000/api/v1/stats
```

## 目录结构

```
notification_service/
├── main.py              # 主应用入口
├── demo.py              # 演示脚本
├── test.py              # 单元测试
├── start.sh             # 启动脚本
├── requirements.txt     # 依赖
├── README.md            # 详细文档
├── api/                 # API层
├── core/                # 核心业务逻辑
├── mocks/               # Mock实现
├── config/              # 配置
├── observability/       # 日志和指标
└── workers/             # 异步Worker
```

## 配置说明

### 供应商配置

系统预配置了4个供应商:
- `ad_provider_a` - 广告供应商A (成功率90%)
- `ad_provider_b` - 广告供应商B (成功率85%)
- `crm_system` - CRM系统 (成功率95%)
- `inventory_system` - 库存系统 (成功率92%)

可以在 `config/settings.py` 中调整Mock成功率和其他参数。

### 环境变量

```bash
export ENVIRONMENT=development     # 环境: development/production
export API_HOST=0.0.0.0           # API监听地址
export API_PORT=8000              # API端口
export LOG_LEVEL=INFO             # 日志级别
```

## Mock说明

系统所有依赖都已Mock:

- **数据库**: 内存字典 (mock_db.py)
- **缓存**: 内存缓存 (mock_cache.py)
- **消息队列**: 内存队列 (mock_queue.py)
- **供应商API**: 模拟HTTP响应 (mock_providers.py)

Mock可配置成功率和响应延迟,模拟真实场景。

## 监控指标

系统收集丰富的监控指标:

访问: http://localhost:8000/api/v1/metrics

```json
{
  "requests": {
    "total": 100,
    "success": 98,
    "failed": 2
  },
  "notifications": {
    "created": 100,
    "success": 85,
    "failed": 5
  },
  "delivery": {
    "success_rate": 0.85,
    "avg_duration_ms": 120
  }
}
```

## 常见问题

### Q: 如何停止服务?
A: 按 `Ctrl+C`

### Q: 端口8000已被占用?
A: 修改环境变量 `export API_PORT=8001` 或修改 `config/settings.py`

### Q: 如何调整Mock成功率?
A: 编辑 `config/settings.py` 中各供应商的 `mock_success_rate` 参数

### Q: 如何查看日志?
A: 日志输出到控制台,JSON格式

### Q: 如何替换Mock为真实实现?
A: 在相应模块中替换Mock类,保持接口一致即可

## 更多信息

- 详细文档: [README.md](notification_service/README.md)
- 系统设计: [design.md](design.md)
- 实现总结: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## 技术支持

如有问题,请查看代码注释或联系开发团队。
