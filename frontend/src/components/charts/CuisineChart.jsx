import React from 'react'
import ReactECharts from 'echarts-for-react'

export default function CuisineChart({ data }) {
  if (!data?.length) return null
  const colors = createDistinctColors(data.length)

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
      radius: ['30%', '80%'],
      center: ['30%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#ffd700' } },
      data: data.map((d, i) => ({
        name: d.name,
        value: d.count,
        itemStyle: {
          color: colors[i],
          borderColor: '#0d1117',
          borderWidth: 1.2,
          decal: createDecal(i),
        },
      })),
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} theme="dark" />
}

function createDistinctColors(count) {
  const colors = []
  const basePalette = [
    '#ff4d6d', '#ffd166', '#06d6a0', '#118ab2', '#ef476f', '#8ecae6',
    '#f77f00', '#52b788', '#9b5de5', '#ff9f1c', '#2ec4b6', '#3a86ff',
    '#e76f51', '#00bbf9', '#c77dff', '#f15bb5', '#90be6d', '#f8961e',
    '#577590', '#43aa8b',
  ]
  for (let i = 0; i < count; i += 1) {
    colors.push(basePalette[i % basePalette.length])
  }
  return colors
}

function createDecal(index) {
  const patterns = [
    { symbol: 'rect', dashArrayX: [1, 0], dashArrayY: [3, 2], rotation: 0 },
    { symbol: 'circle', dashArrayX: [1, 0], dashArrayY: [2, 4], rotation: Math.PI / 6 },
    { symbol: 'triangle', dashArrayX: [1, 1], dashArrayY: [3, 3], rotation: Math.PI / 3 },
    { symbol: 'diamond', dashArrayX: [2, 1], dashArrayY: [2, 3], rotation: Math.PI / 4 },
    { symbol: 'line', dashArrayX: [4, 2], dashArrayY: [2, 2], rotation: Math.PI / 2 },
  ]
  return {
    ...patterns[index % patterns.length],
    color: 'rgba(255,255,255,0.22)',
    symbolSize: 1.3 + (index % 3) * 0.35,
  }
}
