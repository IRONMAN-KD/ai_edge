package response

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// Response 统一响应结构
type Response struct {
	Code      int         `json:"code"`
	Message   string      `json:"message"`
	Data      interface{} `json:"data,omitempty"`
	Error     interface{} `json:"error,omitempty"`
	Timestamp int64       `json:"timestamp"`
	RequestID string      `json:"request_id,omitempty"`
}

// PaginatedResponse 分页响应结构
type PaginatedResponse struct {
	Code      int         `json:"code"`
	Message   string      `json:"message"`
	Data      interface{} `json:"data"`
	Pagination Pagination `json:"pagination"`
	Timestamp int64       `json:"timestamp"`
	RequestID string      `json:"request_id,omitempty"`
}

// Pagination 分页信息
type Pagination struct {
	Page       int   `json:"page"`
	Size       int   `json:"size"`
	Total      int64 `json:"total"`
	TotalPages int   `json:"total_pages"`
	HasNext    bool  `json:"has_next"`
	HasPrev    bool  `json:"has_prev"`
}

// Success 成功响应
func Success(c *gin.Context, data interface{}) {
	response := Response{
		Code:      http.StatusOK,
		Message:   "Success",
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusOK, response)
}

// SuccessWithMessage 带消息的成功响应
func SuccessWithMessage(c *gin.Context, message string, data interface{}) {
	response := Response{
		Code:      http.StatusOK,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusOK, response)
}

// Created 创建成功响应
func Created(c *gin.Context, data interface{}) {
	response := Response{
		Code:      http.StatusCreated,
		Message:   "Created successfully",
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusCreated, response)
}

// Updated 更新成功响应
func Updated(c *gin.Context, data interface{}) {
	response := Response{
		Code:      http.StatusOK,
		Message:   "Updated successfully",
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusOK, response)
}

// Deleted 删除成功响应
func Deleted(c *gin.Context) {
	response := Response{
		Code:      http.StatusOK,
		Message:   "Deleted successfully",
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusOK, response)
}

