import { useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useLearningAssets, useLearningCatalog } from '..'
import { SearchIcon } from '../../../shared/Icons'
import { BookReaderWorkspace } from './BookReaderWorkspace'
import { toReadableBook } from './bookSource'
import {
  CatalogCard,
  LocalBookGrid,
  LocalVideoGrid,
  VideoPreview,
  filterAssetsByType,
  filterLocal,
} from './LibraryMedia'
import './learn-hub.css'
import './learn-hub-catalog.css'

const TABS = [
  ['video', 'Video'],
  ['book', 'Sách'],
  ['paper', 'Tài liệu'],
]

export default function LearningHomePage({ sessionId, onBack }) {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('video')
  const [topic, setTopic] = useState('')
  const [search, setSearch] = useState('')
  const [activeBook, setActiveBook] = useState(null)
  const [activeVideo, setActiveVideo] = useState(null)

  const {
    videoItems: rawVideos,
    bookItems,
    isLoading: assetLoading,
    error: assetError,
  } = useLearningAssets(sessionId)

  const videoAssets = useMemo(() => filterAssetsByType(rawVideos, 'video'), [rawVideos])
  const bookAssets = bookItems || []

  const {
    items: catalogItems,
    topics,
    isLoading: catalogLoading,
    error: catalogError,
  } = useLearningCatalog({
    enabled: Boolean(sessionId),
    kind: tab,
    topic,
  })

  const filteredCatalog = useMemo(() => {
    if (!search.trim()) return catalogItems
    const q = search.toLowerCase().trim()
    return catalogItems.filter((item) => {
      const blob = `${item.title || ''} ${item.description || item.abstract || ''} ${item.author || ''}`.toLowerCase()
      return blob.includes(q)
    })
  }, [catalogItems, search])

  if (!sessionId) {
    return (
      <section className="lh-shell lh-shell--center">
        <div className="lh-empty-card">
          <h1>Cần đăng nhập</h1>
          <p>Learn Hub cần session để mở thư viện video, sách và tài liệu.</p>
          {onBack ? <button type="button" className="lh-btn lh-btn--primary" onClick={onBack}>Về trang chủ</button> : null}
        </div>
      </section>
    )
  }

  if (activeBook) {
    return (
      <BookReaderWorkspace
        book={toReadableBook(activeBook)}
        sessionId={sessionId}
        onClose={() => setActiveBook(null)}
      />
    )
  }

  return (
    <section className="lh-shell" data-domain="learn_hub">
      <header className="lh-top">
        <div className="lh-top__inner lh-top__inner--library">
          <div>
            <p className="lh-top__kicker">Learn Hub</p>
            <h1 className="lh-top__title">Thư viện học liệu</h1>
          </div>
          <button
            type="button"
            className="lh-btn lh-btn--outline"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['learning'] })}
          >
            Làm mới
          </button>
        </div>
      </header>

      <div className="lh-tabs" role="tablist" aria-label="Loại học liệu">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? 'is-active' : undefined}
            onClick={() => {
              setTab(id)
              setActiveVideo(null)
              setSearch('')
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="lh-body">
        <div className="lh-library">
          <div className="lh-library__filters">
            {topics.length ? (
              <select value={topic} onChange={(e) => setTopic(e.target.value)} aria-label="Chủ đề">
                <option value="">Tất cả chủ đề</option>
                {topics.map((item) => (
                  <option key={item.topic_id} value={item.topic_id}>
                    {item.label_vi} ({item.resource_count || 0})
                  </option>
                ))}
              </select>
            ) : null}
            <label className="lh-library__search">
              <SearchIcon className="lh-library__search-icon" aria-hidden="true" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={`Tìm ${tab === 'video' ? 'video' : tab === 'book' ? 'sách' : 'tài liệu'}…`}
              />
            </label>
          </div>

          {tab === 'video' && activeVideo ? (
            <VideoPreview video={activeVideo} onClose={() => setActiveVideo(null)} />
          ) : null}

          {tab === 'video' ? (
            <LocalVideoGrid
              items={filterLocal(videoAssets, search)}
              loading={assetLoading}
              error={assetError}
              onPlay={setActiveVideo}
            />
          ) : null}

          {tab === 'book' ? (
            <LocalBookGrid
              items={filterLocal(bookAssets, search)}
              loading={assetLoading}
              error={assetError}
              onRead={setActiveBook}
            />
          ) : null}

          <section className="lh-library__section" aria-labelledby="lh-catalog-title">
            <h2 id="lh-catalog-title">
              {tab === 'video' ? 'Video từ catalog' : tab === 'book' ? 'Sách từ catalog' : 'Tài liệu từ catalog'}
            </h2>
            {catalogLoading ? <p className="lh-empty">Đang tải catalog…</p> : null}
            {catalogError ? <p className="lh-alert" role="alert">{catalogError}</p> : null}
            {!catalogLoading && !catalogError && !filteredCatalog.length ? (
              <p className="lh-empty">Chưa có mục nào trong catalog.</p>
            ) : null}
            <div className="lh-grid">
              {filteredCatalog.map((item) => (
                <CatalogCard
                  key={item[`${tab}_id`] || item.url || item.title}
                  kind={tab}
                  item={item}
                  onOpenBook={tab === 'book' ? setActiveBook : undefined}
                />
              ))}
            </div>
          </section>
        </div>
      </div>

      <p className="lh-footer-note">Học liệu phục vụ giáo dục — không phải khuyến nghị đầu tư.</p>
    </section>
  )
}
