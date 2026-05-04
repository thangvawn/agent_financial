from __future__ import annotations

from risk_dashboard.modules.learning.domain.entities import (
    LearningCourse,
    LearningGlossaryTerm,
    LearningLesson,
    LearningPath,
    LearningQuizQuestion,
)


LESSONS: dict[str, LearningLesson] = {
    "money-basics-101": LearningLesson(
        lesson_id="money-basics-101",
        title="Tien co ban va cach tranh sai lam som",
        summary="Hieu tien, dong tien va ly do nen bat dau tu su on dinh truoc.",
        tier="financial_basics",
        content_type="micro_lesson",
        estimated_minutes=4,
        body=[
            "Tien khong chi la thu nhap. Dieu quan trong la luong tien con lai sau chi tieu va kha nang chiu duoc su co bat ngo.",
            "Neu chua co he thong quan ly tien co ban, viec dau tu som de bien thanh ap luc hon la co hoi.",
        ],
        glossary=[LearningGlossaryTerm(term="Cash flow", definition="Dong tien vao va ra trong cuoc song hang thang.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Neu thu nhap tang nhung chi tieu tang nhanh hon, dieu gi xau di truoc?",
                options=["Dong tien", "Mau sac app", "Lai kep"],
                correct_answer="Dong tien",
                explanation="Dong tien moi la nen tang de tiet kiem va lap muc tieu.",
            )
        ],
        next_lesson_id="cashflow-basics-101",
    ),
    "cashflow-basics-101": LearningLesson(
        lesson_id="cashflow-basics-101",
        title="Dong tien co ban",
        summary="Biet tien dang di dau de giam stress thanh khoan.",
        tier="financial_basics",
        content_type="practical_tool_lesson",
        estimated_minutes=4,
        body=[
            "Theo doi dong tien khong phai de phan xet ban, ma de biet diem nao dang lam ke hoach tai chinh kho hon.",
            "Chi can nhan ra 1-2 khoan chi lap lai la da tao ra thay doi lon.",
        ],
        glossary=[LearningGlossaryTerm(term="Liquidity stress", definition="Cam giac bi cang tien mat trong ngan han.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Theo doi dong tien giup giam dieu gi som nhat?",
                options=["Liquidity stress", "Ty gia", "Drawdown"],
                correct_answer="Liquidity stress",
                explanation="Dong tien ro rang giup giam ap luc cuoi thang.",
            )
        ],
        next_lesson_id="emergency-fund-101",
    ),
    "emergency-fund-101": LearningLesson(
        lesson_id="emergency-fund-101",
        title="Quy du phong la gi",
        summary="Quy du phong la lop dem truoc khi nghiem tuc mo rong rui ro tai chinh.",
        tier="financial_basics",
        content_type="micro_lesson",
        estimated_minutes=5,
        body=[
            "Quy du phong la so tien de bao ve ban khi thu nhap gian doan hoac chi phi bat ngo xuat hien.",
            "Moc dau tien khong can qua lon. 1 thang chi phi thiet yeu da la buoc di rat co gia tri.",
        ],
        glossary=[LearningGlossaryTerm(term="Emergency fund", definition="Khoan tien de ung pho su co khong du doan truoc.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Moc dau tien hop ly nhat cua quy du phong la gi?",
                options=["1 thang chi phi thiet yeu", "Mua co phieu ngay", "Khong can lam"],
                correct_answer="1 thang chi phi thiet yeu",
                explanation="Bat dau nho de tao dong luc va do an toan.",
            )
        ],
        next_lesson_id="investing-basics-101",
    ),
    "investing-basics-101": LearningLesson(
        lesson_id="investing-basics-101",
        title="Dau tu co ban",
        summary="Dau tu la qua trinh dat tien vao tai san co rui ro de ky vong tang truong dai han.",
        tier="basic_investing_literacy",
        content_type="micro_lesson",
        estimated_minutes=5,
        body=[
            "Dau tu khong phai la doan dung sai ngan han, ma la quan ly ky vong, rui ro va thoi gian.",
            "Neu nen tang tai chinh chua on, dau tu som co the lam tang cam xuc va sai lam.",
        ],
        glossary=[LearningGlossaryTerm(term="Investing literacy", definition="Hieu biet co ban de khong dau tu cam tinh.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Dieu nao quan trong hon trong dau tu ben vung?",
                options=["Quan ly rui ro", "Tin nong", "Phim room chat"],
                correct_answer="Quan ly rui ro",
                explanation="Khung suy nghi dung giup giam sai lam lau dai.",
            )
        ],
        next_lesson_id="risk-basics-101",
    ),
    "risk-basics-101": LearningLesson(
        lesson_id="risk-basics-101",
        title="Rui ro va bien dong co nghia gi",
        summary="Risk score thap khong phai la loi phan xet, ma la cach nhin ve muc do de ton thuong.",
        tier="basic_investing_literacy",
        content_type="contextual_explainer",
        estimated_minutes=4,
        body=[
            "Bien dong la chuyen gia tang giam, con rui ro la kha nang ban khong dat duoc muc tieu hoac khong chiu noi qua trinh do.",
            "Drawdown va risk score giup ban hieu neu minh di nhanh qua thi se dau o dau.",
        ],
        glossary=[LearningGlossaryTerm(term="Drawdown", definition="Muc giam tu dinh xuong day trong mot giai doan.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Risk score thap nen dan den dieu gi truoc?",
                options=["Hoc lai risk basics", "Mua nhanh hon", "Bo qua"],
                correct_answer="Hoc lai risk basics",
                explanation="Giai thich truoc khi hanh dong giup giam sai lam.",
            )
        ],
        next_lesson_id="drawdown-basics-101",
    ),
    "drawdown-basics-101": LearningLesson(
        lesson_id="drawdown-basics-101",
        title="Drawdown basics",
        summary="Hieu drawdown de khong phan ung qua nhanh khi thi truong giam.",
        tier="basic_investing_literacy",
        content_type="contextual_explainer",
        estimated_minutes=4,
        body=[
            "Drawdown khong noi len tat ca, nhung no nhac ban rang duong di luon co luc giam sau.",
            "Ban nen hoi: minh co chiu duoc khoang giam nay ve tam ly va ke hoach khong?",
        ],
        glossary=[LearningGlossaryTerm(term="Recovery", definition="Qua trinh hoi phuc sau khi giam sau.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Khi nhin drawdown, cau hoi dung nhat la gi?",
                options=["Minh co chiu duoc khong", "Mau do co dep khong", "Ai dang mua"],
                correct_answer="Minh co chiu duoc khong",
                explanation="Drawdown can dat trong kha nang chiu dung va muc tieu cua ban.",
            )
        ],
        next_lesson_id="compounding-basics-101",
    ),
    "compounding-basics-101": LearningLesson(
        lesson_id="compounding-basics-101",
        title="Compounding basics",
        summary="Lai kep can thoi gian, ky luat va ky vong thuc te.",
        tier="basic_investing_literacy",
        content_type="micro_lesson",
        estimated_minutes=4,
        body=[
            "Lai kep khong phai phep mau, ma la hieu ung cua viec duy tri deu dan trong thoi gian dai.",
            "Neu nen tang tai chinh yeu, lai kep khong the sua cho dong tien am hoac no qua cao.",
        ],
        glossary=[LearningGlossaryTerm(term="Compounding", definition="Tien sinh loi va phan loi tiep tuc sinh them loi.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Lai kep can dieu gi nhieu nhat?",
                options=["Thoi gian", "Tin nong", "Do may man"],
                correct_answer="Thoi gian",
                explanation="Thoi gian va ky luat moi la lop nang do lai kep.",
            )
        ],
        next_lesson_id="tool-financial-health-101",
    ),
    "tool-financial-health-101": LearningLesson(
        lesson_id="tool-financial-health-101",
        title="Doc Financial Health nhu the nao",
        summary="Score la diem bat dau de uu tien hanh dong, khong phai nhan xet gia tri ban than.",
        tier="product_tool_literacy",
        content_type="practical_tool_lesson",
        estimated_minutes=4,
        body=[
            "Hay nhin sub-scores va risk flags truoc, sau do moi den tong diem.",
            "Muc tieu cua tool nay la chi ra nen sua dau tien o dau, khong phai cham diem cho vui.",
        ],
        glossary=[LearningGlossaryTerm(term="Sub-score", definition="Diem thanh phan giup biet diem manh va diem yeu.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Nen nhin gi truoc trong Financial Health?",
                options=["Sub-scores va risk flags", "Tong diem roi bo qua", "Chi mau sac"],
                correct_answer="Sub-scores va risk flags",
                explanation="Phan thanh phan moi noi len ban can hanh dong o dau.",
            )
        ],
        next_lesson_id="tool-goals-101",
    ),
    "tool-goals-101": LearningLesson(
        lesson_id="tool-goals-101",
        title="Dat Goals nhu the nao",
        summary="Goal tot la goal co deadline, target va pace thuc te.",
        tier="product_tool_literacy",
        content_type="practical_tool_lesson",
        estimated_minutes=4,
        body=[
            "Goal trong app khong phai wish list. No giup ban biet con thieu bao nhieu va moi thang can pace nao.",
            "Neu goal qua stress, dieu do khong co nghia ban that bai. No chi bao rang can doi lai pace hoac nen tang.",
        ],
        glossary=[LearningGlossaryTerm(term="Gap to target", definition="Khoang cach giua hien tai va muc tieu.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Goal tot can dieu gi?",
                options=["Deadline va target ro", "Chi can cam hung", "Khong can current amount"],
                correct_answer="Deadline va target ro",
                explanation="Co moc ro thi moi tinh duoc pace va trade-off.",
            )
        ],
        next_lesson_id="tool-risk-score-101",
    ),
    "tool-risk-score-101": LearningLesson(
        lesson_id="tool-risk-score-101",
        title="Doc Risk Score nhu the nao",
        summary="Risk score dung de giai thich muc de ton thuong cua ke hoach, khong phai de du doan chinh xac.",
        tier="product_tool_literacy",
        content_type="practical_tool_lesson",
        estimated_minutes=4,
        body=[
            "Risk score cho ban biet khi nao nen cham lai, hoc them hoac xem lai muc tieu.",
            "Dung no cung voi drawdown va scenario de hieu boi canh, khong dung no nhu nut mua ban.",
        ],
        glossary=[LearningGlossaryTerm(term="Risk score", definition="Chi so tom tat muc do rui ro tuong doi trong boi canh hien tai.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Risk score nen duoc dung nhu the nao?",
                options=["De giai thich boi canh", "De ra lenh mua", "De khoe do hieu biet"],
                correct_answer="De giai thich boi canh",
                explanation="Cong cu nay uu tien explainer first.",
            )
        ],
        next_lesson_id=None,
    ),
    "fx-basics-101": LearningLesson(
        lesson_id="fx-basics-101",
        title="FX basics cho muc tieu da tien te",
        summary="Muc tieu remittance va xuyen bien gioi can co dem cho bien dong ty gia.",
        tier="financial_basics",
        content_type="contextual_explainer",
        estimated_minutes=4,
        body=[
            "Neu muc tieu cua ban o mot dong tien khac, ban nen lap ke hoach voi mot khoang dem thay vi sat muc.",
            "FX sensitivity khong phai du bao ty gia, ma la cach de tranh bi bat ngo.",
        ],
        glossary=[LearningGlossaryTerm(term="FX sensitivity", definition="Muc do muc tieu thay doi khi ty gia bien dong.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="FX sensitivity dung de lam gi?",
                options=["Tao khoang dem", "Du doan chac chan", "Bo qua ty gia"],
                correct_answer="Tao khoang dem",
                explanation="Muc tieu da tien te can du phong bien dong, khong can su chinh xac gia tao.",
            )
        ],
        next_lesson_id="tool-goals-101",
    ),
    "scenario-thinking-101": LearningLesson(
        lesson_id="scenario-thinking-101",
        title="Scenario thinking cho nguoi da co nen",
        summary="Scenario thinking giup ban nhin nhieu kha nang, khong phai tim du doan duy nhat.",
        tier="basic_investing_literacy",
        content_type="micro_lesson",
        estimated_minutes=4,
        body=[
            "Scenario tot mo rong cach nghi va giam su tu tin qua muc.",
            "Ban dung scenario de hoi neu thi truong xau hon du kien thi ke hoach cua minh se ra sao.",
        ],
        glossary=[LearningGlossaryTerm(term="Scenario", definition="Mot kich ban gia dinh de danh gia tac dong len ke hoach.")],
        quiz_questions=[
            LearningQuizQuestion(
                question_id="q1",
                prompt="Scenario thinking giup dieu gi?",
                options=["Xem nhieu kha nang", "Tim chan ly duy nhat", "Bo qua rui ro"],
                correct_answer="Xem nhieu kha nang",
                explanation="Scenario giup tranh su tu tin qua muc vao mot kich ban duy nhat.",
            )
        ],
        next_lesson_id="tool-risk-score-101",
    ),
}


