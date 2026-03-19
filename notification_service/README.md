# HTTP通知投递系统

一个可靠的内部服务，用于接收业务系统提交的外部HTTP通知请求，并异步投递到目标地址。

## 功能特性

- ✅ **异步处理**: 接收请求立即返回，后台异步投递
- ✅ **自动重试**: 失败自动重试，指数退避策略
- ✅ **多供应商支持**: 灵活配置不同供应商的API参数
- ✅ **完全Mock**: 所有依赖(数据库、缓存、队列、供应商API)均已Mock
- ✅ **可观测**: 完整的日志和监控指标
- ✅ **可扩展**: 模块化设计，易于扩展

## 系统架构

```
业务系统 → FastAPI → 消息队列 → Worker → 供应商API
                ↓
            数据库 + 缓存
```

详细架构设计请参考 [design.md](../design.md)

## 目录结构

```
notification_service/
├── api/                    # API层
│   ├── routes.py          # 路由处理
│   └── schemas.py         # 数据模型
├── core/                   # 核心业务逻辑
│   ├── notification.py    # 通知管理
│   ├── delivery.py        # 投递逻辑
│   └── retry.py           # 重试策略
├── mocks/                  # Mock实现
│   ├── mock_db.py         # Mock数据库
│   ├── mock_cache.py      # Mock缓存
│   ├── mock_queue.py      # Mock队列
│   ├── mock_providers.py  # Mock供应商API
│   └── event_generator.py # 事件生成器
├── config/                 # 配置
│   └── settings.py
├── observability/          # 可观测性
│   ├── logger.py          # 日志
│   └── metrics.py         # 指标
├── workers/                # Worker
│   └── delivery_worker.py
├── main.py                 # 主应用
├── demo.py                 # 演示脚本
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
cd notification_service
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 3. 查看API文档

访问 `http://localhost:8000/docs` 查看交互式API文档

### 4. 运行演示

在另一个终端运行:

```bash
python demo.py
```

## API使用示例

### 1. 创建通知

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

响应:
```json
{
  "notification_id": "uuid",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. 查询通知状态

```bash
curl http://localhost:8000/api/v1/notifications/{notification_id}
```

### 3. 获取统计信息

```bash
curl http://localhost:8000/api/v1/stats
```

### 4. 获取监控指标

```bash
curl http://localhost:8000/api/v1/metrics
```

## 配置说明

### 供应商配置

在 `config/settings.py` 中配置供应商:

```python
providers = {
    "ad_provider_a": ProviderConfig(
        name="ad_provider_a",
        url="https://api.adprovider-a.com/webhook",
        headers={"Content-Type": "application/json"},
        auth_type="bearer",
        auth_token="your_token",
        mock_success_rate=0.9  # Mock成功率
    )
}
```

### 重试配置

```python
retry = RetryConfig(
    max_retry=7,           # 最大重试7次
    initial_delay=1,       # 初始延迟1秒
    max_delay=64,          # 最大延迟64秒
    timeout=30             # 请求超时30秒
)
```

## Mock说明

系统所有依赖均已Mock，无需真实的数据库、缓存、消息队列:

- **数据库**: 使用内存字典模拟PostgreSQL
- **缓存**: 使用内存字典模拟Redis
- **消息队列**: 使用内存队列模拟RabbitMQ
- **供应商API**: 模拟HTTP响应，可配置成功率和延迟

Mock实现完全符合真实接口，可无缝替换为真实实现。

## 监控指标

系统收集以下指标:

- **请求指标**: QPS, 延迟, 错误率
- **通知指标**: 创建数, 待处理数, 成功率
- **投递指标**: 尝试次数, 成功率, 重试次数, 投递延迟
- **队列指标**: 队列长度, 入队/出队数量
- **供应商指标**: 各供应商成功率, 耗时

## 错误处理

### 错误分类

- **临时错误** (5xx, 超时, 限流): 自动重试
- **永久错误** (4xx客户端错误): 不重试，直接失败
- **配置错误**: 立即失败

### 重试策略

采用指数退避: 1s → 2s → 4s → 8s → 16s → 32s → 64s

最多重试7次，超过后标记为失败。

## 日志

日志采用结构化JSON格式:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "notification-service",
  "message": "Notification created",
  "notification_id": "uuid",
  "provider": "ad_provider_a"
}
```

## 测试

使用 `mocks/event_generator.py` 生成测试事件:

```python
from mocks.event_generator import BusinessEventGenerator

generator = BusinessEventGenerator()

# 生成用户注册事件
event = generator.generate_user_registration_event()

# 生成批量事件
events = generator.generate_batch_events(10)
```

## 环境变量

支持通过环境变量配置:

```bash
export ENVIRONMENT=production
export API_HOST=0.0.0.0
export API_PORT=8000
export LOG_LEVEL=INFO
```

## 生产部署建议

1. **替换Mock**: 将Mock实现替换为真实的数据库、缓存、队列
2. **水平扩展**: 可运行多个Worker实例
3. **监控告警**: 接入Prometheus + Grafana
4. **日志收集**: 接入ELK或类似日志系统
5. **负载均衡**: 在API层前加负载均衡器

## 性能特点

- 异步I/O处理
- 无阻塞队列
- 支持水平扩展
- 内存高效(使用Mock时)

## 许可

本项目为内部演示项目。
