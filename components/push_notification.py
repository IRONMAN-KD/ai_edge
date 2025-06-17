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

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("MQTT 库未安装")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests 库未安装")

try:
    import pika
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logger.warning("RabbitMQ 库未安装")

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("Kafka 库未安装")


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
        
        if REQUESTS_AVAILABLE:
            self._init_session()
    
    def _init_session(self):
        """初始化 HTTP 会话"""
        try:
            import requests
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
        if not REQUESTS_AVAILABLE or not self.session:
            return False
        
        try:
            url = self.config.get('url')
            if not url:
                logger.error("HTTP 推送 URL 未配置")
                return False
            
            # 准备请求数据
            data = json.dumps(alert_info, ensure_ascii=False)
            headers = {'Content-Type': 'application/json'}
            
            # 发送请求
            start_time = time.time()
            response = self.session.post(url, data=data, headers=headers)
            response_time = time.time() - start_time
            
            # 检查响应
            if response.status_code == 200:
                logger.log_push("HTTP", True, f"推送成功，状态码: {response.status_code}", response_time)
                return True
            else:
                logger.log_push("HTTP", False, f"推送失败，状态码: {response.status_code}", response_time)
                return False
                
        except Exception as e:
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
        
        if KAFKA_AVAILABLE:
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
        if not KAFKA_AVAILABLE or not self.producer:
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
        mqtt_config = config.get_mqtt_config()
        if mqtt_config.get('enabled', False):
            self.pushers['mqtt'] = MQTTPusher(mqtt_config)
            if self.pushers['mqtt'].connect():
                logger.info("MQTT 推送器连接成功")
            else:
                logger.warning("MQTT 推送器连接失败")
        
        # HTTP 推送器
        http_config = config.get_http_config()
        if http_config.get('enabled', False):
            self.pushers['http'] = HTTPPusher(http_config)
            logger.info("HTTP 推送器初始化成功")
        
        # RabbitMQ 推送器
        rabbitmq_config = config.get_rabbitmq_config()
        if rabbitmq_config.get('enabled', False):
            self.pushers['rabbitmq'] = RabbitMQPusher(rabbitmq_config)
            logger.info("RabbitMQ 推送器初始化成功")
        
        # Kafka 推送器
        kafka_config = config.get_kafka_config()
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