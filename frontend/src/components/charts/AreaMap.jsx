import React, { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import * as echarts from 'echarts'

let mapRegistered = false

async function ensureMap() {
  if (mapRegistered) return
  try {
    const res = await fetch('/shanghai.geojson')
    const json = await res.json()
    echarts.registerMap('shanghai', json)
    mapRegistered = true
  } catch {
    // 地图文件不存在时静默失败
  }
}

export default function AreaMap({ data }) {
  const [ready, setReady] = useState(mapRegistered)

  useEffect(() => {
    if (!mapRegistered) {
      ensureMap().then(() => setReady(true))
    }
  }, [])

  if (!ready || !data?.length) return null

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>餐厅数量：{c}',
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.map((d) => d.value)),
      text: ['多', '少'],
      textStyle: { color: '#8b949e' },
      inRange: { color: ['#1a1a2e', '#e63946'] },
    },
    series: [{
      type: 'map',
      map: 'shanghai',
      roam: false,
      layoutCenter: ['50%', '49%'],
      layoutSize: '95%',
      label: { show: true, color: '#ffffff', fontSize: 10 },
      emphasis: { label: { color: '#ffd700' }, itemStyle: { areaColor: '#ffd700' } },
      data,
    }],
  }

  return <ReactECharts option={option} style={{ height: '100%', width: '100%' }} theme="dark" />
}
