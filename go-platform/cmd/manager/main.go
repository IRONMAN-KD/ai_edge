package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/config"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/database"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/services"
	"ai-edge/ai-edge/ai-edge/go-platform/pkg/grpc/server"

	"github.com/sirupsen/logrus"
	"google.golang.org/grpc"
)

func main() {
	// 加载配置
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// 初始化日志
	logrus.SetLevel(logrus.InfoLevel)
	logrus.SetFormatter(&logrus.JSONFormatter{})

	// 初始化数据库
	db, err := database.Initialize(cfg.Database)
	if err != nil {
		logrus.Fatalf("Failed to initialize database: %v", err)
	}

	// 初始化服务
	services := services.NewServices(db, cfg)

	// 创建gRPC服务器
	grpcServer := grpc.NewServer()
	server.RegisterServices(grpcServer, services)

	// 监听端口
	lis, err := net.Listen("tcp", cfg.GRPC.Address)
	if err != nil {
		logrus.Fatalf("Failed to listen: %v", err)
	}

	// 启动gRPC服务器
	go func() {
		logrus.Infof("Starting gRPC server on %s", cfg.GRPC.Address)
		if err := grpcServer.Serve(lis); err != nil {
			logrus.Fatalf("Failed to serve gRPC: %v", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logrus.Info("Shutting down gRPC server...")

	// 优雅关闭
	grpcServer.GracefulStop()
	logrus.Info("gRPC server exiting")
}