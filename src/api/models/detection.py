import cv2
import numpy as np
from .base import BaseModel
import onnxruntime as ort
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import os
import time
try:
    import acl
except ImportError:
    # Create a dummy acl module to avoid ImportError if it's not installed
    # This allows development on non-Atlas platforms.
    class DummyAcl:
        def __getattr__(self, name):
            def not_implemented(*args, **kwargs):
                raise NotImplementedError(f"ACL is not installed. '{name}' function is not available.")
            return not_implemented
    acl = DummyAcl()

class ONNXDetectionModel(BaseModel):
    def __init__(self, path: str, labels: List[str] = None, **kwargs):
        self.labels = labels if labels else []
        # Call super().__init__ with the correct argument name 'model_path'
        super().__init__(model_path=path)
        # Generate a color palette for each label
        self.colors = np.random.uniform(100, 255, size=(len(self.labels), 3)) if self.labels else []
        
        # Load a font that supports CJK characters
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts', 'NotoSansCJK-Regular.otf')
        try:
            self.font = ImageFont.truetype(font_path, 15)
        except IOError:
            self.font = ImageFont.load_default()

    def load_model(self):
        """Loads the ONNX model and initializes the session."""
        try:
            self.session = ort.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']
            )
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]
            
            input_shape = self.session.get_inputs()[0].shape
            self.input_height = input_shape[2] if isinstance(input_shape[2], int) else 640
            self.input_width = input_shape[3] if isinstance(input_shape[3], int) else 640
            # Set the input_size attribute required by the BaseModel
            self.input_size = (self.input_width, self.input_height)

        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model {self.model_path}: {e}")

    def preprocess(self, image: np.ndarray):
        self.img_height, self.img_width = image.shape[:2]
        
        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        resized_width = int(self.img_width * scale)
        resized_height = int(self.img_height * scale)
        
        resized_image = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
        
        padded_image = np.full((self.input_height, self.input_width, 3), 114, dtype=np.uint8)
        padded_image[(self.input_height - resized_height) // 2:(self.input_height - resized_height) // 2 + resized_height, 
                     (self.input_width - resized_width) // 2:(self.input_width - resized_width) // 2 + resized_width, :] = resized_image

        input_tensor = padded_image.astype(np.float32) / 255.0
        input_tensor = input_tensor.transpose(2, 0, 1)
        return np.expand_dims(input_tensor, axis=0)

    def postprocess(self, outputs: List[np.ndarray]) -> List[Dict[str, Any]]:
        predictions = np.squeeze(outputs[0])
        
        obj_confidence = predictions[:, 4]
        class_probs = predictions[:, 5:]
        
        scores = obj_confidence * np.max(class_probs, axis=1)
        
        keep = scores > 0.25
        if not np.any(keep):
            return []

        predictions = predictions[keep]
        scores = scores[keep]
        class_ids = np.argmax(predictions[:, 5:], axis=1)
        boxes = predictions[:, :4]

        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        pad_x = (self.input_width - self.img_width * scale) / 2
        pad_y = (self.input_height - self.img_height * scale) / 2

        boxes[:, 0] = (boxes[:, 0] - pad_x) / scale
        boxes[:, 1] = (boxes[:, 1] - pad_y) / scale
        boxes[:, 2] /= scale
        boxes[:, 3] /= scale
        
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        
        indices = cv2.dnn.NMSBoxes(
            np.column_stack([x1, y1, boxes[:, 2], boxes[:, 3]]).tolist(), 
            scores.tolist(), 
            0.5,
            0.45
        )
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                class_id = class_ids[i]
                label = self.labels[class_id] if self.labels and len(self.labels) > class_id else f'class_{class_id}'
                detection = {
                    "box": [int(x1[i]), int(y1[i]), int(boxes[i, 2]), int(boxes[i, 3])],
                    "score": float(scores[i]),
                    "label": label,
                    "class_id": int(class_id)
                }
                detections.append(detection)
        
        return detections

    def inference(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], float]:
        import time
        preprocessed_image = self.preprocess(image)
        
        start_time = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: preprocessed_image})
        inference_time = time.time() - start_time
        
        detections = self.postprocess(outputs)
        return detections, inference_time

    def draw_result(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        # Implementation is the same as before
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_img)

        for detection in detections:
            box = detection["box"]
            score = detection["score"]
            label = detection["label"]
            class_id = detection.get("class_id", 0)
            x, y, w, h = box
            color = tuple(self.colors[class_id].astype(int).tolist()) if len(self.colors) > 0 and class_id < len(self.colors) else (0, 255, 0)
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            label_text = f"{label}: {score:.2f}"
            try:
                text_bbox = draw.textbbox((x, y), label_text, font=self.font)
                text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            except AttributeError:
                text_w, text_h = draw.textsize(label_text, font=self.font)
            label_bg_y = y - text_h - 5
            draw.rectangle([x, label_bg_y, x + text_w + 4, y], fill=color)
            draw.text((x + 2, label_bg_y), label_text, font=self.font, fill=(0, 0, 0))
            
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

