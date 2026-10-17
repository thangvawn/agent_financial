# BÁO CÁO KIỂM TOÁN TOÀN DIỆN FRONTEND & TAB LEARN
**Mã phân hệ**: Frontend React / Vite / Tab Learn Hub  
**Người thực hiện**: `explorer_survey_fe`  
**Thời gian hoàn thành**: 2026-10-10T11:15:00Z  
**Phạm vi kiểm toán**: `frontend/src/features/learn-hub`, `frontend/src/app`, `frontend/package.json`, `frontend/vite.config.js`, `frontend/src/__tests__`, và đối soát API Contract với Backend Python/FastAPI (`src/risk_dashboard/modules/learning`).

---

## 1. TỔNG QUAN KIẾN TRÚC FRONTEND VÀ TAB LEARN (LEARN HUB)

### 1.1. Cấu trúc định tuyến và vòng đời hiển thị
- **Entry point**: `frontend/src/App.jsx:6-30` sử dụng bộ định tuyến tùy biến qua `domainRoutes.js:1-57` và `AppShell.jsx`.
- **Mount Tab Learn**: Tại `frontend/src/app/AppShellRoutes.jsx:26-35`, khi `renderedView === 'learning'`, component `LearningHomePage` được render với:
  ```jsx
  <LearningHomePage
    key={`learning-${learningFocus.tab}-${learningFocus.search}`}
    sessionId={sessionId}
    onBack={actions.onBackHome}
    initialSubTab={learningFocus.tab}
    initialSearch={learningFocus.search}
  />
  ```
  *Điểm nghẽn kiến trúc*: Prop `key` gán phụ thuộc vào `learningFocus.tab` và `learningFocus.search`. Mỗi khi người dùng gõ tìm kiếm hoặc chuyển sub-tab từ shell ngoài, React hủy bỏ (unmount) và tạo mới (remount) toàn bộ cây component `LearningHomePage`, làm mất sạch state cục bộ và kích hoạt lại fetch mạng.

### 1.2. Phân rã cấu trúc thành phần (Component Hierarchy) của Tab Learn
Phân hệ `features/learn-hub` gồm 4 tiểu phân hệ chính:
1. **Catalog & Khóa học (`LearningHomePage.jsx`, `CourseCard.jsx`, `CourseSectionHeader.jsx`)**:
   - Hiển thị danh mục khóa học lọc theo search, độ khó và sắp xếp (bài học, thời lượng, bookmark).
   - Tích hợp `useCourseBookmarks.js` (lưu bookmark vào `localStorage`).
2. **Trình phát bài giảng đa phương tiện (`CoursePlayerPage.jsx`, `CourseVideoPlayer.jsx`, `LessonSidebar.jsx`)**:
   - Phát video bài giảng qua thẻ HTML5 `<video>` hoặc YouTube `<iframe>`.
   - Sidebar danh sách bài học và thanh tiến độ.
   - Tabs con: `overview`, `video-agent`, `checkpoint`, `tutor`, `notes`, `resources`.
3. **Không gian đọc tài liệu & Ghi chú thông minh (`BookReaderWorkspace.jsx`, `BookDocumentPane.jsx`, `NotePaper.jsx`, `ReaderChrome.jsx`, `useBookReaderState.js`)**:
   - Split-pane chia đôi: Bên trái đọc PDF (qua proxy hoặc Google Docs Viewer) / văn bản thô; bên phải sổ tay ghi chú vẽ canvas và chèn ảnh chụp.
4. **Phòng thi thử CFA & Socratic Checkpoint (`MockExamRoomPage.jsx`, `CourseCheckpointTab.jsx`, `CheckpointCard.jsx`, `SocraticHintWidget.jsx`)**:
   - `MockExamRoomPage.jsx`: Phòng thi 90 câu trắc nghiệm CFA Level I với đếm ngược thời gian, đánh dấu cờ (flag), gạch phương án loại trừ và highlight.
   - `CourseCheckpointTab.jsx`: Tích hợp câu hỏi Socratic checkpoint và cơ chế xác thực Mastery Proposal (Human-in-the-loop).

