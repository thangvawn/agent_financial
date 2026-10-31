import {paginateNotebookText} from './bookReaderModel'

function createMeasurement(textarea) {
  const mirror = textarea.cloneNode(false)
  mirror.removeAttribute('id')
  mirror.removeAttribute('placeholder')
  mirror.setAttribute('aria-hidden', 'true')
  mirror.tabIndex = -1
  Object.assign(mirror.style, {
    position: 'fixed', left: '-100000px', top: '0', visibility: 'hidden',
    width: `${textarea.getBoundingClientRect().width}px`,
    height: `${textarea.getBoundingClientRect().height}px`,
    minHeight: '0', maxHeight: 'none', pointerEvents: 'none',
  })
  // Keep scoped paper typography/padding, including mobile styles.
  textarea.parentElement.appendChild(mirror)
  return mirror
}

export function paginatePaperInput(textarea) {
  if (!textarea.clientHeight || !textarea.clientWidth) return [textarea.value]
  const mirror = createMeasurement(textarea)
  try {
    return paginateNotebookText(textarea.value, value => {
      mirror.value = value
      return mirror.scrollHeight <= mirror.clientHeight + 1
    })
  } finally { mirror.remove() }
}

export function notebookCaretTop(textarea, offset) {
  const mirror = createMeasurement(textarea)
  try {
    mirror.style.height = '0px'
    mirror.value = textarea.value.slice(0, offset) || ' '
    const style = getComputedStyle(mirror)
    return mirror.scrollHeight - parseFloat(style.paddingBottom) - parseFloat(style.lineHeight)
  } finally { mirror.remove() }
}
