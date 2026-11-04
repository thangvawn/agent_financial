# Docker: timeout khi tải dependency Python

**2026-10-31 · verified.** Người dùng gửi log `ReadTimeoutError` từ `files.pythonhosted.org` khi `pip install ".[auto]"`; image cũ dùng pip 25.0.1. Đã sửa [Dockerfile](../../../../Dockerfile) và bổ sung cách xử lý trong [README](../../../../README.md).

- Pin pip 26.2.2; timeout socket 120 giây, tối đa 10 lần thử kết nối và 10 lần tiếp tục tải dở. Cho phép đổi qua build args `PIP_TIMEOUT`, `PIP_RETRIES`, `PIP_RESUME_RETRIES`.
- Dùng `python -m pip` và cache BuildKit cho cài dependency lẫn editable package. Không đổi dependency nghiệp vụ trong pyproject hoặc cấu hình Compose.
- [Tài liệu pip](https://pip.pypa.io/en/stable/cli/pip/) phân biệt retry kết nối và resume download; [pip 25.2](https://pip.pypa.io/en/stable/news/#v25-2) bật automatic resumption mặc định.

## Kiểm chứng

1. `docker compose config --quiet` và `git diff --check`: đạt.
2. `docker compose --progress plain build app`: exit 0, image `duanagenttaichinh-app:latest` đã build. Image ID: `sha256:138fd38fc93faaf4ec80870b3b1ca288d6618173f299a69ac092a23cdb2c350e`.
3. `python -m pip check` trong image mới: `No broken requirements found`.
4. Container tạm không có mạng ngoài, dùng DB tạm: import app thành công, TestClient `/health` trả 200. ENV thực tế: timeout=120, retries=10, resume_retries=10. Không chạy lifespan/provider live trong smoke này.
5. Cùng probe HTTP loopback làm gián đoạn tệp wheel 3 MiB sau 2 MiB, socket timeout 0,3 giây: pip 25.0.1 dừng với exit 2, không resume; pip 26.2.2 gửi request thứ hai từ offset 2097152, exit 0, SHA-256 của tệp tải xong trùng tệp gốc. Probe chỉ download, không install gói thử.

[Log build, probe và smoke](../../../../output/docker/2026-10-31-pip-timeout/) là artifact local. Chạy lại probe sau build:

```bash
docker run --rm --network none --entrypoint python -v "$PWD/output/docker/2026-10-31-pip-timeout/pip-resume-probe.py:/tmp/probe.py:ro" duanagenttaichinh-app:latest /tmp/probe.py
```

Đã build local; không chạy `compose up`, restart, publish hoặc deploy. Các container kiểm thử đều dùng `--rm`, không mount dữ liệu ứng dụng. 116 mục đã stage từ trước được giữ nguyên; lượt cấu hình này chưa commit.
