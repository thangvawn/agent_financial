/**
 * Quanta Param Parser Utility (< 200 lines)
 * Hỗ trợ trích xuất tham số từ khối params Quanta DSL: `name = val [unit] in [min..max]`
 */

export function extractQuantaParams(code = '') {
  const params = [];
  const paramsSectionMatch = code.match(/params:\s*([\s\S]*?)(?=\n[a-z_@]+:|$)/i);
  if (!paramsSectionMatch) return params;

  const lines = paramsSectionMatch[1].split('\n');
  const dslRegex = /^\s*([a-zA-Z0-9_]+)\s*=\s*(\d+(?:\.\d+)?)(pct|bps|d)?\s+in\s+\[(\d+(?:\.\d+)?)(?:pct|bps|d)?\.\.(\d+(?:\.\d+)?)(?:pct|bps|d)?\]/;
  const yamlRegex = /^\s*([a-zA-Z0-9_]+)\s*:\s*([0-9.]+)/;

  for (const line of lines) {
    const dslMatch = line.match(dslRegex);
    if (dslMatch) {
      const [, name, val, unit, min, max] = dslMatch;
      params.push({
        name,
        value: parseFloat(val),
        unit: unit || '',
        min: parseFloat(min),
        max: parseFloat(max),
      });
      continue;
    }

    const yamlMatch = line.match(yamlRegex);
    if (yamlMatch) {
      const [, name, val] = yamlMatch;
      const numericVal = parseFloat(val);
      params.push({
        name,
        value: numericVal,
        unit: '',
        min: Math.floor(numericVal * 0.5),
        max: Math.ceil(numericVal * 2.5),
      });
    }
  }

  return params;
}

export function parseQuantaParams(code = '') {
  const extracted = extractQuantaParams(code);
  const result = {
    fast_period: 9,
    slow_period: 21,
    take_profit_pct: 8.0,
    stop_loss_pct: 4.0,
    trailing_stop: 2.5,
  };

  for (const item of extracted) {
    result[item.name] = item.value;
    if (item.name === 'fast_len') result.fast_period = item.value;
    if (item.name === 'slow_len') result.slow_period = item.value;
    if (item.name === 'take_profit') result.take_profit_pct = item.value;
    if (item.name === 'stop_loss') result.stop_loss_pct = item.value;
  }

  return result;
}

export function updateQuantaParamInCode(code, name, newValue) {
  const dslRegex = new RegExp(`(\\b${name}\\s*=\\s*)([0-9.]+)(pct|bps|d)?(\\s+in\\s+\\[)`);
  if (dslRegex.test(code)) {
    return code.replace(dslRegex, `$1${newValue}$3$4`);
  }

  const yamlRegex = new RegExp(`(\\b${name}\\s*:\\s*)([0-9.]+)`);
  if (yamlRegex.test(code)) {
    return code.replace(yamlRegex, `$1${newValue}`);
  }

  return code;
}
