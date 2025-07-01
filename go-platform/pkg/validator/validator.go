package validator

import (
	"encoding/json"
	"fmt"
	"reflect"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/go-playground/validator/v10"
	"github.com/go-playground/locales/zh"
	"github.com/go-playground/universal-translator"
	zhTranslations "github.com/go-playground/validator/v10/translations/zh"
)

var (
	validate *validator.Validate
	trans    ut.Translator
)

// ValidationError 验证错误
type ValidationError struct {
	Field   string `json:"field"`
	Tag     string `json:"tag"`
	Value   string `json:"value"`
	Message string `json:"message"`
}

// ValidationErrors 验证错误列表
type ValidationErrors []ValidationError

// Error 实现error接口
func (ve ValidationErrors) Error() string {
	if len(ve) == 0 {
		return "validation failed"
	}

	var messages []string
	for _, err := range ve {
		messages = append(messages, err.Message)
	}
	return strings.Join(messages, "; ")
}

// First 获取第一个错误
func (ve ValidationErrors) First() *ValidationError {
	if len(ve) == 0 {
		return nil
	}
	return &ve[0]
}

// FieldErrors 按字段分组的错误
func (ve ValidationErrors) FieldErrors() map[string][]ValidationError {
	result := make(map[string][]ValidationError)
	for _, err := range ve {
		result[err.Field] = append(result[err.Field], err)
	}
	return result
}

// Init 初始化验证器
func Init() error {
	validate = validator.New()

	// 注册自定义标签名
	validate.RegisterTagNameFunc(func(fld reflect.StructField) string {
		name := strings.SplitN(fld.Tag.Get("json"), ",", 2)[0]
		if name == "-" {
			return ""
		}
		if name != "" {
			return name
		}
		return fld.Name
	})

	// 初始化翻译器
	if err := initTranslator(); err != nil {
		return fmt.Errorf("failed to init translator: %v", err)
	}

	// 注册自定义验证规则
	registerCustomValidations()

	return nil
}

// initTranslator 初始化翻译器
func initTranslator() error {
	zhLocale := zh.New()
	uni := ut.New(zhLocale, zhLocale)

	var ok bool
	trans, ok = uni.GetTranslator("zh")
	if !ok {
		return fmt.Errorf("failed to get zh translator")
	}

	// 注册默认翻译
	if err := zhTranslations.RegisterDefaultTranslations(validate, trans); err != nil {
		return fmt.Errorf("failed to register zh translations: %v", err)
	}

	// 注册自定义翻译
	registerCustomTranslations()

	return nil
}

// registerCustomValidations 注册自定义验证规则
func registerCustomValidations() {
	// 手机号验证
	validate.RegisterValidation("mobile", validateMobile)

	// 身份证号验证
	validate.RegisterValidation("idcard", validateIDCard)

	// 密码强度验证
	validate.RegisterValidation("password", validatePassword)

	// 用户名验证
	validate.RegisterValidation("username", validateUsername)

	// 模型名称验证
	validate.RegisterValidation("model_name", validateModelName)

	// 文件路径验证
	validate.RegisterValidation("filepath", validateFilePath)

	// URL验证（支持http和https）
	validate.RegisterValidation("http_url", validateHTTPURL)

	// 端口验证
	validate.RegisterValidation("port", validatePort)

	// IP地址验证
	validate.RegisterValidation("ip_addr", validateIPAddr)

	// 时间格式验证
	validate.RegisterValidation("datetime", validateDateTime)

	// JSON格式验证
	validate.RegisterValidation("json_string", validateJSONString)

	// 版本号验证
	validate.RegisterValidation("version", validateVersion)

	// 颜色代码验证
	validate.RegisterValidation("color", validateColor)

	// 数组长度范围验证
	validate.RegisterValidation("array_len", validateArrayLen)

	// 字符串包含验证
	validate.RegisterValidation("contains_any", validateContainsAny)

	// 字符串不包含验证
	validate.RegisterValidation("not_contains", validateNotContains)

	// 枚举值验证
	validate.RegisterValidation("enum", validateEnum)
}

