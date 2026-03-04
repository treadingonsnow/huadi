// Axios 请求封装
// 功能：
// - 创建 axios 实例，配置 baseURL (/api/v1)、timeout (10s)
// - 请求拦截器：自动在 Header 中添加 Authorization: Bearer <token>
// - 响应拦截器：
//   - 统一处理错误码（401跳转登录、403提示权限不足、500提示服务器错误）
//   - 统一提取 response.data
// - 导出 get, post, put, del 快捷方法
