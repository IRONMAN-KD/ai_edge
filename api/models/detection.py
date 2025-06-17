import cv2
import numpy as np
from .base import BaseModel
import onnxruntime as ort
from typing import List, Dict, Any

class DetectionModel(BaseModel):
    def __init__(self, model_path: str, labels: List[str] = None, **kwargs):
        self.labels = labels if labels else []
        super().__init__(model_path)

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
        output = outputs[0]
        
        # The output shape of YOLOv5 is (batch_size, 25200, 85) where 85 is box_info (4) + obj_confidence (1) + class_scores (80)
        # We need to transpose it to (batch_size, 85, 25200) to work with it easily
        predictions = np.squeeze(output).T
        
        # Filter out detections with low object confidence
        scores = np.max(predictions[:, 4:], axis=1)
        predictions = predictions[scores > 0.25, :]
        scores = scores[scores > 0.25]
        
        if len(scores) == 0:
            return []
            
        # Get the class with the highest score
        class_ids = np.argmax(predictions[:, 4:], axis=1)
        
        # Get bounding boxes
        boxes = predictions[:, :4]

        # Rescale boxes to original image dimensions
        scale_x = self.img_width / self.input_width
        scale_y = self.img_height / self.input_height
        
        # Un-letterbox
        pad_x = (self.input_width - self.img_width * min(self.input_width / self.img_width, self.input_height / self.img_height)) / 2
        pad_y = (self.input_height - self.img_height * min(self.input_width / self.img_width, self.input_height / self.img_height)) / 2

        boxes -= np.array([pad_x, pad_y, 0, 0])
        boxes[:, 0] *= self.img_width / (self.input_width - 2 * pad_x)
        boxes[:, 1] *= self.img_height / (self.input_height - 2 * pad_y)
        boxes[:, 2] *= self.img_width / (self.input_width - 2 * pad_x)
        boxes[:, 3] *= self.img_height / (self.input_height - 2 * pad_y)
        
        # Convert from (center_x, center_y, width, height) to (x1, y1, w, h) for NMS
        x_center, y_center, width, height = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = x_center - width / 2
        y1 = y_center - height / 2

        # Apply Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(np.column_stack([x1, y1, width, height]).tolist(), scores.tolist(), 0.5, 0.45)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = int(x1[i]), int(y1[i]), int(width[i]), int(height[i])
                class_id = class_ids[i]
                label = self.labels[class_id] if self.labels and len(self.labels) > class_id else f'class_{class_id}'

                detection = {
                    "box": [x, y, w, h],
                    "score": float(scores[i]),
                    "label": label,
                }
                detections.append(detection)
        
        return detections

    def inference(self, image: np.ndarray) -> List[Dict[str, Any]]:
        preprocessed_image = self.preprocess(image)
        outputs = self.session.run(self.output_names, {self.input_name: preprocessed_image})
        return self.postprocess(outputs)

    def draw_result(self, image: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        for detection in detections:
            box = detection["box"]
            score = detection["score"]
            label = detection["label"]
            x, y, w, h = box

            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label_text = f"{label}: {score:.2f}"
            (text_width, text_height), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(image, (x, y - text_height - baseline), (x + text_width, y), (0, 255, 0), -1)
            cv2.putText(image, label_text, (x, y - baseline), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
        return image 