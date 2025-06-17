import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json
from typing import Any, Dict

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化日志配置"""
        # 创建日志目录
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        # 创建日志文件名（按日期）
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"inference_{current_date}.log")

        # 配置根日志记录器
        self.logger = logging.getLogger("inference")
        self.logger.setLevel(logging.INFO)

        # 创建文件处理器（按大小轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _format_message(self, message: Any) -> str:
        """格式化消息"""
        if isinstance(message, (dict, list)):
            return json.dumps(message, ensure_ascii=False)
        return str(message)

    def info(self, message: Any, **kwargs):
        """记录信息日志"""
        self.logger.info(self._format_message(message), **kwargs)

    def error(self, message: Any, exc_info: bool = True, **kwargs):
        """记录错误日志"""
        self.logger.error(self._format_message(message), exc_info=exc_info, **kwargs)

    def warning(self, message: Any, **kwargs):
        """记录警告日志"""
        self.logger.warning(self._format_message(message), **kwargs)

    def debug(self, message: Any, **kwargs):
        """记录调试日志"""
        self.logger.debug(self._format_message(message), **kwargs)

    def log_inference(self, 
                     model_id: int,
                     user_id: int,
                     input_path: str,
                     output_path: str,
                     inference_time: float,
                     status: str,
                     error: str = None):
        """记录推理日志"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "user_id": user_id,
            "input_path": input_path,
            "output_path": output_path,
            "inference_time": inference_time,
            "status": status
        }
        if error:
            log_data["error"] = error

        if status == "completed":
            self.info("推理完成", extra=log_data)
        elif status == "failed":
            self.error("推理失败", extra=log_data)
        else:
            self.info("推理进行中", extra=log_data) 