import React from 'react'
import ReactECharts from 'echarts-for-react'

export default function AreaPriceChart({ data }) {
  if (!data?.length) return null

  const sorted = [...data].sort((a, b) => a.avg_price - b.avg_price)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', formatter: '{b}：¥{c}', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 24, bottom: 8, top: 8, containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#8b949e', formatter: '¥{value}' },
      splitLine: { lineStyle: { color: '#21262d' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((d) => d.name),
      axisLabel: { color: '#8b949e', fontSize: 11 },
      axisLine: { lineStyle: { color: '#30363d' } },
    },
    series: [{
      type: 'bar',
      data: sorted.map((d) => d.avg_price),
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [{ offset: 0, color: '#118ab2' }, { offset: 1, color: '#06d6a0' }],
        },
        borderRadius: [0, 4, 4, 0],
      },
      label: { show: true, position: 'right', color: '#8b949e', fontSize: 10, formatter: '¥{c}' },
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} theme="dark" />
}
