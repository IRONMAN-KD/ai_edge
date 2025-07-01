-- AI Edge Platform Database Initialization Script

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_edge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE ai_edge;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建模型表
CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'inactive',
    accuracy DECIMAL(5,4),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_name_version (name, version),
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_model_type (model_type),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    model_id INT NOT NULL,
    video_source VARCHAR(500),
    regions TEXT,
    schedule VARCHAR(100),
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    status ENUM('running', 'stopped', 'paused', 'error') NOT NULL DEFAULT 'stopped',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_model_id (model_id),
    INDEX idx_status (status),
    INDEX idx_is_enabled (is_enabled),
    INDEX idx_created_by (created_by),
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建推理记录表
CREATE TABLE IF NOT EXISTS inference_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    input_data TEXT NOT NULL,
    output_data TEXT,
    confidence DECIMAL(5,4),
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    error_msg TEXT,
    process_time DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_confidence (confidence),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建告警表
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    task_id INT,
    model_id INT,
    source VARCHAR(100),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_severity (severity),
    INDEX idx_is_read (is_read),
    INDEX idx_is_resolved (is_resolved),
    INDEX idx_task_id (task_id),
    INDEX idx_model_id (model_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户
-- 密码: admin123 (已加密)
INSERT INTO users (username, email, password_hash, role, is_active) VALUES 
('admin', 'admin@ai-edge.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', TRUE),
('demo_user', 'user@ai-edge.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'user', TRUE)
ON DUPLICATE KEY UPDATE username=username;

-- 插入示例模型
INSERT INTO models (name, version, description, model_type, file_path, file_size, status, accuracy, created_by) VALUES 
('YOLOv5', 'v6.0', 'YOLOv5 object detection model', 'detection', '/models/yolov5s.pt', 14000000, 'active', 0.9250, 1),
('ResNet50', 'v1.0', 'ResNet50 image classification model', 'classification', '/models/resnet50.pth', 98000000, 'active', 0.9180, 1),
('MobileNet', 'v2.0', 'MobileNetV2 lightweight model', 'classification', '/models/mobilenet_v2.pth', 14000000, 'inactive', 0.8950, 1)
ON DUPLICATE KEY UPDATE name=name;

-- 插入示例任务
INSERT INTO tasks (name, description, model_id, video_source, regions, schedule, is_enabled, status, created_by) VALUES 
('入口监控', '监控入口区域的人员进出', 1, 'rtsp://192.168.1.100:554/stream1', '[{"x":100,"y":100,"width":400,"height":300}]', '0 * * * *', TRUE, 'running', 1),
('车辆检测', '检测停车场内的车辆', 1, 'rtsp://192.168.1.101:554/stream1', '[{"x":0,"y":0,"width":1920,"height":1080}]', '*/5 * * * *', FALSE, 'stopped', 1)
ON DUPLICATE KEY UPDATE name=name;

-- 插入示例推理记录
INSERT INTO inference_records (task_id, input_data, output_data, confidence, status, process_time) VALUES 
(1, 'frame_001.jpg', '[{"class":"person","confidence":0.95,"bbox":[100,100,200,300]}]', 0.9500, 'completed', 0.1250),
(1, 'frame_002.jpg', '[{"class":"person","confidence":0.88,"bbox":[120,110,180,290]}]', 0.8800, 'completed', 0.1180),
(2, 'frame_003.jpg', '[{"class":"car","confidence":0.92,"bbox":[300,200,500,400]}]', 0.9200, 'completed', 0.1350)
ON DUPLICATE KEY UPDATE task_id=task_id;

-- 插入示例告警
INSERT INTO alerts (title, message, severity, task_id, model_id, source, is_read, is_resolved) VALUES 
('模型准确率下降', 'YOLOv5模型在最近1小时内的平均准确率下降到85%', 'medium', 1, 1, 'system', FALSE, FALSE),
('任务执行失败', '入口监控任务连续3次执行失败', 'high', 1, NULL, 'scheduler', FALSE, FALSE),
('存储空间不足', '模型存储目录剩余空间不足10%', 'critical', NULL, NULL, 'system', TRUE, FALSE)
ON DUPLICATE KEY UPDATE title=title;

-- 创建视图：任务统计
CREATE OR REPLACE VIEW task_stats AS
SELECT 
    t.id,
    t.name,
    t.status,
    COUNT(ir.id) as total_inferences,
    COUNT(CASE WHEN ir.status = 'completed' THEN 1 END) as successful_inferences,
    COUNT(CASE WHEN ir.status = 'failed' THEN 1 END) as failed_inferences,
    AVG(CASE WHEN ir.status = 'completed' THEN ir.confidence END) as avg_confidence,
    AVG(CASE WHEN ir.status = 'completed' THEN ir.process_time END) as avg_process_time
FROM tasks t
LEFT JOIN inference_records ir ON t.id = ir.task_id
GROUP BY t.id, t.name, t.status;

-- 创建视图：模型使用统计
CREATE OR REPLACE VIEW model_usage_stats AS
SELECT 
    m.id,
    m.name,
    m.version,
    m.status,
    COUNT(DISTINCT t.id) as active_tasks,
    COUNT(ir.id) as total_inferences,
    AVG(CASE WHEN ir.status = 'completed' THEN ir.confidence END) as avg_confidence
FROM models m
LEFT JOIN tasks t ON m.id = t.model_id
LEFT JOIN inference_records ir ON t.id = ir.task_id
GROUP BY m.id, m.name, m.version, m.status;

-- 创建存储过程：清理旧的推理记录
DELIMITER //
CREATE PROCEDURE CleanOldInferenceRecords(IN days_to_keep INT)
BEGIN
    DECLARE records_deleted INT DEFAULT 0;
    
    DELETE FROM inference_records 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    SET records_deleted = ROW_COUNT();
    
    SELECT CONCAT('Deleted ', records_deleted, ' old inference records') as result;
END //
DELIMITER ;

-- 创建存储过程：获取系统统计信息
DELIMITER //
CREATE PROCEDURE GetSystemStats()
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
        (SELECT COUNT(*) FROM models WHERE status = 'active') as active_models,
        (SELECT COUNT(*) FROM tasks WHERE is_enabled = TRUE) as enabled_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'running') as running_tasks,
        (SELECT COUNT(*) FROM alerts WHERE is_resolved = FALSE) as unresolved_alerts,
        (SELECT COUNT(*) FROM inference_records WHERE DATE(created_at) = CURDATE()) as today_inferences;
END //
DELIMITER ;

-- 创建触发器：更新任务的updated_at字段
DELIMITER //
CREATE TRIGGER update_task_timestamp 
    BEFORE UPDATE ON tasks
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END //
DELIMITER ;

-- 创建触发器：在推理记录插入时检查是否需要创建告警
DELIMITER //
CREATE TRIGGER check_inference_failure 
    AFTER INSERT ON inference_records
    FOR EACH ROW
BEGIN
    DECLARE failure_count INT DEFAULT 0;
    DECLARE task_name VARCHAR(100);
    
    IF NEW.status = 'failed' THEN
        -- 检查最近10分钟内的失败次数
        SELECT COUNT(*) INTO failure_count
        FROM inference_records 
        WHERE task_id = NEW.task_id 
        AND status = 'failed' 
        AND created_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE);
        
        -- 如果失败次数超过5次，创建告警
        IF failure_count >= 5 THEN
            SELECT name INTO task_name FROM tasks WHERE id = NEW.task_id;
            
            INSERT INTO alerts (title, message, severity, task_id, source)
            VALUES (
                CONCAT('任务频繁失败: ', task_name),
                CONCAT('任务 "', task_name, '" 在最近10分钟内失败了 ', failure_count, ' 次'),
                'high',
                NEW.task_id,
                'auto_trigger'
            );
        END IF;
    END IF;
END //
DELIMITER ;

-- 创建索引优化查询性能
CREATE INDEX idx_inference_records_created_at_status ON inference_records(created_at, status);
CREATE INDEX idx_alerts_created_at_severity ON alerts(created_at, severity);
CREATE INDEX idx_tasks_status_enabled ON tasks(status, is_enabled);

-- 设置数据库字符集和排序规则
ALTER DATABASE ai_edge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

COMMIT;