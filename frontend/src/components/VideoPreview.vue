<template>
  <div class="video-preview-container" ref="containerRef">
    <img 
      v-if="streamUrl"
      :src="streamUrl" 
      alt="Video Stream"
      class="video-stream"
      @load="onImageLoad"
      ref="imageRef"
    />
    <canvas ref="canvasRef" class="overlay-canvas"></canvas>
    <div v-if="!streamUrl" class="no-stream">
      <el-icon><VideoCamera /></el-icon>
      <span>无视频流</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useUserStore } from '@/stores/user';
import { VideoCamera } from '@element-plus/icons-vue';

const props = defineProps({
  taskId: {
    type: Number,
    required: true,
  },
  streamUrl: {
    type: String,
    required: true,
  },
});

const userStore = useUserStore();
const ws = ref(null);
const containerRef = ref(null);
const imageRef = ref(null);
const canvasRef = ref(null);
const naturalSize = ref({ width: 0, height: 0 });

const connectWebSocket = () => {
  if (!props.taskId || !userStore.token) return;

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // 根据环境自动适配WebSocket地址 - Docker环境通过相对路径访问
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/tasks/${props.taskId}/stream?token=${userStore.token}`;

  console.log("Attempting to connect to WebSocket:", wsUrl);
  ws.value = new WebSocket(wsUrl);

  ws.value.onopen = () => {
    console.log(`WebSocket connected for task ${props.taskId}`);
  };

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.detections) {
      drawDetections(data.detections);
    }
  };

  ws.value.onclose = () => {
    console.log('WebSocket disconnected.');
  };

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
};

const drawDetections = (detections) => {
  const canvas = canvasRef.value;
  const image = imageRef.value;
  if (!canvas || !image) return;

  const ctx = canvas.getContext('2d');
  const { clientWidth: displayWidth, clientHeight: displayHeight } = image;
  const { width: naturalWidth, height: naturalHeight } = naturalSize.value;
  
  if (naturalWidth === 0 || naturalHeight === 0) return;

  canvas.width = displayWidth;
  canvas.height = displayHeight;
  
  canvas.style.top = `${image.offsetTop}px`;
  canvas.style.left = `${image.offsetLeft}px`;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scaleX = displayWidth / naturalWidth;
  const scaleY = displayHeight / naturalHeight;

  detections.forEach(det => {
    const [x, y, w, h] = det.box;
    const score = det.score;
    const label = det.label;

    ctx.strokeStyle = '#409eff';
    ctx.lineWidth = 2;
    ctx.strokeRect(x * scaleX, y * scaleY, w * scaleX, h * scaleY);

    ctx.fillStyle = '#409eff';
    const text = `${label}: ${score.toFixed(2)}`;
    ctx.font = '14px Arial';
    const textMetrics = ctx.measureText(text);
    ctx.fillRect(
      x * scaleX,
      y * scaleY - 18,
      textMetrics.width + 8,
      18
    );
    ctx.fillStyle = 'white';
    ctx.fillText(text, x * scaleX + 4, y * scaleY - 5);
  });
};

const onImageLoad = () => {
  const image = imageRef.value;
  if (image) {
    naturalSize.value = { width: image.naturalWidth, height: image.naturalHeight };
  }
};

let resizeObserver;
onMounted(() => {
  connectWebSocket();
  
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      const canvas = canvasRef.value;
      const image = imageRef.value;
      if (canvas && image) {
        canvas.width = image.clientWidth;
        canvas.height = image.clientHeight;
        canvas.style.top = `${image.offsetTop}px`;
        canvas.style.left = `${image.offsetLeft}px`;
      }
    });
    resizeObserver.observe(containerRef.value);
  }
});

onUnmounted(() => {
  if (ws.value) {
    ws.value.close();
  }
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});

watch(() => props.taskId, (newId, oldId) => {
  if (newId !== oldId) {
    if (ws.value) {
      ws.value.close();
    }
    connectWebSocket();
  }
});
</script>

<style scoped>
.video-preview-container {
  position: relative;
  width: 100%;
  height: 60vh;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}
.video-stream {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.overlay-canvas {
  position: absolute;
  pointer-events: none;
}
.no-stream {
  color: #ccc;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 1.2rem;
  gap: 12px;
}
.no-stream .el-icon {
  font-size: 3rem;
}
</style> 