---

## 2. DANH MỤC LỖ HỔNG & BOTTLEENECK HIỆU NĂNG (RISK MATRIX)

| Mã ID | Vấn đề / Lỗ hổng | Vị trí (File & Dòng) | Phân loại | Mức độ rủi ro |
|---|---|---|---|---|
| **FE-PERF-01** | Vòng lặp re-render liên tục 4-5 lần/giây khi phát video | `CoursePlayerPage.jsx:41,122`, `CourseVideoPlayer.jsx:42` | Re-render Cascade | **CRITICAL** |
| **FE-PERF-02** | YouTube embed mất kết nối đồng bộ mốc thời gian (currentTime = 0) | `CourseVideoPlayer.jsx:16-24`, `CoursePlayerPage.jsx:63-64` | State Asynchrony | **CRITICAL** |
| **FE-MEM-01** | Rò rỉ bộ nhớ đồ họa GPU: Canvas 960x1400 cho mỗi trang ghi chú | `NotePaper.jsx:125-135`, `useBookReaderState.js:18,92-120` | Memory / DOM Bloat | **CRITICAL** |
| **FE-DATA-01** | Lộ 100% đáp án đề thi trắc nghiệm CFA ở mã nguồn Client | `mockExamData.js:9-417`, `MockExamRoomPage.jsx:153-178` | Security & Integrity | **CRITICAL** |
| **FE-PERF-03** | Nghẽn I/O main thread: Ghi đè `localStorage` mỗi giây và mỗi item render | `MockExamRoomPage.jsx:219-234`, `LearningHomePage.jsx:27-32,149` | Synchronous I/O | **HIGH** |
| **FE-DATA-02** | Không bắt lỗi `QuotaExceededError` khi lưu ảnh/vẽ base64 vào localStorage | `useBookReaderState.js:150-168` | Exception Crash | **HIGH** |
| **FE-STATE-01** | Tiến độ học tập chỉ lưu cục bộ ở Client, không đồng bộ Backend DB | `CoursePlayerPage.jsx:14-22,73-82`, `CourseCheckpointTab.jsx:83-94` | State Synchronization | **HIGH** |
| **FE-PERF-04** | Parser Regex Markdown chạy thô không memoize trong AI Tutor | `TutorMessageContent.jsx:59-197` | CPU Bottleneck | **HIGH** |
| **FE-NET-01** | Thiếu `AbortController` khi tải nội dung văn bản sách | `BookDocumentPane.jsx:93-105` | Missing Cleanup | **MEDIUM** |
| **FE-ARCH-01** | Kho custom hook và component rác bị bỏ rơi (Orphaned Dead Code) | `useLearningHome.js`, `useLearningMutations.js`, `LibraryMedia.jsx`... | Code Smells | **MEDIUM** |
| **FE-TEST-01** | Test runner thiếu lệnh `npm test` và mock tĩnh `renderToString` | `frontend/package.json:6-14`, `src/__tests__/test-helpers.js` | Test Fidelity Gap | **HIGH** |
| **FE-DRIFT-01** | Lệch Contract: Backend `GetQuizItemOutput` thiếu trường `socratic_coaching` | `schemas/agent_tools.py:57-64` vs `types/learningTypes.js:14` | API Contract Drift | **HIGH** |

---

## 3. CHI TIẾT TỪNG PHÁT HIỆN KIỂM TOÁN (EVIDENCE & ROOT CAUSE)

### 3.1. FE-PERF-01: Vòng lặp re-render liên tục 4-5 lần/giây khi phát video (CRITICAL)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx`: dòng 41, 122:
    ```javascript
    41: const [currentTimeSeconds, setCurrentTimeSeconds] = useState(0)
    ...
    122: onTimeUpdate={(event) => setCurrentTimeSeconds(event.currentTarget.currentTime)}
    ```
  - `frontend/src/features/learn-hub/pages/CourseVideoPlayer.jsx`: dòng 42:
    ```javascript
    42: onTimeUpdate={onTimeUpdate}
    ```
