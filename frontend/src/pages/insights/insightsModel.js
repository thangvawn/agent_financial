export const DEFAULT_INSIGHTS = {
  marketSummary: {
    regime: 'Cautious',
    riskLevel: 'Watch',
    crossAssetTheme: 'Rates & USD',
    topDriver: 'USD Strength',
    alertsCount: 2,
    summary:
      'Thị trường đang ở trạng thái thận trọng do sức mạnh của USD và áp lực lãi suất duy trì ở mức cao. Dòng tiền có xu hướng chọn lọc, ưu tiên chất lượng và phòng thủ.',
  },
  narrative: {
    confidence: 'High',
    bullets: [
      'USD duy trì mạnh khi kỳ vọng Fed chưa sớm hạ lãi suất, gây áp lực lên tỷ giá và dòng vốn ngoại.',
      'Lợi suất trái phiếu Mỹ tăng trở lại, kéo mặt bằng lãi suất toàn cầu đi lên, ảnh hưởng nhóm tăng trưởng.',
      'Dòng tiền trong nước thận trọng, tập trung vào nhóm phòng thủ và cổ phiếu cơ bản tốt.',
    ],
    monitors: ['Dữ liệu CPI Mỹ', 'Diễn biến USD Index', 'Diễn biến lợi suất US 10Y', 'Dòng vốn ETF'],
  },
  trendRadar: [
    { key: 'fx', label: 'FX Pressure', value: 'USD/VND ↑ 0.18%', status: 'Elevated', note: 'USD mạnh, áp lực tỷ giá', series: [42, 48, 45, 54, 58, 62, 59, 66] },
    { key: 'rates', label: 'Rates (US 10Y)', value: '4.48% ↑ 7bps', status: 'Elevated', note: 'Lợi suất tăng, áp lực định giá', series: [48, 50, 52, 56, 55, 59, 62, 64] },
    { key: 'energy', label: 'Energy (Oil)', value: '$83.2 ↓ 0.7%', status: 'Mixed', note: 'Nguồn cung ổn định, nhu cầu yếu', series: [58, 55, 59, 53, 50, 48, 49, 46] },
    { key: 'breadth', label: 'Equity Breadth', value: '52%', status: 'Neutral', note: 'Độ rộng trung tính, phân hóa', series: [45, 49, 52, 51, 54, 52, 50, 52] },
    { key: 'liquidity', label: 'Liquidity (Funding)', value: 'Ổn định', status: 'Adequate', note: 'Thanh khoản hệ thống dồi dào', series: [55, 55, 56, 56, 57, 57, 58, 58] },
  ],
  crossAssetSeries: [
    { key: 'vn_index', label: 'VN-Index', color: '#0d8a82', latest: '+3.2%', values: [100, 101, 100.8, 102, 102.4, 103.1, 102.7, 103.2] },
    { key: 'usd_vnd', label: 'USD/VND', color: '#2877bd', latest: '+0.6%', values: [100, 100.2, 100.1, 100.4, 100.5, 100.4, 100.7, 100.6] },
    { key: 'gold', label: 'Gold (USD/oz)', color: '#d08a24', latest: '+7.1%', values: [100, 101.2, 102.1, 102.7, 103.4, 104.1, 105.4, 107.1] },
    { key: 'oil', label: 'Oil (USD/bbl)', color: '#6a58c8', latest: '-4.3%', values: [100, 97.6, 95.2, 93.8, 92.5, 94.2, 93.3, 95.7] },
    { key: 'us10y', label: 'US 10Y Yield', color: '#b35c4f', latest: '+1.5%', values: [100, 100.4, 100.9, 101.1, 100.8, 101.4, 101.2, 101.5] },
  ],
  scenarios: [
    { key: 'base', name: 'Base Case', summary: 'Tăng trưởng chậm lại, lạm phát hạ nhiệt dần', probability: 50, impact: 'Medium' },
    { key: 'fx', name: 'FX Stress', summary: 'USD mạnh lên, dòng vốn rút khỏi EM', probability: 25, impact: 'High' },
    { key: 'rates', name: 'Rate Shock', summary: 'Lợi suất tăng nhanh, thanh khoản thắt chặt', probability: 15, impact: 'High' },
    { key: 'risk_off', name: 'Risk-off', summary: 'Tăng trưởng suy yếu, rủi ro địa chính trị', probability: 7, impact: 'High' },
    { key: 'commodity', name: 'Commodity Spike', summary: 'Giá hàng hóa tăng đột biến, lạm phát quay lại', probability: 3, impact: 'Medium' },
  ],
  sectors: [
    { sector: 'Banks', view: 'Tích cực', score: 68 },
    { sector: 'Real Estate', view: 'Tiêu cực', score: 34 },
    { sector: 'Retail', view: 'Trung tính', score: 51 },
    { sector: 'Energy', view: 'Trung tính', score: 55 },
    { sector: 'Technology', view: 'Tích cực', score: 72 },
  ],
  watchlistImpact: [
    { ticker: 'VCB', theme: 'Rates-sensitive', level: 'Medium', note: 'Lợi suất tăng, NIM chịu áp lực' },
    { ticker: 'MWG', theme: 'Consumer demand', level: 'Low', note: 'Tiêu dùng hồi phục chậm' },
    { ticker: 'DGC', theme: 'FX-sensitive', level: 'High', note: 'USD mạnh, chi phí đầu vào cao' },
    { ticker: 'HPG', theme: 'Commodity price', level: 'Medium', note: 'Thép phục hồi nhưng chậm' },
  ],
  learnLinks: [
    { id: 'risk-on-off', title: 'Risk-on / Risk-off là gì?', subtext: 'Hiểu cách dòng tiền chuyển dịch theo rủi ro.', duration: '7 phút đọc' },
    { id: 'fx-impact', title: 'Tỷ giá ảnh hưởng thị trường thế nào?', subtext: 'Tác động của USD/VND tới cổ phiếu và vĩ mô.', duration: '6 phút đọc' },
    { id: 'rates-impact', title: 'Lãi suất tăng ảnh hưởng cổ phiếu ra sao?', subtext: 'Góc nhìn định giá và lợi nhuận doanh nghiệp.', duration: '6 phút đọc' },
  ],
  macroEvents: [
    { date: '25/06', name: 'US Core PCE (MoM)', impact: 'Cao' },
    { date: '27/06', name: 'GDP Việt Nam Q2/2025', impact: 'Trung bình' },
    { date: '01/07', name: 'FOMC Minutes', impact: 'Cao' },
    { date: '04/07', name: 'US Nonfarm Payrolls', impact: 'Cao' },
  ],
}

