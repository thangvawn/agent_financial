import { useEffect, useState } from 'react'

import ProductModuleShell from '../../../shared/ui/ProductModuleShell'
import {
  archiveProLabBlueprint,
  compareProLabBlueprints,
  createProLabBlueprint,
  fetchProLabWorkspace,
  issueProLabAccessToken,
  runProLabBacktest,
  updateProLabBlueprint,
} from '../services/proLabApi'
import ProLabBlueprintsPage from './ProLabBlueprintsPage'
import ProLabExperimentsPage from './ProLabExperimentsPage'
import SimLabAnalyticsPage from './SimLabAnalyticsPage'

const DEFAULT_STRATEGY = {
  name: 'VN Quality Rotation',
  objective: 'Quy tắc mua/bán giả lập để thực hành kỷ luật rủi ro, không phải tín hiệu mua bán.',
  asset_universe: 'FPT,VCB,MWG',
  benchmark: 'VNINDEX',
  rebalance_frequency: 'monthly',
  risk_constraints: 'Max concentration 35%, cắt lỗ khi drawdown vượt ngưỡng',
  assumptions_note: 'Chỉ dùng cho Simulation Lab giáo dục.',
}

const TABS = [
  { id: 'strategy', label: 'Xây quy tắc' },
  { id: 'scenarios', label: 'Kịch bản lịch sử' },
  { id: 'analytics', label: 'Đọc kết quả' },
]

