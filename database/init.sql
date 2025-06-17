-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_edge;
USE ai_edge;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建模型表
CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    file_path VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建推理记录表
CREATE TABLE IF NOT EXISTS inference_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT NOT NULL,
    user_id INT NOT NULL,
    input_path VARCHAR(255) NOT NULL,
    output_path VARCHAR(255) NOT NULL,
    inference_time FLOAT,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建默认管理员用户（密码：admin123）
INSERT INTO users (username, password_hash, email) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpR1IOBYyGqK8y', 'admin@example.com')
ON DUPLICATE KEY UPDATE username=username; 