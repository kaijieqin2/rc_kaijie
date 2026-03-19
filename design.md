# HTTP通知投递系统 - 系统设计文档

## 1. 架构约束 (Architecture Constraints)

### 1.1 技术栈
- **语言**: Python 3.11+
- **Web框架**: FastAPI (异步, 高性能)
- **消息队列**: Mock RabbitMQ/Kafka
- **数据库**: Mock PostgreSQL
- **缓存**: Mock Redis
- **任务调度**: Celery + Beat
- **监控**: 内置日志和指标收集

### 1.2 核心架构原则
- **异步处理**: 业务系统提交请求立即返回，后台异步投递
- **重试机制**: 失败自动重试，指数退避策略
- **幂等性**: 保证通知投递的幂等性
- **可观测**: 完整的日志和监控
- **可扩展**: 水平扩展能力

## 2. 模块化边界 (Modularity)

### 2.1 核心模块

```
notification-service/
├── api/                    # API层
│   ├── routes/            # 路由定义
│   └── schemas/           # 请求/响应模型
├── core/                   # 核心业务逻辑
│   ├── notification.py    # 通知管理
│   ├── delivery.py        # 投递逻辑
│   └── retry.py           # 重试策略
├── providers/              # 供应商适配层
│   ├── base.py            # 基础接口
│   ├── ad_provider.py     # 广告系统
│   ├── crm_provider.py    # CRM系统
│   └── inventory_provider.py # 库存系统
├── storage/                # 存储层
│   ├── database.py        # 数据库操作
│   ├── cache.py           # 缓存操作
│   └── queue.py           # 消息队列
├── config/                 # 配置管理
│   └── settings.py        # 配置定义
├── mocks/                  # Mock实现
│   ├── mock_db.py         # Mock数据库
│   ├── mock_cache.py      # Mock缓存
│   ├── mock_queue.py      # Mock队列
│   └── mock_providers.py  # Mock供应商API
└── observability/          # 可观测性
    ├── logger.py          # 日志
    └── metrics.py         # 指标
```

## 3. 配置化要求 (Configuration)

### 3.1 配置层次
- **环境配置**: 开发/测试/生产环境
- **供应商配置**: 各供应商API配置
- **重试配置**: 重试策略和限制
- **系统配置**: 系统运行参数

### 3.2 配置方式
- YAML/JSON配置文件
- 环境变量覆盖
- 运行时动态配置

## 4. Mock 规范 (Mock Strategy)

### 4.1 Mock范围
1. **基础设施Mock**
   - PostgreSQL: 内存字典模拟
   - Redis: 内存缓存模拟
   - RabbitMQ: 内存队列模拟

2. **供应商API Mock**
   - 广告系统API: 模拟响应
   - CRM系统API: 模拟响应
   - 库存系统API: 模拟响应

3. **业务系统Mock**
   - 事件生成器: 模拟业务事件

### 4.2 Mock实现原则
- 接口一致性: Mock与真实接口保持一致
- 可配置性: 可配置成功/失败场景
- 可观测性: Mock操作可追踪

## 5. 错误处理规范 (Error Handling)

### 5.1 错误分类
- **临时错误**: 网络超时, 5xx错误 → 重试
- **永久错误**: 4xx错误, 认证失败 → 不重试
- **配置错误**: 供应商不存在 → 立即失败

### 5.2 重试策略
- **指数退避**: 1s, 2s, 4s, 8s, 16s, 32s, 64s
- **最大重试**: 7次
- **超时时间**: 30秒
- **熔断机制**: 连续失败自动熔断

### 5.3 失败处理
- 记录详细错误日志
- 更新通知状态
- 触发告警 (严重错误)

## 6. 可观测性 (Observability)

### 6.1 日志
- **结构化日志**: JSON格式
- **日志级别**: DEBUG/INFO/WARNING/ERROR/CRITICAL
- **关键字段**: request_id, notification_id, provider, status

### 6.2 指标
- **请求指标**: QPS, 延迟, 错误率
- **投递指标**: 成功率, 重试次数, 投递延迟
- **系统指标**: 队列长度, 任务积压

### 6.3 追踪
- 请求追踪: 完整链路追踪
- 状态流转: 记录所有状态变化

## 7. 数据模型

### 7.1 通知记录 (Notification)
```python
{
    "id": "uuid",
    "business_system": "string",  # 来源系统
    "event_type": "string",       # 事件类型
    "provider": "string",         # 供应商
    "target_url": "string",       # 目标URL
    "headers": "dict",            # HTTP头
    "body": "dict",               # 请求体
    "status": "enum",             # pending/processing/success/failed
    "retry_count": "int",         # 重试次数
    "max_retry": "int",           # 最大重试次数
    "next_retry_at": "datetime",  # 下次重试时间
    "created_at": "datetime",
    "updated_at": "datetime",
    "delivered_at": "datetime"
}
```

### 7.2 投递记录 (DeliveryLog)
```python
{
    "id": "uuid",
    "notification_id": "uuid",
    "attempt": "int",             # 第几次尝试
    "status_code": "int",         # HTTP状态码
    "response": "text",           # 响应内容
    "error": "text",              # 错误信息
    "duration_ms": "int",         # 耗时
    "created_at": "datetime"
}
```

## 8. API设计

### 8.1 提交通知
```
POST /api/v1/notifications
Body: {
    "business_system": "user-service",
    "event_type": "user_registered",
    "provider": "ad_provider_a",
    "data": {...}
}
Response: {
    "notification_id": "uuid",
    "status": "pending"
}
```

### 8.2 查询通知状态
```
GET /api/v1/notifications/{notification_id}
Response: {
    "notification_id": "uuid",
    "status": "success",
    "retry_count": 2,
    "delivered_at": "2024-01-01T00:00:00Z"
}
```

### 8.3 查询统计
```
GET /api/v1/stats
Response: {
    "total_notifications": 1000,
    "success_rate": 0.95,
    "avg_delivery_time_ms": 150
}
```

## 9. 部署架构

```
┌─────────────┐
│ Business    │
│ Systems     │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│  FastAPI    │◄───── Load Balancer
│  Service    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Message    │
│  Queue      │
└──────┬──────┘
       │
       ▼
┌─────────────┐       ┌─────────────┐
│  Celery     │◄─────►│  Database   │
│  Worker     │       │  + Cache    │
└──────┬──────┘       └─────────────┘
       │
       ▼
┌─────────────┐
│  External   │
│  Providers  │
└─────────────┘
```

## 10. 运行流程

1. **接收请求**
   - 业务系统提交通知请求
   - 验证请求格式和供应商配置
   - 创建通知记录 (状态: pending)
   - 将任务放入消息队列
   - 立即返回通知ID

2. **异步投递**
   - Celery Worker从队列取任务
   - 根据供应商配置构建HTTP请求
   - 发送HTTP请求到目标地址
   - 记录投递日志

3. **成功处理**
   - 更新通知状态为success
   - 记录投递时间
   - 更新统计指标

4. **失败重试**
   - 判断错误类型
   - 如果可重试且未达上限: 计算下次重试时间, 重新入队
   - 如果不可重试或达上限: 标记为failed
   - 记录错误信息

5. **定时扫描**
   - Celery Beat定时扫描到期的重试任务
   - 将到期任务重新入队
