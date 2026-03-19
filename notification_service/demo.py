"""
演示脚本 - 完整系统运行示例
"""
import time
import sys
import requests
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from mocks.event_generator import BusinessEventGenerator


def run_demo():
    """运行演示"""
    print("=" * 60)
    print("HTTP通知投递系统 - 演示")
    print("=" * 60)
    print()

    # API基础URL
    base_url = "http://localhost:8000/api/v1"

    # 检查服务健康
    print("1. 检查服务健康...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print(f"   ✓ 服务运行正常: {response.json()}")
        else:
            print("   ✗ 服务未响应，请先启动服务: python notification_service/main.py")
            return
    except Exception as e:
        print(f"   ✗ 无法连接到服务: {e}")
        print("   请先启动服务: python notification_service/main.py")
        return

    print()

    # 创建事件生成器
    generator = BusinessEventGenerator()

    # 2. 创建通知
    print("2. 创建通知...")
    notifications = []

    # 生成10个事件
    events = generator.generate_batch_events(10)

    for i, event in enumerate(events, 1):
        try:
            response = requests.post(f"{base_url}/notifications", json=event)
            if response.status_code == 201:
                result = response.json()
                notifications.append(result["notification_id"])
                print(f"   ✓ 通知 {i}: {result['notification_id']} - {event['event_type']} -> {event['provider']}")
            else:
                print(f"   ✗ 创建失败: {response.text}")
        except Exception as e:
            print(f"   ✗ 错误: {e}")

        time.sleep(0.1)  # 避免过快

    print()

    # 3. 等待投递处理
    print("3. 等待投递处理 (5秒)...")
    for i in range(5):
        print(f"   等待中... {5-i}秒")
        time.sleep(1)
    print()

    # 4. 查询通知状态
    print("4. 查询通知状态...")
    status_summary = {"pending": 0, "processing": 0, "success": 0, "failed": 0}

    for notification_id in notifications[:5]:  # 只显示前5个
        try:
            response = requests.get(f"{base_url}/notifications/{notification_id}")
            if response.status_code == 200:
                result = response.json()
                status = result["status"]
                status_summary[status] = status_summary.get(status, 0) + 1
                print(f"   通知 {notification_id[:8]}... : {status} (重试: {result['retry_count']}次)")
        except Exception as e:
            print(f"   ✗ 查询失败: {e}")

    print()

    # 5. 获取统计信息
    print("5. 获取系统统计...")
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   总通知数: {stats['total_notifications']}")
            print(f"   状态分布: {stats['status_counts']}")
            print(f"   成功率: {stats['success_rate'] * 100:.2f}%")
            print(f"   队列大小: {stats['queue']['queue_size']}")
            print(f"   供应商统计:")
            for provider, counts in stats['provider_counts'].items():
                print(f"      {provider}: 总计={counts['total']}, 成功={counts['success']}, 失败={counts['failed']}")
    except Exception as e:
        print(f"   ✗ 获取统计失败: {e}")

    print()

    # 6. 获取监控指标
    print("6. 获取监控指标...")
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   请求指标:")
            print(f"      总请求: {metrics['requests']['total']}")
            print(f"      成功: {metrics['requests']['success']}")
            print(f"      失败: {metrics['requests']['failed']}")
            print(f"   投递指标:")
            print(f"      投递尝试: {metrics['delivery']['attempts']}")
            print(f"      投递成功: {metrics['delivery']['success']}")
            print(f"      投递失败: {metrics['delivery']['failed']}")
            if metrics['delivery']['duration']['count'] > 0:
                print(f"      平均耗时: {metrics['delivery']['duration']['avg']:.2f}ms")
    except Exception as e:
        print(f"   ✗ 获取指标失败: {e}")

    print()

    # 7. 查询投递日志 (第一个通知)
    if notifications:
        print("7. 查询投递日志 (第一个通知)...")
        try:
            notification_id = notifications[0]
            response = requests.get(f"{base_url}/notifications/{notification_id}/logs")
            if response.status_code == 200:
                logs = response.json()
                print(f"   通知 {notification_id} 的投递日志 (共 {logs['count']} 条):")
                for log in logs['logs']:
                    status_code = log['status_code'] or 'N/A'
                    print(f"      尝试 {log['attempt']}: 状态码={status_code}, 耗时={log['duration_ms']:.2f}ms")
                    if log['error']:
                        print(f"         错误: {log['error']}")
        except Exception as e:
            print(f"   ✗ 获取日志失败: {e}")

    print()
    print("=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