- **Bằng chứng & Hiện tượng**:
  Khi phát video HTML5 thông thường, sự kiện `timeupdate` của trình duyệt bắn ra liên tục mỗi 200ms – 250ms (tương đương 4-5 lần/giây).
  Mỗi lần bắn, callback gọi thẳng `setCurrentTimeSeconds` ở root state của `CoursePlayerPage`.
- **Hệ quả**:
  Toàn bộ cây DOM của `CoursePlayerPage` — bao gồm `CourseVideoPlayer`, thanh thông tin bài học `lhp-lesson-info`, danh sách tab `PLAYER_TABS`, nội dung tab `CoursePlayerTabContent`, và thanh mục lục sidebar `LessonSidebar` — bị re-render lại toàn bộ 4-5 lần mỗi giây. Điều này gây giật lag (frame drops), tiêu tốn pin trên thiết bị di động và làm mất focus của các input trong tab con.
- **Giải pháp đề xuất**:
  Không nâng `currentTimeSeconds` lên state của page cha. Sử dụng `useRef` lưu thời gian hiện tại (`currentTimeRef`) hoặc tách riêng context thời gian chỉ re-render widget hiển thị timestamp, hoặc throttling sự kiện `timeupdate` (1 giây/lần).

---

### 3.2. FE-PERF-02: YouTube Embed mất kết nối đồng bộ mốc thời gian (CRITICAL)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/CourseVideoPlayer.jsx`: dòng 16-24:
    ```javascript
    16: <iframe
    17:   key={activeLessonId}
    18:   className="lhp-player lhp-player--youtube"
    19:   src={youtubeEmbed}
    20:   title={activeLesson?.title || courseTitle}
    ...
    ```
  - `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx`: dòng 63-64:
    ```javascript
    63: const isYouTube = isYouTubeUrl(activeLesson?.video_url)
    64: const youtubeEmbed = toYouTubeEmbed(activeLesson?.video_url)
    ```
- **Bằng chứng & Hiện tượng**:
  Hầu hết các bài giảng trong `demoCourses.js` đều là video YouTube. Tuy nhiên, `CourseVideoPlayer` chỉ render một thẻ `<iframe>` thông thường trỏ tới `youtube.com/embed/...`. Thẻ `<iframe>` KHÔNG gắn thuộc tính `enablejsapi=1`, cũng không khởi tạo YouTube IFrame Player API (`YT.Player`) hay lắng nghe `window.onmessage`.
- **Hệ quả**:
  1. Thẻ `<iframe>` không bao giờ kích hoạt sự kiện `onTimeUpdate`.
  2. Biến `currentTimeSeconds` vĩnh viễn bằng `0` khi người dùng học các bài giảng YouTube.
  3. Khi chuyển sang tab `Video Learning Agent` hoặc `AI Gia Sư`, mốc thời gian gửi lên Backend API (`fetchVideoAgentCheckpoint`, `askVideoAgent`, `sendTutorMessage`) luôn luôn là `0`! Agent không thể định vị đoạn video người dùng đang xem để đưa ra gợi ý ngữ cảnh chính xác.

---

### 3.3. FE-MEM-01: Rò rỉ bộ nhớ GPU: Khởi tạo Canvas 960x1400 cho mỗi trang ghi chú (CRITICAL)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/NotePaper.jsx`: dòng 125-135:
    ```javascript
    125: <canvas
    126:   ref={canvasRef}
    127:   className={`br-paper__canvas${inkActive ? ' is-ink' : ''}`}
    128:   width={960}
    129:   height={1400}
    ...
    ```
  - `frontend/src/features/learn-hub/pages/useBookReaderState.js`: dòng 91-118:
    Render danh sách `pages.map((page, index) => <NotePaper ... />)`.