class AtlasDetectionModel(BaseModel):
    def __init__(self, path: str, device_id: int = 0, **kwargs):
        self.acl = acl
        self.device_id = device_id
        self.context = None
        self.stream = None  # 添加stream属性
        self.model_id = None
        self.model_desc = None
        self.labels = kwargs.get('labels', [])
        self.confidence_threshold = kwargs.get('confidence_threshold', 0.4)
        self.nms_threshold = kwargs.get('nms_threshold', 0.45)
        
        # Generate a color palette for each label
        self.colors = np.random.uniform(100, 255, size=(len(self.labels), 3)) if self.labels else []
        
        # Load a font that supports CJK characters
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts', 'NotoSansCJK-Regular.otf')
        try:
            self.font = ImageFont.truetype(font_path, 15)
        except IOError:
            self.font = ImageFont.load_default()
        
        self.input_dataset = None
        self.output_dataset = None
        self.input_buffers = []
        self.output_buffers = []
        
        # 尝试初始化ACL，如果失败就抛出异常让工厂类处理
        self._initialize_acl()
        
        super().__init__(model_path=path)
        self._prepare_model_io()
        
        # Get input size for postprocessing reference
        input_dims, _ = self.acl.mdl.get_input_dims(self.model_desc, 0)
        self.input_height = input_dims['dims'][2]
        self.input_width = input_dims['dims'][3]
        self.input_size = (self.input_width, self.input_height)

    def _initialize_acl(self):
        try:
            # 步骤1: 初始化ACL（按照华为官方文档，不传参数或传None）
            ret = self.acl.init()
            if ret != 0: 
                raise RuntimeError(f"acl.init() failed with return code: {ret}")
            
            # 步骤2: 设置设备
            ret = self.acl.rt.set_device(self.device_id)
            if ret != 0: 
                raise RuntimeError(f"Failed to set device {self.device_id}, return code: {ret}")
            
            # 步骤3: 创建Context（传入正确的device_id）
            self.context, ret = self.acl.rt.create_context(self.device_id)
            if ret != 0: 
                raise RuntimeError(f"Failed to create context, return code: {ret}")
            
            # 步骤4: 创建Stream（华为官方文档中的标准步骤）
            self.stream, ret = self.acl.rt.create_stream()
            if ret != 0: 
                raise RuntimeError(f"Failed to create stream, return code: {ret}")
                
        except Exception as e:
            # 添加更详细的错误信息，帮助判断是否是设备不可用
            raise RuntimeError(f"Atlas ACL initialization failed: {e}. This might be because Atlas device is not available in current environment.")

    def load_model(self):
        self.model_id, ret = self.acl.mdl.load_from_file(self.model_path)
        if ret != 0: raise RuntimeError(f"Failed to load model from {self.model_path}")
        self.model_desc = self.acl.mdl.create_desc()
        self.acl.mdl.get_desc(self.model_desc, self.model_id)

    def _prepare_model_io(self):
        self.input_dataset = self.acl.mdl.create_dataset()
        num_inputs = self.acl.mdl.get_num_inputs(self.model_desc)
        for i in range(num_inputs):
            buffer_size = self.acl.mdl.get_input_size_by_index(self.model_desc, i)
            buffer, _ = self.acl.rt.malloc(buffer_size, acl.ACL_MEM_MALLOC_HUGE_FIRST)
            data_buffer = self.acl.create_data_buffer(buffer, buffer_size)
            self.acl.mdl.add_dataset_buffer(self.input_dataset, data_buffer)
            self.input_buffers.append({'buffer': buffer, 'size': buffer_size})

        self.output_dataset = self.acl.mdl.create_dataset()
        num_outputs = self.acl.mdl.get_num_outputs(self.model_desc)
        for i in range(num_outputs):
            buffer_size = self.acl.mdl.get_output_size_by_index(self.model_desc, i)
            buffer, _ = self.acl.rt.malloc(buffer_size, acl.ACL_MEM_MALLOC_HUGE_FIRST)
            data_buffer = self.acl.create_data_buffer(buffer, buffer_size)
            self.acl.mdl.add_dataset_buffer(self.output_dataset, data_buffer)
            self.output_buffers.append({'buffer': buffer, 'size': buffer_size})

    def __del__(self):
        try:
            # 只有在ACL正确初始化后才清理资源
            if hasattr(self, 'acl') and hasattr(self.acl, 'rt') and callable(getattr(self.acl.rt, 'free', None)):
                if hasattr(self, 'input_dataset') and self.input_dataset:
                    for item in self.input_buffers: 
                        self.acl.rt.free(item['buffer'])
                    self.acl.mdl.destroy_dataset(self.input_dataset)
                if hasattr(self, 'output_dataset') and self.output_dataset:
                    for item in self.output_buffers: 
                        self.acl.rt.free(item['buffer'])
                    self.acl.mdl.destroy_dataset(self.output_dataset)
                if hasattr(self, 'model_id') and self.model_id: 
                    self.acl.mdl.unload(self.model_id)
                if hasattr(self, 'model_desc') and self.model_desc: 
                    self.acl.mdl.destroy_desc(self.model_desc)
                # 添加对stream的清理
                if hasattr(self, 'stream') and self.stream: 
                    self.acl.rt.destroy_stream(self.stream)
                if hasattr(self, 'context') and self.context: 
                    self.acl.rt.destroy_context(self.context)
                if hasattr(self, 'device_id'):
                    self.acl.rt.reset_device(self.device_id)
                self.acl.finalize()
        except Exception:
            # 忽略析构函数中的错误，避免影响程序正常退出
            pass

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        img_h, img_w, _ = image.shape
        scale = min(self.input_width / img_w, self.input_height / img_h)
        resized_w, resized_h = int(img_w * scale), int(img_h * scale)
        resized_img = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
        padded_img = np.full((self.input_height, self.input_width, 3), 114, dtype=np.uint8)
        top, left = (self.input_height - resized_h) // 2, (self.input_width - resized_w) // 2
        padded_img[top:top + resized_h, left:left + resized_w, :] = resized_img
        return np.ascontiguousarray(padded_img)

    def _execute_model(self, image_bytes: bytes) -> List[np.ndarray]:
        ret = self.acl.rt.memcpy(self.input_buffers[0]['buffer'], self.input_buffers[0]['size'], image_bytes, len(image_bytes), acl.ACL_MEMCPY_HOST_TO_DEVICE)
        if ret != 0: raise RuntimeError("memcpy H2D failed")

        ret = self.acl.mdl.execute(self.model_id, self.input_dataset, self.output_dataset)
        if ret != 0: raise RuntimeError(f"Model execution failed: {ret}")

        outputs = []
        for i, item in enumerate(self.output_buffers):
            buffer_device, buffer_size = item['buffer'], item['size']
            host_buffer, _ = self.acl.rt.malloc_host(buffer_size)
            self.acl.rt.memcpy(host_buffer, buffer_size, buffer_device, buffer_size, acl.ACL_MEMCPY_DEVICE_TO_HOST)
            dims, _ = self.acl.mdl.get_output_dims(self.model_desc, i)
            shape = tuple(dims['dims'])
            dtype = np.dtype(acl.util.get_numpy_type(acl.mdl.get_output_data_type(self.model_desc, i)))
            outputs.append(np.frombuffer(acl.util.ptr_to_numpy(host_buffer, (buffer_size,)), dtype=dtype).reshape(shape))
            self.acl.rt.free_host(host_buffer)
        return outputs

    def postprocess(self, outputs: List[np.ndarray], original_image_shape: Tuple[int, int]) -> List[Dict[str, Any]]:
        self.img_height, self.img_width = original_image_shape
        predictions = np.squeeze(outputs[0])
        
        obj_confidence = predictions[:, 4]
        class_probs = predictions[:, 5:]
        scores = obj_confidence * np.max(class_probs, axis=1)

        keep = scores > self.confidence_threshold
        if not np.any(keep): return []

        predictions, scores = predictions[keep], scores[keep]
        class_ids = np.argmax(predictions[:, 5:], axis=1)
        boxes = predictions[:, :4]

        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        pad_x = (self.input_width - self.img_width * scale) / 2
        pad_y = (self.input_height - self.img_height * scale) / 2

        boxes[:, 0] = (boxes[:, 0] - pad_x) / scale
        boxes[:, 1] = (boxes[:, 1] - pad_y) / scale
        boxes[:, 2] /= scale
        boxes[:, 3] /= scale
        
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        
        indices = cv2.dnn.NMSBoxes(np.column_stack([x1, y1, boxes[:, 2], boxes[:, 3]]).tolist(), scores.tolist(), self.confidence_threshold, self.nms_threshold)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                class_id = class_ids[i]
                detection = {
                    "box": [int(x1[i]), int(y1[i]), int(boxes[i, 2]), int(boxes[i, 3])],
                    "score": float(scores[i]),
                    "label": self.labels[class_id] if self.labels and class_id < len(self.labels) else f'class_{class_id}',
                    "class_id": int(class_id)
                }
                detections.append(detection)
        return detections
    
    def inference(self, image: np.ndarray) -> Tuple[List[Dict[str, Any]], float]:
        original_shape = image.shape[:2]
        preprocessed_image = self.preprocess(image)
        
        start_time = time.time()
        raw_outputs = self._execute_model(preprocessed_image.tobytes())
        inference_time = time.time() - start_time
        
        detections = self.postprocess(raw_outputs, original_shape)
        return detections, inference_time

    def draw_result(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        # Implementation is the same as before
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_img)

        for detection in detections:
            box = detection["box"]
            score = detection["score"]
            label = detection["label"]
            class_id = detection.get("class_id", 0)
            x, y, w, h = box
            color = tuple(self.colors[class_id].astype(int).tolist()) if len(self.colors) > 0 and class_id < len(self.colors) else (0, 255, 0)
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            label_text = f"{label}: {score:.2f}"
            try:
                text_bbox = draw.textbbox((x, y), label_text, font=self.font)
                text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            except AttributeError:
                text_w, text_h = draw.textsize(label_text, font=self.font)
            label_bg_y = y - text_h - 5
            draw.rectangle([x, label_bg_y, x + text_w + 4, y], fill=color)
            draw.text((x + 2, label_bg_y), label_text, font=self.font, fill=(0, 0, 0))
            
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR) 