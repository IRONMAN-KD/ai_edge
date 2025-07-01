import subprocess
import threading
import time
import uuid
import json
from flask import Flask, Response, request, jsonify
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class VideoStreamManager:
    def __init__(self):
        self.streams = {}  # {stream_id: StreamProxy}
        self.lock = threading.Lock()
        
    def create_stream(self, source_url, stream_id=None):
        """创建视频流代理"""
        if not stream_id:
            stream_id = str(uuid.uuid4())
            
        logger.info(f"创建流代理: {stream_id} <- {source_url}")
        
        with self.lock:
            # 如果已存在，先停止
            if stream_id in self.streams:
                self.streams[stream_id].stop()
                
            proxy = StreamProxy(source_url, stream_id)
            if proxy.start():
                self.streams[stream_id] = proxy
                logger.info(f"流代理创建成功: {stream_id}")
                return stream_id
            else:
                logger.error(f"流代理创建失败: {stream_id}")
                return None
                
    def get_stream(self, stream_id):
        with self.lock:
            return self.streams.get(stream_id)
            
    def remove_stream(self, stream_id):
        with self.lock:
            if stream_id in self.streams:
                self.streams[stream_id].stop()
                del self.streams[stream_id]
                logger.info(f"流代理已移除: {stream_id}")
                
    def list_active_streams(self):
        with self.lock:
            active = {}
            for sid, proxy in self.streams.items():
                if proxy.is_running():
                    active[sid] = {
                        'source_url': proxy.source_url,
                        'created_at': proxy.created_at,
                        'frame_count': proxy.frame_count
                    }
            return active

class StreamProxy:
    def __init__(self, source_url, stream_id):
        self.source_url = source_url
        self.stream_id = stream_id
        self.created_at = time.time()
        self.ffmpeg_process = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        self.frame_count = 0
        self.last_frame_time = 0
        
    def _build_ffmpeg_command(self):
        """根据视频源类型构建ffmpeg命令"""
        url = self.source_url.lower()
        
        # 基础命令
        cmd = ['ffmpeg', '-loglevel', 'error']
        
        # 根据源类型添加输入参数
        if url.startswith('rtsp://'):
            cmd.extend(['-rtsp_transport', 'tcp', '-i', self.source_url])
        elif url.startswith('rtmp://'):
            cmd.extend(['-i', self.source_url])
        elif url.startswith('http://') or url.startswith('https://'):
            cmd.extend(['-i', self.source_url])
        elif '/dev/video' in url or url.isdigit():
            cmd.extend(['-f', 'v4l2', '-i', self.source_url])
        else:
            cmd.extend(['-i', self.source_url])
            
        # 输出参数
        cmd.extend([
            '-f', 'mjpeg',
            '-q:v', '8',  # 稍微降低质量以提高性能
            '-r', '10',   # 10fps
            '-s', '1280x720',  # 固定分辨率
            'pipe:1'
        ])
        
        return cmd
        
    def start(self):
        """启动流代理"""
        try:
            cmd = self._build_ffmpeg_command()
            logger.info(f"启动ffmpeg: {' '.join(cmd)}")
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_frames, daemon=True)
            self.reader_thread.start()
            
            # 等待首帧
            start_time = time.time()
            while time.time() - start_time < 10:  # 最多等待10秒
                if self.current_frame is not None:
                    logger.info(f"流代理启动成功，已获取首帧: {self.stream_id}")
                    return True
                time.sleep(0.1)
                
            # 检查ffmpeg是否已退出
            if self.ffmpeg_process.poll() is not None:
                stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"ffmpeg启动失败: {stderr}")
                return False
                
            logger.warning(f"流代理启动超时，但ffmpeg仍在运行: {self.stream_id}")
            return True  # ffmpeg还在运行，可能只是需要更多时间
            
        except Exception as e:
            logger.error(f"启动流代理异常: {e}")
            return False
            
    def _read_frames(self):
        """读取视频帧"""
        buffer = b''
        while self.running and self.ffmpeg_process:
            try:
                data = self.ffmpeg_process.stdout.read(8192)
                if not data:
                    logger.warning(f"ffmpeg输出结束: {self.stream_id}")
                    break
                    
                buffer += data
                
                # 查找JPEG帧边界
                while True:
                    start_marker = buffer.find(b'\xff\xd8')
                    end_marker = buffer.find(b'\xff\xd9')
                    
                    if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
                        # 找到完整的JPEG帧
                        frame = buffer[start_marker:end_marker + 2]
                        buffer = buffer[end_marker + 2:]
                        
                        with self.frame_lock:
                            self.current_frame = frame
                            self.frame_count += 1
                            self.last_frame_time = time.time()
                            
                        if self.frame_count % 50 == 0:
                            logger.debug(f"已处理 {self.frame_count} 帧: {self.stream_id}")
                    else:
                        break
                        
            except Exception as e:
                logger.error(f"读取帧异常: {e}")
                break
                
        logger.info(f"帧读取线程退出: {self.stream_id}")
        
    def get_frame(self):
        """获取当前帧"""
        with self.frame_lock:
            return self.current_frame
            
    def is_running(self):
        """检查是否正在运行"""
        if not self.running or not self.ffmpeg_process:
            return False
            
        # 检查进程状态
        if self.ffmpeg_process.poll() is not None:
            return False
            
        # 检查是否有新帧（最近10秒内）
        return time.time() - self.last_frame_time < 10.0
        
    def stop(self):
        """停止流代理"""
        logger.info(f"停止流代理: {self.stream_id}")
        self.running = False
        
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                logger.warning(f"强制终止ffmpeg: {self.stream_id}")
                self.ffmpeg_process.kill()

# 全局管理器
manager = VideoStreamManager()

@app.route('/api/streams', methods=['POST'])
def create_stream():
    """创建视频流"""
    try:
        data = request.get_json()
        source_url = data.get('source_url')
        stream_id = data.get('stream_id')
        
        if not source_url:
            return jsonify({'error': 'source_url is required'}), 400
            
        result_id = manager.create_stream(source_url, stream_id)
        if result_id:
            return jsonify({
                'success': True,
                'stream_id': result_id,
                'stream_url': f'http://127.0.0.1:8090/stream/{result_id}'
            })
        else:
            return jsonify({'error': 'Failed to create stream'}), 500
            
    except Exception as e:
        logger.error(f"创建流API异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams', methods=['GET'])
def list_streams():
    """列出活跃流"""
    try:
        streams = manager.list_active_streams()
        return jsonify({'success': True, 'streams': streams})
    except Exception as e:
        logger.error(f"列出流API异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<stream_id>', methods=['DELETE'])
def delete_stream(stream_id):
    """删除流"""
    try:
        manager.remove_stream(stream_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"删除流API异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<stream_id>')
def get_stream(stream_id):
    """获取视频流"""
    proxy = manager.get_stream(stream_id)
    if not proxy:
        return "Stream not found", 404
        
    def generate():
        last_frame = None
        while proxy.is_running():
            frame = proxy.get_frame()
            if frame and frame != last_frame:
                last_frame = frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)  # 10fps
            
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """健康检查"""
    active_count = len(manager.list_active_streams())
    return jsonify({
        'status': 'ok',
        'active_streams': active_count,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    logger.info("启动视频流服务...")
    app.run(host='0.0.0.0', port=8090, threaded=True, debug=False)