- **Bằng chứng & Hiện tượng**:
  Mỗi trang ghi chú trong `BookReaderWorkspace` mount một thẻ HTML5 Canvas cố định kích thước `960 × 1400` pixel.
  Mỗi canvas 2D chiếm:
  $$\text{Memory} = 960 \times 1400 \times 4 \text{ bytes (RGBA)} \approx 5.376.000 \text{ bytes} \approx 5.38 \text{ MB}$$
  Nếu người dùng tạo 10 trang ghi chú trong một quyển sách, trình duyệt phải cấp phát hơn **53.8 MB** bộ nhớ bitmap thô trên GPU/Compositor.
  Ngoài ra, hàm `snapshotCanvas()` (`NotePaper.jsx:32-34`) gọi `canvas.toDataURL('image/png')` đồng bộ trên CPU mỗi khi nhả chuột (`pointerUp`), gây đông cứng giao diện (freeze 30-60ms) với các nét vẽ phức tạp.
- **Giải pháp đề xuất**:
  Chỉ render Canvas cho trang ghi chú đang hoạt động (active page) hoặc chuyển sang lưu trữ đường vẽ vector (SVG paths / SVG strokes) thay vì raster bitmap PNG base64.

---

### 3.4. FE-DATA-01: Lộ 100% đáp án đề thi trắc nghiệm CFA ở mã nguồn Client (CRITICAL)
- **Vị trí**:
  - `frontend/src/features/learn-hub/content/mockExamData.js`: dòng 9-22 và dòng 26-417:
    File dài 417 dòng (59.5 KB) chứa toàn bộ 90 câu hỏi CFA Level I kèm trực tiếp thuộc tính `correctOptionId`, `explanation`, và `takeaway`.
  - `frontend/src/features/learn-hub/pages/MockExamRoomPage.jsx`: dòng 153-165:
    ```javascript
    153: const calculateResult = useCallback((reason = 'manual', remainingOverride = null) => {
    154:   const correctCount = MOCK_EXAM.questions.reduce(
    155:     (count, item) => count + (answers[item.id] === item.correctOptionId ? 1 : 0),
    156:     0,
    157:   )
    ...
    ```
- **Bằng chứng & Hiện tượng**:
  Việc chấm điểm bài thi CFA được thực hiện hoàn toàn ở client bằng cách so khớp lựa chọn của người dùng với `item.correctOptionId` đã đóng gói sẵn trong file JS của frontend.
- **Hệ quả**:
  1. Người dùng chỉ cần mở Chrome DevTools (Console/Sources) là có thể xem trước toàn bộ đáp án của cả 90 câu hỏi.
  2. Không có bất kỳ API request nào gửi về Backend để chấm điểm hoặc ghi nhận chứng chỉ/kết quả thi thật, vi phạm nguyên tắc bảo mật và tính toàn vẹn (Zero-Leakage Invariant) mà hệ thống đặt ra cho Checkpoint.

---

### 3.5. FE-PERF-03: Nghẽn I/O Main Thread: Ghi đè `localStorage` mỗi giây và mỗi item render (HIGH)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/MockExamRoomPage.jsx`: dòng 219-234:
    ```javascript
    219: useEffect(() => {
    220:   if (mode !== 'running' || !startedAt || typeof window === 'undefined') return
    221:   const payload = {
    ...
    227:     remaining,
    ...
    232:   }
    233:   try { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload)) } catch { /* storage is optional */ }
    234: }, [answers, attemptMode, currentIndex, eliminated, flags, highlighted, mode, remaining, startedAt])
    ```
  - `frontend/src/features/learn-hub/pages/LearningHomePage.jsx`: dòng 27-32, 149:
    ```javascript
    27: function getCourseProgress(courseId, totalLessons, sessionId) {
    28:   const saved = readAllProgress(sessionId) // JSON.parse(localStorage.getItem(...))
    ...
    149: progress={getCourseProgress(course.course_id, course.lesson_count, sessionId)}
    ```
