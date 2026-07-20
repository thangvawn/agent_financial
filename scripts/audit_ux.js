/**
 * UX Audit Script — Northstar Frontend
 * Routes: /markets, /learn, /bctc, /news, /simulation-lab
 * Viewports: Desktop 1440x900, Mobile 390x844
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:8000/dashboard-static';
const ROUTES = [
  { path: '#/markets', name: 'markets' },
  { path: '#/learn', name: 'learn' },
  { path: '#/bctc', name: 'bctc' },
  { path: '#/news', name: 'news' },
  { path: '#/simulation-lab', name: 'simulation-lab' },
];
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844, isMobile: true },
];

const OUT_DIR = path.join(__dirname, '..', 'output', 'ux-audit');
fs.mkdirSync(OUT_DIR, { recursive: true });

const findings = [];

function log(route, viewport, category, severity, finding, recommendation) {
  findings.push({ route, viewport, category, severity, finding, recommendation });
  console.log(`[${severity}] [${viewport}] ${route} — ${category}: ${finding}`);
}

async function auditRoute(page, routeInfo, vpName, isMobile) {
  const url = `${BASE_URL}/${routeInfo.path}`;
  const { name } = routeInfo;

  await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 }).catch(() => {
    log(name, vpName, 'Load', 'CRITICAL', 'Page failed to load / network error', 'Ensure dev server is running at port 8001');
  });

  // Give time for React to hydrate
  await page.waitForTimeout(1500);

  // Screenshot — full page
  const ssPath = path.join(OUT_DIR, `${name}-${vpName}.png`);
  await page.screenshot({ path: ssPath, fullPage: true });
  console.log(`  📸 Screenshot: ${ssPath}`);

  // ── 1. Page title / heading hierarchy ──────────────────────────────────
  const h1Count = await page.locator('h1').count();
  const h2Count = await page.locator('h2').count();
  if (h1Count === 0) {
    log(name, vpName, 'Information Hierarchy', 'HIGH',
      'No <h1> found — screen readers and SEO have no primary heading',
      'Add a single descriptive <h1> as the first content landmark on this page');
  } else if (h1Count > 1) {
    log(name, vpName, 'Information Hierarchy', 'MEDIUM',
      `${h1Count} <h1> elements found — multiple page titles confuse screen readers`,
      'Keep exactly one <h1> per page/view');
  }

  // ── 2. Interactive element touch target size ────────────────────────────
  if (isMobile) {
    const buttons = page.locator('button, a, [role="button"], [role="link"]');
    const btnCount = await buttons.count();
    let smallTargets = 0;
    for (let i = 0; i < Math.min(btnCount, 40); i++) {
      try {
        const box = await buttons.nth(i).boundingBox({ timeout: 500 });
        if (box && (box.width < 44 || box.height < 44)) smallTargets++;
      } catch (_) {}
    }
    if (smallTargets > 0) {
      log(name, vpName, 'Touch Targets', 'HIGH',
        `${smallTargets} of ${Math.min(btnCount, 40)} sampled interactive elements are below 44×44px (WCAG 2.5.5)`,
        'Set min-height/min-width: 44px (or 48px for Material) on all tappable elements');
    }
  }

  // ── 3. Images with alt text ─────────────────────────────────────────────
  const imgNoAlt = await page.locator('img:not([alt])').count();
  const imgEmptyAlt = await page.locator('img[alt=""]').count();
  if (imgNoAlt > 0) {
    log(name, vpName, 'Accessibility', 'HIGH',
      `${imgNoAlt} <img> element(s) missing alt attribute`,
      'Add descriptive alt text to informative images; alt="" for decorative ones');
  }

  // ── 4. Form labels ──────────────────────────────────────────────────────
  const inputsNoLabel = await page.evaluate(() => {
    const inputs = [...document.querySelectorAll('input:not([type="hidden"]), select, textarea')];
    return inputs.filter(el => {
      const id = el.id;
      const hasLabel = id && document.querySelector(`label[for="${id}"]`);
      const hasAriaLabel = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      const hasPlaceholderOnly = el.placeholder && !hasLabel && !hasAriaLabel;
      return !hasLabel && !hasAriaLabel;
    }).length;
  });
  if (inputsNoLabel > 0) {
    log(name, vpName, 'Accessibility', 'HIGH',
      `${inputsNoLabel} input(s) have no associated <label> or aria-label`,
      'Add <label for="..."> or aria-label to every form control');
  }

  // ── 5. Focus outline / keyboard navigation ──────────────────────────────
  const focusOutlineIssues = await page.evaluate(() => {
    const focusable = [...document.querySelectorAll('button, a, input, select, textarea, [tabindex]')];
    let noOutline = 0;
    for (const el of focusable.slice(0, 20)) {
      const style = window.getComputedStyle(el, ':focus');
      const outline = style.outline;
      const boxShadow = style.boxShadow;
      if ((outline === 'none' || outline === '0px none rgb(0, 0, 0)' || outline.startsWith('0px')) &&
          (boxShadow === 'none' || boxShadow === '')) {
        noOutline++;
      }
    }
    return noOutline;
  });
  // Note: computed :focus styles in headless are unreliable; report if many
  if (focusOutlineIssues > 10) {
    log(name, vpName, 'Keyboard / Focus', 'MEDIUM',
      `Many focusable elements appear to have no visible focus ring (${focusOutlineIssues}/20 sampled)`,
      'Ensure :focus-visible styles are applied globally; do not suppress outline without a custom alternative');
  }

  // ── 6. Loading / skeleton states ───────────────────────────────────────
  const skeletonOrSpinner = await page.locator('[class*="skeleton"], [class*="spinner"], [class*="loading"], [role="progressbar"], [aria-busy="true"]').count();
  const emptyState = await page.locator('[class*="empty"], [class*="no-data"], [class*="placeholder"]').count();

  // ── 7. Horizontal overflow (mobile) ────────────────────────────────────
  if (isMobile) {
    const hasHorizScroll = await page.evaluate(() => document.body.scrollWidth > window.innerWidth);
    if (hasHorizScroll) {
      log(name, vpName, 'Responsive Overflow', 'HIGH',
        `Body scrollWidth (${document.body ? 'check' : 'N/A'}) exceeds viewport width — horizontal scrollbar present`,
        'Audit elements wider than 100vw; use overflow-x: hidden or max-width: 100% on containers');
    }

    const overflow = await page.evaluate(() => {
      const vw = window.innerWidth;
      const offenders = [];
      document.querySelectorAll('*').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.right > vw + 2) {
          offenders.push(el.tagName + (el.className ? '.' + el.className.toString().split(' ')[0] : ''));
        }
      });
      return [...new Set(offenders)].slice(0, 8);
    });
    if (overflow.length > 0) {
      log(name, vpName, 'Responsive Overflow', 'HIGH',
        `Elements overflowing viewport: ${overflow.join(', ')}`,
        'Add max-width: 100%; overflow-x: hidden to offending containers; use responsive grid/flex');
    }
  }

  // ── 8. Color contrast proxy — detect very light text ────────────────────
  const lightTextNodes = await page.evaluate(() => {
    const result = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    let node;
    while ((node = walker.nextNode())) {
      const el = node.parentElement;
      if (!el || !node.textContent.trim()) continue;
      const style = window.getComputedStyle(el);
      const color = style.color;
      const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (match) {
        const [r, g, b] = match.slice(1).map(Number);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
        if (luminance > 210) result.push(el.tagName + ': ' + node.textContent.trim().slice(0, 30));
      }
      if (result.length > 5) break;
    }
    return result;
  });
  if (lightTextNodes.length > 3) {
    log(name, vpName, 'Text Readability', 'MEDIUM',
      `Multiple text nodes appear very light-colored (possible contrast issue): ${lightTextNodes.slice(0, 3).join(' | ')}`,
      'Verify contrast ratio ≥ 4.5:1 for body text, ≥ 3:1 for large text (WCAG AA)');
  }

  // ── 9. Financial disclaimers / disclosures ──────────────────────────────
  const pageText = await page.evaluate(() => document.body.innerText.toLowerCase());
  const hasBuyTrade = /buy|sell|trade|invest|portfolio|return|profit|loss|signal/i.test(pageText);
  const hasDisclaimer = /disclaimer|not financial advice|investment risk|past performance|consult|regulatory/i.test(pageText);
  if (hasBuyTrade && !hasDisclaimer) {
    log(name, vpName, 'Financial Trust / Disclosures', 'HIGH',
      'Page presents investment/trading content without a visible disclaimer or risk disclosure',
      'Add a persistent footer or inline disclaimer: "Not financial advice. Past performance does not guarantee future results."');
  }

  // ── 10. CTA / actionable next steps ────────────────────────────────────
  const ctaButtons = await page.locator('button:not([disabled]), a[href]:not([href="#"]):not([href=""])').count();
  if (ctaButtons === 0) {
    log(name, vpName, 'Actionable Next Steps', 'MEDIUM',
      'No active CTA buttons or links found — user has no clear next action',
      'Add at least one primary CTA guiding users to the next step in their learning or investing journey');
  }

  // ── 11. Education-first clarity: check for jargon-heavy headers ─────────
  const allHeadings = await page.evaluate(() =>
    [...document.querySelectorAll('h1,h2,h3')].map(h => h.textContent.trim()).filter(Boolean)
  );
  const jargonTerms = ['VaR', 'CAGR', 'EPS', 'P/E', 'EBITDA', 'MACD', 'RSI', 'BB', 'ATR', 'alpha', 'beta'];
  const jargonHeadings = allHeadings.filter(h => jargonTerms.some(t => h.includes(t)));
  if (jargonHeadings.length > 0) {
    log(name, vpName, 'Education-First Clarity', 'MEDIUM',
      `Heading(s) use unexplained financial jargon: ${jargonHeadings.slice(0, 3).join(' | ')}`,
      'Add tooltip, footnote, or inline explanation for technical terms — education-first principle');
  }

  // ── 12. Empty / loading states visible ─────────────────────────────────
  const visibleText = await page.evaluate(() => document.body.innerText.trim().length);
  if (visibleText < 200) {
    log(name, vpName, 'Empty / Loading States', 'MEDIUM',
      'Very little visible text — page may be in an empty, loading, or error state',
      'Ensure loading skeletons, empty state illustrations, and error messages are shown appropriately');
  }

  // ── 13. Role landmarks ──────────────────────────────────────────────────
  const mainLandmarks = await page.locator('main, [role="main"]').count();
  const navLandmarks = await page.locator('nav, [role="navigation"]').count();
  if (mainLandmarks === 0) {
    log(name, vpName, 'Accessibility', 'MEDIUM',
      'No <main> landmark found — screen reader users cannot skip to main content',
      'Wrap the primary content area in <main> or add role="main"');
  }
  if (navLandmarks === 0) {
    log(name, vpName, 'Accessibility', 'LOW',
      'No <nav> landmark found',
      'Wrap navigation in <nav> elements with aria-label');
  }

  // ── 14. Cognitive load: count of distinct interactive panels/cards ──────
  const cardCount = await page.locator('[class*="card"], [class*="panel"], [class*="widget"], [class*="tile"]').count();
  if (cardCount > 12) {
    log(name, vpName, 'Cognitive Load', 'MEDIUM',
      `${cardCount} card/panel/widget elements detected — high information density`,
      'Apply progressive disclosure: hide secondary data behind expand/drill-down, prioritize top 5 signals');
  }

  // Collect meta for report
  return {
    route: name,
    viewport: vpName,
    headings: allHeadings,
    ctaButtons,
    skeletonOrSpinner,
    emptyState,
    cardCount,
    pageTextLength: visibleText,
    screenshot: ssPath,
  };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const meta = [];

  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.isMobile || false,
      userAgent: vp.isMobile
        ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        : undefined,
    });
    const page = await context.newPage();

    // Capture console errors
    const consoleErrors = {};
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const key = `${msg.text().slice(0, 80)}`;
        consoleErrors[key] = (consoleErrors[key] || 0) + 1;
      }
    });

    for (const route of ROUTES) {
      console.log(`\n── Auditing /${route.name} @ ${vp.name} (${vp.width}x${vp.height}) ──`);
      const result = await auditRoute(page, route, vp.name, vp.isMobile || false);
      if (result) {
        result.consoleErrors = Object.keys(consoleErrors).slice(0, 5);
        meta.push(result);
      }
    }

    await context.close();
  }

  await browser.close();

  // ── Write JSON report ──────────────────────────────────────────────────
  const report = { timestamp: new Date().toISOString(), findings, meta };
  const reportPath = path.join(OUT_DIR, 'audit-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  // ── Print summary ──────────────────────────────────────────────────────
  console.log('\n\n══════════════════════════════════════════');
  console.log('AUDIT SUMMARY');
  console.log('══════════════════════════════════════════');
  const bySeverity = { CRITICAL: [], HIGH: [], MEDIUM: [], LOW: [] };
  for (const f of findings) {
    (bySeverity[f.severity] || bySeverity['LOW']).push(f);
  }
  for (const [sev, items] of Object.entries(bySeverity)) {
    if (items.length) {
      console.log(`\n[${sev}] ${items.length} finding(s):`);
      items.forEach(f => console.log(`  • [${f.route}/${f.viewport}] ${f.category}: ${f.finding.slice(0, 100)}`));
    }
  }
  console.log(`\nTotal findings: ${findings.length}`);
  console.log(`Report: ${reportPath}`);
  console.log(`Screenshots in: ${OUT_DIR}`);
})();
