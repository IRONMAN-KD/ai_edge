package grpc

import (
	"context"
	"fmt"
	"net"
	"time"

	"ai-edge/ai-edge/ai-edge/go-platform/api/proto/inference"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"

	"github.com/sirupsen/logrus"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/reflection"
)

// Server gRPC服务器
type Server struct {
	server   *grpc.Server
	listener net.Listener
	addr     string
	logger   *logrus.Logger

	// 服务依赖
	userService      services.UserService
	modelService     services.ModelService
	taskService      services.TaskService
	inferenceService services.InferenceService
	alertService     services.AlertService
}

// NewServer 创建gRPC服务器
func NewServer(
	addr string,
	logger *logrus.Logger,
	userService services.UserService,
	modelService services.ModelService,
	taskService services.TaskService,
	inferenceService services.InferenceService,
	alertService services.AlertService,
) (*Server, error) {
	listener, err := net.Listen("tcp", addr)
	if err != nil {
		return nil, fmt.Errorf("failed to listen on %s: %w", addr, err)
	}

	// 配置服务器参数
	kaep := keepalive.EnforcementPolicy{
		MinTime:             5 * time.Second, // 客户端发送keepalive ping的最小间隔
		PermitWithoutStream: true,            // 允许在没有活动流时发送keepalive ping
	}

	kasp := keepalive.ServerParameters{
		MaxConnectionIdle:     15 * time.Second, // 连接空闲超时
		MaxConnectionAge:      30 * time.Second, // 连接最大存活时间
		MaxConnectionAgeGrace: 5 * time.Second,  // 连接优雅关闭时间
		Time:                  5 * time.Second,  // 发送keepalive ping的间隔
		Timeout:               1 * time.Second,  // 等待keepalive ping响应的超时时间
	}

	// 创建gRPC服务器
	grpcServer := grpc.NewServer(
		grpc.KeepaliveEnforcementPolicy(kaep),
		grpc.KeepaliveParams(kasp),
		grpc.MaxRecvMsgSize(1024*1024*10), // 10MB
		grpc.MaxSendMsgSize(1024*1024*10), // 10MB
	)

	server := &Server{
		server:           grpcServer,
		listener:         listener,
		addr:             addr,
		logger:           logger,
		userService:      userService,
		modelService:     modelService,
		taskService:      taskService,
		inferenceService: inferenceService,
		alertService:     alertService,
	}

	// 注册服务
	inference.RegisterInferenceServiceServer(grpcServer, server)

	// 启用反射（用于调试）
	reflection.Register(grpcServer)

	return server, nil
}

// Start 启动服务器
func (s *Server) Start() error {
	s.logger.Infof("Starting gRPC server on %s", s.addr)
	return s.server.Serve(s.listener)
}

// Stop 停止服务器
func (s *Server) Stop() {
	s.logger.Info("Stopping gRPC server")
	s.server.GracefulStop()
}

// ExecuteInference 执行推理
func (s *Server) ExecuteInference(ctx context.Context, req *inference.InferenceRequest) (*inference.InferenceResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"request_id":    req.RequestId,
		"task_id":       req.TaskId,
		"model_name":    req.ModelName,
		"model_version": req.ModelVersion,
	}).Info("Executing inference")

	startTime := time.Now()

	// 这里应该调用实际的推理服务
	// 目前返回模拟响应
	resp := &inference.InferenceResponse{
		RequestId:   req.RequestId,
		Success:     true,
		Confidence:  0.95,
		ProcessTime: time.Since(startTime).Seconds(),
		Detections: []*inference.Detection{
			{
				ClassName:  "person",
				Confidence: 0.95,
				Bbox: &inference.BoundingBox{
					X:      100,
					Y:      100,
					Width:  200,
					Height: 300,
				},
			},
		},
		Metadata: map[string]string{
			"timestamp": time.Now().Format(time.RFC3339),
			"version":   "1.0.0",
		},
	}

	s.logger.WithFields(logrus.Fields{
		"request_id":   req.RequestId,
		"process_time": resp.ProcessTime,
		"detections":   len(resp.Detections),
	}).Info("Inference completed")

	return resp, nil
}

