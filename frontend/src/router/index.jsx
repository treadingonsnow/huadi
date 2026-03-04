// 前端路由配置 (React Router v7)
// 使用 createBrowserRouter + RouterProvider
// 路由结构：
// /                    首页 (Home)
// /login               登录页 (Login)
// /search              餐厅搜索 (Search)
// /restaurant/:id      餐厅详情 (RestaurantDetail)
// /analysis            数据分析 (Analysis)
// /reports             报告生成 (Reports)
// /admin               后台管理布局（需admin角色，路由守卫）
//   /admin/dashboard   管理仪表盘 (Dashboard)
//   /admin/crawl-tasks 爬虫任务管理 (CrawlTasks)
//   /admin/users       用户管理 (UserManage)
//   /admin/datasource  数据源管理 (DataSource)
// 路由守卫：ProtectedRoute 组件，检查JWT Token有效性，未登录跳转/login，权限不足跳转403
