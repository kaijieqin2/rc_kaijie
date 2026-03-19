"""
简单测试 - 验证核心功能
"""
import sys
from pathlib import Path
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_database():
    """测试Mock数据库"""
    from mocks.mock_db import MockDatabase

    print("测试Mock数据库...")
    db = MockDatabase()

    # 创建通知
    notification_id = db.create_notification({
        "business_system": "test",
        "event_type": "test_event",
        "provider": "test_provider",
        "body": {"key": "value"}
    })

    # 查询通知
    notification = db.get_notification(notification_id)
    assert notification is not None
    assert notification["business_system"] == "test"

    # 更新通知
    db.update_notification(notification_id, {"status": "success"})
    updated = db.get_notification(notification_id)
    assert updated["status"] == "success"

    print("  ✓ Mock数据库测试通过")


def test_cache():
    """测试Mock缓存"""
    from mocks.mock_cache import MockCache

    print("测试Mock缓存...")
    cache = MockCache()

    # 设置值
    cache.set("test_key", "test_value", ttl=10)

    # 获取值
    value = cache.get("test_key")
    assert value == "test_value"

    # 删除值
    cache.delete("test_key")
    assert cache.get("test_key") is None

    # 计数器
    cache.incr("counter")
    cache.incr("counter")
    assert cache.get("counter") == 2

    print("  ✓ Mock缓存测试通过")


def test_queue():
    """测试Mock队列"""
    from mocks.mock_queue import MockQueue

    print("测试Mock队列...")
    queue = MockQueue("test")

    # 入队
    queue.enqueue("msg1", {"data": "test"})
    assert queue.size() == 1

    # 出队
    message = queue.dequeue(timeout=1.0)
    assert message is not None
    assert message.payload["data"] == "test"

    # 确认
    queue.ack(message.id)
    assert queue.processing_count() == 0

    print("  ✓ Mock队列测试通过")


def test_provider():
    """测试Mock供应商"""
    from mocks.mock_providers import MockProviderAPI
    from config.settings import ProviderConfig

    print("测试Mock供应商...")
    config = ProviderConfig(
        name="test_provider",
        url="https://test.com",
        mock_success_rate=1.0
    )

    provider = MockProviderAPI(config)
    response = provider.send_notification({}, {"test": "data"})

    assert response.status_code == 200
    assert provider.request_count == 1

    print("  ✓ Mock供应商测试通过")


def test_retry_strategy():
    """测试重试策略"""
    from core.retry import RetryStrategy

    print("测试重试策略...")

    # 测试应该重试的情况
    assert RetryStrategy.should_retry(500, 0) is True  # 5xx错误
    assert RetryStrategy.should_retry(408, 0) is True  # 超时
    assert RetryStrategy.should_retry(429, 0) is True  # 限流

    # 测试不应该重试的情况
    assert RetryStrategy.should_retry(400, 0) is False  # 4xx错误
    assert RetryStrategy.should_retry(200, 0) is False  # 成功

    # 测试超过最大重试次数
    assert RetryStrategy.should_retry(500, 10) is False

    # 测试永久失败判断
    assert RetryStrategy.is_permanent_failure(404) is True
    assert RetryStrategy.is_permanent_failure(500) is False

    print("  ✓ 重试策略测试通过")


def test_event_generator():
    """测试事件生成器"""
    from mocks.event_generator import BusinessEventGenerator

    print("测试事件生成器...")
    generator = BusinessEventGenerator()

    # 生成各类事件
    event1 = generator.generate_user_registration_event()
    assert event1["event_type"] == "user_registered"

    event2 = generator.generate_payment_success_event()
    assert event2["event_type"] == "payment_success"

    event3 = generator.generate_order_created_event()
    assert event3["event_type"] == "order_created"

    # 批量生成
    events = generator.generate_batch_events(5)
    assert len(events) == 5

    print("  ✓ 事件生成器测试通过")


def test_notification_service():
    """测试通知服务"""
    from core.notification import NotificationService
    from mocks.mock_db import MockDatabase

    print("测试通知服务...")

    # 重置数据库
    db = MockDatabase()
    db.clear_all()

    service = NotificationService()

    # 创建通知
    request = {
        "business_system": "test-service",
        "event_type": "test_event",
        "provider": "ad_provider_a",
        "data": {"test": "data"}
    }

    result = service.create_notification(request)
    assert "notification_id" in result
    assert result["status"] == "pending"

    # 查询通知
    notification_id = result["notification_id"]
    detail = service.get_notification(notification_id)
    assert detail["id"] == notification_id

    print("  ✓ 通知服务测试通过")


def test_metrics():
    """测试指标收集"""
    from observability.metrics import MetricsCollector

    print("测试指标收集...")
    metrics = MetricsCollector()

    # 记录请求
    metrics.record_request(100, success=True)
    metrics.record_request(200, success=False)

    # 记录通知
    metrics.record_notification_created()
    metrics.record_notification_processing()
    metrics.record_notification_completed(success=True)

    # 记录投递
    metrics.record_delivery("test_provider", 150, success=True, retry_count=1)

    # 获取指标
    all_metrics = metrics.get_all_metrics()
    assert all_metrics["requests"]["total"] == 2
    assert all_metrics["requests"]["success"] == 1
    assert all_metrics["notifications"]["created"] == 1

    print("  ✓ 指标收集测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行单元测试")
    print("=" * 60)
    print()

    tests = [
        test_database,
        test_cache,
        test_queue,
        test_provider,
        test_retry_strategy,
        test_event_generator,
        test_notification_service,
        test_metrics,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
