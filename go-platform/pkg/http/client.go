package http

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"

	"go.uber.org/zap"

	"ai-edge/pkg/logger"
)

// Client HTTP客户端
type Client struct {
	client *http.Client
	config Config
	logger *zap.Logger
}

// Config HTTP客户端配置
type Config struct {
	Timeout         time.Duration     `yaml:"timeout" json:"timeout"`
	MaxIdleConns    int               `yaml:"max_idle_conns" json:"max_idle_conns"`
	MaxConnsPerHost int               `yaml:"max_conns_per_host" json:"max_conns_per_host"`
	IdleConnTimeout time.Duration     `yaml:"idle_conn_timeout" json:"idle_conn_timeout"`
	TLSTimeout      time.Duration     `yaml:"tls_timeout" json:"tls_timeout"`
	KeepAlive       time.Duration     `yaml:"keep_alive" json:"keep_alive"`
	InsecureSkipTLS bool              `yaml:"insecure_skip_tls" json:"insecure_skip_tls"`
	UserAgent       string            `yaml:"user_agent" json:"user_agent"`
	Headers         map[string]string `yaml:"headers" json:"headers"`
	Retry           RetryConfig       `yaml:"retry" json:"retry"`
	Proxy           ProxyConfig       `yaml:"proxy" json:"proxy"`
	Auth            AuthConfig        `yaml:"auth" json:"auth"`
	Logging         LoggingConfig     `yaml:"logging" json:"logging"`
}

// RetryConfig 重试配置
type RetryConfig struct {
	Enabled     bool          `yaml:"enabled" json:"enabled"`
	MaxRetries  int           `yaml:"max_retries" json:"max_retries"`
	InitialWait time.Duration `yaml:"initial_wait" json:"initial_wait"`
	MaxWait     time.Duration `yaml:"max_wait" json:"max_wait"`
	Multiplier  float64       `yaml:"multiplier" json:"multiplier"`
	StatusCodes []int         `yaml:"status_codes" json:"status_codes"`
}

// ProxyConfig 代理配置
type ProxyConfig struct {
	Enabled  bool   `yaml:"enabled" json:"enabled"`
	URL      string `yaml:"url" json:"url"`
	Username string `yaml:"username" json:"username"`
	Password string `yaml:"password" json:"password"`
}

