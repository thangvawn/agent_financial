import { MessageSquareText, Newspaper } from 'lucide-react'
import { resolvePathForView } from '../../../../app/domainRoutes'

export default function NewsWorkspaceTabs({ active, onNews, onSocial }) {
  return <nav className="news-workspace-tabs" aria-label="Không gian tin tức">
    {[
      { key: 'news', label: 'Tin tức', icon: <Newspaper size={16} aria-hidden="true" />, onClick: onNews },
      { key: 'news_social', label: 'Social', icon: <MessageSquareText size={16} aria-hidden="true" />, onClick: onSocial },
    ].map(({ key, label, icon, onClick }) => <a key={key} href={resolvePathForView(key)}
      aria-current={active === key ? 'page' : undefined}
      onClick={e => { if (onClick && !e.metaKey && !e.ctrlKey && !e.shiftKey) { e.preventDefault(); onClick() } }}>
      {icon}{label}
    </a>)}
  </nav>
}
