"""
推送通知模块
支持 MQTT、HTTP、RabbitMQ、Kafka 等多种协议
"""

import json
import time
import threading
from typing import Dict, Any, List, Optional
from utils.logging import logger
from utils.config_parser import ConfigParser
import requests
import logging

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("MQTT 库未安装")

try:
    import pika
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logger.warning("RabbitMQ 库未安装")

try:
    from kafka import KafkaProducer
    KAFKA_PYTHON_AVAILABLE = True
except ImportError:
    KAFKA_PYTHON_AVAILABLE = False
    logging.warning("kafka-python library not installed, Kafka push will not be available.")


class MQTTPusher:
    """MQTT 推送器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.is_connected = False
        self.connection_retries = 0
        self.max_retries = 3
        
        if MQTT_AVAILABLE:
            self._init_client()
    
    def _init_client(self):
        """初始化 MQTT 客户端"""
        try:
            self.client = mqtt.Client(
                client_id=self.config.get('client_id', 'atlas_vision_system')
            )
            
            # 设置认证信息
            username = self.config.get('username')
            password = self.config.get('password')
            if username and password:
                self.client.username_pw_set(username, password)
            
            # 设置回调
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            logger.info("MQTT 客户端初始化成功")
            
        except Exception as e:
            logger.error(f"MQTT 客户端初始化失败: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.is_connected = True
            self.connection_retries = 0
            logger.info("MQTT 连接成功")
        else:
            self.is_connected = False
            logger.error(f"MQTT 连接失败，错误码: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.is_connected = False
        logger.warning("MQTT 连接断开")
    
    def _on_publish(self, client, userdata, mid):
        """发布回调"""
        logger.debug(f"MQTT 消息发布成功，消息ID: {mid}")
    
    def connect(self) -> bool:
        """连接 MQTT 服务器"""
        if not MQTT_AVAILABLE or not self.client:
            return False
        
        try:
            broker = self.config.get('broker', 'localhost')
            port = self.config.get('port', 1883)
            keepalive = self.config.get('keepalive', 60)
            
            self.client.connect(broker, port, keepalive)
            self.client.loop_start()
            
            # 等待连接
            timeout = 5
            while not self.is_connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"MQTT 连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
    
    def push(self, alert_info: Dict[str, Any]) -> bool:
        """推送告警信息"""
        if not MQTT_AVAILABLE or not self.client or not self.is_connected:
            return False
        
        try:
            topic = self.config.get('topic', 'atlas/alerts')
            payload = json.dumps(alert_info, ensure_ascii=False)
            
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.log_push("MQTT", True, f"消息已发送到主题: {topic}")
                return True
            else:
                logger.log_push("MQTT", False, f"发送失败，错误码: {result.rc}")
                return False
                
        except Exception as e:
            logger.log_push("MQTT", False, f"推送异常: {e}")
            return False


class HTTPPusher:
    """HTTP 推送器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        
        if requests.Session:
            self._init_session()
    
    def _init_session(self):
        """初始化 HTTP 会话"""
        try:
            self.session = requests.Session()
            
            # 设置默认头部
            headers = self.config.get('headers', {})
            if headers:
                self.session.headers.update(headers)
            
            # 设置超时
            timeout = self.config.get('timeout', 10)
            self.session.timeout = timeout
            
            logger.info("HTTP 会话初始化成功")
            
        except Exception as e:
            logger.error(f"HTTP 会话初始化失败: {e}")
    
    def push(self, alert_info: Dict[str, Any]) -> bool:
        """推送告警信息"""
        if not requests.Session or not self.session:
            logger.error("❌ HTTPPusher: Session未初始化")
            return False
        
        try:
            url = self.config.get('url')
            if not url:
                logger.error("❌ HTTPPusher: HTTP推送URL未配置")
                return False
            
            # 获取配置信息
            method = self.config.get('method', 'POST').upper()
            timeout = self.config.get('timeout', 10)
            custom_headers = self.config.get('headers', {})
            
            # 详细日志输出
            logger.info("🔄 ==================== HTTPPusher推送开始 ====================")
            logger.info(f"📍 目标URL: {url}")
            logger.info(f"📋 HTTP方法: {method}")
            logger.info(f"⏱️ 超时设置: {timeout}秒")
            
            # 设置请求头部
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
                logger.info(f"🔐 自定义Headers:")
                for key, value in cleaned_headers.items():
                    # 隐藏敏感信息（如token）
                    if 'token' in key.lower() or 'auth' in key.lower() or 'key' in key.lower():
                        logger.info(f"     {key}: {value[:10]}***" if len(str(value)) > 10 else f"     {key}: ***")
                    else:
                        logger.info(f"     {key}: {value}")
            else:
                logger.info("🔐 使用默认Headers: Content-Type: application/json")
            
            # 准备请求数据
            data = json.dumps(alert_info, ensure_ascii=False)
            logger.info(f"📦 推送数据:")
            logger.info(f"     数据大小: {len(data)}字节")
            logger.info(f"     数据内容: {json.dumps(alert_info, indent=2, ensure_ascii=False)}")
            
            # 发送请求
            logger.info(f"📡 正在发送{method}请求...")
            start_time = time.time()
            
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=timeout, params=alert_info)
                logger.info(f"📤 GET请求已发送，查询参数: {alert_info}")
            elif method == 'PUT':
                response = self.session.put(url, data=data, headers=headers, timeout=timeout)
                logger.info(f"📤 PUT请求已发送")
            elif method == 'PATCH':
                response = self.session.patch(url, data=data, headers=headers, timeout=timeout)
                logger.info(f"📤 PATCH请求已发送")
            else:  # 默认POST
                response = self.session.post(url, data=data, headers=headers, timeout=timeout)
                logger.info(f"📤 POST请求已发送")
            
            response_time = time.time() - start_time
            
            # 详细响应信息
            logger.info(f"📨 服务器响应:")
            logger.info(f"     HTTP状态码: {response.status_code}")
            logger.info(f"     响应时间: {response_time:.3f}秒")
            logger.info(f"     响应头: {dict(response.headers)}")
            
            # 响应内容
            try:
                response_text = response.text
                if len(response_text) > 300:
                    logger.info(f"     响应内容: {response_text[:300]}... (已截断，完整长度: {len(response_text)})")
                else:
                    logger.info(f"     响应内容: {response_text}")
            except Exception as e:
                logger.warning(f"⚠️ 无法读取响应内容: {e}")
            
            # 检查响应状态
            if 200 <= response.status_code < 300:
                logger.info(f"✅ HTTPPusher推送成功! 状态码: {response.status_code}, 耗时: {response_time:.3f}秒")
                logger.info("🎉 ==================== HTTPPusher推送完成 ====================")
                logger.log_push("HTTP", True, f"推送成功，状态码: {response.status_code}", response_time)
                return True
            else:
                logger.error(f"❌ HTTPPusher推送失败! HTTP状态码: {response.status_code}")
                logger.error(f"💥 错误响应: {response.text}")
                logger.error("💔 ==================== HTTPPusher推送失败 ====================")
                logger.log_push("HTTP", False, f"推送失败，状态码: {response.status_code}", response_time)
                return False
                
        except requests.exceptions.Timeout as e:
            logger.error(f"⏰ HTTPPusher推送超时! 超时时间: {self.config.get('timeout', 10)}秒")
            logger.error(f"💥 超时详情: {e}")
            logger.error("💔 ==================== HTTPPusher推送超时 ====================")
            logger.log_push("HTTP", False, f"推送超时: {e}")
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 HTTPPusher连接失败! 无法连接到: {self.config.get('url')}")
            logger.error(f"💥 连接错误: {e}")
            logger.error("💔 ==================== HTTPPusher连接失败 ====================")
            logger.log_push("HTTP", False, f"连接失败: {e}")
            return False
            
        except Exception as e:
            logger.error(f"💀 HTTPPusher未知异常!")
            logger.error(f"💥 异常详情: {e}")
            logger.error("💔 ==================== HTTPPusher异常 ====================")
            logger.log_push("HTTP", False, f"推送异常: {e}")
            return False


