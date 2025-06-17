-- 华为 AI Edge 智能小站 - 数据库表结构
-- 数据库名: ai_edge_hw

-- 1. 模型管理表
CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '模型名称',
    version VARCHAR(50) NOT NULL COMMENT '模型版本',
    type VARCHAR(50) NOT NULL COMMENT '模型类型: object_detection, face_detection, vehicle_detection等',
    file_path VARCHAR(500) NOT NULL COMMENT '模型文件路径',
    file_size BIGINT COMMENT '文件大小(字节)',
    input_size VARCHAR(50) COMMENT '输入尺寸: 640x640',
    confidence_threshold DECIMAL(3,2) DEFAULT 0.5 COMMENT '置信度阈值',
    nms_threshold DECIMAL(3,2) DEFAULT 0.4 COMMENT 'NMS阈值',
    classes JSON COMMENT '支持的类别列表',
    description TEXT COMMENT '模型描述',
    status ENUM('active', 'inactive', 'deleted') DEFAULT 'active' COMMENT '状态',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(50) COMMENT '创建者',
    labels JSON DEFAULT NULL COMMENT '模型标签列表',
    UNIQUE KEY uk_name_version (name, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型管理表';

-- 2. 模型预设配置表
CREATE TABLE IF NOT EXISTS model_presets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '预设名称',
    description TEXT COMMENT '预设描述',
    confidence_threshold DECIMAL(3,2) NOT NULL COMMENT '置信度阈值',
    nms_threshold DECIMAL(3,2) NOT NULL COMMENT 'NMS阈值',
    input_size VARCHAR(50) COMMENT '输入尺寸',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模型预设配置表';

-- 3. 应用场景表
CREATE TABLE IF NOT EXISTS scenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '场景名称',
    description TEXT COMMENT '场景描述',
    recommended_models JSON COMMENT '推荐模型列表',
    preset_id INT COMMENT '默认预设ID',
    alert_rules JSON COMMENT '告警规则配置',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (preset_id) REFERENCES model_presets(id),
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应用场景表';

-- 4. 视频源配置表
CREATE TABLE IF NOT EXISTS video_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '视频源名称',
    type ENUM('rtsp', 'rtmp', 'http', 'file', 'usb') NOT NULL COMMENT '视频源类型',
    url VARCHAR(500) NOT NULL COMMENT '视频源地址',
    username VARCHAR(100) COMMENT '用户名',
    password VARCHAR(100) COMMENT '密码',
    fps INT DEFAULT 30 COMMENT '帧率',
    resolution VARCHAR(50) COMMENT '分辨率: 1920x1080',
    status ENUM('active', 'inactive', 'error') DEFAULT 'active' COMMENT '状态',
    last_check_time TIMESTAMP NULL COMMENT '最后检查时间',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频源配置表';

-- 5. 任务配置表
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    model_id INT NOT NULL COMMENT '模型ID',
    preset_id INT COMMENT '预设ID',
    video_sources JSON COMMENT '视频源列表',
    detection_areas JSON COMMENT '检测区域配置',
    alert_config JSON COMMENT '告警配置',
    status ENUM('running', 'stopped', 'error') DEFAULT 'stopped' COMMENT '任务状态',
    last_start_time TIMESTAMP NULL COMMENT '实际上次开始时间',
    last_stop_time TIMESTAMP NULL COMMENT '实际上次停止时间',
    
    -- Scheduling fields
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '任务是否启用调度',
    schedule_type VARCHAR(20) DEFAULT 'continuous' COMMENT '调度类型: continuous, daily, weekly, monthly',
    schedule_days JSON DEFAULT NULL COMMENT '每周/每月执行日',
    start_time TIME DEFAULT '00:00:00' COMMENT '每日执行开始时间',
    end_time TIME DEFAULT '23:59:59' COMMENT '每日执行结束时间',
    confidence_threshold FLOAT DEFAULT 0.8,
    alert_debounce_interval INT DEFAULT 60, -- in seconds
    alert_message VARCHAR(255) DEFAULT '',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(50) COMMENT '创建者',
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (preset_id) REFERENCES model_presets(id),
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务配置表';

-- 6. 告警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    level VARCHAR(50) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    confidence FLOAT NOT NULL,
    task_id INT NOT NULL,
    task_name VARCHAR(255),
    model_name VARCHAR(255),
    alert_image VARCHAR(255),
    detection_class VARCHAR(100), -- For debouncing logic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警记录表';

-- 7. 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description TEXT COMMENT '配置描述',
    category VARCHAR(50) COMMENT '配置分类',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 8. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(100) COMMENT '邮箱',
    role ENUM('admin', 'operator', 'viewer') DEFAULT 'viewer' COMMENT '用户角色',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT '状态',
    last_login_time TIMESTAMP NULL COMMENT '最后登录时间',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 9. 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    operation VARCHAR(100) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(50) COMMENT '资源类型',
    resource_id INT COMMENT '资源ID',
    details JSON COMMENT '操作详情',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_time (user_id, create_time),
    INDEX idx_operation (operation),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 插入默认数据
INSERT INTO model_presets (name, description, confidence_threshold, nms_threshold) VALUES
('high_accuracy', '高精度模式，减少误报但可能漏检', 0.8, 0.3),
('balanced', '平衡模式，精度和召回率均衡', 0.6, 0.4),
('high_recall', '高召回率模式，减少漏检但可能增加误报', 0.4, 0.5),
('realtime', '实时模式，优先考虑处理速度', 0.5, 0.4);

INSERT INTO scenarios (name, description, recommended_models, preset_id, alert_rules) VALUES
('security_monitoring', '安防监控场景', '["person_detection", "intrusion_detection"]', 2, '[{"target_class": "person", "min_confidence": 0.6, "alert_message": "检测到人员活动"}]'),
('traffic_monitoring', '交通监控场景', '["vehicle_detection", "yolov8"]', 2, '[{"target_class": "car", "min_confidence": 0.6, "alert_message": "检测到车辆"}, {"target_class": "truck", "min_confidence": 0.7, "alert_message": "检测到大型车辆"}]'),
('general_monitoring', '通用监控场景', '["yolov5", "yolov8"]', 2, '[{"target_class": "person", "min_confidence": 0.5, "alert_message": "检测到目标对象"}]');

INSERT INTO users (username, password_hash, email, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i', 'admin@example.com', 'admin');

-- 创建索引优化查询性能
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_alerts_task_status ON alerts(task_id, status);
CREATE INDEX idx_alerts_create_time ON alerts(create_time DESC); 