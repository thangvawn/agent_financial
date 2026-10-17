import './page-skeleton.css'

export default function PageSkeleton() {
  return (
    <div className="page-skeleton" aria-busy="true" aria-label="Đang tải dữ liệu trang...">
      <div className="page-skeleton__top">
        <div className="page-skeleton__shimmer page-skeleton__title" />
        <div className="page-skeleton__shimmer page-skeleton__pill" />
      </div>
      <div className="page-skeleton__grid">
        <div className="page-skeleton__shimmer page-skeleton__card page-skeleton__card--main" />
        <div className="page-skeleton__col">
          <div className="page-skeleton__shimmer page-skeleton__card" />
          <div className="page-skeleton__shimmer page-skeleton__card" />
        </div>
      </div>
    </div>
  )
}