class RabbitMQPusher:
    """RabbitMQ 推送器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.channel = None
        
        if RABBITMQ_AVAILABLE:
            self._init_connection()
    
    def _init_connection(self):
        """初始化 RabbitMQ 连接"""
        try:
            # 连接参数
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 5672)
            username = self.config.get('username', 'guest')
            password = self.config.get('password', 'guest')
            
            # 创建连接
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(host, port, '/', credentials)
            self.connection = pika.BlockingConnection(parameters)
            
            # 创建通道
            self.channel = self.connection.channel()
            
            # 声明交换机
            exchange = self.config.get('exchange', 'atlas_alerts')
            self.channel.exchange_declare(exchange, 'topic', durable=True)
            
            logger.info("RabbitMQ 连接初始化成功")
            
        except Exception as e:
            logger.error(f"RabbitMQ 连接初始化失败: {e}")
    
    def push(self, alert_info: Dict[str, Any]) -> bool:
        """推送告警信息"""
        if not RABBITMQ_AVAILABLE or not self.channel:
            return False
        
        try:
            exchange = self.config.get('exchange', 'atlas_alerts')
            routing_key = self.config.get('routing_key', 'vision.detection')
            
            # 准备消息
            message = json.dumps(alert_info, ensure_ascii=False)
            
            # 发送消息
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 持久化消息
                    content_type='application/json'
                )
            )
            
            logger.log_push("RabbitMQ", True, f"消息已发送到交换机: {exchange}")
            return True
            
        except Exception as e:
            logger.log_push("RabbitMQ", False, f"推送异常: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()


class KafkaPusher:
    """Kafka 推送器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.producer = None
        
        if KAFKA_PYTHON_AVAILABLE:
            self._init_producer()
    
    def _init_producer(self):
        """初始化 Kafka 生产者"""
        try:
            bootstrap_servers = self.config.get('bootstrap_servers', ['localhost:9092'])
            client_id = self.config.get('client_id', 'atlas_vision_producer')
            
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                client_id=client_id,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
            )
            
            logger.info("Kafka 生产者初始化成功")
            
        except Exception as e:
            logger.error(f"Kafka 生产者初始化失败: {e}")
    
    def push(self, alert_info: Dict[str, Any]) -> bool:
        """推送告警信息"""
        if not KAFKA_PYTHON_AVAILABLE or not self.producer:
            return False
        
        try:
            topic = self.config.get('topic', 'atlas_alerts')
            
            # 发送消息
            future = self.producer.send(topic, alert_info)
            record_metadata = future.get(timeout=10)
            
            logger.log_push("Kafka", True, 
                          f"消息已发送到主题: {topic}, 分区: {record_metadata.partition}, "
                          f"偏移量: {record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.log_push("Kafka", False, f"推送异常: {e}")
            return False
    
    def close(self):
        """关闭生产者"""
        if self.producer:
            self.producer.close()

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
                # Add a timeout for producer to avoid blocking indefinitely
                request_timeout_ms=5000 
            )
            
            # Send the message
            future = producer.send(topic, value=alert_data)
            
            # Block for 'synchronous' sends
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