- **Bằng chứng & Hiện tượng**:
  1. Trong `MockExamRoomPage.jsx`, timer đếm ngược gọi `setRemaining` mỗi 1000ms. Do `remaining` nằm trong mảng dependency của `useEffect`, toàn bộ payload bài thi (bao gồm 90 answers, flags, eliminated) bị `JSON.stringify` và ghi đè vào `window.localStorage.setItem` **đúng 1 lần mỗi giây**.
  2. Trong `LearningHomePage.jsx`, hàm `getCourseProgress` được gọi trong vòng lặp `.map()` của toàn bộ danh sách khóa học. Với 50 khóa học, mỗi lần re-render trang danh mục sẽ kích hoạt 50 lần `localStorage.getItem()` và 50 lần `JSON.parse()` đồng bộ liên tiếp!
- **Hệ quả**:
  `localStorage` là API đồng bộ (synchronous blocking I/O) trên main thread. Việc đọc/ghi liên tục gây nghẽn event loop, tụt FPS và giảm độ phản hồi của UI.

---

### 3.6. FE-DATA-02: Không bắt lỗi `QuotaExceededError` khi lưu ảnh và canvas vào localStorage (HIGH)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/useBookReaderState.js`: dòng 150-168:
    ```javascript
    150: function saveReaderState() {
    ...
    157:   window.localStorage.setItem(readerStorageKey(sessionId, book.asset_id), JSON.stringify({
    158:     pages: pagesToSave,
    159:     activePageId: active?.id || '',
    160:     noteHtml: composeNoteHtml(active?.noteText || '', active?.images || []),
    161:     noteText: active?.noteText || '',
    162:     images: active?.images || [],
    163:     drawingDataUrl: active?.drawingDataUrl || '',
    164:     savedAt: savedIso,
    165:   }))
    ...
    ```
- **Bằng chứng & Hiện tượng**:
  Dữ liệu trang vẽ (`drawingDataUrl`) và ảnh paste từ clipboard (`images`) được chuyển thành base64 data URL. Khi người dùng bấm Lưu hoặc chuyển trang, hàm `saveReaderState` gọi trực tiếp `window.localStorage.setItem` mà **hoàn toàn không có khối `try ... catch`**.
- **Hệ quả**:
  Dung lượng lưu trữ của `localStorage` bị trình duyệt giới hạn ở mức ~5MB. Một vài nét vẽ và 2-3 bức ảnh chụp màn hình có thể dễ dàng vượt quá 5MB. Trình duyệt sẽ ném ra ngoại lệ `DOMException: QuotaExceededError`, làm ứng dụng bị crash hoặc rơi vào Error Boundary, làm mất toàn bộ ghi chú của người dùng.

---

### 3.7. FE-STATE-01: Tiến độ học tập chỉ lưu ở Client LocalStorage, không đồng bộ Backend DB (HIGH)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/CoursePlayerPage.jsx`: dòng 73-82:
    ```javascript
    73: const markComplete = (lessonId) => {
    74:   setCompletedSet((prev) => {
    ...
    79:     writeProgress(sessionId, saved) // Chỉ ghi vào localStorage!
    80:     return next
    81:   })
    82: }
    ```
  - Backend cung cấp endpoint `POST /api/v1/public/learning/lessons/{lesson_id}/complete` (`public.py:305-321`), nhưng frontend **hoàn toàn không bao giờ gọi endpoint này** khi người dùng học xong bài giảng.
- **Hệ quả**:
  - Khi người dùng xóa cache trình duyệt, chuyển máy tính khác hoặc đăng nhập trên điện thoại, toàn bộ lịch sử và tiến độ học tập bị biến mất (0%).
  - Bảng thống kê tiến độ học tập trên dashboard backend không bao giờ nhận được dữ liệu thực tế.

---

### 3.8. FE-PERF-04: Parser Regex Markdown chạy thô không memoize trong AI Tutor (HIGH)
- **Vị trí**:
  - `frontend/src/features/learn-hub/components/TutorMessageContent.jsx`: dòng 59-197:
    Hàm `TutorMessageContent({ content })` thực hiện phân tách dòng:
    `const rawLines = content.split('\n')`
    và duyệt vòng lặp `while (idx < rawLines.length)` với hàng chục biểu thức chính quy (Regex math `$$`, callout `>`, heading `###`, divider `---`, bullet `^([*•-]|(\d+\.))\s+`) và thay thế `cleaned.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1) / ($2)')`.
