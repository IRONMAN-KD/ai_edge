class InferenceError(Exception):
    """推理服务基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ModelError(InferenceError):
    """模型相关错误"""
    pass

class ModelNotFoundError(ModelError):
    """模型不存在错误"""
    def __init__(self, model_id: int):
        super().__init__(
            f"模型不存在: {model_id}",
            error_code="MODEL_NOT_FOUND"
        )

class ModelLoadError(ModelError):
    """模型加载错误"""
    def __init__(self, model_path: str, error: str):
        super().__init__(
            f"模型加载失败: {model_path}, 错误: {error}",
            error_code="MODEL_LOAD_ERROR"
        )

class ModelInferenceError(ModelError):
    """模型推理错误"""
    def __init__(self, model_id: int, error: str):
        super().__init__(
            f"模型推理失败: {model_id}, 错误: {error}",
            error_code="MODEL_INFERENCE_ERROR"
        )

class FileError(InferenceError):
    """文件相关错误"""
    pass

class FileNotFoundError(FileError):
    """文件不存在错误"""
    def __init__(self, file_path: str):
        super().__init__(
            f"文件不存在: {file_path}",
            error_code="FILE_NOT_FOUND"
        )

class FileUploadError(FileError):
    """文件上传错误"""
    def __init__(self, file_name: str, error: str):
        super().__init__(
            f"文件上传失败: {file_name}, 错误: {error}",
            error_code="FILE_UPLOAD_ERROR"
        )

class DatabaseError(InferenceError):
    """数据库相关错误"""
    pass

class RecordNotFoundError(DatabaseError):
    """记录不存在错误"""
    def __init__(self, record_id: int):
        super().__init__(
            f"推理记录不存在: {record_id}",
            error_code="RECORD_NOT_FOUND"
        )

class DatabaseOperationError(DatabaseError):
    """数据库操作错误"""
    def __init__(self, operation: str, error: str):
        super().__init__(
            f"数据库操作失败: {operation}, 错误: {error}",
            error_code="DATABASE_OPERATION_ERROR"
        ) 