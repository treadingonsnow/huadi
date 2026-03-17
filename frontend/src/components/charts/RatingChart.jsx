import React from 'react'
import ReactECharts from 'echarts-for-react'

export default function RatingChart({ data }) {
  if (!data?.length) return null

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 16, right: 16, bottom: 8, top: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.range),
      axisLabel: { color: '#8b949e', fontSize: 11 },
      axisLine: { lineStyle: { color: '#30363d' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#21262d' } },
    },
    series: [{
      type: 'bar',
      data: data.map((d) => d.count),
      itemStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#ffd700' }, { offset: 1, color: '#7a6200' }],
        },
        borderRadius: [4, 4, 0, 0],
      },
      label: { show: true, position: 'top', color: '#8b949e', fontSize: 11 },
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} theme="dark" />
}