// registerCustomTranslations 注册自定义翻译
func registerCustomTranslations() {
	translations := map[string]string{
		"mobile":       "{0}必须是有效的手机号码",
		"idcard":       "{0}必须是有效的身份证号码",
		"password":     "{0}必须包含大小写字母、数字和特殊字符，长度8-32位",
		"username":     "{0}只能包含字母、数字和下划线，长度3-20位",
		"model_name":   "{0}只能包含字母、数字、下划线和连字符，长度1-50位",
		"filepath":     "{0}必须是有效的文件路径",
		"http_url":     "{0}必须是有效的HTTP或HTTPS URL",
		"port":         "{0}必须是有效的端口号(1-65535)",
		"ip_addr":      "{0}必须是有效的IP地址",
		"datetime":     "{0}必须是有效的日期时间格式",
		"json_string":  "{0}必须是有效的JSON字符串",
		"version":      "{0}必须是有效的版本号(如1.0.0)",
		"color":        "{0}必须是有效的颜色代码",
		"array_len":    "{0}数组长度不符合要求",
		"contains_any": "{0}必须包含指定的字符",
		"not_contains": "{0}不能包含指定的字符",
		"enum":         "{0}必须是有效的枚举值",
	}

	for tag, message := range translations {
		validate.RegisterTranslation(tag, trans, func(ut ut.Translator) error {
			return ut.Add(tag, message, true)
		}, func(ut ut.Translator, fe validator.FieldError) string {
			t, _ := ut.T(tag, fe.Field())
			return t
		})
	}
}

// Validate 验证结构体
func Validate(s interface{}) error {
	if validate == nil {
		if err := Init(); err != nil {
			return err
		}
	}

	err := validate.Struct(s)
	if err == nil {
		return nil
	}

	var validationErrors ValidationErrors
	for _, err := range err.(validator.ValidationErrors) {
		validationErrors = append(validationErrors, ValidationError{
			Field:   err.Field(),
			Tag:     err.Tag(),
			Value:   fmt.Sprintf("%v", err.Value()),
			Message: err.Translate(trans),
		})
	}

	return validationErrors
}

// ValidateVar 验证单个变量
func ValidateVar(field interface{}, tag string) error {
	if validate == nil {
		if err := Init(); err != nil {
			return err
		}
	}

	err := validate.Var(field, tag)
	if err == nil {
		return nil
	}

	var validationErrors ValidationErrors
	for _, err := range err.(validator.ValidationErrors) {
		validationErrors = append(validationErrors, ValidationError{
			Field:   "field",
			Tag:     err.Tag(),
			Value:   fmt.Sprintf("%v", err.Value()),
			Message: err.Translate(trans),
		})
	}

	return validationErrors
}

// 自定义验证函数

// validateMobile 验证手机号
func validateMobile(fl validator.FieldLevel) bool {
	mobile := fl.Field().String()
	matched, _ := regexp.MatchString(`^1[3-9]\d{9}$`, mobile)
	return matched
}

// validateIDCard 验证身份证号
func validateIDCard(fl validator.FieldLevel) bool {
	idcard := fl.Field().String()
	// 18位身份证号验证
	matched, _ := regexp.MatchString(`^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$`, idcard)
	return matched
}

// validatePassword 验证密码强度
func validatePassword(fl validator.FieldLevel) bool {
	password := fl.Field().String()
	if len(password) < 8 || len(password) > 32 {
		return false
	}

	// 必须包含大写字母、小写字母、数字和特殊字符
	hasUpper := false
	hasLower := false
	hasDigit := false
	hasSpecial := false

	for _, char := range password {
		switch {
		case unicode.IsUpper(char):
			hasUpper = true
		case unicode.IsLower(char):
			hasLower = true
		case unicode.IsDigit(char):
			hasDigit = true
		case unicode.IsPunct(char) || unicode.IsSymbol(char):
			hasSpecial = true
		}
	}

	return hasUpper && hasLower && hasDigit && hasSpecial
}

