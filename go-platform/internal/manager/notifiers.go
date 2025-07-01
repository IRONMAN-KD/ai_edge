package manager

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/smtp"
	"strconv"
	"strings"
	"time"

	"ai-edge-platform/internal/models"
)

// EmailNotifier 邮件通知器
type EmailNotifier struct {
	config *EmailConfig
}

// NewEmailNotifier 创建邮件通知器
func NewEmailNotifier(config *EmailConfig) *EmailNotifier {
	return &EmailNotifier{
		config: config,
	}
}

// Notify 发送邮件通知
func (en *EmailNotifier) Notify(ctx context.Context, alert *models.Alert) error {
	// 构建邮件内容
	subject := en.buildSubject(alert)
	body := en.buildBody(alert)

	// 构建邮件消息
	msg := en.buildMessage(subject, body)

	// 发送邮件
	auth := smtp.PlainAuth("", en.config.Username, en.config.Password, en.config.SMTPHost)
	addr := fmt.Sprintf("%s:%d", en.config.SMTPHost, en.config.SMTPPort)

	err := smtp.SendMail(addr, auth, en.config.From, en.config.To, []byte(msg))
	if err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}

// GetType 获取通知器类型
func (en *EmailNotifier) GetType() string {
	return "email"
}

// buildSubject 构建邮件主题
func (en *EmailNotifier) buildSubject(alert *models.Alert) string {
	if en.config.Subject != "" {
		return fmt.Sprintf(en.config.Subject, alert.Level, alert.Type)
	}
	return fmt.Sprintf("[%s] Alert: %s", strings.ToUpper(alert.Level), alert.Type)
}

// buildBody 构建邮件正文
func (en *EmailNotifier) buildBody(alert *models.Alert) string {
	if en.config.Template != "" {
		// 使用模板（这里简化处理）
		return fmt.Sprintf(en.config.Template, alert.Type, alert.Level, alert.Message, alert.Source, alert.CreatedAt.Format(time.RFC3339))
	}

	// 默认模板
	return fmt.Sprintf(`
Alert Details:

Type: %s
Level: %s
Message: %s
Source: %s
Time: %s

Please check the system for more details.
`,
		alert.Type,
		alert.Level,
		alert.Message,
		alert.Source,
		alert.CreatedAt.Format(time.RFC3339),
	)
}

// buildMessage 构建邮件消息
func (en *EmailNotifier) buildMessage(subject, body string) string {
	msg := fmt.Sprintf("From: %s\r\n", en.config.From)
	msg += fmt.Sprintf("To: %s\r\n", strings.Join(en.config.To, ","))
	msg += fmt.Sprintf("Subject: %s\r\n", subject)
	msg += "Content-Type: text/plain; charset=UTF-8\r\n"
	msg += "\r\n"
	msg += body
	return msg
}

// WebhookNotifier Webhook 通知器
type WebhookNotifier struct {
	config *WebhookConfig
	client *http.Client
}

// NewWebhookNotifier 创建 Webhook 通知器
func NewWebhookNotifier(config *WebhookConfig) *WebhookNotifier {
	return &WebhookNotifier{
		config: config,
		client: &http.Client{
			Timeout: config.Timeout,
		},
	}
}

