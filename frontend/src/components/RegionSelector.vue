<template>
  <div class="region-selector">
    <div class="canvas-container" ref="containerRef">
      <img
        ref="imageRef"
        :src="imageUrl"
        @load="initialize"
        style="display: none; max-width: 100%;"
      />
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

const props = defineProps({
  imageUrl: {
    type: String,
    required: true,
  },
  initialRoi: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['update:roi']);

const containerRef = ref(null);
const canvasRef = ref(null);
const imageRef = ref(null);
const ctx = ref(null);
const rect = ref({});
const drag = ref(false);

const initialize = () => {
  const image = imageRef.value;
  const container = containerRef.value;
  const canvas = canvasRef.value;

  if (!image || !container || !canvas) return;

  const containerWidth = container.offsetWidth;
  const imageAspectRatio = image.naturalWidth / image.naturalHeight;
  
  let canvasWidth = containerWidth;
  let canvasHeight = containerWidth / imageAspectRatio;

  canvas.width = canvasWidth;
  canvas.height = canvasHeight;
  
  ctx.value = canvas.getContext('2d');
  
  drawImage();
  
  if (props.initialRoi) {
    const scaleX = canvas.width / image.naturalWidth;
    const scaleY = canvas.height / image.naturalHeight;
    rect.value = {
        startX: props.initialRoi.x * scaleX,
        startY: props.initialRoi.y * scaleY,
        w: props.initialRoi.w * scaleX,
        h: props.initialRoi.h * scaleY,
    };
    drawRect();
  }

  addEventListeners();
};

const drawImage = () => {
  if (ctx.value && imageRef.value) {
    ctx.value.drawImage(imageRef.value, 0, 0, canvasRef.value.width, canvasRef.value.height);
  }
}

const addEventListeners = () => {
  const canvas = canvasRef.value;
  canvas.addEventListener('mousedown', mouseDown);
  canvas.addEventListener('mouseup', mouseUp);
  canvas.addEventListener('mousemove', mouseMove);
};

const removeEventListeners = () => {
    const canvas = canvasRef.value;
    if (canvas) {
        canvas.removeEventListener('mousedown', mouseDown);
        canvas.removeEventListener('mouseup', mouseUp);
        canvas.removeEventListener('mousemove', mouseMove);
    }
}

const mouseDown = (e) => {
  rect.value.startX = e.offsetX;
  rect.value.startY = e.offsetY;
  drag.value = true;
};

const mouseUp = () => {
  drag.value = false;
  emitRoi();
};

const mouseMove = (e) => {
  if (drag.value) {
    rect.value.w = e.offsetX - rect.value.startX;
    rect.value.h = e.offsetY - rect.value.startY;
    drawImage();
    drawRect();
  }
};

const drawRect = () => {
    if (ctx.value) {
        ctx.value.strokeStyle = '#FF0000';
        ctx.value.lineWidth = 2;
        ctx.value.strokeRect(rect.value.startX, rect.value.startY, rect.value.w, rect.value.h);
    }
};

const emitRoi = () => {
    const canvas = canvasRef.value;
    const image = imageRef.value;
    const scaleX = image.naturalWidth / canvas.width;
    const scaleY = image.naturalHeight / canvas.height;

    const roi = {
        x: Math.round(rect.value.startX * scaleX),
        y: Math.round(rect.value.startY * scaleY),
        w: Math.round(rect.value.w * scaleX),
        h: Math.round(rect.value.h * scaleY),
    };
    emit('update:roi', roi);
};

const clearSelection = () => {
    rect.value = {};
    drawImage();
    emit('update:roi', null);
}

onMounted(() => {
  // The image @load event will trigger initialization
});

onUnmounted(() => {
    removeEventListeners();
})
</script>

<style scoped>
.canvas-container {
  width: 100%;
  position: relative;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
}
canvas {
  display: block;
  cursor: crosshair;
}
</style> 