import React, { useState, useEffect } from 'react'
import { Input, Select, Button, Card, Modal, Tag, Pagination, Rate, Empty, Spin, message } from 'antd'
import { SearchOutlined, EnvironmentOutlined, PhoneOutlined, ShopOutlined, HeartOutlined, HeartFilled } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { searchRestaurants, getFavorites, toggleFavorite } from '@/api/restaurants'
import { useUserStore } from '@/store'

const CUISINES = ['甜品/饮品', '本帮菜', '面食/小吃', '日本料理', '韩国料理', '火锅', '粤菜/港式', '东南亚菜', '烧烤/烤肉', '自助餐', '西餐', '川湘菜', '北方菜', '海鲜', '江浙菜', '素食']
const DISTRICTS = ['浦东新区', '黄浦区', '徐汇区', '静安区', '长宁区', '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区', '松江区', '青浦区', '奉贤区', '金山区', '崇明区']
const PRICE_RANGES = [
  { label: '50元以下', min: 0, max: 50 },
  { label: '50-100元', min: 50, max: 100 },
  { label: '100-200元', min: 100, max: 200 },
  { label: '200-300元', min: 200, max: 300 },
  { label: '300元以上', min: 300, max: 9999 },
]

export default function Search() {
  const navigate = useNavigate()
  const logout = useUserStore((s) => s.logout)
  const [keyword, setKeyword] = useState('')
  const [filters, setFilters] = useState({ cuisine: undefined, district: undefined, priceRange: undefined, rating_min: undefined, favFilter: undefined })
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [favorites, setFavorites] = useState(new Set())
  const [messageApi, contextHolder] = message.useMessage()

  const doSearch = async (p = 1) => {
    setLoading(true)
    const pr = filters.priceRange !== undefined ? PRICE_RANGES[filters.priceRange] : {}
    const params = {
      keyword: keyword || undefined,
      cuisine: filters.cuisine,
      district: filters.district,
      price_min: pr.min,
      price_max: pr.max,
      rating_min: filters.rating_min,
      favorites_only: filters.favFilter === 'fav' ? true : undefined,
      exclude_favorites: filters.favFilter === 'unfav' ? true : undefined,
      page: p,
      page_size: 12,
    }
    try {
      const res = await searchRestaurants(params)
      if (res.code === 200) {
        setResults(res.data.items)
        setTotal(res.data.total)
        setPage(p)
      }
    } finally {
      setLoading(false)
    }
  }

  const loadFavorites = async () => {
    try {
      const res = await getFavorites({ page: 1, page_size: 100 })
      if (res.code === 200) {
        const ids = (res.data.items || [])
          .map((item) => item.restaurant?.id)
          .filter((id) => id !== undefined && id !== null)
        setFavorites(new Set(ids))
      }
    } catch {
      messageApi.error('收藏列表获取失败')
    }
  }

  useEffect(() => {
    doSearch(1)
    loadFavorites()
  }, [])

  useEffect(() => {
    doSearch(1)
  }, [filters.favFilter])

  const handleToggleFavorite = async (restaurantId) => {
    const targetId = String(restaurantId)
    try {
      const res = await toggleFavorite(targetId)
      if (res.code === 200) {
        const action = res.data?.action
        setFavorites((prev) => {
          const next = new Set(prev)
          if (action === 'remove') {
            next.delete(targetId)
          } else {
            next.add(targetId)
          }
          return next
        })
        if (action === 'remove') {
          messageApi.success('已取消收藏')
        } else if (action === 'add') {
          messageApi.success('已加入收藏')
        }
        loadFavorites()
      } else {
        messageApi.error('收藏失败')
        if (res.message) {
          messageApi.error(res.message)
        }
      }
    } catch {
      messageApi.error('收藏失败')
    }
  }

  const handleLogout = () => { logout(); navigate('/login') }

  const filteredResults = results

  return (
    <div style={S.page}>
      {contextHolder}
      {/* 顶部导航 */}
      <header style={S.header}>
        <span style={S.logo} onClick={() => navigate('/dashboard')}>🍜 上海美食大数据平台</span>
        <div style={S.headerRight}>
          <span style={S.navLink} onClick={() => navigate('/dashboard')}>数据大屏</span>
          <span style={S.divider}>|</span>
          <span style={S.navLink} onClick={handleLogout}>退出登录</span>
        </div>
      </header>

      <div style={S.content}>
        {/* 搜索栏 */}
        <div style={S.searchBar}>
          <Input
            size="large"
            placeholder="搜索餐厅名称、菜系、区域..."
            prefix={<SearchOutlined style={{ color: '#8b949e' }} />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={() => doSearch(1)}
            style={S.searchInput}
            allowClear
          />
          <Button type="primary" size="large" onClick={() => doSearch(1)} style={S.searchBtn}>搜索</Button>
        </div>

        {/* 筛选条件 */}
        <div style={S.filterRow}>
          <Select
            placeholder="菜系"
            allowClear
            style={{ width: 130 }}
            value={filters.cuisine}
            onChange={(v) => setFilters((f) => ({ ...f, cuisine: v }))}
            options={CUISINES.map((c) => ({ label: c, value: c }))}
          />
          <Select
            placeholder="区域"
            allowClear
            style={{ width: 130 }}
            value={filters.district}
            onChange={(v) => setFilters((f) => ({ ...f, district: v }))}
            options={DISTRICTS.map((d) => ({ label: d, value: d }))}
          />
          <Select
            placeholder="价格区间"
            allowClear
            style={{ width: 140 }}
            value={filters.priceRange}
            onChange={(v) => setFilters((f) => ({ ...f, priceRange: v }))}
            options={PRICE_RANGES.map((p, i) => ({ label: p.label, value: i }))}
          />
          <Select
            placeholder="最低评分"
            allowClear
            style={{ width: 120 }}
            value={filters.rating_min}
            onChange={(v) => setFilters((f) => ({ ...f, rating_min: v }))}
            options={[4.5, 4.0, 3.5, 3.0].map((r) => ({ label: `${r}分以上`, value: r }))}
          />
          <Select
            placeholder="收藏状态"
            allowClear
            style={{ width: 120 }}
            value={filters.favFilter}
            onChange={(v) => setFilters((f) => ({ ...f, favFilter: v }))}
            options={[{ label: '已收藏', value: 'fav' }, { label: '未收藏', value: 'unfav' }]}
          />
          <Button onClick={() => { setFilters({ cuisine: undefined, district: undefined, priceRange: undefined, rating_min: undefined, favFilter: undefined }); setKeyword('') }}>
            重置
          </Button>
        </div>

        {/* 结果统计 */}
        <div style={S.resultInfo}>共找到 <span style={{ color: '#e63946', fontWeight: 600 }}>{total}</span> 家餐厅</div>

        {/* 餐厅卡片列表 */}
        <Spin spinning={loading}>
          {filteredResults.length === 0 && !loading ? (
            <Empty description="暂无数据" style={{ marginTop: 60 }} />
          ) : (
            <div style={S.cardGrid}>
              {filteredResults.map((r) => (
                <RestaurantCard
                  key={r.id}
                  data={r}
                  onClick={() => setSelected(r)}
                  isFavorite={favorites.has(r.id)}
                  onToggleFavorite={() => handleToggleFavorite(r.id)}
                />
              ))}
            </div>
          )}
        </Spin>

        {/* 分页 */}
        {total > 12 && (
          <div style={S.pagination}>
            <Pagination
              current={page}
              total={total}
              pageSize={12}
              onChange={(p) => doSearch(p)}
              showTotal={(t) => `共 ${t} 条`}
            />
          </div>
        )}
      </div>

      {/* 详情弹窗 */}
      <Modal
        open={!!selected}
        onCancel={() => setSelected(null)}
        footer={null}
        title={<span style={{ color: '#ffffff' }}>{selected?.name}</span>}
        styles={{ content: { background: '#161b22', border: '1px solid #30363d' }, header: { background: '#161b22', borderBottom: '1px solid #30363d' } }}
      >
        {selected && (
          <div style={{ color: '#c9d1d9' }}>
            <div style={S.detailRow}><Tag color="red">{selected.cuisine_type}</Tag><Tag color="blue">{selected.district}</Tag></div>
            <div style={S.detailRow}><Rate disabled defaultValue={selected.rating} allowHalf style={{ fontSize: 14 }} /><span style={{ marginLeft: 8, color: '#ffd700' }}>{selected.rating}分</span><span style={{ marginLeft: 8, color: '#8b949e' }}>({selected.review_count}条评价)</span></div>
            <div style={S.detailRow}><EnvironmentOutlined style={{ color: '#8b949e', marginRight: 6 }} />{selected.address}</div>
            <div style={S.detailRow}><PhoneOutlined style={{ color: '#8b949e', marginRight: 6 }} />{selected.phone}</div>
            <div style={S.detailRow}><ShopOutlined style={{ color: '#8b949e', marginRight: 6 }} />人均消费：<span style={{ color: '#06d6a0', fontWeight: 600 }}>¥{selected.avg_price}</span></div>
          </div>
        )}
      </Modal>
    </div>
  )
}

function RestaurantCard({ data, onClick, isFavorite, onToggleFavorite }) {
  return (
    <Card
      hoverable
      onClick={onClick}
      style={S.rCard}
      styles={{ body: { padding: '14px 16px' } }}
    >
      <div style={S.rHeader}>
        <div style={S.rName}>{data.name}</div>
        <Button
          type="text"
          onClick={(event) => {
            event.stopPropagation()
            onToggleFavorite()
          }}
          icon={isFavorite ? <HeartFilled style={S.rFavIconActive} /> : <HeartOutlined style={S.rFavIcon} />}
          style={S.rFavBtn}
        />
      </div>
      <div style={S.rTags}>
        <Tag color="red" style={{ fontSize: 11 }}>{data.cuisine_type}</Tag>
        <Tag color="default" style={{ fontSize: 11 }}>{data.district}</Tag>
      </div>
      <div style={S.rMeta}>
        <span style={S.rRating}>⭐ {data.rating}</span>
        <span style={S.rPrice}>¥{data.avg_price}/人</span>
      </div>
      <div style={S.rAddress}><EnvironmentOutlined style={{ marginRight: 4 }} />{data.business_area}</div>
    </Card>
  )
}

const S = {
  page: { minHeight: '100vh', background: '#0d1117', color: '#ffffff' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 24px', height: 56,
    background: '#161b22', borderBottom: '1px solid #30363d',
  },
  logo: { fontSize: 16, fontWeight: 700, color: '#ffffff', cursor: 'pointer' },
  headerRight: { display: 'flex', alignItems: 'center', gap: 8 },
  navLink: { color: '#8b949e', cursor: 'pointer', fontSize: 13 },
  divider: { color: '#30363d' },
  content: { maxWidth: 1200, margin: '0 auto', padding: '24px 16px' },
  searchBar: { display: 'flex', gap: 8, marginBottom: 16 },
  searchInput: { flex: 1, background: '#161b22', borderColor: '#30363d' },
  searchBtn: { background: '#e63946', borderColor: '#e63946', minWidth: 80 },
  filterRow: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 },
  resultInfo: { color: '#8b949e', fontSize: 13, marginBottom: 16 },
  cardGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 },
  pagination: { marginTop: 24, textAlign: 'center' },
  rCard: { background: '#161b22', border: '1px solid #30363d', cursor: 'pointer' },
  rHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 8 },
  rName: { fontSize: 15, fontWeight: 600, color: '#ffffff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  rFavBtn: { padding: 0, height: 24, width: 24 },
  rFavIcon: { color: '#8b949e', fontSize: 18 },
  rFavIconActive: { color: '#e63946', fontSize: 18 },
  rTags: { marginBottom: 8 },
  rMeta: { display: 'flex', justifyContent: 'space-between', marginBottom: 6 },
  rRating: { color: '#ffd700', fontWeight: 600 },
  rPrice: { color: '#06d6a0', fontWeight: 600 },
  rAddress: { color: '#8b949e', fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  detailRow: { marginBottom: 12, display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 4 },
}