// AuthConfig 认证配置
type AuthConfig struct {
	Type     string `yaml:"type" json:"type"` // basic, bearer, api_key
	Username string `yaml:"username" json:"username"`
	Password string `yaml:"password" json:"password"`
	Token    string `yaml:"token" json:"token"`
	APIKey   string `yaml:"api_key" json:"api_key"`
	Header   string `yaml:"header" json:"header"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Enabled       bool `yaml:"enabled" json:"enabled"`
	LogRequest    bool `yaml:"log_request" json:"log_request"`
	LogResponse   bool `yaml:"log_response" json:"log_response"`
	LogBody       bool `yaml:"log_body" json:"log_body"`
	MaxBodySize   int  `yaml:"max_body_size" json:"max_body_size"`
	SensitiveKeys []string `yaml:"sensitive_keys" json:"sensitive_keys"`
}

// Request HTTP请求
type Request struct {
	Method  string
	URL     string
	Headers map[string]string
	Body    interface{}
	Query   map[string]string
	Timeout time.Duration
	Retry   *RetryConfig
	Auth    *AuthConfig
}

// Response HTTP响应
type Response struct {
	StatusCode int
	Headers    http.Header
	Body       []byte
	Duration   time.Duration
	Request    *http.Request
}

// DefaultConfig 默认配置
func DefaultConfig() Config {
	return Config{
		Timeout:         30 * time.Second,
		MaxIdleConns:    100,
		MaxConnsPerHost: 10,
		IdleConnTimeout: 90 * time.Second,
		TLSTimeout:      10 * time.Second,
		KeepAlive:       30 * time.Second,
		InsecureSkipTLS: false,
		UserAgent:       "AI-Edge-Platform/1.0",
		Headers:         make(map[string]string),
		Retry: RetryConfig{
			Enabled:     true,
			MaxRetries:  3,
			InitialWait: 1 * time.Second,
			MaxWait:     30 * time.Second,
			Multiplier:  2.0,
			StatusCodes: []int{500, 502, 503, 504, 429},
		},
		Proxy: ProxyConfig{
			Enabled: false,
		},
		Auth: AuthConfig{
			Type: "none",
		},
		Logging: LoggingConfig{
			Enabled:       true,
			LogRequest:    true,
			LogResponse:   true,
			LogBody:       false,
			MaxBodySize:   1024,
			SensitiveKeys: []string{"password", "token", "api_key", "secret"},
		},
	}
}

// NewClient 创建HTTP客户端
func NewClient(cfg Config) *Client {
	// 创建传输层
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   cfg.TLSTimeout,
			KeepAlive: cfg.KeepAlive,
		}).DialContext,
		MaxIdleConns:        cfg.MaxIdleConns,
		MaxIdleConnsPerHost: cfg.MaxConnsPerHost,
		IdleConnTimeout:     cfg.IdleConnTimeout,
		TLSHandshakeTimeout: cfg.TLSTimeout,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: cfg.InsecureSkipTLS,
		},
	}

	// 配置代理
	if cfg.Proxy.Enabled && cfg.Proxy.URL != "" {
		proxyURL, err := url.Parse(cfg.Proxy.URL)
		if err == nil {
			if cfg.Proxy.Username != "" && cfg.Proxy.Password != "" {
				proxyURL.User = url.UserPassword(cfg.Proxy.Username, cfg.Proxy.Password)
			}
			transport.Proxy = http.ProxyURL(proxyURL)
		}
	}

	// 创建HTTP客户端
	httpClient := &http.Client{
		Transport: transport,
		Timeout:   cfg.Timeout,
	}

	return &Client{
		client: httpClient,
		config: cfg,
		logger: logger.GetLogger(),
	}
}

// Get 发送GET请求
func (c *Client) Get(ctx context.Context, url string, options ...RequestOption) (*Response, error) {
	req := &Request{
		Method: "GET",
		URL:    url,
	}

	for _, option := range options {
		option(req)
	}

	return c.Do(ctx, req)
}

// Post 发送POST请求
func (c *Client) Post(ctx context.Context, url string, body interface{}, options ...RequestOption) (*Response, error) {
	req := &Request{
		Method: "POST",
		URL:    url,
		Body:   body,
	}

	for _, option := range options {
		option(req)
	}

	return c.Do(ctx, req)
}

// Put 发送PUT请求
func (c *Client) Put(ctx context.Context, url string, body interface{}, options ...RequestOption) (*Response, error) {
	req := &Request{
		Method: "PUT",
		URL:    url,
		Body:   body,
	}

	for _, option := range options {
		option(req)
	}

	return c.Do(ctx, req)
}

// Patch 发送PATCH请求
func (c *Client) Patch(ctx context.Context, url string, body interface{}, options ...RequestOption) (*Response, error) {
	req := &Request{
		Method: "PATCH",
		URL:    url,
		Body:   body,
	}

	for _, option := range options {
		option(req)
	}

	return c.Do(ctx, req)
}

// Delete 发送DELETE请求
func (c *Client) Delete(ctx context.Context, url string, options ...RequestOption) (*Response, error) {
	req := &Request{
		Method: "DELETE",
		URL:    url,
	}

	for _, option := range options {
		option(req)
	}

	return c.Do(ctx, req)
}

// Do 执行HTTP请求
func (c *Client) Do(ctx context.Context, req *Request) (*Response, error) {
	start := time.Now()

	// 构建HTTP请求
	httpReq, err := c.buildRequest(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to build request: %v", err)
	}

	// 记录请求日志
	if c.config.Logging.Enabled && c.config.Logging.LogRequest {
		c.logRequest(httpReq, req)
	}

	// 执行请求（带重试）
	var resp *http.Response
	if req.Retry != nil && req.Retry.Enabled {
		resp, err = c.doWithRetry(httpReq, req.Retry)
	} else if c.config.Retry.Enabled {
		resp, err = c.doWithRetry(httpReq, &c.config.Retry)
	} else {
		resp, err = c.client.Do(httpReq)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %v", err)
	}
	defer resp.Body.Close()

	// 读取响应体
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %v", err)
	}

	duration := time.Since(start)
	response := &Response{
		StatusCode: resp.StatusCode,
		Headers:    resp.Header,
		Body:       body,
		Duration:   duration,
		Request:    httpReq,
	}

	// 记录响应日志
	if c.config.Logging.Enabled && c.config.Logging.LogResponse {
		c.logResponse(response)
	}

	return response, nil
}

// buildRequest 构建HTTP请求
func (c *Client) buildRequest(ctx context.Context, req *Request) (*http.Request, error) {
	// 构建URL
	reqURL := req.URL
	if len(req.Query) > 0 {
		u, err := url.Parse(reqURL)
		if err != nil {
			return nil, fmt.Errorf("invalid URL: %v", err)
		}

		q := u.Query()
		for key, value := range req.Query {
			q.Set(key, value)
		}
		u.RawQuery = q.Encode()
		reqURL = u.String()
	}

	// 构建请求体
	var body io.Reader
	if req.Body != nil {
		switch v := req.Body.(type) {
		case string:
			body = strings.NewReader(v)
		case []byte:
			body = bytes.NewReader(v)
		case io.Reader:
			body = v
		default:
			data, err := json.Marshal(req.Body)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal request body: %v", err)
			}
			body = bytes.NewReader(data)
		}
	}

	// 创建HTTP请求
	httpReq, err := http.NewRequestWithContext(ctx, req.Method, reqURL, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	// 设置默认头部
	httpReq.Header.Set("User-Agent", c.config.UserAgent)
	if req.Body != nil && httpReq.Header.Get("Content-Type") == "" {
		httpReq.Header.Set("Content-Type", "application/json")
	}

	// 设置全局头部
	for key, value := range c.config.Headers {
		httpReq.Header.Set(key, value)
	}

	// 设置请求头部
	if req.Headers != nil {
		for key, value := range req.Headers {
			httpReq.Header.Set(key, value)
		}
	}

	// 设置认证
	auth := req.Auth
	if auth == nil {
		auth = &c.config.Auth
	}
	c.setAuth(httpReq, auth)

	// 设置超时
	if req.Timeout > 0 {
		ctx, cancel := context.WithTimeout(ctx, req.Timeout)
		_ = cancel // 避免内存泄漏
		httpReq = httpReq.WithContext(ctx)
	}

	return httpReq, nil
}

// setAuth 设置认证
func (c *Client) setAuth(req *http.Request, auth *AuthConfig) {
	if auth == nil || auth.Type == "none" {
		return
	}

	switch auth.Type {
	case "basic":
		req.SetBasicAuth(auth.Username, auth.Password)
	case "bearer":
		req.Header.Set("Authorization", "Bearer "+auth.Token)
	case "api_key":
		header := auth.Header
		if header == "" {
			header = "X-API-Key"
		}
		req.Header.Set(header, auth.APIKey)
	}
}

// doWithRetry 带重试的请求执行
func (c *Client) doWithRetry(req *http.Request, retryConfig *RetryConfig) (*http.Response, error) {
	var lastErr error
	wait := retryConfig.InitialWait

	for attempt := 0; attempt <= retryConfig.MaxRetries; attempt++ {
		// 克隆请求（因为Body可能被消费）
		reqClone := req.Clone(req.Context())
		if req.Body != nil {
			// 重新设置Body
			if req.GetBody != nil {
				body, err := req.GetBody()
				if err != nil {
					return nil, fmt.Errorf("failed to get request body: %v", err)
				}
				reqClone.Body = body
			}
		}

		// 执行请求
		resp, err := c.client.Do(reqClone)
		if err != nil {
			lastErr = err
			if attempt < retryConfig.MaxRetries {
				c.logger.Warn("Request failed, retrying",
					zap.Int("attempt", attempt+1),
					zap.Duration("wait", wait),
					zap.Error(err),
				)
				time.Sleep(wait)
				wait = time.Duration(float64(wait) * retryConfig.Multiplier)
				if wait > retryConfig.MaxWait {
					wait = retryConfig.MaxWait
				}
				continue
			}
			return nil, lastErr
		}

		// 检查状态码是否需要重试
		if c.shouldRetry(resp.StatusCode, retryConfig.StatusCodes) {
			resp.Body.Close()
			lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
			if attempt < retryConfig.MaxRetries {
				c.logger.Warn("Request returned retryable status code, retrying",
					zap.Int("attempt", attempt+1),
					zap.Int("status_code", resp.StatusCode),
					zap.Duration("wait", wait),
				)
				time.Sleep(wait)
				wait = time.Duration(float64(wait) * retryConfig.Multiplier)
				if wait > retryConfig.MaxWait {
					wait = retryConfig.MaxWait
				}
				continue
			}
			return resp, nil
		}

		return resp, nil
	}

	return nil, lastErr
}

// shouldRetry 检查是否应该重试
func (c *Client) shouldRetry(statusCode int, retryCodes []int) bool {
	for _, code := range retryCodes {
		if statusCode == code {
			return true
		}
	}
	return false
}

// logRequest 记录请求日志
func (c *Client) logRequest(req *http.Request, originalReq *Request) {
	fields := []zap.Field{
		zap.String("method", req.Method),
		zap.String("url", req.URL.String()),
		zap.Any("headers", c.sanitizeHeaders(req.Header)),
	}

	if c.config.Logging.LogBody && originalReq.Body != nil {
		body := c.sanitizeBody(originalReq.Body)
		if len(body) <= c.config.Logging.MaxBodySize {
			fields = append(fields, zap.String("body", body))
		} else {
			fields = append(fields, zap.String("body", body[:c.config.Logging.MaxBodySize]+"..."))
		}
	}

	c.logger.Info("HTTP Request", fields...)
}

// logResponse 记录响应日志
func (c *Client) logResponse(resp *Response) {
	fields := []zap.Field{
		zap.Int("status_code", resp.StatusCode),
		zap.Duration("duration", resp.Duration),
		zap.Any("headers", c.sanitizeHeaders(resp.Headers)),
	}

	if c.config.Logging.LogBody && len(resp.Body) > 0 {
		body := string(resp.Body)
		if len(body) <= c.config.Logging.MaxBodySize {
			fields = append(fields, zap.String("body", body))
		} else {
			fields = append(fields, zap.String("body", body[:c.config.Logging.MaxBodySize]+"..."))
		}
	}

	if resp.StatusCode >= 400 {
		c.logger.Error("HTTP Response", fields...)
	} else {
		c.logger.Info("HTTP Response", fields...)
	}
}

// sanitizeHeaders 清理敏感头部信息
func (c *Client) sanitizeHeaders(headers http.Header) map[string]string {
	result := make(map[string]string)
	for key, values := range headers {
		value := strings.Join(values, ", ")
		if c.isSensitiveKey(key) {
			value = "***"
		}
		result[key] = value
	}
	return result
}

// sanitizeBody 清理敏感请求体信息
func (c *Client) sanitizeBody(body interface{}) string {
	switch v := body.(type) {
	case string:
		return c.sanitizeString(v)
	case []byte:
		return c.sanitizeString(string(v))
	default:
		data, err := json.Marshal(body)
		if err != nil {
			return fmt.Sprintf("failed to marshal body: %v", err)
		}
		return c.sanitizeString(string(data))
	}
}

// sanitizeString 清理敏感字符串信息
func (c *Client) sanitizeString(str string) string {
	for _, key := range c.config.Logging.SensitiveKeys {
		if strings.Contains(strings.ToLower(str), strings.ToLower(key)) {
			return "*** (contains sensitive data) ***"
		}
	}
	return str
}

// isSensitiveKey 检查是否为敏感键
func (c *Client) isSensitiveKey(key string) bool {
	key = strings.ToLower(key)
	for _, sensitiveKey := range c.config.Logging.SensitiveKeys {
		if strings.Contains(key, strings.ToLower(sensitiveKey)) {
			return true
		}
	}
	return false
}

// JSON 解析JSON响应
func (r *Response) JSON(dest interface{}) error {
	return json.Unmarshal(r.Body, dest)
}

// String 获取字符串响应
func (r *Response) String() string {
	return string(r.Body)
}

// IsSuccess 检查是否成功
func (r *Response) IsSuccess() bool {
	return r.StatusCode >= 200 && r.StatusCode < 300
}

// IsClientError 检查是否客户端错误
func (r *Response) IsClientError() bool {
	return r.StatusCode >= 400 && r.StatusCode < 500
}

// IsServerError 检查是否服务器错误
func (r *Response) IsServerError() bool {
	return r.StatusCode >= 500
}

// RequestOption 请求选项
type RequestOption func(*Request)

// WithHeaders 设置请求头
func WithHeaders(headers map[string]string) RequestOption {
	return func(req *Request) {
		if req.Headers == nil {
			req.Headers = make(map[string]string)
		}
		for key, value := range headers {
			req.Headers[key] = value
		}
	}
}

// WithHeader 设置单个请求头
func WithHeader(key, value string) RequestOption {
	return func(req *Request) {
		if req.Headers == nil {
			req.Headers = make(map[string]string)
		}
		req.Headers[key] = value
	}
}

// WithQuery 设置查询参数
func WithQuery(query map[string]string) RequestOption {
	return func(req *Request) {
		if req.Query == nil {
			req.Query = make(map[string]string)
		}
		for key, value := range query {
			req.Query[key] = value
		}
	}
}

// WithQueryParam 设置单个查询参数
func WithQueryParam(key, value string) RequestOption {
	return func(req *Request) {
		if req.Query == nil {
			req.Query = make(map[string]string)
		}
		req.Query[key] = value
	}
}

// WithTimeout 设置请求超时
func WithTimeout(timeout time.Duration) RequestOption {
	return func(req *Request) {
		req.Timeout = timeout
	}
}

// WithRetry 设置重试配置
func WithRetry(retry RetryConfig) RequestOption {
	return func(req *Request) {
		req.Retry = &retry
	}
}

// WithAuth 设置认证
func WithAuth(auth AuthConfig) RequestOption {
	return func(req *Request) {
		req.Auth = &auth
	}
}

// WithBasicAuth 设置基础认证
func WithBasicAuth(username, password string) RequestOption {
	return func(req *Request) {
		req.Auth = &AuthConfig{
			Type:     "basic",
			Username: username,
			Password: password,
		}
	}
}

// WithBearerToken 设置Bearer令牌
func WithBearerToken(token string) RequestOption {
	return func(req *Request) {
		req.Auth = &AuthConfig{
			Type:  "bearer",
			Token: token,
		}
	}
}

// WithAPIKey 设置API密钥
func WithAPIKey(apiKey, header string) RequestOption {
	return func(req *Request) {
		req.Auth = &AuthConfig{
			Type:   "api_key",
			APIKey: apiKey,
			Header: header,
		}
	}
}

// WithContentType 设置内容类型
func WithContentType(contentType string) RequestOption {
	return WithHeader("Content-Type", contentType)
}

// WithUserAgent 设置用户代理
func WithUserAgent(userAgent string) RequestOption {
	return WithHeader("User-Agent", userAgent)
}

// WithJSON 设置JSON内容类型
func WithJSON() RequestOption {
	return WithContentType("application/json")
}

// WithForm 设置表单内容类型
func WithForm() RequestOption {
	return WithContentType("application/x-www-form-urlencoded")
}

// WithXML 设置XML内容类型
func WithXML() RequestOption {
	return WithContentType("application/xml")
}