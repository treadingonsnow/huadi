import React, { useEffect, useState, useRef } from 'react'
import {
  Table, Tag, Select, Button, Space, Popconfirm, Badge, message, Input,
} from 'antd'
import {
  ReloadOutlined, DeleteOutlined, ArrowLeftOutlined, SyncOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getLogs, getTaskNames, clearLogs } from '@/api/logs'

const LEVEL_COLOR = { INFO: 'blue', WARNING: 'orange', ERROR: 'red' }
const STAGE_COLOR = {
  load: 'cyan', dedup: 'purple', normalize: 'geekblue',
  validate: 'gold', insert: 'green', hdfs: 'blue', hive: 'magenta',
}

export default function CleanLogs() {
  const navigate = useNavigate()
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [filterTask, setFilterTask] = useState(undefined)
  const [filterLevel, setFilterLevel] = useState(undefined)
  const [taskOptions, setTaskOptions] = useState([])
  const timerRef = useRef(null)

  const fetchLogs = async (p = page) => {
    setLoading(true)
    try {
      const res = await getLogs({
        page: p, page_size: 50,
        task_name: filterTask || undefined,
        level: filterLevel || undefined,
      })
      if (res.code === 200) {
        setLogs(res.data.items)
        setTotal(res.data.total)
        setPage(p)
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchTaskNames = async () => {
    const res = await getTaskNames()
    if (res.code === 200) {
      setTaskOptions(res.data.tasks.map((t) => ({ label: t, value: t })))
    }
  }

  useEffect(() => {
    fetchLogs(1)
    fetchTaskNames()
  }, [filterTask, filterLevel])

  useEffect(() => {
    if (autoRefresh) {
      timerRef.current = setInterval(() => fetchLogs(page), 3000)
    } else {
      clearInterval(timerRef.current)
    }
    return () => clearInterval(timerRef.current)
  }, [autoRefresh, page, filterTask, filterLevel])

  const handleClear = async () => {
    const res = await clearLogs(filterTask || undefined)
    if (res.code === 200) {
      message.success(`已删除 ${res.data.deleted} 条日志`)
      fetchLogs(1)
      fetchTaskNames()
    }
  }

  const columns = [
    {
      title: '时间', dataIndex: 'create_time', width: 160,
      render: (v) => <span style={{ color: '#8b949e', fontSize: 12 }}>{v}</span>,
    },
    {
      title: '任务', dataIndex: 'task_name', ellipsis: true, width: 180,
      render: (v) => <span style={{ color: '#c9d1d9', fontSize: 12 }}>{v}</span>,
    },
    {
      title: '阶段', dataIndex: 'stage', width: 90,
      render: (v) => v ? <Tag color={STAGE_COLOR[v] || 'default'} style={{ fontSize: 11 }}>{v}</Tag> : '-',
    },
    {
      title: '级别', dataIndex: 'level', width: 80,
      render: (v) => (
        <Badge status={v === 'INFO' ? 'processing' : v === 'WARNING' ? 'warning' : 'error'} />
      ),
    },
    {
      title: '日志内容', dataIndex: 'message',
      render: (v, row) => (
        <span style={{ color: row.level === 'ERROR' ? '#e63946' : row.level === 'WARNING' ? '#ffd700' : '#c9d1d9', fontSize: 13 }}>
          {v}
        </span>
      ),
    },
    {
      title: '记录数', dataIndex: 'record_count', width: 80,
      render: (v) => v != null ? <Tag color="green">{v}</Tag> : '-',
    },
  ]

  return (
    <div style={S.page}>
      <header style={S.header}>
        <Button type="text" icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard')} style={{ color: '#8b949e' }}>
          返回大屏
        </Button>
        <span style={S.headerTitle}>数据清洗日志</span>
        <span />
      </header>

      <div style={S.body}>
        {/* 工具栏 */}
        <div style={S.toolbar}>
          <Space wrap>
            <Select
              placeholder="筛选任务"
              allowClear
              style={{ width: 220 }}
              value={filterTask}
              onChange={(v) => { setFilterTask(v); setPage(1) }}
              options={taskOptions}
            />
            <Select
              placeholder="日志级别"
              allowClear
              style={{ width: 130 }}
              value={filterLevel}
              onChange={(v) => { setFilterLevel(v); setPage(1) }}
              options={[
                { label: '全部', value: undefined },
                { label: 'INFO', value: 'INFO' },
                { label: 'WARNING', value: 'WARNING' },
                { label: 'ERROR', value: 'ERROR' },
              ]}
            />
            <Button icon={<ReloadOutlined spin={loading} />} onClick={() => fetchLogs(1)}>
              刷新
            </Button>
            <Button
              icon={<SyncOutlined spin={autoRefresh} />}
              onClick={() => setAutoRefresh((v) => !v)}
              type={autoRefresh ? 'primary' : 'default'}
              style={autoRefresh ? { background: '#06d6a0', borderColor: '#06d6a0' } : {}}
            >
              {autoRefresh ? '自动刷新中（3s）' : '开启自动刷新'}
            </Button>
            <Popconfirm
              title={`确认清空${filterTask ? `「${filterTask}」的` : '全部'}日志？`}
              onConfirm={handleClear}
              okText="确认" cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />}>
                清空{filterTask ? '当前任务' : '全部'}日志
              </Button>
            </Popconfirm>
          </Space>
          <span style={{ color: '#8b949e', fontSize: 12 }}>共 {total} 条</span>
        </div>

        {/* 统计小卡片 */}
        <div style={S.statRow}>
          {Object.entries(LEVEL_COLOR).map(([level, color]) => {
            const cnt = logs.filter((l) => l.level === level).length
            return (
              <div key={level} style={S.statCard}>
                <Tag color={color} style={{ fontSize: 13, padding: '2px 10px' }}>{level}</Tag>
                <span style={{ color: '#c9d1d9', marginLeft: 8, fontWeight: 600 }}>{cnt}</span>
                <span style={{ color: '#8b949e', fontSize: 11, marginLeft: 2 }}>条（本页）</span>
              </div>
            )
          })}
        </div>

        <Table
          rowKey="id"
          columns={columns}
          dataSource={logs}
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 50,
            onChange: (p) => fetchLogs(p),
            showTotal: (t) => `共 ${t} 条`,
            style: { color: '#8b949e' },
          }}
          size="small"
          scroll={{ y: 520 }}
          style={{ background: 'transparent' }}
          className="dark-table"
          rowClassName={(row) =>
            row.level === 'ERROR' ? 'log-row-error' : row.level === 'WARNING' ? 'log-row-warning' : ''
          }
        />
      </div>
    </div>
  )
}

const S = {
  page: { minHeight: '100vh', background: '#0d1117', color: '#ffffff' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 24px', height: 56,
    background: '#161b22', borderBottom: '1px solid #30363d',
  },
  headerTitle: { fontSize: 16, fontWeight: 700, color: '#ffffff' },
  body: { maxWidth: 1400, margin: '0 auto', padding: '24px 16px' },
  toolbar: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 12, flexWrap: 'wrap', gap: 8,
  },
  statRow: { display: 'flex', gap: 12, marginBottom: 12 },
  statCard: {
    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 6, padding: '6px 14px', display: 'flex', alignItems: 'center',
  },
}
