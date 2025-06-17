<template>
  <div class="video-preview-container" ref="containerRef">
    <img 
      v-if="streamUrl" 
      :src="streamUrl" 
      class="video-feed" 
      ref="videoFeed"
      alt="Video Stream" 
      @load="handleStreamLoad"
    />
    <canvas v-if="streamUrl" ref="overlayCanvas" class="overlay-canvas"></canvas>
    <div v-if="!streamUrl || connectionStatus === 'failed'" class="status-overlay">
      <el-icon><CircleCloseFilled /></el-icon>
      <span>{{ errorMessage || '无效的任务或视频源' }}</span>
    </div>
     <div v-else-if="connectionStatus === 'connecting'" class="status-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在连接数据流...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue';

const props = defineProps({
  task: {
    type: Object,
    required: true,
  },
});

const containerRef = ref(null);
const videoFeed = ref(null);
const overlayCanvas = ref(null);
const latestDetections = ref([]);
const connectionStatus = ref('connecting'); // connecting, connected, failed, closed
const errorMessage = ref('');
let ws = null;

const streamUrl = computed(() => {
  if (props.task && props.task.id) {
    return `/api/tasks/${props.task.id}/stream`;
  }
  return null;
});

const setupWebSocket = () => {
  if (!props.task || !props.task.id) return;

  const token = localStorage.getItem('token');
  if (!token) {
    connectionStatus.value = 'failed';
    errorMessage.value = '未找到认证令牌，请重新登录。';
    return;
  }

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/tasks/${props.task.id}/stream?token=${token}`;
  
  ws = new WebSocket(wsUrl);
  connectionStatus.value = 'connecting';

  ws.onopen = () => {
    connectionStatus.value = 'connected';
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.detections) {
      latestDetections.value = data.detections;
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    connectionStatus.value = 'failed';
    errorMessage.value = '数据流连接失败。';
  };

  ws.onclose = (event) => {
    if (event.code !== 1000) {
      connectionStatus.value = 'failed';
      errorMessage.value = `数据流已断开: ${event.reason || '未知错误'}`;
    } else {
      connectionStatus.value = 'closed';
    }
  };
};

const drawOverlay = () => {
  const img = videoFeed.value;
  const canvas = overlayCanvas.value;
  const ctx = canvas?.getContext('2d');
  const detections = latestDetections.value;

  if (!img || !canvas || !ctx || img.naturalWidth === 0) return;

  // Match canvas size to the displayed image size
  const { width, height, top, left } = getRenderedSize(img);
  canvas.width = width;
  canvas.height = height;
  canvas.style.top = `${top}px`;
  canvas.style.left = `${left}px`;
  
  const scaleX = canvas.width / img.naturalWidth;
  const scaleY = canvas.height / img.naturalHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  if (!detections) return;

  detections.forEach(det => {
    const { box, label, score } = det;
    const [x, y, w, h] = box;

    const scaledX = x * scaleX;
    const scaledY = y * scaleY;
    const scaledW = w * scaleX;
    const scaledH = h * scaleY;

    ctx.strokeStyle = '#409EFF';
    ctx.lineWidth = 2;
    ctx.strokeRect(scaledX, scaledY, scaledW, scaledH);
    
    const text = `${label} ${score.toFixed(2)}`;
    ctx.font = 'bold 14px Arial';
    const textMetrics = ctx.measureText(text);
    
    ctx.fillStyle = '#409EFF';
    ctx.fillRect(scaledX, scaledY - 20, textMetrics.width + 8, 20);

    ctx.fillStyle = 'white';
    ctx.fillText(text, scaledX + 4, scaledY - 5);
  });
};

const getRenderedSize = (img) => {
  if (!img || !img.parentElement) return { width: 0, height: 0, top: 0, left: 0 };
  
  const container = img.parentElement;
  const containerAspect = container.clientWidth / container.clientHeight;
  const imgAspect = img.naturalWidth / img.naturalHeight;
  
  let renderedWidth, renderedHeight, top, left;

  if (imgAspect > containerAspect) {
    renderedWidth = container.clientWidth;
    renderedHeight = renderedWidth / imgAspect;
    top = (container.clientHeight - renderedHeight) / 2;
    left = 0;
  } else {
    renderedHeight = container.clientHeight;
    renderedWidth = renderedHeight * imgAspect;
    left = (container.clientWidth - renderedWidth) / 2;
    top = 0;
  }
  return { width: renderedWidth, height: renderedHeight, top, left };
};

const handleStreamLoad = () => {
  // When the MJPEG stream image loads for the first time, resize the canvas.
  drawOverlay();
};

watch(latestDetections, () => {
  drawOverlay();
});

let resizeObserver;
onMounted(() => {
  setupWebSocket();
  const container = containerRef.value;
  if (container) {
    resizeObserver = new ResizeObserver(() => {
      drawOverlay();
    });
    resizeObserver.observe(container);
  }
});

onUnmounted(() => {
  if (ws) {
    ws.close(1000, "Component unmounted");
  }
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});

</script>

<style scoped>
.video-preview-container {
  position: relative;
  width: 100%;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
  overflow: hidden;
}

.video-feed {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.overlay-canvas {
  position: absolute;
  pointer-events: none;
}

.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  z-index: 10;
}

.status-overlay .el-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}
</style> 