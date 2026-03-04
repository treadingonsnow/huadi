// 热力图组件
// 功能：
// - 基于 echarts-for-react + 高德地图 渲染餐厅分布热力图
// - Props: heatmapData (经纬度+权重数组), center (地图中心点), zoom (缩放级别)
// - 使用 useEffect 初始化高德地图实例，叠加 ECharts 热力图层
// - 支持缩放、拖拽交互
// - 支持商圈边界叠加显示
// - 支持地铁线路叠加显示
