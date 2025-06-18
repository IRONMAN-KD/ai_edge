import cv2
import numpy as np
from .base import BaseModel
import onnxruntime as ort
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import os

class DetectionModel(BaseModel):
    def __init__(self, model_path: str, labels: List[str] = None, **kwargs):
        self.labels = labels if labels else []
        super().__init__(model_path)
        # Generate a color palette for each label, ensuring colors are visually distinct
        self.colors = np.random.uniform(100, 255, size=(len(self.labels), 3)) if self.labels else []
        
        # Load a font that supports CJK characters
        font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts', 'NotoSansCJK-Regular.otf')
        try:
            self.font = ImageFont.truetype(font_path, 15)
        except IOError:
            print(f"Warning: Font file not found at {font_path}. Using default font. Non-ASCII characters may not render correctly.")
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
            
            # Assuming a fixed input shape for simplicity, e.g., 640x640
            input_shape = self.session.get_inputs()[0].shape
            self.input_height = input_shape[2] if isinstance(input_shape[2], int) else 640
            self.input_width = input_shape[3] if isinstance(input_shape[3], int) else 640

        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model_path}: {e}")

    def preprocess(self, image: np.ndarray):
        self.img_height, self.img_width = image.shape[:2]
        
        # Letterbox resizing
        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        resized_width = int(self.img_width * scale)
        resized_height = int(self.img_height * scale)
        
        resized_image = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
        
        padded_image = np.full((self.input_height, self.input_width, 3), 114, dtype=np.uint8)
        padded_image[(self.input_height - resized_height) // 2:(self.input_height - resized_height) // 2 + resized_height, 
                     (self.input_width - resized_width) // 2:(self.input_width - resized_width) // 2 + resized_width, :] = resized_image

        # Normalize and transpose
        input_tensor = padded_image.astype(np.float32) / 255.0
        input_tensor = input_tensor.transpose(2, 0, 1)
        return np.expand_dims(input_tensor, axis=0)

    def postprocess(self, outputs: List[np.ndarray]) -> List[Dict[str, Any]]:
        # The output of YOLOv5 is (batch_size, 25200, 85), where 85 = 4 (box) + 1 (obj_conf) + 80 (class_scores)
        # We remove the incorrect transpose operation here.
        predictions = np.squeeze(outputs[0])
        
        # Correctly calculate confidence scores and class IDs
        obj_confidence = predictions[:, 4]
        class_probs = predictions[:, 5:]
        
        # The final confidence score is the object confidence multiplied by the highest class probability
        scores = obj_confidence * np.max(class_probs, axis=1)
        
        # Filter out predictions below a confidence threshold
        keep = scores > 0.25
        if not np.any(keep):
            return []

        predictions = predictions[keep]
        scores = scores[keep]
        class_ids = np.argmax(predictions[:, 5:], axis=1)
        boxes = predictions[:, :4]

        # Rescale boxes from model input size (e.g., 640x640) to original image size
        scale = min(self.input_width / self.img_width, self.input_height / self.img_height)
        pad_x = (self.input_width - self.img_width * scale) / 2
        pad_y = (self.input_height - self.img_height * scale) / 2

        boxes[:, 0] = (boxes[:, 0] - pad_x) / scale  # x_center
        boxes[:, 1] = (boxes[:, 1] - pad_y) / scale  # y_center
        boxes[:, 2] /= scale  # width
        boxes[:, 3] /= scale  # height
        
        # Convert from (center_x, center_y, width, height) to (x1, y1, width, height) for NMS
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        
        # Apply Non-Maximum Suppression
        # Note: cv2.dnn.NMSBoxes requires (x, y, w, h) as a list of lists/tuples
        indices = cv2.dnn.NMSBoxes(
            np.column_stack([x1, y1, boxes[:, 2], boxes[:, 3]]).tolist(), 
            scores.tolist(), 
            0.5,  # score_threshold
            0.45  # nms_threshold
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

    def inference(self, image: np.ndarray) -> List[Dict[str, Any]]:
        preprocessed_image = self.preprocess(image)
        outputs = self.session.run(self.output_names, {self.input_name: preprocessed_image})
        return self.postprocess(outputs)

    def draw_result(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        # Convert OpenCV image (BGR) to Pillow image (RGB)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_img)

        for detection in detections:
            box = detection["box"]
            score = detection["score"]
            label = detection["label"]
            class_id = detection.get("class_id", 0)
            x, y, w, h = box

            color = tuple(self.colors[class_id].astype(int).tolist()) if self.colors is not None and class_id < len(self.colors) else (0, 255, 0)

            # Draw bounding box
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            
            # Prepare text and draw background rectangle
            label_text = f"{label}: {score:.2f}"
            
            try:
                # Use textbbox for more accurate size calculation with Pillow 9.2.0+
                text_bbox = draw.textbbox((x, y), label_text, font=self.font)
                text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            except AttributeError:
                # Fallback for older Pillow versions
                text_w, text_h = draw.textsize(label_text, font=self.font)

            label_bg_y = y - text_h - 5
            draw.rectangle([x, label_bg_y, x + text_w + 4, y], fill=color)
            
            # Draw text
            draw.text((x + 2, label_bg_y), label_text, font=self.font, fill=(0, 0, 0))
            
        # Convert back to OpenCV image (BGR)
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR) 