- **Bằng chứng & Hiện tượng**:
  Toàn bộ quá trình phân tích cú pháp chuỗi Markdown/LaTeX này **không được bọc trong `useMemo`**.
  Mỗi khi người dùng gõ phím vào ô chat `inputText` trong `LearnTutorPanel.jsx`, hoặc component cha re-render, toàn bộ tin nhắn trước đó (có thể lên tới hàng chục tin nhắn) đều chạy lại thuật toán phân tích regex từ đầu.
  Đồng thời, các danh sách bullet và callout render phần tử con với `key={i}` (chỉ số mảng) gây re-mount DOM không cần thiết.

---

### 3.9. FE-NET-01: Thiếu `AbortController` khi tải nội dung văn bản sách (MEDIUM)
- **Vị trí**:
  - `frontend/src/features/learn-hub/pages/BookDocumentPane.jsx`: dòng 93-105:
    ```javascript
    93: useEffect(() => {
    94:   let cancelled = false
    95:   fetch(url)
    96:     .then(async (response) => { ... })
    ...
    104:   return () => { cancelled = true }
    105: }, [url])
    ```
- **Hiện tượng**:
  Sử dụng cờ `cancelled` cục bộ để bỏ qua kết quả trả về, nhưng không truyền tín hiệu hủy `signal: controller.signal` vào `fetch(url)`. Khi người dùng chuyển đổi nhanh giữa các cuốn sách, các kết nối HTTP tải file sách cũ vẫn tiếp tục tải ngầm dưới nền, lãng phí băng thông mạng.

---

### 3.10. FE-ARCH-01: Kho Custom Hook và Component rác bị bỏ rơi (Orphaned Dead Code) (MEDIUM)
Qua rà soát toàn bộ cây mã nguồn `frontend/src`, các file sau đây tồn tại nhưng **hoàn toàn không được sử dụng hoặc import bởi bất kỳ UI component nào**:
1. `features/learn-hub/hooks/useLearningHome.js`: Hook gọi `fetchLearningHome`, 0 nơi sử dụng.
2. `features/learn-hub/hooks/useLearningAssets.js`: Hook gọi `fetchLearningAssets`, 0 nơi sử dụng.
3. `features/learn-hub/hooks/useLearningMutations.js`: Hook `useSubmitLearningQuiz` và `useCompleteLearningLesson`, 0 nơi sử dụng.
4. `features/learn-hub/hooks/useLearningNextLessonBundle.js`: Hook `useQueries`, 0 nơi sử dụng.
5. `features/learn-hub/hooks/useMasteryProposal.js`: Khởi tạo state proposal, nhưng `CourseCheckpointTab.jsx` lại tự code inline và chỉ lấy duy nhất hàm helper `resolveMasteryThreshold`.
6. `features/learn-hub/pages/LibraryMedia.jsx`: 103 dòng code chứa `LocalVideoGrid`, `LocalBookGrid`, `CatalogCard`, hoàn toàn không được import ở đâu.
7. `features/learn-hub/pages/LearnHubPage.jsx`: Component bọc thừa, vì `AppShellRoutes.jsx` import trực tiếp `LearningHomePage.jsx`.
8. `features/learn-hub/schemas/learningSchemas.js`: Chứa duy nhất 8 dòng định nghĩa mock object không tác dụng.

---

## 4. KIỂM TOÁN HỆ THỐNG TEST SUITE & ĐỘ TRUNG THỰC KIỂM THỬ (TEST FIDELITY)

### 4.1. Kết quả thực thi thực tế (Execution Proof)
1. **Lệnh `npm test`**:
   - Lệnh: `npm test` tại thư mục `frontend/`
   - Kết quả: **FAIL (Exit code 1)**
   - Log lỗi:
     ```
     npm error Missing script: "test"
     npm error To see a list of scripts, run: npm run
     ```
   - Nguyên nhân: Trong `frontend/package.json`, chỉ có script `"test:unit": "node ./scripts/test-runner.mjs"`, hoàn toàn không có entry `"test"`.