// Error 错误响应
func Error(c *gin.Context, code int, message string, err interface{}) {
	response := Response{
		Code:      code,
		Message:   message,
		Error:     err,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(code, response)
}

// BadRequest 400错误响应
func BadRequest(c *gin.Context, message string, err interface{}) {
	Error(c, http.StatusBadRequest, message, err)
}

// Unauthorized 401错误响应
func Unauthorized(c *gin.Context, message string) {
	Error(c, http.StatusUnauthorized, message, nil)
}

// Forbidden 403错误响应
func Forbidden(c *gin.Context, message string) {
	Error(c, http.StatusForbidden, message, nil)
}

// NotFound 404错误响应
func NotFound(c *gin.Context, message string) {
	Error(c, http.StatusNotFound, message, nil)
}

// Conflict 409错误响应
func Conflict(c *gin.Context, message string, err interface{}) {
	Error(c, http.StatusConflict, message, err)
}

// UnprocessableEntity 422错误响应
func UnprocessableEntity(c *gin.Context, message string, err interface{}) {
	Error(c, http.StatusUnprocessableEntity, message, err)
}

// InternalServerError 500错误响应
func InternalServerError(c *gin.Context, message string, err interface{}) {
	Error(c, http.StatusInternalServerError, message, err)
}

// ServiceUnavailable 503错误响应
func ServiceUnavailable(c *gin.Context, message string) {
	Error(c, http.StatusServiceUnavailable, message, nil)
}

// Paginated 分页响应
func Paginated(c *gin.Context, data interface{}, page, size int, total int64) {
	totalPages := int((total + int64(size) - 1) / int64(size))
	hasNext := page < totalPages
	hasPrev := page > 1

	pagination := Pagination{
		Page:       page,
		Size:       size,
		Total:      total,
		TotalPages: totalPages,
		HasNext:    hasNext,
		HasPrev:    hasPrev,
	}

	response := PaginatedResponse{
		Code:       http.StatusOK,
		Message:    "Success",
		Data:       data,
		Pagination: pagination,
		Timestamp:  time.Now().Unix(),
		RequestID:  getRequestID(c),
	}

	c.JSON(http.StatusOK, response)
}

// PaginatedWithMessage 带消息的分页响应
func PaginatedWithMessage(c *gin.Context, message string, data interface{}, page, size int, total int64) {
	totalPages := int((total + int64(size) - 1) / int64(size))
	hasNext := page < totalPages
	hasPrev := page > 1

	pagination := Pagination{
		Page:       page,
		Size:       size,
		Total:      total,
		TotalPages: totalPages,
		HasNext:    hasNext,
		HasPrev:    hasPrev,
	}

	response := PaginatedResponse{
		Code:       http.StatusOK,
		Message:    message,
		Data:       data,
		Pagination: pagination,
		Timestamp:  time.Now().Unix(),
		RequestID:  getRequestID(c),
	}

	c.JSON(http.StatusOK, response)
}

// NoContent 204无内容响应
func NoContent(c *gin.Context) {
	c.Status(http.StatusNoContent)
}

// Accepted 202接受响应
func Accepted(c *gin.Context, message string) {
	response := Response{
		Code:      http.StatusAccepted,
		Message:   message,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusAccepted, response)
}

// PartialContent 206部分内容响应
func PartialContent(c *gin.Context, data interface{}, message string) {
	response := Response{
		Code:      http.StatusPartialContent,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusPartialContent, response)
}

// TooManyRequests 429限流响应
func TooManyRequests(c *gin.Context, message string) {
	Error(c, http.StatusTooManyRequests, message, nil)
}

// ValidationError 验证错误响应
func ValidationError(c *gin.Context, errors interface{}) {
	response := Response{
		Code:      http.StatusUnprocessableEntity,
		Message:   "Validation failed",
		Error:     errors,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(http.StatusUnprocessableEntity, response)
}

// Custom 自定义响应
func Custom(c *gin.Context, code int, message string, data interface{}) {
	response := Response{
		Code:      code,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSON(code, response)
}

// getRequestID 获取请求ID
func getRequestID(c *gin.Context) string {
	if requestID, exists := c.Get("request_id"); exists {
		if id, ok := requestID.(string); ok {
			return id
		}
	}
	return c.GetHeader("X-Request-ID")
}

// Stream 流式响应
func Stream(c *gin.Context, contentType string, data []byte) {
	c.Header("Content-Type", contentType)
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Data(http.StatusOK, contentType, data)
}

// File 文件响应
func File(c *gin.Context, filepath string) {
	c.File(filepath)
}

// FileAttachment 文件下载响应
func FileAttachment(c *gin.Context, filepath, filename string) {
	c.Header("Content-Disposition", "attachment; filename="+filename)
	c.File(filepath)
}

// Redirect 重定向响应
func Redirect(c *gin.Context, location string) {
	c.Redirect(http.StatusFound, location)
}

// PermanentRedirect 永久重定向响应
func PermanentRedirect(c *gin.Context, location string) {
	c.Redirect(http.StatusMovedPermanently, location)
}

// JSONP JSONP响应
func JSONP(c *gin.Context, callback string, data interface{}) {
	response := Response{
		Code:      http.StatusOK,
		Message:   "Success",
		Data:      data,
		Timestamp: time.Now().Unix(),
		RequestID: getRequestID(c),
	}
	c.JSONP(http.StatusOK, response)
}

// XML XML响应
func XML(c *gin.Context, data interface{}) {
	c.XML(http.StatusOK, data)
}

// YAML YAML响应
func YAML(c *gin.Context, data interface{}) {
	c.YAML(http.StatusOK, data)
}

// ProtoBuf ProtoBuf响应
func ProtoBuf(c *gin.Context, data interface{}) {
	c.ProtoBuf(http.StatusOK, data)
}

// SSE 服务器发送事件响应
func SSE(c *gin.Context, event, data string) {
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("Access-Control-Allow-Origin", "*")
	
	if event != "" {
		c.SSEvent(event, data)
	} else {
		c.SSEvent("message", data)
	}
}