export function adaptDashboard(payload) {
  if (!payload) return DEFAULT_INSIGHTS
  return {
    ...DEFAULT_INSIGHTS,
    marketSummary: {
      ...DEFAULT_INSIGHTS.marketSummary,
      regime: titleCase(payload.market_summary?.regime?.replaceAll('_', ' ')) || DEFAULT_INSIGHTS.marketSummary.regime,
      riskLevel: titleCase(payload.market_summary?.risk_level) || DEFAULT_INSIGHTS.marketSummary.riskLevel,
      crossAssetTheme: payload.market_summary?.cross_asset_theme || DEFAULT_INSIGHTS.marketSummary.crossAssetTheme,
      topDriver: payload.market_summary?.top_driver || DEFAULT_INSIGHTS.marketSummary.topDriver,
      alertsCount: payload.market_summary?.alerts_count ?? DEFAULT_INSIGHTS.marketSummary.alertsCount,
      summary: payload.market_summary?.summary || DEFAULT_INSIGHTS.marketSummary.summary,
    },
    narrative: {
      ...DEFAULT_INSIGHTS.narrative,
      bullets: payload.market_narrative?.key_points?.length ? payload.market_narrative.key_points : DEFAULT_INSIGHTS.narrative.bullets,
      confidence: titleCase(payload.market_narrative?.confidence) || DEFAULT_INSIGHTS.narrative.confidence,
      monitors: payload.market_narrative?.what_to_monitor?.length ? payload.market_narrative.what_to_monitor : DEFAULT_INSIGHTS.narrative.monitors,
    },
    crossAssetSeries: payload.cross_asset_pulse?.series?.length
      ? payload.cross_asset_pulse.series.slice(0, 5).map((item, index) => ({
        key: item.asset_key,
        label: item.label,
        color: DEFAULT_INSIGHTS.crossAssetSeries[index]?.color || '#0d8a82',
        latest: `${item.latest_change_pct > 0 ? '+' : ''}${item.latest_change_pct}%`,
        values: item.values.map((point) => point.normalized_value),
      }))
      : DEFAULT_INSIGHTS.crossAssetSeries,
  }
}

function titleCase(value = '') {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : ''
}
