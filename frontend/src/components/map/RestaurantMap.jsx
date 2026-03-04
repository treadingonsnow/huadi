// 餐厅地图组件
// 功能：
// - 基于高德地图 JS API 渲染交互式地图
// - Props: restaurants (餐厅列表，含经纬度), center, zoom, filters, onMarkerClick
// - 使用 useEffect + useRef 管理地图实例生命周期
// - 餐厅位置标注（Marker），点击弹出信息窗口（名称、评分、人均）
// - 聚合显示：缩小时聚合（MarkerCluster），放大时展开
// - 筛选功能：按菜系、价格、评分筛选地图上的标注
// - 地铁线路叠加显示
