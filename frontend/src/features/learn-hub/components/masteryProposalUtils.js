export function handleKeyDown(e, onReject) {
  if (e?.key === 'Escape' && typeof onReject === 'function') {
    e.preventDefault?.()
    onReject()
  }
}
