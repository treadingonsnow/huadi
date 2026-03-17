import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  const [overview, setOverview] = useState(null)
  const [areaData, setAreaData] = useState([])
  const [cuisineData, setCuisineData] = useState([])
  const [priceData, setPriceData] = useState([])
  const [ratingData, setRatingData] = useState([])
  const [keywords, setKeywords] = useState({ positive: [], negative: [] })
  const [areaPriceData, setAreaPriceData] = useState([])

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
          <span style={S.navLink} onClick={() => navigate('/search')}>餐厅搜索</span>
          <span style={S.divider}>|</span>
          <span style={S.navLink} onClick={handleLogout}>退出登录</span>
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

        <ChartCard title="各区人均消费对比" style={{ gridColumn: 'span 2' }}>
          <AreaPriceChart data={areaPriceData} />
        </ChartCard>

        <ChartCard title="口碑关键词词云" style={{ gridColumn: 'span 1' }}>
          <WordCloud positive={keywords.positive} negative={keywords.negative} />
        </ChartCard>
      </div>

      <footer style={S.footer}>数据来源：美团 · 上海美食大数据分析平台 © 2026</footer>
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
  headerRight: { display: 'flex', alignItems: 'center', gap: 8 },
  navLink: { color: '#8b949e', cursor: 'pointer', fontSize: 13, ':hover': { color: '#ffd700' } },
  divider: { color: '#30363d' },
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
