const cache = new Map();
async function expectJson() { return { test: 1 }; }
async function fetchWithCache(key, url, refresh = false) {
  if (!refresh && cache.has(key)) return cache.get(key)
  const payload = await expectJson()
  cache.set(key, payload)
  return payload
}
async function run() {
  const res1 = await fetchWithCache('a', 'a');
  console.log(res1);
  const res2 = await fetchWithCache('a', 'a');
  console.log(res2);
}
run();
