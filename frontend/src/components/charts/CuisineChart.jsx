import React from 'react'
import ReactECharts from 'echarts-for-react'

export default function CuisineChart({ data }) {
  if (!data?.length) return null

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}：{c}家 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#8b949e', fontSize: 11 },
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['32%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#ffd700' } },
      data: data.map((d, i) => ({
        name: d.name,
        value: d.count,
        itemStyle: { color: COLORS[i % COLORS.length] },
      })),
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} theme="dark" />
}

const COLORS = ['#e63946', '#ffd700', '#06d6a0', '#118ab2', '#ef476f', '#ffc43d', '#1b9aaa', '#f4a261', '#e76f51', '#a8dadc']