PATHS: dict[str, LearningPath] = {
    "starter-foundations": LearningPath(
        path_id="starter-foundations",
        title="Starter Foundations",
        persona_segment="starter",
        lesson_ids=["money-basics-101", "cashflow-basics-101", "emergency-fund-101", "investing-basics-101"],
        description="Bat dau tu tien co ban, dong tien va quy du phong truoc khi di xa hon.",
    ),
    "financial-health-foundations": LearningPath(
        path_id="financial-health-foundations",
        title="Financial Health Foundations",
        persona_segment="household_manager",
        lesson_ids=["cashflow-basics-101", "emergency-fund-101", "tool-financial-health-101", "tool-goals-101"],
        description="Giu cho money system va goals cua gia dinh on dinh va de theo doi hon.",
    ),
    "guided-investing-foundations": LearningPath(
        path_id="guided-investing-foundations",
        title="Guided Investing Foundations",
        persona_segment="beginner_investor",
        lesson_ids=["investing-basics-101", "risk-basics-101", "drawdown-basics-101", "tool-risk-score-101"],
        description="Hoc risk va drawdown truoc khi dung Guided Investing de khong FOMO.",
    ),
    "market-context-fast-track": LearningPath(
        path_id="market-context-fast-track",
        title="Market Context Fast Track",
        persona_segment="advanced_pro",
        lesson_ids=["scenario-thinking-101", "drawdown-basics-101", "tool-risk-score-101"],
        description="Du da co nen, ban van nen bat dau bang context va scenario thay vi tin hieu.",
    ),
    "diaspora-crossborder-foundations": LearningPath(
        path_id="diaspora-crossborder-foundations",
        title="Cross-border Foundations",
        persona_segment="diaspora_vn",
        lesson_ids=["money-basics-101", "fx-basics-101", "tool-goals-101"],
        description="Tap trung vao remittance, FX basics va lap goal da tien te.",
    ),
}