class PushNotificationManager:
    """推送通知管理器"""
    
    def __init__(self, config: ConfigParser):
        self.config = config
        self.pushers = {}
        self.push_threads = {}
        self.is_running = False
        
        self._init_pushers()
    
    def _init_pushers(self):
        """初始化推送器"""
        # MQTT 推送器
        mqtt_config = self.config.get_mqtt_config()
        if mqtt_config.get('enabled', False):
            self.pushers['mqtt'] = MQTTPusher(mqtt_config)
            if self.pushers['mqtt'].connect():
                logger.info("MQTT 推送器连接成功")
            else:
                logger.warning("MQTT 推送器连接失败")
        
        # HTTP 推送器
        http_config = self.config.get_http_config()
        if http_config.get('enabled', False):
            self.pushers['http'] = HTTPPusher(http_config)
            logger.info("HTTP 推送器初始化成功")
        
        # RabbitMQ 推送器
        rabbitmq_config = self.config.get_rabbitmq_config()
        if rabbitmq_config.get('enabled', False):
            self.pushers['rabbitmq'] = RabbitMQPusher(rabbitmq_config)
            logger.info("RabbitMQ 推送器初始化成功")
        
        # Kafka 推送器
        kafka_config = self.config.get_kafka_config()
        if kafka_config.get('enabled', False):
            self.pushers['kafka'] = KafkaPusher(kafka_config)
            logger.info("Kafka 推送器初始化成功")
        
        logger.info(f"初始化了 {len(self.pushers)} 个推送器")
    
    def push_alert(self, alert_info: Dict[str, Any]) -> Dict[str, bool]:
        """推送告警信息"""
        results = {}
        
        for protocol, pusher in self.pushers.items():
            try:
                success = pusher.push(alert_info)
                results[protocol] = success
            except Exception as e:
                logger.error(f"{protocol} 推送异常: {e}")
                results[protocol] = False
        
        return results
    
    def push_alert_async(self, alert_info: Dict[str, Any]):
        """异步推送告警信息"""
        def push_task():
            results = self.push_alert(alert_info)
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"异步推送完成，成功: {success_count}/{len(results)}")
        
        thread = threading.Thread(target=push_task, daemon=True)
        thread.start()
        return thread
    
    def get_status(self) -> Dict[str, Any]:
        """获取推送器状态"""
        status = {}
        
        for protocol, pusher in self.pushers.items():
            if hasattr(pusher, 'is_connected'):
                status[protocol] = {
                    'connected': pusher.is_connected,
                    'available': True
                }
            else:
                status[protocol] = {
                    'connected': True,  # 假设可用
                    'available': True
                }
        
        return status
    
    def cleanup(self):
        """清理资源"""
        for protocol, pusher in self.pushers.items():
            try:
                if hasattr(pusher, 'disconnect'):
                    pusher.disconnect()
                elif hasattr(pusher, 'close'):
                    pusher.close()
                logger.info(f"{protocol} 推送器已清理")
            except Exception as e:
                logger.error(f"清理 {protocol} 推送器失败: {e}")
        
        self.pushers.clear()


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
                response = requests.get(url, headers=headers, params=alert_data, timeout=timeout)
                logging.info(f"📤 GET请求已发送，参数: {alert_data}")
            elif method == 'PUT':
                response = requests.put(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 PUT请求已发送，数据大小: {len(data)}字节")
            elif method == 'PATCH':
                response = requests.patch(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 PATCH请求已发送，数据大小: {len(data)}字节")
            else:  # 默认POST
                response = requests.post(url, data=data, headers=headers, timeout=timeout)
                logging.info(f"📤 POST请求已发送，数据大小: {len(data)}字节")
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 打印响应信息
            logging.info(f"📨 收到响应:")
            logging.info(f"     状态码: {response.status_code}")
            logging.info(f"     响应时间: {response_time:.3f}秒")
            logging.info(f"     响应头: {dict(response.headers)}")
            
            # 打印响应内容（限制长度）
            try:
                response_text = response.text
                if len(response_text) > 500:
                    logging.info(f"     响应内容: {response_text[:500]}... (已截断)")
                else:
                    logging.info(f"     响应内容: {response_text}")
            except Exception as e:
                logging.warning(f"⚠️ 无法读取响应内容: {e}")
            
            # 检查响应状态
            if 200 <= response.status_code < 300:
                logging.info(f"✅ HTTP推送成功! 状态码: {response.status_code}, 耗时: {response_time:.3f}秒")
                logging.info("🎉 ==================== HTTP告警推送完成 ====================")
            else:
                logging.error(f"❌ HTTP推送失败! 状态码: {response.status_code}")
                logging.error(f"💥 服务器错误响应: {response.text}")
                logging.error("💔 ==================== HTTP告警推送失败 ====================")
                
        except requests.exceptions.Timeout as e:
            logging.error(f"⏰ HTTP推送超时! 超时时间: {timeout}秒")
            logging.error(f"💥 错误详情: {e}")
            logging.error("💔 ==================== HTTP告警推送超时 ====================")
            
        except requests.exceptions.ConnectionError as e:
            logging.error(f"🔌 HTTP推送连接失败! 无法连接到: {url}")
            logging.error(f"💥 错误详情: {e}")
            logging.error("💔 ==================== HTTP告警推送连接失败 ====================")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ HTTP推送请求异常!")
            logging.error(f"💥 错误详情: {e}")
            logging.error("💔 ==================== HTTP告警推送异常 ====================")
            
        except Exception as e:
            logging.error(f"💀 HTTP推送未知错误!")
            logging.error(f"💥 错误详情: {e}")
            logging.error("💔 ==================== HTTP告警推送异常 ====================")

    def _send_mqtt_notification(self, alert_data: Dict[str, Any]):
        if not MQTT_AVAILABLE:
            logging.error("MQTT push is enabled, but 'paho-mqtt' library is not installed.")
            return

        broker = self.config.get('mqtt_broker')
        port = self.config.get('mqtt_port', 1883)
        topic = self.config.get('mqtt_topic')

        if not all([broker, port, topic]):
            logging.error("MQTT push is enabled, but broker, port, or topic is not fully configured.")
            return
            
        logging.info(f"Sending MQTT notification to topic '{topic}' on broker '{broker}:{port}'")

        client = None
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            
            username = self.config.get('username')
            password = self.config.get('password')
            if username:
                client.username_pw_set(username, password)

            client.connect(broker, port, 60)
            client.loop_start()

            payload = json.dumps(alert_data, ensure_ascii=False)
            msg_info = client.publish(topic, payload, qos=1)
            
            # Wait for the message to be published
            msg_info.wait_for_publish(timeout=5)

            if msg_info.is_published():
                logging.info(f"MQTT notification sent successfully to topic '{topic}'.")
            else:
                logging.error("Failed to publish MQTT message in time.")

        except Exception as e:
            logging.error(f"Failed to send MQTT notification. Error: {e}")
        finally:
            if client:
                client.loop_stop()
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
                # Add a timeout for producer to avoid blocking indefinitely
                request_timeout_ms=5000 
            )
            
            # Send the message
            future = producer.send(topic, value=alert_data)
            
            # Block for 'synchronous' sends
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

# Example usage (for testing purposes)
def example():
    config_data = {
        "push_notification": {
            "enabled": True,
            "type": "http",
            "url": "https://webhook.site/your-unique-url"
        }
    }
    alert = {"id": 1, "title": "Test Alert", "description": "This is a test"}
    notifier = PushNotificationService(config_data)
    notifier.send_notification(alert) 