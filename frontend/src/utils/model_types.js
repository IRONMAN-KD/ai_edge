export const MODEL_TYPES = [
  { value: 'object_detection', label: '目标检测' },
  { value: 'classification', label: '图像分类' },
  { value: 'face_detection', label: '人脸检测' },
  { value: 'vehicle_detection', label: '车辆检测' },
  { value: 'ocr', label: '文字识别' },
  { value: 'segmentation', label: '图像分割' },
];

export const getModelTypeLabel = (value) => {
  const type = MODEL_TYPES.find(t => t.value === value);
  return type ? type.label : '其他';
}; 