import {
  Activity,
  BarChart3,
  Brain,
  Cpu,
  Folder,
  Globe,
  Landmark,
  Layers,
  PiggyBank,
  TrendingUp,
} from 'lucide-react'

const ICON_MAP = {
  Folder,
  Globe,
  BarChart3,
  TrendingUp,
  Cpu,
  Activity,
  Landmark,
  Layers,
  Brain,
  PiggyBank,
}

export default function DocumentFolderNav({ folders, activeFolderId, onSelectFolder, counts = {} }) {
  return (
    <div className="lh-folder-nav" role="tablist" aria-label="Thư mục chủ đề">
      <div className="lh-folder-nav__header">
        <span className="lh-folder-nav__title">
          <Folder size={15} className="lh-folder-nav__title-icon" />
          <span>Thư mục Chủ đề</span>
        </span>
      </div>
      <div className="lh-folder-nav__list">
        {folders.map((folder) => {
          const IconComponent = ICON_MAP[folder.icon] || Folder
          const isActive = activeFolderId === folder.id
          const count = counts[folder.id] ?? 0
          return (
            <button
              key={folder.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`lh-folder-item ${isActive ? 'is-active' : ''}`}
              onClick={() => onSelectFolder(folder.id)}
              title={folder.description}
            >
              <div className="lh-folder-item__icon-wrap">
                <IconComponent size={15} />
              </div>
              <span className="lh-folder-item__label">{folder.label}</span>
              <span className="lh-folder-item__count">{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
