import React, { useState } from 'react'
import {
  Upload, Button, Select, Form, Input,
  Steps, Alert, Descriptions, message, Tag,
} from 'antd'
import {
  InboxOutlined, DatabaseOutlined,
  CheckCircleOutlined, ArrowLeftOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Dragger } = Upload
const { Option } = Select

const DEST_OPTIONS = [
  {
    value: 'mysql',
    label: 'MySQL 数据库',
    icon: <DatabaseOutlined />,
    color: '#e63946',
    desc: '直接写入 restaurant_info 表，立即可用于图表展示',
  },
]

export default function DataImport() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [dest, setDest] = useState('mysql')
  const [fileList, setFileList] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (values) => {
    if (fileList.length === 0) {
      message.error('请先选择要上传的文件')
      return
    }
    setLoading(true)
    setResult(null)
    setError(null)

    const fd = new FormData()
    fd.append('file', fileList[0].originFileObj)
    fd.append('destination', dest)
    fd.append('task_name', values.task_name || '')

    try {
      const res = await fetch('/api/v1/import/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        body: fd,
      }).then((r) => r.json())

      if (res.code === 200) {
        setResult(res.data)
        message.success('导入成功！')
      } else {
        setError(res.message || '导入失败')
      }
    } catch (e) {
      setError('网络错误：' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const selectedDest = DEST_OPTIONS.find((d) => d.value === dest)

  return (
    <div style={S.page}>
      <header style={S.header}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard')}
          style={{ color: '#8b949e' }}
        >
          返回大屏
        </Button>
        <span style={S.headerTitle}>数据导入</span>
        <span />
      </header>

      <div style={S.body}>
        {/* 目标选择 */}
        <div style={S.section}>
          <div style={S.sectionTitle}>选择存储目标</div>
          <div style={S.destGrid}>
            {DEST_OPTIONS.map((opt) => (
              <div
                key={opt.value}
                onClick={() => setDest(opt.value)}
                style={{
                  ...S.destCard,
                  border: `2px solid ${dest === opt.value ? opt.color : 'rgba(255,255,255,0.1)'}`,
                  background: dest === opt.value ? `${opt.color}15` : 'rgba(255,255,255,0.03)',
                }}
              >
                <span style={{ fontSize: 28, color: opt.color }}>{opt.icon}</span>
                <div style={{ fontWeight: 600, color: '#ffffff', marginTop: 8 }}>{opt.label}</div>
                <div style={{ color: '#8b949e', fontSize: 12, marginTop: 4 }}>{opt.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={S.twoCol}>
          {/* 左：文件上传 + 表单 */}
          <div style={S.leftCol}>
            <div style={S.section}>
              <div style={S.sectionTitle}>上传数据文件</div>
              <Dragger
                accept=".csv,.json,.xlsx,.xls"
                maxCount={1}
                fileList={fileList}
                onChange={({ fileList: fl }) => setFileList(fl)}
                beforeUpload={() => false}
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.2)' }}
              >
                <p style={{ color: '#8b949e', fontSize: 32 }}><InboxOutlined /></p>
                <p style={{ color: '#ffffff' }}>点击或拖拽文件到此处</p>
                <p style={{ color: '#8b949e', fontSize: 12 }}>支持 CSV / JSON / Excel（.xlsx/.xls）</p>
              </Dragger>
            </div>

            <div style={S.section}>
              <div style={S.sectionTitle}>导入配置</div>
              <Form form={form} layout="vertical" onFinish={handleSubmit}>
                <Form.Item label={<span style={S.label}>任务名称（可选）</span>} name="task_name">
                  <Input placeholder="不填则自动生成" style={S.input} />
                </Form.Item>

                <Form.Item style={{ marginTop: 16 }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    block
                    size="large"
                    style={{ background: selectedDest?.color, borderColor: selectedDest?.color }}
                  >
                    {loading ? '导入中，请稍候…' : `开始导入到 ${selectedDest?.label}`}
                  </Button>
                </Form.Item>
              </Form>
            </div>
          </div>

          {/* 右：结果 */}
          <div style={S.rightCol}>
            <div style={S.section}>
              <div style={S.sectionTitle}>导入结果</div>
              {!result && !error && !loading && (
                <div style={{ color: '#8b949e', textAlign: 'center', padding: '40px 0' }}>
                  上传文件并点击「开始导入」后，结果将显示在此处
                </div>
              )}
              {loading && (
                <div style={{ color: '#ffd700', textAlign: 'center', padding: '40px 0' }}>
                  正在处理中，请查看底部清洗日志页面了解实时进度…
                </div>
              )}
              {error && (
                <Alert message="导入失败" description={error} type="error" showIcon />
              )}
              {result && (
                <>
                  <Alert
                    message="导入成功"
                    description={`任务：${result.task_name}`}
                    type="success"
                    showIcon
                    icon={<CheckCircleOutlined />}
                    style={{ marginBottom: 16 }}
                  />
                  <Descriptions column={1} bordered size="small"
                    labelStyle={{ color: '#8b949e', background: 'transparent' }}
                    contentStyle={{ color: '#ffffff', background: 'transparent' }}>
                    <Descriptions.Item label="目标存储">
                      <Tag color={selectedDest?.color}>{result.destination?.toUpperCase()}</Tag>
                    </Descriptions.Item>
                    {result.inserted !== undefined && (
                      <Descriptions.Item label="新增记录">{result.inserted} 条</Descriptions.Item>
                    )}
                    {result.skipped !== undefined && (
                      <Descriptions.Item label="跳过（已存在）">{result.skipped} 条</Descriptions.Item>
                    )}
                    {result.rows !== undefined && (
                      <Descriptions.Item label="上传行数">{result.rows} 条</Descriptions.Item>
                    )}
                  </Descriptions>
                  <Button
                    style={{ marginTop: 12 }}
                    onClick={() => navigate('/clean-logs')}
                  >
                    查看清洗日志
                  </Button>
                </>
              )}
            </div>

            <div style={S.section}>
              <div style={S.sectionTitle}>文件格式说明</div>
              <div style={{ color: '#8b949e', fontSize: 12, lineHeight: 2 }}>
                <div>支持字段（自动识别列名）：</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                  {['name/餐厅名称', 'address/地址', 'cuisine/菜系',
                    'district/行政区', 'avg_price/人均', 'rating/评分',
                    'review_count/评论数', 'phone/电话', 'business_area/商圈'].map((f) => (
                    <Tag key={f} color="default" style={{ fontSize: 11 }}>{f}</Tag>
                  ))}
                </div>
                <div style={{ marginTop: 8 }}>
                  清洗规则：自动去重 · 脱敏手机号 · 标准化 16 区名称 · 过滤空名称行
                </div>
              </div>
            </div>
          </div>
        </div>
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
  body: { maxWidth: 1200, margin: '0 auto', padding: '24px 16px' },
  section: {
    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8, padding: '16px 20px', marginBottom: 16,
  },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#ffd700', marginBottom: 12 },
  destGrid: { display: 'grid', gridTemplateColumns: 'repeat(1, 1fr)', gap: 12 },
  destCard: {
    padding: '16px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'center',
    transition: 'all 0.2s',
  },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  leftCol: {},
  rightCol: {},
  label: { color: '#8b949e', fontSize: 13 },
  input: { background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.15)', color: '#ffffff' },
}