2. **Lệnh `npm run test:unit`**:
   - Lệnh: `npm run test:unit`
   - Kết quả: **PASS (20 tests passed, 6 suites, thời gian: ~2.18s)**
   - Danh sách test chạy thành công:
     - `Frontend Baseline Test Suite`: 1 test
     - `Learn Hub fallback catalog`: 2 tests
     - `CheckpointCard Component Contract & Zero-Leakage (TASK UI-03)`: 8 tests
     - `Mock exam room contract`: 2 tests
     - `BCTC raw data challenge`: 1 test
     - `SocraticHintWidget Component Contract & Progressive Disclosure (TASK UI-04)`: 6 tests
3. **Bộ kiểm thử Backend (`pytest`)**:
   - `tests/test_learning.py` + `tests/test_ai_tutor_learning.py`: **8 passed in 15.40s**.
   - `tests/test_learning_agent_*.py` + `tests/test_video_learning_agent.py`: **23 passed in 15.23s**.
   - `tests/test_ai_tutor_api.py` + `tests/test_ai_tutor_security_hardening.py`: **5 passed in 10.06s**.

### 4.2. Đánh giá chất lượng và lỗ hổng kiểm thử (Mock Fidelity & Missing Coverage)
Mặc dù `npm run test:unit` hiển thị "20 pass", việc kiểm toán chuyên sâu phát hiện các lỗ hổng nghiêm trọng sau:
1. **Không có môi trường trình duyệt thật (Zero DOM Environment)**:
   - Các test sử dụng `node:test` kết hợp `react-dom/server` (`renderToString`) thông qua `test-helpers.js:30`.
   - `renderToString` chỉ tạo ra chuỗi HTML tĩnh. Trong môi trường này:
     * `useEffect` và `useLayoutEffect` **hoàn toàn không bao giờ chạy**.
     * Các sự kiện tương tác (`onClick`, `onChange`, `onKeyDown`, `onPointerDown`) **không thể kiểm thử hành vi động**.
     * Trạng thái phản hồi của state (`useState`, `useReducer`) sau tương tác không được xác nhận.
2. **Test giả / Dummy Assertion**:
   - Trong `frontend/src/__tests__/learningAgent.test.js:6`:
     ```javascript
     it('verifies baseline test runner is operational', () => {
       assert.strictEqual(1 + 1, 2)
     })
     ```
     Test này chỉ kiểm tra `1 + 1 == 2`, hoàn toàn không test bất kỳ logic nào của `learningAgent`.
3. **Thiếu giả lập mạng (Zero Mock Fidelity)**:
   - Không có bất kỳ thư viện mock mạng nào (như `msw` - Mock Service Worker hay `nock`).
   - Mọi hàm gọi API trong `services/learningApi.js` và `services/aiTutorApi.js` đều có **0% coverage kiểm thử**.
4. **Vùng trống kiểm thử (Missing Coverage)**:
   - Toàn bộ custom hooks: `useBookReaderState`, `useCourseBookmarks`, `useLearningCatalog`, `useMasteryProposal` đạt 0% coverage.
   - Luồng phát video, đồng bộ mốc thời gian, xử lý lỗi iframe, tải file PDF đạt 0% coverage.

---

## 5. ĐỐI SOÁT HỢP ĐỒNG API (FRONTEND VS BACKEND CONTRACT DRIFT)

### 5.1. Lệch cấu trúc Checkpoint & Socratic Coaching (HIGH)
- **Backend**: Schema `GetQuizItemOutput` trong `src/risk_dashboard/modules/learning/schemas/agent_tools.py:57-64` chỉ trả về:
  ```python
  class GetQuizItemOutput(BaseModel):
      schema_version: str = "1.0.0"
      checkpoint_id: str
      lesson_id: str
      prompt: str
      options: tuple[str, ...]
      expires_at: str
  ```
- **Frontend**: Trong `features/learn-hub/types/learningTypes.js:14` và `SocraticHintWidget.jsx:13,35`, frontend kỳ vọng trường:
  ```javascript
  socratic_coaching?: { focus_concept?: string, hint?: string }
  ```
