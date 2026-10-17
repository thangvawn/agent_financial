import { BookOpen, Code2, Library, Sparkles } from 'lucide-react'
import { QUANTA_SECTIONS, TUTORIAL_FAST_TRACK } from '../content/quantaCurriculumData'
import { WIKI_FUNCTION_GROUPS } from '../content/quantaWikiData'

export default function QuantaDocsHome({ onSelectLesson, onSwitchToWiki, onOpenStudioModal }) {
  return (
    <div className="qd-home-container thin-scrollbar">
      {/* Hero Banner */}
      <div className="qd-hero-banner">
        <div className="qd-hero-content">
          <div className="qd-hero-icon-box">
            <Sparkles size={26} className="text-cyan-200" />
          </div>
          <div className="qd-hero-text">
            <h1 className="qd-hero-title">Tài liệu Quanta DSL</h1>
            <p className="qd-hero-desc">
              Ngôn ngữ Quanta Story: giáo trình từng bước, wiki hàm built-in, namespace, render candora, act/risk. Viết một script chạy chart, backtest, screener và live.
            </p>
            <div className="qd-badge-row">
              <span className="qd-badge qd-badge--cyan">Quanta Story</span>
              <span className="qd-badge qd-badge--purple">59 hàm built-in</span>
              <span className="qd-badge qd-badge--emerald">6 bài mẫu</span>
              <span className="qd-badge qd-badge--amber">3 mẫu code</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3 Main Action Cards */}
      <div className="qd-action-grid">
        <button
          type="button"
          className="qd-action-card qd-action-card--cyan"
          onClick={() => onSelectLesson('quanta-overview')}
        >
          <BookOpen size={22} className="qd-action-icon text-cyan-300" />
          <h2 className="qd-action-title">Bắt đầu giáo trình</h2>
          <p className="qd-action-desc">
            Lộ trình 20 bài từ grammar đến tooling AI; mỗi bài có snippet chạy trên Studio.
          </p>
        </button>

        <button
          type="button"
          className="qd-action-card qd-action-card--purple"
          onClick={onSwitchToWiki}
        >
          <Library size={22} className="qd-action-icon text-purple-300" />
          <h2 className="qd-action-title">Wiki tra cứu</h2>
          <p className="qd-action-desc">
            Khái niệm, namespace, plot, 59 hàm, bài mẫu và ví dụ — đã nhóm theo lộ trình học.
          </p>
        </button>

        <button
          type="button"
          className="qd-action-card qd-action-card--amber"
          onClick={onOpenStudioModal}
        >
          <Code2 size={22} className="qd-action-icon text-amber-300" />
          <h2 className="qd-action-title">Mở Studio</h2>
          <p className="qd-action-desc">
            Editor Monaco + autocomplete + compile + backtest chiến lược giao dịch tự động.
          </p>
        </button>
      </div>

      {/* Tutorial Nhanh 5 bài đầu */}
      <div className="qd-fast-track-box">
        <div className="qd-fast-track-header">TUTORIAL NHANH — 5 BÀI ĐẦU</div>
        <p className="qd-fast-track-desc">Bắt đầu từ bài 1 để nắm vững cú pháp Quanta Story cốt lõi:</p>
        <div className="qd-fast-track-pills">
          {TUTORIAL_FAST_TRACK.map((item) => (
            <button
              key={item.slug}
              type="button"
              className="qd-ft-pill"
              onClick={() => onSelectLesson(item.slug)}
            >
              <strong>{item.num}.</strong> {item.title}
            </button>
          ))}
        </div>
      </div>

      {/* Lộ trình giáo trình */}
      <h2 className="qd-section-headline">Lộ trình giáo trình</h2>
      <div className="qd-curriculum-grid">
        {QUANTA_SECTIONS.map((sec) => (
          <div key={sec.id} className="qd-curriculum-card">
            <h3 className="qd-curr-title">{sec.title}</h3>
            <p className="qd-curr-sub">{sec.subtitle}</p>
            <ul className="qd-curr-list">
              {sec.lessons.map((l) => (
                <li key={l.slug}>
                  <button
                    type="button"
                    className="qd-curr-link"
                    onClick={() => onSelectLesson(l.slug)}
                  >
                    · {l.title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Mục lục Wiki */}
      <h2 className="qd-section-headline">Mục lục Wiki hàm built-in</h2>
      <div className="qd-curriculum-grid">
        {WIKI_FUNCTION_GROUPS.map((grp) => (
          <div key={grp.id} className="qd-curriculum-card">
            <div className="qd-wiki-card-head">
              <span className="qd-curr-title text-purple-200">{grp.title}</span>
              <span className="qd-badge-pill">{grp.count}</span>
            </div>
            <div className="qd-wiki-tag-row">
              {grp.items.map((fn) => (
                <button
                  key={fn}
                  type="button"
                  className="qd-fn-tag"
                  onClick={onSwitchToWiki}
                >
                  {fn}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