// Notify 发送 Webhook 通知
func (wn *WebhookNotifier) Notify(ctx context.Context, alert *models.Alert) error {
	// 构建请求数据
	payload := map[string]interface{}{
		"alert_id":   alert.ID,
		"type":       alert.Type,
		"level":      alert.Level,
		"message":    alert.Message,
		"source":     alert.Source,
		"status":     alert.Status,
		"created_at": alert.CreatedAt.Format(time.RFC3339),
		"timestamp":  time.Now().Unix(),
	}

	// 序列化为 JSON
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal webhook payload: %w", err)
	}

	// 创建请求
	req, err := http.NewRequestWithContext(ctx, wn.config.Method, wn.config.URL, bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("failed to create webhook request: %w", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")
	for key, value := range wn.config.Headers {
		req.Header.Set(key, value)
	}

	// 发送请求
	resp, err := wn.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send webhook request: %w", err)
	}
	defer resp.Body.Close()

	// 检查响应状态
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("webhook request failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

// GetType 获取通知器类型
func (wn *WebhookNotifier) GetType() string {
	return "webhook"
}

// SlackNotifier Slack 通知器
type SlackNotifier struct {
	config *SlackConfig
	client *http.Client
}

// NewSlackNotifier 创建 Slack 通知器
func NewSlackNotifier(config *SlackConfig) *SlackNotifier {
	return &SlackNotifier{
		config: config,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Notify 发送 Slack 通知
func (sn *SlackNotifier) Notify(ctx context.Context, alert *models.Alert) error {
	// 构建 Slack 消息
	payload := map[string]interface{}{
		"channel":   sn.config.Channel,
		"username":  sn.config.Username,
		"icon_emoji": sn.config.IconEmoji,
		"text":      sn.buildSlackMessage(alert),
		"attachments": []map[string]interface{}{
			{
				"color":     sn.getAlertColor(alert.Level),
				"title":     fmt.Sprintf("Alert: %s", alert.Type),
				"text":      alert.Message,
				"timestamp": alert.CreatedAt.Unix(),
				"fields": []map[string]interface{}{
					{
						"title": "Level",
						"value": alert.Level,
						"short": true,
					},
					{
						"title": "Source",
						"value": alert.Source,
						"short": true,
					},
					{
						"title": "Time",
						"value": alert.CreatedAt.Format(time.RFC3339),
						"short": true,
					},
				},
			},
		},
	}

	// 序列化为 JSON
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal slack payload: %w", err)
	}

	// 发送请求
	resp, err := sn.client.Post(sn.config.WebhookURL, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("failed to send slack notification: %w", err)
	}
	defer resp.Body.Close()

	// 检查响应状态
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("slack notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

// GetType 获取通知器类型
func (sn *SlackNotifier) GetType() string {
	return "slack"
}

// buildSlackMessage 构建 Slack 消息
func (sn *SlackNotifier) buildSlackMessage(alert *models.Alert) string {
	return fmt.Sprintf(":warning: *%s Alert*: %s", strings.ToUpper(alert.Level), alert.Type)
}

// getAlertColor 获取告警颜色
func (sn *SlackNotifier) getAlertColor(level string) string {
	switch strings.ToLower(level) {
	case "critical":
		return "danger"
	case "warning":
		return "warning"
	case "info":
		return "good"
	default:
		return "#439FE0"
	}
}

// DingTalkNotifier 钉钉通知器
type DingTalkNotifier struct {
	config *DingTalkConfig
	client *http.Client
}

// NewDingTalkNotifier 创建钉钉通知器
func NewDingTalkNotifier(config *DingTalkConfig) *DingTalkNotifier {
	return &DingTalkNotifier{
		config: config,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Notify 发送钉钉通知
func (dn *DingTalkNotifier) Notify(ctx context.Context, alert *models.Alert) error {
	// 构建钉钉消息
	payload := map[string]interface{}{
		"msgtype": "markdown",
		"markdown": map[string]interface{}{
			"title": fmt.Sprintf("Alert: %s", alert.Type),
			"text":  dn.buildDingTalkMessage(alert),
		},
	}

	// 添加 @ 信息
	if len(dn.config.AtMobiles) > 0 || dn.config.AtAll {
		at := map[string]interface{}{
			"atMobiles": dn.config.AtMobiles,
			"isAtAll":   dn.config.AtAll,
		}
		payload["at"] = at
	}

	// 序列化为 JSON
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal dingtalk payload: %w", err)
	}

	// 构建请求 URL（包含签名）
	url := dn.buildRequestURL()

	// 发送请求
	resp, err := dn.client.Post(url, "application/json", bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("failed to send dingtalk notification: %w", err)
	}
	defer resp.Body.Close()

	// 检查响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read dingtalk response: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return fmt.Errorf("failed to parse dingtalk response: %w", err)
	}

	// 检查返回码
	if errCode, ok := result["errcode"]; ok {
		if code, ok := errCode.(float64); ok && code != 0 {
			return fmt.Errorf("dingtalk notification failed with code %.0f: %v", code, result["errmsg"])
		}
	}

	return nil
}

// GetType 获取通知器类型
func (dn *DingTalkNotifier) GetType() string {
	return "dingtalk"
}

// buildDingTalkMessage 构建钉钉消息
func (dn *DingTalkNotifier) buildDingTalkMessage(alert *models.Alert) string {
	levelEmoji := dn.getLevelEmoji(alert.Level)

	return fmt.Sprintf(`## %s %s Alert

**Type:** %s

**Level:** %s

**Message:** %s

**Source:** %s

**Time:** %s

---

> Please check the system for more details.`,
		levelEmoji,
		strings.ToUpper(alert.Level),
		alert.Type,
		alert.Level,
		alert.Message,
		alert.Source,
		alert.CreatedAt.Format("2006-01-02 15:04:05"),
	)
}

// getLevelEmoji 获取级别对应的表情
func (dn *DingTalkNotifier) getLevelEmoji(level string) string {
	switch strings.ToLower(level) {
	case "critical":
		return "🚨"
	case "warning":
		return "⚠️"
	case "info":
		return "ℹ️"
	default:
		return "📢"
	}
}

// buildRequestURL 构建请求 URL（包含签名）
func (dn *DingTalkNotifier) buildRequestURL() string {
	if dn.config.Secret == "" {
		return dn.config.WebhookURL
	}

	// 生成时间戳
	timestamp := time.Now().UnixNano() / 1e6

	// 生成签名
	signature := dn.generateSignature(timestamp)

	// 构建完整 URL
	return fmt.Sprintf("%s&timestamp=%d&sign=%s", dn.config.WebhookURL, timestamp, signature)
}

// generateSignature 生成钉钉签名
func (dn *DingTalkNotifier) generateSignature(timestamp int64) string {
	// 构建待签名字符串
	stringToSign := fmt.Sprintf("%d\n%s", timestamp, dn.config.Secret)

	// 使用 HmacSHA256 算法计算签名
	h := hmac.New(sha256.New, []byte(dn.config.Secret))
	h.Write([]byte(stringToSign))
	signature := base64.StdEncoding.EncodeToString(h.Sum(nil))

	return signature
}

// ConsoleNotifier 控制台通知器（用于测试）
type ConsoleNotifier struct{}

// NewConsoleNotifier 创建控制台通知器
func NewConsoleNotifier() *ConsoleNotifier {
	return &ConsoleNotifier{}
}

// Notify 发送控制台通知
func (cn *ConsoleNotifier) Notify(ctx context.Context, alert *models.Alert) error {
	fmt.Printf("[ALERT] %s | %s | %s | %s | %s\n",
		alert.CreatedAt.Format("2006-01-02 15:04:05"),
		strings.ToUpper(alert.Level),
		alert.Type,
		alert.Source,
		alert.Message,
	)
	return nil
}

// GetType 获取通知器类型
func (cn *ConsoleNotifier) GetType() string {
	return "console"
}