// validateUsername 验证用户名
func validateUsername(fl validator.FieldLevel) bool {
	username := fl.Field().String()
	matched, _ := regexp.MatchString(`^[a-zA-Z0-9_]{3,20}$`, username)
	return matched
}

// validateModelName 验证模型名称
func validateModelName(fl validator.FieldLevel) bool {
	modelName := fl.Field().String()
	matched, _ := regexp.MatchString(`^[a-zA-Z0-9_-]{1,50}$`, modelName)
	return matched
}

// validateFilePath 验证文件路径
func validateFilePath(fl validator.FieldLevel) bool {
	filePath := fl.Field().String()
	// 简单的文件路径验证
	matched, _ := regexp.MatchString(`^[^<>:"|?*]+$`, filePath)
	return matched && len(filePath) > 0
}

// validateHTTPURL 验证HTTP URL
func validateHTTPURL(fl validator.FieldLevel) bool {
	url := fl.Field().String()
	matched, _ := regexp.MatchString(`^https?://[^\s/$.?#].[^\s]*$`, url)
	return matched
}

// validatePort 验证端口号
func validatePort(fl validator.FieldLevel) bool {
	port := fl.Field().Int()
	return port >= 1 && port <= 65535
}

// validateIPAddr 验证IP地址
func validateIPAddr(fl validator.FieldLevel) bool {
	ip := fl.Field().String()
	// IPv4验证
	ipv4Regex := `^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$`
	matched, _ := regexp.MatchString(ipv4Regex, ip)
	if matched {
		return true
	}

	// IPv6验证（简化版）
	ipv6Regex := `^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$`
	matched, _ = regexp.MatchString(ipv6Regex, ip)
	return matched
}

// validateDateTime 验证日期时间格式
func validateDateTime(fl validator.FieldLevel) bool {
	dateTime := fl.Field().String()
	formats := []string{
		"2006-01-02 15:04:05",
		"2006-01-02T15:04:05Z",
		"2006-01-02T15:04:05.000Z",
		"2006-01-02",
		time.RFC3339,
	}

	for _, format := range formats {
		if _, err := time.Parse(format, dateTime); err == nil {
			return true
		}
	}
	return false
}

// validateJSONString 验证JSON字符串
func validateJSONString(fl validator.FieldLevel) bool {
	jsonStr := fl.Field().String()
	return isValidJSON(jsonStr)
}

// validateVersion 验证版本号
func validateVersion(fl validator.FieldLevel) bool {
	version := fl.Field().String()
	// 语义化版本验证
	matched, _ := regexp.MatchString(`^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$`, version)
	return matched
}

// validateColor 验证颜色代码
func validateColor(fl validator.FieldLevel) bool {
	color := fl.Field().String()
	// 支持hex颜色代码
	matched, _ := regexp.MatchString(`^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$`, color)
	return matched
}

// validateArrayLen 验证数组长度
func validateArrayLen(fl validator.FieldLevel) bool {
	param := fl.Param()
	parts := strings.Split(param, "-")
	if len(parts) != 2 {
		return false
	}

	min, err1 := strconv.Atoi(parts[0])
	max, err2 := strconv.Atoi(parts[1])
	if err1 != nil || err2 != nil {
		return false
	}

	length := fl.Field().Len()
	return length >= min && length <= max
}

// validateContainsAny 验证包含任意字符
func validateContainsAny(fl validator.FieldLevel) bool {
	value := fl.Field().String()
	chars := fl.Param()
	return strings.ContainsAny(value, chars)
}

// validateNotContains 验证不包含指定字符
func validateNotContains(fl validator.FieldLevel) bool {
	value := fl.Field().String()
	substr := fl.Param()
	return !strings.Contains(value, substr)
}

// validateEnum 验证枚举值
func validateEnum(fl validator.FieldLevel) bool {
	value := fl.Field().String()
	enumValues := strings.Split(fl.Param(), "|")
	for _, enumValue := range enumValues {
		if value == enumValue {
			return true
		}
	}
	return false
}

// 辅助函数

// isValidJSON 检查是否为有效JSON
func isValidJSON(str string) bool {
	var js interface{}
	return json.Unmarshal([]byte(str), &js) == nil
}

