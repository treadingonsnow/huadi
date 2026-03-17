import React from 'react'
import ReactECharts from 'echarts-for-react'
import 'echarts-wordcloud'

export default function WordCloud({ positive = [], negative = [] }) {
  const allWords = [
    ...positive.map((w) => ({ name: w.word, value: w.count, textStyle: { color: '#06d6a0' } })),
    ...negative.map((w) => ({ name: w.word, value: w.count, textStyle: { color: '#e63946' } })),
  ]

  if (!allWords.length) return null

  const option = {
    backgroundColor: 'transparent',
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      width: '100%',
      height: '100%',
      sizeRange: [14, 48],
      rotationRange: [-30, 30],
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = ['#e63946', '#ffd700', '#06d6a0', '#118ab2', '#f4a261', '#a8dadc']
          return colors[Math.floor(Math.random() * colors.length)]
        },
      },
      emphasis: { textStyle: { shadowBlur: 10, shadowColor: '#ffd700' } },
      data: allWords,
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
}
