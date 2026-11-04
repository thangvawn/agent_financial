import { createHeatmapLayoutEngine } from './marketHeatmapLayout'

const layout = createHeatmapLayoutEngine()
self.onmessage = event => {
  const { key, groups, width, height, options } = event.data
  try { self.postMessage({ key, layout: layout(groups, width, height, options) }) }
  catch (error) { self.postMessage({ key, error: error.message || 'Không dựng được bản đồ.' }) }
}
