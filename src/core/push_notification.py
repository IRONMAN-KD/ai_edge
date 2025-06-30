"""
推送通知服务模块
支持多种推送协议：HTTP、MQTT、Kafka
"""

import json
import time
import logging
from typing import Dict, Any
import requests

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("MQTT library not installed, MQTT push will not be available.")

try:
    from kafka import KafkaProducer
    KAFKA_PYTHON_AVAILABLE = True
except ImportError:
    KAFKA_PYTHON_AVAILABLE = False
    logging.warning("kafka-python library not installed, Kafka push will not be available.")


class PushNotificationService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('push_notification', {})

    def send_notification(self, alert_data: Dict[str, Any]):
        """
        Sends a notification based on the configured method.
        """
        logging.info("=" * 80)
        logging.info("🚨 ==================== 告警推送触发 ====================")
        logging.info(f"⏰ 触发时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.config.get('enabled'):
            logging.warning("⚠️ 告警推送已禁用，跳过推送")
            logging.info("🔇 ==================== 推送已跳过 ====================")
            return

        push_type = self.config.get('type', 'http')
        logging.info(f"📡 推送类型: {push_type.upper()}")
        logging.info(f"⚙️ 推送配置: {json.dumps(self.config, indent=2, ensure_ascii=False)}")
        logging.info(f"📋 告警数据:")
        logging.info(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")

        try:
            if push_type == 'http':
                logging.info("🔄 执行HTTP推送...")
                self._send_http_notification(alert_data)
            elif push_type == 'mqtt':
                logging.info("🔄 执行MQTT推送...")
                self._send_mqtt_notification(alert_data)
            elif push_type == 'kafka':
                logging.info("🔄 执行Kafka推送...")
                self._send_kafka_notification(alert_data)
            else:
                logging.error(f"❌ 不支持的推送类型: {push_type}")
                logging.error("💔 ==================== 推送类型错误 ====================")
        except Exception as e:
            logging.error(f"💀 推送执行异常: {e}")
            logging.error("💔 ==================== 推送执行失败 ====================")

    def _send_http_notification(self, alert_data: Dict[str, Any]):
        url = self.config.get('url')
        if not url:
            logging.error("❌ HTTP推送失败: 未配置推送URL")
            return

        # 获取推送配置信息
        method = self.config.get('method', 'POST').upper()
        timeout = self.config.get('timeout', 10)
        custom_headers = self.config.get('headers', {})
        
        # 打印推送配置信息
        logging.info("🚀 ==================== HTTP告警推送开始 ====================")
        logging.info(f"📍 推送URL: {url}")
        logging.info(f"📋 请求方法: {method}")
        logging.info(f"⏱️  超时时间: {timeout}秒")
        
        # 设置基础headers
        headers = {'Content-Type': 'application/json'}
        
        # 合并自定义headers，并清理空格
        if custom_headers:
            cleaned_headers = {}
            for key, value in custom_headers.items():
                # 清理header值中的前后空格，避免HTTP请求错误
                cleaned_key = str(key).strip()
                cleaned_value = str(value).strip()
                cleaned_headers[cleaned_key] = cleaned_value
                
            headers.update(cleaned_headers)
            logging.info(f"🔐 自定义Headers:")
            for key, value in cleaned_headers.items():
                # 隐藏敏感信息（如token）
                if 'token' in key.lower() or 'auth' in key.lower() or 'key' in key.lower():
                    logging.info(f"     {key}: {value[:10]}***" if len(str(value)) > 10 else f"     {key}: ***")
                else:
                    logging.info(f"     {key}: {value}")
        else:
            logging.info("🔐 使用默认Headers: Content-Type: application/json")
        
        # 打印告警数据
        logging.info("📦 推送数据内容:")
        try:
            formatted_data = json.dumps(alert_data, indent=2, ensure_ascii=False)
            logging.info(f"{formatted_data}")
        except Exception as e:
            logging.warning(f"⚠️ 无法格式化告警数据: {e}")
            logging.info(f"📦 告警数据: {alert_data}")

        # 准备请求数据
        data = json.dumps(alert_data, ensure_ascii=False)
        
        try:
            # 记录请求开始时间
            start_time = time.time()
            logging.info(f"📡 开始发送{method}请求...")
            
            # 根据方法发送请求
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, params=alert_data)
                logging.info(f"📤 GET请求已发送，查询参数大小: {len(str(alert_data))}字节")
            elif method == 'PUT':
                response = requests.put(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 PUT请求已发送，数据大小: {len(data)}字节")
            elif method == 'PATCH':
                response = requests.patch(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 PATCH请求已发送，数据大小: {len(data)}字节")
            else:  # 默认POST
                response = requests.post(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 POST请求已发送，数据大小: {len(data)}字节")
            
            response_time = time.time() - start_time
            
            # 详细响应信息
            logging.info(f"📨 收到响应:")
            logging.info(f"     状态码: {response.status_code}")
            logging.info(f"     响应时间: {response_time:.3f}秒")
            logging.info(f"     响应头: {dict(response.headers)}")
            
            # 响应内容
            try:
                response_text = response.text
                if len(response_text) > 300:
                    logging.info(f"     响应内容: {response_text[:300]}... (已截断，完整长度: {len(response_text)})")
                else:
                    logging.info(f"     响应内容: {response_text}")
            except Exception as e:
                logging.warning(f"⚠️ 无法读取响应内容: {e}")
            
            # 检查响应状态
            if 200 <= response.status_code < 300:
                logging.info(f"✅ HTTP推送成功! 状态码: {response.status_code}, 耗时: {response_time:.3f}秒")
                logging.info("🎉 ==================== HTTP告警推送完成 ====================")
                return True
            else:
                logging.error(f"❌ HTTP推送失败! HTTP状态码: {response.status_code}")
                logging.error(f"💥 错误响应: {response.text}")
                logging.error(f"📦 推送失败的告警数据:")
                logging.error(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")
                logging.error("💔 ==================== HTTP告警推送失败 ====================")
                return False
                
        except requests.exceptions.Timeout as e:
            logging.error(f"⏰ HTTP推送超时! 超时时间: {timeout}秒")
            logging.error(f"💥 错误详情: {e}")
            logging.error(f"📦 推送失败的告警数据:")
            logging.error(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")
            logging.error("💔 ==================== HTTP告警推送超时 ====================")
            return False
            
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔌 HTTP推送连接失败! 无法连接到: {url}")
            logging.error(f"💥 错误详情: {e}")
            logging.error(f"📦 推送失败的告警数据:")
            logging.error(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")
            logging.error("💔 ==================== HTTP告警推送连接失败 ====================")
            return False
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ HTTP推送请求异常!")
            logging.error(f"💥 错误详情: {e}")
            logging.error(f"📦 推送失败的告警数据:")
            logging.error(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")
            logging.error("💔 ==================== HTTP告警推送异常 ====================")
            return False
            
        except Exception as e:
            logging.error(f"💀 HTTP推送未知错误!")
            logging.error(f"💥 错误详情: {e}")
            logging.error(f"📦 推送失败的告警数据:")
            logging.error(f"{json.dumps(alert_data, indent=2, ensure_ascii=False)}")
            logging.error("💔 ==================== HTTP告警推送异常 ====================")
            return False

    def _send_mqtt_notification(self, alert_data: Dict[str, Any]):
        if not MQTT_AVAILABLE:
            logging.error("MQTT push is enabled, but 'paho-mqtt' library is not installed.")
            return

        broker = self.config.get('mqtt_broker')
        port = self.config.get('mqtt_port', 1883)
        topic = self.config.get('mqtt_topic')
        username = self.config.get('mqtt_username')
        password = self.config.get('mqtt_password')

        if not broker or not topic:
            logging.error("MQTT push is enabled, but broker or topic is not configured.")
            return

        logging.info(f"Sending MQTT notification to broker '{broker}:{port}' on topic '{topic}'")
        
        client = None
        try:
            client = mqtt.Client()
            
            if username and password:
                client.username_pw_set(username, password)
            
            client.connect(broker, port, 60)
            
            message = json.dumps(alert_data, ensure_ascii=False)
            result = client.publish(topic, message)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info("MQTT notification sent successfully.")
            else:
                logging.error(f"Failed to send MQTT notification. Return code: {result.rc}")
                
        except Exception as e:
            logging.error(f"Failed to send MQTT notification. Error: {e}")
        finally:
            if client:
                client.disconnect()
                logging.info("MQTT client disconnected.")

    def _send_kafka_notification(self, alert_data: Dict[str, Any]):
        if not KAFKA_PYTHON_AVAILABLE:
            logging.error("Kafka push is enabled, but 'kafka-python' library is not installed.")
            return

        servers = self.config.get('kafka_bootstrap_servers')
        topic = self.config.get('kafka_topic')

        if not servers or not topic:
            logging.error("Kafka push is enabled, but bootstrap servers or topic is not configured.")
            return

        logging.info(f"Sending Kafka notification to topic '{topic}' on servers '{servers}'")
        
        producer = None
        try:
            producer = KafkaProducer(
                bootstrap_servers=servers.split(','),
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                request_timeout_ms=5000 
            )
            
            future = producer.send(topic, value=alert_data)
            record_metadata = future.get(timeout=10)
            
            logging.info(
                f"Kafka notification sent successfully. "
                f"Topic: {record_metadata.topic}, Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )

        except Exception as e:
            logging.error(f"Failed to send Kafka notification. Error: {e}")
        finally:
            if producer:
                producer.flush()
                producer.close()
                logging.info("Kafka producer closed.")


def example():
    """示例用法"""
    config_data = {
        'push_notification': {
            'enabled': True,
            'type': 'http',
            'url': 'https://your-webhook-url.com/alert',
            'method': 'POST',
            'timeout': 30,
            'headers': {
                'Authorization': 'Bearer your-token',
                'X-API-Key': 'your-api-key'
            }
        }
    }
    
    alert_data = {
        'task_id': 1,
        'task_name': '测试任务',
        'model_name': '人员检测模型',
        'alert_image': 'alert_123.jpg',
        'confidence': 0.95,
        'detection_class': '人员',
        'title': '检测到人员活动',
        'description': '在监控区域检测到人员活动',
        'created_at': '2024-01-01 12:00:00'
    }
    
    notifier = PushNotificationService(config_data)
    notifier.send_notification(alert_data)


if __name__ == "__main__":
    example() 