// IsEmail 验证邮箱格式
func IsEmail(email string) bool {
	emailRegex := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
	matched, _ := regexp.MatchString(emailRegex, email)
	return matched
}

// IsMobile 验证手机号格式
func IsMobile(mobile string) bool {
	mobileRegex := `^1[3-9]\d{9}$`
	matched, _ := regexp.MatchString(mobileRegex, mobile)
	return matched
}

// IsURL 验证URL格式
func IsURL(url string) bool {
	urlRegex := `^https?://[^\s/$.?#].[^\s]*$`
	matched, _ := regexp.MatchString(urlRegex, url)
	return matched
}

// IsIPv4 验证IPv4地址
func IsIPv4(ip string) bool {
	ipv4Regex := `^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$`
	matched, _ := regexp.MatchString(ipv4Regex, ip)
	return matched
}

// IsPort 验证端口号
func IsPort(port int) bool {
	return port >= 1 && port <= 65535
}

// IsAlphaNumeric 验证是否只包含字母和数字
func IsAlphaNumeric(str string) bool {
	alphaNumericRegex := `^[a-zA-Z0-9]+$`
	matched, _ := regexp.MatchString(alphaNumericRegex, str)
	return matched
}

// IsAlpha 验证是否只包含字母
func IsAlpha(str string) bool {
	alphaRegex := `^[a-zA-Z]+$`
	matched, _ := regexp.MatchString(alphaRegex, str)
	return matched
}

// IsNumeric 验证是否只包含数字
func IsNumeric(str string) bool {
	numericRegex := `^[0-9]+$`
	matched, _ := regexp.MatchString(numericRegex, str)
	return matched
}

// IsLength 验证字符串长度
func IsLength(str string, min, max int) bool {
	length := len(str)
	return length >= min && length <= max
}

// IsIn 验证值是否在指定列表中
func IsIn(value string, list []string) bool {
	for _, item := range list {
		if value == item {
			return true
		}
	}
	return false
}

// IsNotEmpty 验证字符串是否非空
func IsNotEmpty(str string) bool {
	return strings.TrimSpace(str) != ""
}

// IsPositive 验证数字是否为正数
func IsPositive(num float64) bool {
	return num > 0
}

// IsNonNegative 验证数字是否为非负数
func IsNonNegative(num float64) bool {
	return num >= 0
}

// IsInRange 验证数字是否在指定范围内
func IsInRange(num, min, max float64) bool {
	return num >= min && num <= max
}

// SanitizeString 清理字符串
func SanitizeString(str string) string {
	// 移除前后空格
	str = strings.TrimSpace(str)
	// 移除多余的空格
	str = regexp.MustCompile(`\s+`).ReplaceAllString(str, " ")
	return str
}

// SanitizeEmail 清理邮箱地址
func SanitizeEmail(email string) string {
	return strings.ToLower(strings.TrimSpace(email))
}

// SanitizePhone 清理手机号
func SanitizePhone(phone string) string {
	// 移除所有非数字字符
	return regexp.MustCompile(`[^0-9]`).ReplaceAllString(phone, "")
}

// ValidateStruct 验证结构体（别名）
func ValidateStruct(s interface{}) error {
	return Validate(s)
}

// MustValidate 验证结构体，如果失败则panic
func MustValidate(s interface{}) {
	if err := Validate(s); err != nil {
		panic(err)
	}
}

// ValidateAndSanitize 验证并清理结构体
func ValidateAndSanitize(s interface{}) error {
	// 首先进行清理
	sanitizeStruct(s)
	// 然后进行验证
	return Validate(s)
}

// sanitizeStruct 清理结构体中的字符串字段
func sanitizeStruct(s interface{}) {
	v := reflect.ValueOf(s)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}

	if v.Kind() != reflect.Struct {
		return
	}

	for i := 0; i < v.NumField(); i++ {
		field := v.Field(i)
		if field.Kind() == reflect.String && field.CanSet() {
			field.SetString(SanitizeString(field.String()))
		}
	}
}