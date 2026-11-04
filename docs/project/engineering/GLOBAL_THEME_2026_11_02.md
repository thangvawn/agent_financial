# Đồng bộ sáng/tối toàn ứng dụng

2026-11-02 · implemented and verified on local QA.

Yêu cầu: một lựa chọn sáng/tối dùng cho mọi tab, tiếp nối Global Terminal.

Nghiệm thu: switch chung có thể thao tác ở các workspace; giữ lựa chọn khi chuyển trang/reload và giữa browser tabs; các bề mặt, form, hộp thoại, charts và nội dung chữ theo chế độ; PDF/giấy A4 và nội dung ảnh không đảo màu. Không thay đổi dữ liệu, trạng thái đang nhập hoặc DB người dùng.

Các bước: mở rộng theme provider và di chuyển switch; thay màu cố định trong Learn Hub/BCTC/Simulation, kiểm tra News/các tab Market; kiểm chứng desktop/mobile + luồng chuyển tab với DB QA tạm, lint/CSS/build và test phù hợp; ghi bằng chứng và giới hạn.

Hoàn tất: preference `public-beta.theme` dùng chung, đọc lại lựa chọn Market cũ, switch trên navigation và reader/auth; portal/chart kế thừa cùng palette. 176 unit test, 39 nhóm browser, CSS56 và build đạt; ESLint 0 lỗi/1 warning Social có sẵn. [Báo cáo nghiệm thu và giới hạn](../qa/results/GLOBAL_THEME_2026_11_02.md).
