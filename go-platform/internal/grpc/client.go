package grpc

import (
	"context"
	"fmt"
	"time"

	"ai-edge/ai-edge/ai-edge/go-platform/api/proto/inference"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"
)

// InferenceClient gRPC推理客户端
type InferenceClient struct {
	conn   *grpc.ClientConn
	client inference.InferenceServiceClient
	addr   string
}

// NewInferenceClient 创建推理客户端
func NewInferenceClient(addr string) (*InferenceClient, error) {
	// 配置连接参数
	kacp := keepalive.ClientParameters{
		Time:                10 * time.Second, // 发送keepalive ping的间隔
		Timeout:             time.Second,      // 等待keepalive ping响应的超时时间
		PermitWithoutStream: true,             // 允许在没有活动流时发送keepalive ping
	}

	// 建立连接
	conn, err := grpc.Dial(addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithKeepaliveParams(kacp),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(1024*1024*10), // 10MB
			grpc.MaxCallSendMsgSize(1024*1024*10), // 10MB
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to inference service: %w", err)
	}

	client := inference.NewInferenceServiceClient(conn)

	return &InferenceClient{
		conn:   conn,
		client: client,
		addr:   addr,
	}, nil
}

// Close 关闭连接
func (c *InferenceClient) Close() error {
	return c.conn.Close()
}

// ExecuteInference 执行推理
func (c *InferenceClient) ExecuteInference(ctx context.Context, req *inference.InferenceRequest) (*inference.InferenceResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	resp, err := c.client.ExecuteInference(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("inference execution failed: %w", err)
	}

	return resp, nil
}

// BatchInference 批量推理
func (c *InferenceClient) BatchInference(ctx context.Context, req *inference.BatchInferenceRequest) (*inference.BatchInferenceResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 60*time.Second)
	defer cancel()

	resp, err := c.client.BatchInference(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("batch inference failed: %w", err)
	}

	return resp, nil
}

// GetModelStatus 获取模型状态
func (c *InferenceClient) GetModelStatus(ctx context.Context, req *inference.ModelStatusRequest) (*inference.ModelStatusResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	resp, err := c.client.GetModelStatus(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("get model status failed: %w", err)
	}

	return resp, nil
}

// LoadModel 加载模型
func (c *InferenceClient) LoadModel(ctx context.Context, req *inference.LoadModelRequest) (*inference.LoadModelResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 120*time.Second) // 加载模型可能需要更长时间
	defer cancel()

	resp, err := c.client.LoadModel(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("load model failed: %w", err)
	}

	return resp, nil
}

// UnloadModel 卸载模型
func (c *InferenceClient) UnloadModel(ctx context.Context, req *inference.UnloadModelRequest) (*inference.UnloadModelResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	resp, err := c.client.UnloadModel(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("unload model failed: %w", err)
	}

	return resp, nil
}

// HealthCheck 健康检查
func (c *InferenceClient) HealthCheck(ctx context.Context, req *inference.HealthCheckRequest) (*inference.HealthCheckResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	resp, err := c.client.HealthCheck(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("health check failed: %w", err)
	}

	return resp, nil
}

// IsHealthy 检查服务是否健康
func (c *InferenceClient) IsHealthy(ctx context.Context) bool {
	req := &inference.HealthCheckRequest{
		Service: "inference",
	}

	resp, err := c.HealthCheck(ctx, req)
	if err != nil {
		return false
	}

	return resp.Status == inference.HealthStatus_HEALTH_SERVING
}

// InferenceClientPool gRPC客户端池
type InferenceClientPool struct {
	clients []*InferenceClient
	index   int
	addr    string
}

// NewInferenceClientPool 创建客户端池
func NewInferenceClientPool(addr string, poolSize int) (*InferenceClientPool, error) {
	if poolSize <= 0 {
		poolSize = 5 // 默认池大小
	}

	clients := make([]*InferenceClient, poolSize)
	for i := 0; i < poolSize; i++ {
		client, err := NewInferenceClient(addr)
		if err != nil {
			// 清理已创建的客户端
			for j := 0; j < i; j++ {
				clients[j].Close()
			}
			return nil, fmt.Errorf("failed to create client %d: %w", i, err)
		}
		clients[i] = client
	}

	return &InferenceClientPool{
		clients: clients,
		index:   0,
		addr:    addr,
	}, nil
}

// GetClient 获取一个客户端（轮询方式）
func (p *InferenceClientPool) GetClient() *InferenceClient {
	client := p.clients[p.index]
	p.index = (p.index + 1) % len(p.clients)
	return client
}

// Close 关闭所有客户端
func (p *InferenceClientPool) Close() error {
	for _, client := range p.clients {
		if err := client.Close(); err != nil {
			return err
		}
	}
	return nil
}

// Size 返回池大小
func (p *InferenceClientPool) Size() int {
	return len(p.clients)
}