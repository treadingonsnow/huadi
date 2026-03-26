import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Dropdown, message } from 'antd'
import {
  DownloadOutlined,
  DownOutlined,
  LoadingOutlined,
  SearchOutlined,
  InboxOutlined,
  LineChartOutlined,
  FileSearchOutlined,
} from '@ant-design/icons'
import { useUserStore } from '@/store'
import {
  getOverview, getAreaDistribution, getCuisineDistribution,
  getPriceDistribution, getRatingDistribution, getReviewKeywords, getAreaAvgPrice,
} from '@/api/analysis'
import AreaMap from '@/components/charts/AreaMap'
import CuisineChart from '@/components/charts/CuisineChart'
import PriceChart from '@/components/charts/PriceChart'
import RatingChart from '@/components/charts/RatingChart'
import AreaPriceChart from '@/components/charts/AreaPriceChart'
import WordCloud from '@/components/charts/WordCloud'

export default function Dashboard() {
  const navigate = useNavigate()
  const logout = useUserStore((s) => s.logout)
  const token = useUserStore((s) => s.token)
  const [overview, setOverview] = useState(null)
  const [areaData, setAreaData] = useState([])
  const [cuisineData, setCuisineData] = useState([])
  const [priceData, setPriceData] = useState([])
  const [ratingData, setRatingData] = useState([])
  const [keywords, setKeywords] = useState({ positive: [], negative: [] })
  const [areaPriceData, setAreaPriceData] = useState([])
  const [exporting, setExporting] = useState(false)
  const [hoveredNav, setHoveredNav] = useState('')
  const [accountHovered, setAccountHovered] = useState(false)

  const currentAccount = (() => {
    if (!token) return '未登录'
    try {
      const payloadBase64 = token.split('.')[1]
      if (!payloadBase64) return '未登录'
      const normalized = payloadBase64.replace(/-/g, '+').replace(/_/g, '/')
      const decoded = JSON.parse(atob(normalized))
      return decoded.username || decoded.sub || '未登录'
    } catch {
      return '未登录'
    }
  })()

  useEffect(() => {
    getOverview().then((r) => r.code === 200 && setOverview(r.data))
    getAreaDistribution().then((r) => r.code === 200 && setAreaData(r.data.districts.map((d) => ({ name: d.name, value: d.count }))))
    getCuisineDistribution().then((r) => r.code === 200 && setCuisineData(r.data.cuisines))
    getPriceDistribution().then((r) => r.code === 200 && setPriceData(r.data.ranges))
    getRatingDistribution().then((r) => r.code === 200 && setRatingData(r.data.ratings))
    getReviewKeywords().then((r) => r.code === 200 && setKeywords(r.data))
    getAreaAvgPrice().then((r) => r.code === 200 && setAreaPriceData(r.data.districts))
  }, [])

  const handleLogout = () => { logout(); navigate('/login') }
  const accountMenu = {
    items: [{ key: 'logout', label: '退出登录' }],
    onClick: ({ key }) => {
      if (key === 'logout') handleLogout()
    },
  }

  const handleExportReport = async () => {
    setExporting(true)
    message.loading({ content: '正在生成报告，请稍候…', key: 'export', duration: 0 })
    try {
      const res = await fetch('/api/v1/report/generate', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      if (!res.ok) {
        let errMsg = `报告生成失败 (HTTP ${res.status})`
        try { const j = await res.json(); errMsg = j.message || errMsg } catch {}
        message.error({ content: errMsg, key: 'export' })
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.style.display = 'none'
      const now = new Date()
      a.download = `上海美食分析报告_${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.pdf`
      document.body.appendChild(a)   // 必须插入 DOM 才能触发下载
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 30000)  // 延迟释放，确保下载完成
      message.success({ content: '报告已下载', key: 'export' })
    } catch (e) {
      message.error({ content: '导出失败：' + e.message, key: 'export' })
    } finally {
      setExporting(false)
    }
  }

  const navItems = [
    { key: 'search', label: '餐厅搜索', icon: <SearchOutlined />, path: '/search' },
    { key: 'import', label: '数据导入', icon: <InboxOutlined />, path: '/import' },
    { key: 'predict', label: '评分预测', icon: <LineChartOutlined />, path: '/predict' },
    { key: 'clean', label: '清洗日志', icon: <FileSearchOutlined />, path: '/clean-logs' },
  ]

  return (
    <div style={S.page}>
      {/* 顶部标题栏 */}
      <header style={S.header}>
        <div style={S.headerLeft}>
          <span style={S.headerIcon}>🍜</span>
          <span style={S.headerTitle}>上海美食大数据分析平台</span>
          <span style={S.headerSub}>Shanghai Food Analytics Dashboard</span>
        </div>
        <div style={S.headerRight}>
          {navItems.map((item) => (
            <span
              key={item.key}
              style={hoveredNav === item.key ? { ...S.topBtn, ...S.topBtnHover } : S.topBtn}
              onMouseEnter={() => setHoveredNav(item.key)}
              onMouseLeave={() => setHoveredNav('')}
              onClick={() => navigate(item.path)}
            >
              <span style={S.topBtnIcon}>{item.icon}</span>
              <span>{item.label}</span>
            </span>
          ))}
          <Button
            size="small"
            icon={exporting ? <LoadingOutlined /> : <DownloadOutlined />}
            loading={exporting}
            onClick={handleExportReport}
            style={S.exportBtn}
          >
            导出报告
          </Button>
          <Dropdown menu={accountMenu} trigger={['click']}>
            <span
              style={accountHovered ? { ...S.accountName, ...S.accountNameHover } : S.accountName}
              onMouseEnter={() => setAccountHovered(true)}
              onMouseLeave={() => setAccountHovered(false)}
            >
              当前账号：{currentAccount} <DownOutlined style={{ fontSize: 11 }} />
            </span>
          </Dropdown>
        </div>
      </header>

      {/* 概览卡片 */}
      <div style={S.overviewRow}>
        {[
          { label: '餐厅总数', value: overview?.total_count?.toLocaleString() ?? '--', unit: '家', color: '#e63946' },
          { label: '平均评分', value: overview?.avg_rating ?? '--', unit: '分', color: '#ffd700' },
          { label: '人均消费', value: overview ? `¥${overview.avg_price}` : '--', unit: '', color: '#06d6a0' },
          { label: '覆盖区域', value: overview?.district_count ?? '--', unit: '个区', color: '#118ab2' },
        ].map((item) => (
          <div key={item.label} style={S.overviewCard}>
            <div style={{ ...S.overviewValue, color: item.color }}>{item.value}<span style={S.overviewUnit}>{item.unit}</span></div>
            <div style={S.overviewLabel}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* 图表网格 */}
      <div style={S.grid}>
        <ChartCard title="上海各区餐厅分布" style={{ gridColumn: 'span 2', gridRow: 'span 2' }}>
          <AreaMap data={areaData} />
        </ChartCard>

        <ChartCard title="菜系分布">
          <CuisineChart data={cuisineData} />
        </ChartCard>

        <ChartCard title="价格区间分布">
          <PriceChart data={priceData} />
        </ChartCard>

        <ChartCard title="评分分布">
          <RatingChart data={ratingData} />
        </ChartCard>

        <ChartCard title="各区人均消费对比" style={{ gridColumn: 'span 2', gridRow: 'span 2' }}>
          <AreaPriceChart data={areaPriceData} />
        </ChartCard>

        <ChartCard title="口碑关键词词云" style={{ gridColumn: 'span 1' }}>
          <WordCloud positive={keywords.positive} negative={keywords.negative} />
        </ChartCard>
      </div>

      <footer style={S.footer}>数据来源：大众点评·上海美食大数据分析平台 © 2026</footer>
    </div>
  )
}

function ChartCard({ title, children, style }) {
  return (
    <div style={{ ...S.card, ...style }}>
      <div style={S.cardTitle}>{title}</div>
      <div style={S.cardBody}>{children}</div>
    </div>
  )
}

const S = {
  page: {
    minHeight: '100vh',
    background: '#0d1117',
    color: '#ffffff',
    display: 'flex',
    flexDirection: 'column',
    padding: '0 0 16px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    height: 60,
    background: 'linear-gradient(90deg, #0d1117 0%, #1a1a2e 50%, #0d1117 100%)',
    borderBottom: '1px solid rgba(230,57,70,0.3)',
    flexShrink: 0,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 12 },
  headerIcon: { fontSize: 28 },
  headerTitle: { fontSize: 20, fontWeight: 700, color: '#ffffff', letterSpacing: 1 },
  headerSub: { fontSize: 12, color: '#ffd700', letterSpacing: 2 },
  headerRight: { display: 'flex', alignItems: 'center', gap: 10 },
  topBtn: {
    color: '#eaf1ff',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 500,
    padding: '6px 12px',
    borderRadius: 10,
    border: '1px solid rgba(122,162,255,0.35)',
    background: 'linear-gradient(180deg, rgba(67,91,155,0.18) 0%, rgba(35,49,84,0.38) 100%)',
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18), 0 4px 10px rgba(0,0,0,0.18)',
  },
  topBtnHover: {
    transform: 'translateY(-1px)',
    border: '1px solid rgba(137,178,255,0.7)',
    background: 'linear-gradient(180deg, rgba(88,126,220,0.38) 0%, rgba(48,77,144,0.5) 100%)',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.22), 0 8px 18px rgba(62,110,226,0.3)',
  },
  topBtnIcon: {
    fontSize: 12,
    color: '#d7e5ff',
  },
  exportBtn: {
    background: 'linear-gradient(120deg, #ff5e6d 0%, #ff3a49 55%, #ff6571 100%)',
    borderColor: '#ff4a59',
    color: '#fff',
    borderRadius: 10,
    height: 32,
    paddingInline: 14,
    fontWeight: 600,
    boxShadow: '0 8px 18px rgba(255,74,89,0.34), inset 0 1px 0 rgba(255,255,255,0.35)',
  },
  accountName: {
    color: '#e8ecff',
    fontSize: 13,
    cursor: 'pointer',
    fontWeight: 500,
    padding: '6px 12px',
    borderRadius: 10,
    border: '1px solid rgba(166,185,230,0.32)',
    background: 'linear-gradient(180deg, rgba(78,92,128,0.2) 0%, rgba(43,52,76,0.42) 100%)',
    transition: 'all 0.2s ease',
  },
  accountNameHover: {
    border: '1px solid rgba(196,213,255,0.55)',
    background: 'linear-gradient(180deg, rgba(99,121,168,0.3) 0%, rgba(58,76,121,0.48) 100%)',
    boxShadow: '0 8px 18px rgba(58,92,172,0.26)',
  },
  overviewRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 12,
    padding: '12px 16px',
  },
  overviewCard: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8,
    padding: '16px 20px',
    textAlign: 'center',
  },
  overviewValue: { fontSize: 32, fontWeight: 700, lineHeight: 1 },
  overviewUnit: { fontSize: 14, fontWeight: 400, marginLeft: 4 },
  overviewLabel: { color: '#8b949e', fontSize: 13, marginTop: 6 },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gridAutoRows: '280px',
    gap: 12,
    padding: '0 16px',
    flex: 1,
  },
  card: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  cardTitle: {
    padding: '10px 16px',
    fontSize: 13,
    fontWeight: 600,
    color: '#ffd700',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    flexShrink: 0,
  },
  cardBody: { flex: 1, overflow: 'hidden', padding: 4 },
  footer: {
    textAlign: 'center',
    color: '#30363d',
    fontSize: 12,
    padding: '8px 0 0',
  },
}
