import React, { useEffect, useState } from 'react'
import {
  Button, Form, Select, InputNumber, Slider, Card,
  Statistic, Alert, Tag, Progress, Spin, Divider, message,
} from 'antd'
import {
  ExperimentOutlined, ThunderboltOutlined, RobotOutlined, ArrowLeftOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getModelInfo, trainModel, predictRating } from '@/api/ml'

const CUISINES = ['川菜', '本帮菜', '日料', '火锅', '粤菜', '西餐', '烧烤', '面食', '海鲜', '台湾菜', '北京菜', '甜品饮品']
const DISTRICTS = ['浦东新区', '黄浦区', '徐汇区', '静安区', '长宁区', '普陀区', '虹口区', '杨浦区', '闵行区', '宝山区', '嘉定区', '松江区', '青浦区', '奉贤区', '金山区', '崇明区']

export default function Predict() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [modelInfo, setModelInfo] = useState(null)
  const [training, setTraining] = useState(false)
  const [predicting, setPredicting] = useState(false)
  const [prediction, setPrediction] = useState(null)
  const [predError, setPredError] = useState(null)

  const loadInfo = () => {
    getModelInfo().then((res) => res.code === 200 && setModelInfo(res.data))
  }

  useEffect(() => { loadInfo() }, [])

  const handleTrain = async () => {
    setTraining(true)
    setPrediction(null)
    try {
      const res = await trainModel()
      if (res.code === 200) {
        message.success(`训练完成！R² = ${res.data.r2}，RMSE = ${res.data.rmse}`)
        setModelInfo({ trained: true, ...res.data })
      } else {
        message.error(res.message || '训练失败')
      }
    } catch {
      message.error('训练请求失败')
    } finally {
      setTraining(false)
    }
  }

  const handlePredict = async (values) => {
    setPredicting(true)
    setPrediction(null)
    setPredError(null)
    try {
      const res = await predictRating(values)
      if (res.code === 200) {
        setPrediction(res.data)
      } else {
        setPredError(res.message || '预测失败')
      }
    } catch {
      setPredError('网络错误')
    } finally {
      setPredicting(false)
    }
  }

  const ratingColor = (r) => {
    if (r >= 4.5) return '#06d6a0'
    if (r >= 4.0) return '#ffd700'
    if (r >= 3.5) return '#ff9f1c'
    return '#e63946'
  }

  const ratingLabel = (r) => {
    if (r >= 4.5) return '优秀'
    if (r >= 4.0) return '良好'
    if (r >= 3.5) return '一般'
    return '偏低'
  }

  const availableCuisines = modelInfo?.available_cuisines?.length > 0
    ? modelInfo.available_cuisines
    : CUISINES
  const availableDistricts = modelInfo?.available_districts?.length > 0
    ? modelInfo.available_districts
    : DISTRICTS

  return (
    <div style={S.page}>
      <header style={S.header}>
        <Button type="text" icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/dashboard')} style={{ color: '#8b949e' }}>
          返回大屏
        </Button>
        <span style={S.headerTitle}><RobotOutlined /> 机器学习评分预测</span>
        <span />
      </header>

      <div style={S.body}>
        {/* 模型状态卡 */}
        <div style={S.modelCard}>
          <div style={S.sectionTitle}>模型状态</div>
          {!modelInfo ? (
            <Spin />
          ) : modelInfo.trained ? (
            <div style={S.statsRow}>
              <div style={S.statItem}>
                <div style={S.statVal}>{modelInfo.r2}</div>
                <div style={S.statLabel}>R² 决定系数</div>
                <div style={{ color: '#8b949e', fontSize: 11 }}>越接近 1 越好</div>
              </div>
              <div style={S.statItem}>
                <div style={S.statVal}>{modelInfo.rmse}</div>
                <div style={S.statLabel}>RMSE 均方根误差</div>
                <div style={{ color: '#8b949e', fontSize: 11 }}>误差（分制）</div>
              </div>
              <div style={S.statItem}>
                <div style={S.statVal}>{modelInfo.sample_count?.toLocaleString()}</div>
                <div style={S.statLabel}>训练样本数</div>
                <div style={{ color: '#8b949e', fontSize: 11 }}>条有效餐厅数据</div>
              </div>
              {modelInfo.feature_importances && (
                <div style={S.statItem}>
                  <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 8 }}>特征重要性</div>
                  {Object.entries(modelInfo.feature_importances).map(([k, v]) => (
                    <div key={k} style={{ marginBottom: 4 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c9d1d9', fontSize: 12 }}>
                        <span>{k}</span><span>{(v * 100).toFixed(1)}%</span>
                      </div>
                      <Progress
                        percent={v * 100} showInfo={false} size="small"
                        strokeColor="#e63946" trailColor="rgba(255,255,255,0.1)"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <Alert
              message="模型尚未训练"
              description="点击下方「训练模型」按钮，基于数据库中的餐厅数据训练随机森林回归模型。"
              type="info" showIcon
              style={{ background: 'rgba(17,138,178,0.1)', border: '1px solid rgba(17,138,178,0.3)' }}
            />
          )}
          <Button
            icon={<ThunderboltOutlined />}
            onClick={handleTrain}
            loading={training}
            style={{ marginTop: 16, background: '#e63946', borderColor: '#e63946', color: '#fff' }}
          >
            {training ? '训练中…' : modelInfo?.trained ? '重新训练模型' : '训练模型'}
          </Button>
          <span style={{ color: '#8b949e', fontSize: 12, marginLeft: 12 }}>
            算法：随机森林回归（n_estimators=100）·&nbsp;特征：菜系 + 区域 + 人均消费 → 预测评分
          </span>
        </div>

        <div style={S.twoCol}>
          {/* 预测表单 */}
          <div style={S.section}>
            <div style={S.sectionTitle}><ExperimentOutlined /> 输入餐厅特征</div>
            <Form form={form} layout="vertical" onFinish={handlePredict}>
              <Form.Item
                label={<span style={S.label}>菜系类型</span>}
                name="cuisine_type"
                rules={[{ required: true, message: '请选择菜系' }]}
              >
                <Select placeholder="选择菜系" style={S.select}
                  options={availableCuisines.map((c) => ({ label: c, value: c }))} />
              </Form.Item>
              <Form.Item
                label={<span style={S.label}>所在区域</span>}
                name="district"
                rules={[{ required: true, message: '请选择区域' }]}
              >
                <Select placeholder="选择行政区" style={S.select}
                  options={availableDistricts.map((d) => ({ label: d, value: d }))} />
              </Form.Item>
              <Form.Item
                label={<span style={S.label}>人均消费（元）</span>}
                name="avg_price"
                rules={[{ required: true, message: '请输入人均消费' }]}
              >
                <InputNumber
                  min={5} max={2000} step={10} placeholder="例如 85"
                  style={{ ...S.select, width: '100%' }}
                />
              </Form.Item>
              <Form.Item style={{ marginTop: 8 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={predicting}
                  block size="large"
                  disabled={!modelInfo?.trained}
                  style={{ background: '#e63946', borderColor: '#e63946' }}
                >
                  {predicting ? '预测中…' : '预测评分'}
                </Button>
                {!modelInfo?.trained && (
                  <div style={{ color: '#8b949e', fontSize: 12, textAlign: 'center', marginTop: 6 }}>
                    请先训练模型
                  </div>
                )}
              </Form.Item>
            </Form>
          </div>

          {/* 预测结果 */}
          <div style={S.section}>
            <div style={S.sectionTitle}>预测结果</div>
            {predError && <Alert message={predError} type="error" showIcon style={{ marginBottom: 12 }} />}
            {predicting && <div style={{ textAlign: 'center', padding: '40px 0' }}><Spin size="large" /></div>}
            {prediction && !predicting && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 72, fontWeight: 800, color: ratingColor(prediction.predicted_rating), lineHeight: 1, marginBottom: 8 }}>
                  {prediction.predicted_rating}
                </div>
                <Tag color={ratingColor(prediction.predicted_rating)} style={{ fontSize: 14, padding: '4px 12px' }}>
                  {ratingLabel(prediction.predicted_rating)}
                </Tag>
                <div style={{ color: '#8b949e', fontSize: 13, marginTop: 12 }}>
                  预测区间：{prediction.confidence_low} ~ {prediction.confidence_high} 分
                </div>
                <Divider style={{ borderColor: 'rgba(255,255,255,0.1)' }} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div style={S.miniStat}>
                    <div style={S.miniVal}>{prediction.model_r2}</div>
                    <div style={S.miniLabel}>模型 R²</div>
                  </div>
                  <div style={S.miniStat}>
                    <div style={S.miniVal}>{prediction.model_rmse}</div>
                    <div style={S.miniLabel}>模型 RMSE</div>
                  </div>
                </div>
                <div style={{ color: '#8b949e', fontSize: 11, marginTop: 12 }}>
                  基于 {prediction.sample_count?.toLocaleString()} 条数据训练的随机森林模型
                </div>
              </div>
            )}
            {!prediction && !predicting && !predError && (
              <div style={{ color: '#8b949e', textAlign: 'center', padding: '60px 0' }}>
                填写左侧特征后点击「预测评分」
              </div>
            )}
          </div>
        </div>

        {/* 说明 */}
        <div style={{ ...S.section, background: 'rgba(255,215,0,0.05)', border: '1px solid rgba(255,215,0,0.2)' }}>
          <div style={{ color: '#ffd700', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>模型说明</div>
          <div style={{ color: '#8b949e', fontSize: 12, lineHeight: 2 }}>
            • 算法：随机森林回归（Random Forest Regressor），100 棵决策树集成<br />
            • 输入特征：菜系类型（类别编码）、所属行政区（类别编码）、人均消费（数值）<br />
            • 预测目标：餐厅综合评分（1.0 - 5.0 分）<br />
            • 置信区间：所有决策树预测值的标准差，反映预测的不确定性<br />
            • 注意：模型精度受数据量和数据质量影响，仅供参考
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
  body: { maxWidth: 1100, margin: '0 auto', padding: '24px 16px' },
  section: {
    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8, padding: '16px 20px', marginBottom: 16,
  },
  modelCard: {
    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 8, padding: '16px 20px', marginBottom: 16,
  },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#ffd700', marginBottom: 12 },
  statsRow: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 },
  statItem: { textAlign: 'center' },
  statVal: { fontSize: 28, fontWeight: 700, color: '#06d6a0' },
  statLabel: { color: '#c9d1d9', fontSize: 12, marginTop: 4 },
  twoCol: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  label: { color: '#8b949e', fontSize: 13 },
  select: { background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.15)' },
  miniStat: { background: 'rgba(255,255,255,0.04)', borderRadius: 6, padding: '8px 0' },
  miniVal: { fontSize: 20, fontWeight: 700, color: '#ffd700' },
  miniLabel: { color: '#8b949e', fontSize: 11, marginTop: 2 },
}
