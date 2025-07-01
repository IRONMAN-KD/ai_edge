import subprocess
import threading
import time
import uuid
import cv2
from flask import Flask, Response, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class UniversalStreamProxy:
    def __init__(self):
        self.streams = {}  # {stream_id: StreamHandler}
        self.lock = threading.Lock()
        
    def create_stream(self, source_url, stream_id=None):
        """创建新的流代理"""
        if not stream_id:
            stream_id = str(uuid.uuid4())
            
        with self.lock:
            if stream_id in self.streams:
                self.streams[stream_id].stop()
                
            handler = StreamHandler(source_url)
            if handler.start():
                self.streams[stream_id] = handler
                return stream_id
            else:
                return None
                
    def get_stream(self, stream_id):
        """获取流处理器"""
        with self.lock:
            return self.streams.get(stream_id)
            
    def remove_stream(self, stream_id):
        """移除流"""
        with self.lock:
            if stream_id in self.streams:
                self.streams[stream_id].stop()
                del self.streams[stream_id]
                
    def list_streams(self):
        """列出所有活跃流"""
        with self.lock:
            return {sid: handler.source_url for sid, handler in self.streams.items() if handler.is_active()}

class StreamHandler:
    def __init__(self, source_url):
        self.source_url = source_url
        self.ffmpeg_process = None
        self.frame_buffer = None
        self.buffer_lock = threading.Lock()
        self.running = False
        self.read_thread = None
        self.last_frame_time = 0
        
    def _detect_source_type(self):
        """检测视频源类型并返回ffmpeg参数"""
        url = self.source_url.lower()
        
        if url.startswith('rtsp://'):
            return ['-rtsp_transport', 'tcp', '-i', self.source_url]
        elif url.startswith('rtmp://'):
            return ['-i', self.source_url]
        elif url.startswith('http://') or url.startswith('https://'):
            return ['-i', self.source_url]
        elif url.startswith('/dev/video') or url.isdigit():
            # USB摄像头
            return ['-f', 'v4l2', '-i', self.source_url]
        elif '.' in url and any(url.endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov', '.flv']):
            # 本地文件
            return ['-re', '-i', self.source_url]  # -re 表示按原始帧率读取
        else:
            # 默认尝试直接输入
            return ['-i', self.source_url]
        
    def start(self):
        """启动流处理"""
        try:
            input_args = self._detect_source_type()
            
            cmd = ['ffmpeg'] + input_args + [
                '-f', 'mjpeg',
                '-q:v', '5',
                '-r', '15',  # 15fps，平衡实时性和带宽
                '-vf', 'scale=1280:720',  # 统一分辨率，减少处理负担
                'pipe:1'
            ]
            
            app.logger.info(f"启动ffmpeg: {' '.join(cmd)}")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            self.running = True
            self.read_thread = threading.Thread(target=self._read_frames, daemon=True)
            self.read_thread.start()
            
            # 等待一小段时间确认启动成功
            time.sleep(1)
            return self.is_active()
            
        except Exception as e:
            app.logger.error(f"启动流处理失败: {e}")
            return False
            
    def _read_frames(self):
        """读取ffmpeg输出的MJPEG帧"""
        buffer = b''
        while self.running and self.ffmpeg_process:
            try:
                chunk = self.ffmpeg_process.stdout.read(8192)
                if not chunk:
                    break
                    
                buffer += chunk
                
                # 查找JPEG边界
                while True:
                    start = buffer.find(b'\xff\xd8')
                    end = buffer.find(b'\xff\xd9')
                    
                    if start != -1 and end != -1 and end > start:
                        jpeg_frame = buffer[start:end+2]
                        buffer = buffer[end+2:]
                        
                        with self.buffer_lock:
                            self.frame_buffer = jpeg_frame
                            self.last_frame_time = time.time()
                    else:
                        break
                        
            except Exception as e:
                app.logger.error(f"读取帧错误: {e}")
                break
                
        app.logger.info(f"停止读取帧: {self.source_url}")
        
    def get_frame(self):
        """获取最新帧"""
        with self.buffer_lock:
            return self.frame_buffer
            
    def is_active(self):
        """检查流是否活跃"""
        if not self.running or not self.ffmpeg_process:
            return False
        
        # 检查ffmpeg进程是否还在运行
        if self.ffmpeg_process.poll() is not None:
            return False
            
        # 检查是否在最近5秒内有新帧
        return time.time() - self.last_frame_time < 5.0
        
    def stop(self):
        """停止流处理"""
        self.running = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()

# 全局代理实例
proxy = UniversalStreamProxy()

@app.route('/api/stream/create', methods=['POST'])
def create_stream():
    """创建新的流代理"""
    data = request.get_json()
    source_url = data.get('source_url')
    stream_id = data.get('stream_id')
    
    if not source_url:
        return jsonify({'error': 'source_url is required'}), 400
        
    result_id = proxy.create_stream(source_url, stream_id)
    if result_id:
        return jsonify({
            'stream_id': result_id,
            'stream_url': f'http://127.0.0.1:8090/stream/{result_id}',
            'status': 'created'
        })
    else:
        return jsonify({'error': 'Failed to create stream'}), 500

@app.route('/api/stream/list', methods=['GET'])
def list_streams():
    """列出所有活跃流"""
    streams = proxy.list_streams()
    return jsonify({'streams': streams})

@app.route('/api/stream/remove/<stream_id>', methods=['DELETE'])
def remove_stream(stream_id):
    """移除指定流"""
    proxy.remove_stream(stream_id)
    return jsonify({'status': 'removed'})

@app.route('/stream/<stream_id>')
def get_stream(stream_id):
    """获取MJPEG流"""
    handler = proxy.get_stream(stream_id)
    if not handler:
        return "Stream not found", 404
        
    def generate():
        while handler.is_active():
            frame = handler.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.067)  # ~15fps
            
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'active_streams': len(proxy.list_streams())})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, threaded=True)
