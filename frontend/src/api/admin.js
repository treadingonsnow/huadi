// 后台管理 API 调用
// - getRoles()                     获取角色列表 GET /admin/roles
// - updateRole(roleId, data)       更新角色权限 PUT /admin/roles/{roleId}
// - getUsers(params)               获取用户列表 GET /admin/users
// - updateUserRole(userId, role)   更新用户角色 PUT /admin/users/{userId}/role
// - toggleUserStatus(userId)       启用/禁用用户 PUT /admin/users/{userId}/status
// - getCrawlTasks(params)          获取爬虫任务列表 GET /admin/crawl-tasks
// - createCrawlTask(data)          创建爬虫任务 POST /admin/crawl-tasks
// - triggerCrawlTask(taskId)       手动触发任务 POST /admin/crawl-tasks/{taskId}/trigger
// - getDataSources(params)         获取数据源列表 GET /admin/datasources
// - getSystemLogs(params)          获取系统日志 GET /admin/logs