// BatchInference 批量推理
func (s *Server) BatchInference(ctx context.Context, req *inference.BatchInferenceRequest) (*inference.BatchInferenceResponse, error) {
	s.logger.WithField("batch_size", len(req.Requests)).Info("Executing batch inference")

	responses := make([]*inference.InferenceResponse, len(req.Requests))
	for i, inferenceReq := range req.Requests {
		resp, err := s.ExecuteInference(ctx, inferenceReq)
		if err != nil {
			resp = &inference.InferenceResponse{
				RequestId:    inferenceReq.RequestId,
				Success:      false,
				ErrorMessage: err.Error(),
			}
		}
		responses[i] = resp
	}

	return &inference.BatchInferenceResponse{
		Responses: responses,
	}, nil
}

// GetModelStatus 获取模型状态
func (s *Server) GetModelStatus(ctx context.Context, req *inference.ModelStatusRequest) (*inference.ModelStatusResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"model_name":    req.ModelName,
		"model_version": req.ModelVersion,
	}).Info("Getting model status")

	// 查询模型信息
	model, err := s.modelService.GetByNameAndVersion(req.ModelName, req.ModelVersion)
	if err != nil {
		return &inference.ModelStatusResponse{
			ModelName:    req.ModelName,
			ModelVersion: req.ModelVersion,
			State:        inference.ModelState_MODEL_ERROR,
			ErrorMessage: err.Error(),
		}, nil
	}

	// 根据模型状态返回相应信息
	var state inference.ModelState
	switch model.Status {
	case "active":
		state = inference.ModelState_MODEL_READY
	case "inactive":
		state = inference.ModelState_MODEL_UNKNOWN
	default:
		state = inference.ModelState_MODEL_ERROR
	}

	return &inference.ModelStatusResponse{
		ModelName:    model.Name,
		ModelVersion: model.Version,
		State:        state,
		LoadTime:     model.CreatedAt.Unix(),
		LastUsed:     model.UpdatedAt.Unix(),
		Metrics: &inference.ModelMetrics{
			TotalRequests:      100, // 模拟数据
			SuccessfulRequests: 95,
			FailedRequests:     5,
			AverageLatency:     0.1,
			MemoryUsage:        512.0,
			GpuUsage:           75.0,
		},
	}, nil
}

// LoadModel 加载模型
func (s *Server) LoadModel(ctx context.Context, req *inference.LoadModelRequest) (*inference.LoadModelResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"model_name":    req.ModelName,
		"model_version": req.ModelVersion,
		"model_path":    req.ModelPath,
	}).Info("Loading model")

	startTime := time.Now()

	// 这里应该实现实际的模型加载逻辑
	// 目前返回模拟响应
	time.Sleep(100 * time.Millisecond) // 模拟加载时间

	loadTime := time.Since(startTime).Milliseconds()

	return &inference.LoadModelResponse{
		Success:  true,
		LoadTime: loadTime,
	}, nil
}

// UnloadModel 卸载模型
func (s *Server) UnloadModel(ctx context.Context, req *inference.UnloadModelRequest) (*inference.UnloadModelResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"model_name":    req.ModelName,
		"model_version": req.ModelVersion,
	}).Info("Unloading model")

	// 这里应该实现实际的模型卸载逻辑
	// 目前返回模拟响应
	return &inference.UnloadModelResponse{
		Success: true,
	}, nil
}

// HealthCheck 健康检查
func (s *Server) HealthCheck(ctx context.Context, req *inference.HealthCheckRequest) (*inference.HealthCheckResponse, error) {
	return &inference.HealthCheckResponse{
		Status:  inference.HealthStatus_HEALTH_SERVING,
		Message: "Service is healthy",
		Details: map[string]string{
			"timestamp": time.Now().Format(time.RFC3339),
			"version":   "1.0.0",
			"uptime":    time.Since(time.Now()).String(),
		},
	}, nil
}