- **Hệ quả thực tế**: Vì backend không trả về trường này, prop `socraticCoaching` luôn là `undefined`, khiến widget Socratic ở frontend luôn phải rơi về chuỗi gợi ý tĩnh mặc định ("Hãy xem lại nguyên lý lý thuyết cơ sở liên quan đến câu hỏi").

### 5.2. Lỗi định dạng URL Video Agent (HIGH)
- **Backend**: `VideoAgentAskRequest` và `VideoAgentPrepareRequest` trong `src/risk_dashboard/modules/learning/schemas/video_agent.py:21,100` quy định:
  ```python
  source_url: HttpUrl | None = None
  ```
  Pydantic yêu cầu `source_url` phải là một URL đầy đủ (bắt đầu bằng `http://` hoặc `https://`).
- **Frontend**: Trong trường hợp bài giảng là file local (`/learning-assets/videos/...`), frontend truyền trực tiếp đường dẫn tương đối này vào `prepareVideoAgent` hoặc `askVideoAgent`.
- **Hệ quả**: Backend sẽ ném ra lỗi validation HTTP 422: `URL scheme not permitted`.

### 5.3. Bất tương thích bộ lọc độ khó (Difficulty Filter Mismatch) (MEDIUM)
- **Frontend**: `LearningHomePage.jsx:37` lọc theo nhãn tiếng Việt: `'all' | 'Cơ bản' | 'Trung bình' | 'Nâng cao'`.
- **Backend**: Endpoint `GET /api/v1/public/learning/catalog` trong `public.py:407` nhận tham số `tier: str` với các giá trị chuẩn: `'beginner' | 'intermediate' | 'advanced'`. Khi frontend truyền trực tiếp hoặc normalize không khớp, backend query vào SQLite sẽ không khớp dữ liệu.

---

## 6. KHUYẾN NGHỊ TÁI THIẾT KẾ CHO GIAI ĐOẠN R2 & R3

1. **Chuẩn hóa kiến trúc State & Cache**:
   - Chuyển toàn bộ các lệnh `fetch` thô trong `LearningHomePage`, `BookGrid` sang sử dụng `@tanstack/react-query` với staleTime và cache invalidation rõ ràng.
   - Thay thế việc ghi đè `localStorage` mỗi giây trong `MockExamRoomPage` bằng debounced state (chỉ lưu khi người dùng chọn đáp án hoặc tạm dừng).
2. **Tách biệt Video Player và Agent Time Controller**:
   - Sử dụng YouTube IFrame API chính thức để trích xuất `getCurrentTime()` theo chu kỳ 1s mà không làm re-render toàn bộ trang `CoursePlayerPage`.
   - Đưa `currentTime` vào một lightweight context hoặc ref để các panel trợ lý AI tự đọc khi người dùng bấm gửi câu hỏi.
3. **Tái cấu trúc Reader & Sổ tay ghi chú (Vector over Raster)**:
   - Chuyển đổi mô hình lưu nét vẽ từ Base64 Canvas PNG sang mảng tọa độ vector SVG. Giảm kích thước lưu trữ từ vài MB xuống còn vài KB, triệt tiêu nguy cơ tràn hạn mức `localStorage`.
   - Thiết lập cơ chế lưu ghi chú lên Backend qua API REST thay vì chỉ lưu cục bộ ở Client.
4. **Di chuyển logic chấm thi CFA về Backend**:
   - Loại bỏ 59.5KB `mockExamData.js` chứa đáp án ra khỏi client bundle.
   - Thiết kế endpoint `POST /api/v1/public/learning/exams/{exam_id}/submit` để backend thực hiện chấm điểm bảo mật.
5. **Nâng cấp Test Suite**:
   - Bổ sung script `"test": "node ./scripts/test-runner.mjs"` vào `package.json`.
   - Cài đặt `@testing-library/react` và môi trường giả lập DOM (JSDOM hoặc Vitest) để test tương tác thật của người dùng thay vì chỉ test chuỗi `renderToString`.
