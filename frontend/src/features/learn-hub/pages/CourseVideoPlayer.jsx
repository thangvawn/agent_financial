export default function CourseVideoPlayer({
  activeLessonId,
  activeLesson,
  courseTitle,
  isYouTube,
  youtubeEmbed,
  videoError,
  videoRef,
  onVideoEnded,
  onVideoError,
  onTimeUpdate,
}) {
  return (
    <div className="lhp-player-wrap">
      {isYouTube && youtubeEmbed ? (
        <iframe
          key={activeLessonId}
          className="lhp-player lhp-player--youtube"
          src={youtubeEmbed}
          title={activeLesson?.title || courseTitle}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerPolicy="strict-origin-when-cross-origin"
          allowFullScreen
        />
      ) : videoError ? (
        <div className="lhp-player lhp-player--placeholder">
          <p>Không phát được video trong app</p>
          {activeLesson?.video_url ? (
            <a className="lhc-btn lhc-btn--primary" href={activeLesson.video_url} target="_blank" rel="noreferrer">
              Mở trên YouTube
            </a>
          ) : null}
        </div>
      ) : (
        <video
          ref={videoRef}
          className="lhp-player"
          controls
          src={activeLesson?.video_url || ''}
          onEnded={onVideoEnded}
          onError={onVideoError}
          onTimeUpdate={onTimeUpdate}
        />
      )}
    </div>
  )
}