export default function ProLabPage({ sessionId, onBack, onOpenBacktestStudio }) {
  const [tab, setTab] = useState('strategy')
  const [accessToken, setAccessToken] = useState(() => window.localStorage.getItem('pro_lab.access_token') || '')
  const [workspace, setWorkspace] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(DEFAULT_STRATEGY)
  const [selectedBlueprintId, setSelectedBlueprintId] = useState('')
  const [compareRightId, setCompareRightId] = useState('')
  const [compareResult, setCompareResult] = useState(null)
  const [lastRun, setLastRun] = useState(null)

  useEffect(() => {
    window.localStorage.setItem('pro_lab.access_token', accessToken)
  }, [accessToken])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError('')
      try {
        if (!accessToken) {
          setWorkspace(null)
          return
        }
        const ws = await fetchProLabWorkspace(sessionId, accessToken)
        if (!cancelled) setWorkspace(ws)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Không tải được Simulation Lab')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [sessionId, accessToken])

  async function handleIssueToken() {
    setError('')
    try {
      const payload = await issueProLabAccessToken(sessionId)
      setAccessToken(payload.access_token)
    } catch (err) {
      setError(err.message || 'Không cấp được quyền vào Lab')
    }
  }

  async function reloadWorkspace() {
    if (!accessToken) return
    const ws = await fetchProLabWorkspace(sessionId, accessToken)
    setWorkspace(ws)
  }

  async function handleSaveBlueprint() {
    if (!accessToken) return
    setError('')
    try {
      await createProLabBlueprint(toStrategyPayload(sessionId, form), accessToken)
      await reloadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi lưu chiến lược')
    }
  }

  async function handleUpdateBlueprint(blueprintId, patch) {
    if (!accessToken) return
    setError('')
    try {
      await updateProLabBlueprint(blueprintId, toStrategyPayload(sessionId, { ...form, ...patch }), accessToken)
      await reloadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi cập nhật chiến lược')
    }
  }

  async function handleArchiveBlueprint(blueprintId) {
    if (!accessToken) return
    setError('')
    try {
      await archiveProLabBlueprint(blueprintId, sessionId, accessToken)
      await reloadWorkspace()
    } catch (err) {
      setError(err.message || 'Lỗi lưu trữ chiến lược')
    }
  }

  async function handleCompareBlueprints() {
    if (!accessToken || !selectedBlueprintId || !compareRightId) return
    setError('')
    try {
      setCompareResult(await compareProLabBlueprints(sessionId, selectedBlueprintId, compareRightId, accessToken))
    } catch (err) {
      setError(err.message || 'Lỗi so sánh chiến lược')
    }
  }

  async function handleScenarioRun(blueprintId, start, end, label) {
    if (!accessToken || !blueprintId) return
    setError('')
    try {
      const payload = await runProLabBacktest({
        user_id: sessionId,
        blueprint_id: blueprintId,
        start_date: start,
        end_date: end,
        initial_capital: 100000,
      }, accessToken)
      setLastRun({ type: 'scenario', label, start, end, payload })
      setTab('analytics')
    } catch (err) {
      setError(err.message || 'Lỗi chạy kịch bản lịch sử')
    }
  }

  function openReplay() {
    onOpenBacktestStudio?.({
      selectedBlueprintId,
      workspace,
      accessToken,
    })
  }

  return (
    <ProductModuleShell
      domain="simulation_lab"
      tone="pro"
      eyebrow="Simulation Lab"
      title="Backtest & thực hành chiến lược"
      subtitle="Biến một giả thuyết thành quy tắc, thử trên dữ liệu quá khứ và học từ rủi ro."
      learning={{
        objective: 'Hiểu cách quy tắc đầu tư phản ứng trong nhiều giai đoạn thị trường.',
        practice: 'Viết điều kiện, chạy lại dữ liệu và đọc lợi nhuận cùng mức sụt giảm.',
        riskNote: 'Kết quả quá khứ không dự báo kết quả tương lai. Phí, trượt giá và thanh khoản có thể làm kết quả thực tế khác biệt.',
      }}
      tabs={TABS}
      activeTab={tab}
      onTabChange={setTab}
      actions={(
        <>
          <button type="button" className="pm-btn" onClick={openReplay} disabled={!accessToken}>Tua dữ liệu</button>
          <button type="button" className="pm-btn" onClick={onBack}>Về trang chủ</button>
        </>
      )}
    >
      {!accessToken ? (
        <div className="mp-empty" style={{ borderColor: 'rgba(45,212,191,0.35)', background: 'rgba(45,212,191,0.08)', color: '#8eaea8' }}>
          <p style={{ margin: '0 0 12px' }}>Cần mở workspace giả lập trước khi dựng chiến lược và chạy lại lịch sử.</p>
          <button type="button" className="pm-btn pm-btn--primary" onClick={handleIssueToken}>
            Mở phòng mô phỏng
          </button>
        </div>
      ) : null}

      {loading ? <p className="text-xs" style={{ color: '#8eaea8' }}>Đang tải…</p> : null}
      {error ? <p className="mp-empty" style={{ color: '#fda4af', borderColor: 'rgba(244,63,94,0.35)' }}>{error}</p> : null}

      {tab === 'strategy' ? (
        <ProLabBlueprintsPage
          form={form}
          setForm={setForm}
          selectedBlueprintId={selectedBlueprintId}
          setSelectedBlueprintId={setSelectedBlueprintId}
          compareRightId={compareRightId}
          setCompareRightId={setCompareRightId}
          compareResult={compareResult}
          workspace={workspace}
          onSaveBlueprint={handleSaveBlueprint}
          onUpdateBlueprint={handleUpdateBlueprint}
          onArchiveBlueprint={handleArchiveBlueprint}
          onCompareBlueprints={handleCompareBlueprints}
        />
      ) : null}

      {tab === 'scenarios' ? (
        <ProLabExperimentsPage
          workspace={workspace}
          selectedBlueprintId={selectedBlueprintId}
          onScenarioRun={handleScenarioRun}
          onOpenReplay={openReplay}
        />
      ) : null}

      {tab === 'analytics' ? (
        <SimLabAnalyticsPage lastRun={lastRun} workspace={workspace} onOpenReplay={openReplay} />
      ) : null}
    </ProductModuleShell>
  )
}

function toStrategyPayload(sessionId, form) {
  const universe = Array.isArray(form.asset_universe)
    ? form.asset_universe
    : String(form.asset_universe || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  return {
    user_id: sessionId,
    name: form.name,
    objective: form.objective,
    asset_universe: universe,
    benchmark: form.benchmark,
    rebalance_frequency: form.rebalance_frequency,
    risk_constraints: form.risk_constraints,
    assumptions_note: form.assumptions_note || null,
  }
}
