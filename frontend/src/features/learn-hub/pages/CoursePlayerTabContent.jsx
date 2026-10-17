import CourseCheckpointTab from '../components/CourseCheckpointTab'
import LearnTutorPanel from './LearnTutorPanel'
import VideoLearningAgentPanel from './VideoLearningAgentPanel'

export default function CoursePlayerTabContent({
  activeTab,
  course,
  courseId,
  activeLesson,
  activeLessonId,
  sessionId,
  completedSet,
  allLessons,
  onCompleteCheckpoint,
  currentTimeSeconds,
}) {
  return (
    <div
      id={`lhp-panel-${activeTab}`}
      className="lhp-tab-content"
      role="tabpanel"
      aria-labelledby={`lhp-tab-${activeTab}`}
    >
      {activeTab === 'checkpoint' ? (
        <CourseCheckpointTab
          lessonId={activeLessonId}
          sessionId={sessionId}
          onCompleteLesson={onCompleteCheckpoint}
        />
      ) : null}

      {activeTab === 'tutor' ? (
        <LearnTutorPanel courseId={courseId} lessonId={activeLessonId} sessionId={sessionId} videoTimeSeconds={currentTimeSeconds} />
      ) : null}

      {activeTab === 'video-agent' ? (
        <VideoLearningAgentPanel lessonId={activeLessonId} lesson={activeLesson} sessionId={sessionId} currentTimeSeconds={currentTimeSeconds} />
      ) : null}

      {activeTab === 'overview' ? (
        <div className="lhp-overview">
          <h3>Về khóa học</h3>
          <p>{course.description}</p>
          <div className="lhp-overview__meta">
            <span>Giảng viên: <strong>{course.instructor}</strong></span>
            <span>Độ khó: <strong>{course.difficulty}</strong></span>
            <span>Thời lượng: <strong>{course.total_duration}</strong></span>
          </div>
          <h3>Tiến độ</h3>
          <div className="lhp-overview__progress">
            <div className="lhc-card__progress-bar lhp-overview__bar">
              <div
                className="lhc-card__progress-fill"
                style={{ width: `${allLessons.length ? (completedSet.size / allLessons.length) * 100 : 0}%` }}
              />
            </div>
            <span>{completedSet.size}/{allLessons.length} bài đã hoàn thành</span>
          </div>
        </div>
      ) : null}

      {activeTab === 'notes' ? (
        <p className="lhp-notes__placeholder">Ghi chú bài học đang phát triển.</p>
      ) : null}

      {activeTab === 'resources' ? (
        activeLesson?.video_url ? (
          <p>Nguồn: <a href={activeLesson.video_url} target="_blank" rel="noreferrer">{activeLesson.video_url}</a></p>
        ) : (
          <p className="lhp-notes__placeholder">Chưa có tài liệu đính kèm.</p>
        )
      ) : null}
    </div>
  )
}
