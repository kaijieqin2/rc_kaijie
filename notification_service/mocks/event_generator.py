"""
模拟业务系统事件生成器
模拟不同业务系统产生的事件
"""
import random
import time
from typing import Dict, Any, List
from datetime import datetime


class BusinessEventGenerator:
    """业务事件生成器"""

    def __init__(self):
        self.event_count = 0

    def generate_user_registration_event(self) -> Dict[str, Any]:
        """生成用户注册事件"""
        self.event_count += 1
        user_id = f"user_{self.event_count}_{random.randint(1000, 9999)}"

        return {
            "business_system": "user-service",
            "event_type": "user_registered",
            "provider": random.choice(["ad_provider_a", "ad_provider_b"]),
            "data": {
                "user_id": user_id,
                "email": f"{user_id}@example.com",
                "registration_time": datetime.utcnow().isoformat() + "Z",
                "source": random.choice(["google_ads", "facebook_ads", "direct"]),
                "campaign_id": f"campaign_{random.randint(100, 999)}"
            }
        }

    def generate_payment_success_event(self) -> Dict[str, Any]:
        """生成支付成功事件"""
        self.event_count += 1
        order_id = f"order_{self.event_count}_{random.randint(1000, 9999)}"

        return {
            "business_system": "payment-service",
            "event_type": "payment_success",
            "provider": "crm_system",
            "data": {
                "order_id": order_id,
                "user_id": f"user_{random.randint(1, 1000)}",
                "amount": round(random.uniform(10.0, 1000.0), 2),
                "currency": "USD",
                "payment_time": datetime.utcnow().isoformat() + "Z",
                "subscription_type": random.choice(["basic", "premium", "enterprise"])
            }
        }

    def generate_order_created_event(self) -> Dict[str, Any]:
        """生成订单创建事件"""
        self.event_count += 1
        order_id = f"order_{self.event_count}_{random.randint(1000, 9999)}"

        return {
            "business_system": "order-service",
            "event_type": "order_created",
            "provider": "inventory_system",
            "data": {
                "order_id": order_id,
                "user_id": f"user_{random.randint(1, 1000)}",
                "items": [
                    {
                        "product_id": f"product_{random.randint(1, 100)}",
                        "quantity": random.randint(1, 5),
                        "price": round(random.uniform(10.0, 500.0), 2)
                    }
                    for _ in range(random.randint(1, 3))
                ],
                "total_amount": round(random.uniform(20.0, 1500.0), 2),
                "order_time": datetime.utcnow().isoformat() + "Z"
            }
        }

    def generate_random_event(self) -> Dict[str, Any]:
        """随机生成一个事件"""
        event_generators = [
            self.generate_user_registration_event,
            self.generate_payment_success_event,
            self.generate_order_created_event,
        ]
        generator = random.choice(event_generators)
        return generator()

    def generate_batch_events(self, count: int) -> List[Dict[str, Any]]:
        """批量生成事件"""
        return [self.generate_random_event() for _ in range(count)]


if __name__ == "__main__":
    """测试事件生成器"""
    generator = BusinessEventGenerator()

    print("=== 生成示例事件 ===\n")

    print("1. 用户注册事件:")
    print(generator.generate_user_registration_event())
    print()

    print("2. 支付成功事件:")
    print(generator.generate_payment_success_event())
    print()

    print("3. 订单创建事件:")
    print(generator.generate_order_created_event())
    print()

    print("4. 批量随机事件 (3个):")
    events = generator.generate_batch_events(3)
    for i, event in enumerate(events, 1):
        print(f"  事件 {i}: {event['event_type']} -> {event['provider']}")