COURSES: dict[str, LearningCourse] = {
    "financial-basics": LearningCourse(
        course_id="financial-basics",
        title="Financial Basics",
        description="Tien, dong tien, quy du phong, no va nhung nen tang tai chinh can co.",
        tier="financial_basics",
        lesson_ids=["money-basics-101", "cashflow-basics-101", "emergency-fund-101", "fx-basics-101"],
    ),
    "basic-investing-literacy": LearningCourse(
        course_id="basic-investing-literacy",
        title="Basic Investing Literacy",
        description="Hoc risk, drawdown, compounding va framework dau tu can ban.",
        tier="basic_investing_literacy",
        lesson_ids=[
            "investing-basics-101",
            "risk-basics-101",
            "drawdown-basics-101",
            "compounding-basics-101",
            "scenario-thinking-101",
        ],
    ),
    "product-tool-literacy": LearningCourse(
        course_id="product-tool-literacy",
        title="Product & Tool Literacy",
        description="Biet dung Financial Health, Goals va Risk Score dung luc.",
        tier="product_tool_literacy",
        lesson_ids=["tool-financial-health-101", "tool-goals-101", "tool-risk-score-101"],
    ),
}


CONTEXT_TRIGGER_TO_LESSON = {
    "drawdown": "drawdown-basics-101",
    "compound_interest": "compounding-basics-101",
    "risk_score_low": "risk-basics-101",
    "goal_off_track": "tool-goals-101",
    "financial_health_low": "emergency-fund-101",
}
