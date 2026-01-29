import streamlit as st
import json
import os

st.set_page_config(page_title="사진 단어시험 자동채점기", layout="centered")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
ANSWERS_FILE = os.path.join(DATA_DIR, "answers.json")

if not os.path.exists(ANSWERS_FILE):
    with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False)

def load_json():
    with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data):
    with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize(text):
    if not text:
        return ""
    return (
        text.replace(" ", "")
        .replace(",", "")
        .replace("/", "")
        .replace(".", "")
        .replace("하다", "")
        .strip()
    )

def is_correct(student, answers):
    s = normalize(student)
    for a in answers:
        if normalize(a) in s or s in normalize(a):
            return True
    return False

st.title("📸 단어시험 자동채점기")

tab1, tab2 = st.tabs(["1️⃣ 답지 등록", "2️⃣ 학생 답안 채점"])

# -------------------------
# 1. 답지 등록
# -------------------------
with tab1:
    st.subheader("답지 등록")
    test_name = st.text_input("시험 이름")
    answer_imgs = st.file_uploader(
        "답지 이미지 업로드 (여러 장 가능)",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

    ocr_answers = ""

    if answer_imgs:
        st.markdown("#### 🔍 OCR 결과 (자동 추출)")
        for img in answer_imgs:
            st.image(img, width=200)
            st.components.v1.html(
                f"""
                <script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
                <script>
                const img = document.querySelector("img:last-of-type");
                Tesseract.recognize(img.src, "kor+eng").then(result => {{
                    const text = result.data.text;
                    const textarea = parent.document.querySelector("textarea");
                    if (textarea) {{
                        textarea.value += "\\n" + text;
                    }}
                });
                </script>
                """,
                height=0,
            )

        ocr_answers = st.text_area(
            "OCR 결과 (자동 채워짐, 필요하면 수정 가능)",
            height=200,
            key="answer_text"
        )

    if st.button("답지 저장"):
        if not test_name or not ocr_answers.strip():
            st.error("시험 이름과 OCR 결과가 필요합니다.")
        else:
            answers = {}
            for line in ocr_answers.split("\n"):
                if "." in line:
                    try:
                        num, rest = line.split(".", 1)
                        num = num.strip()
                        meaning = rest.strip()
                        if num.isdigit():
                            meanings = (
                                meaning.replace("(", "")
                                .replace(")", "")
                                .replace("·", ",")
                                .split(",")
                            )
                            meanings = [m.strip() for m in meanings if m.strip()]
                            answers[num] = meanings
                    except:
                        pass

            all_answers = load_json()
            all_answers[test_name] = answers
            save_json(all_answers)
            st.success("답지가 저장되었습니다!")

# -------------------------
# 2. 학생 답안 채점
# -------------------------
with tab2:
    st.subheader("학생 답안 채점")
    tests = load_json()
    if tests:
        selected_test = st.selectbox("시험 선택", list(tests.keys()))
        student_imgs = st.file_uploader(
            "학생 시험지 이미지 업로드 (여러 장 가능)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True
        )

        ocr_student = ""

        if student_imgs:
            st.markdown("#### 🔍 OCR 결과 (자동 추출)")
            for img in student_imgs:
                st.image(img, width=200)
                st.components.v1.html(
                    f"""
                    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
                    <script>
                    const img = document.querySelector("img:last-of-type");
                    Tesseract.recognize(img.src, "kor+eng").then(result => {{
                        const text = result.data.text;
                        const textarea = parent.document.querySelectorAll("textarea")[1];
                        if (textarea) {{
                            textarea.value += "\\n" + text;
                        }}
                    });
                    </script>
                    """,
                    height=0,
                )

        student_text = st.text_area(
            "OCR 결과 (자동 채워짐, 필요하면 수정 가능)",
            height=200,
            key="student_text"
        )

        if st.button("채점하기"):
            if not student_text.strip():
                st.error("학생 OCR 결과가 필요합니다.")
            else:
                student_answers = {}
                for line in student_text.split("\n"):
                    if "." in line:
                        try:
                            num, rest = line.split(".", 1)
                            num = num.strip()
                            answer = rest.strip()
                            if num.isdigit():
                                student_answers[num] = answer
                        except:
                            pass

                correct = 0
                wrong = []

                answer_key = tests[selected_test]
                for num, correct_answers in answer_key.items():
                    student_answer = student_answers.get(num, "")
                    if is_correct(student_answer, correct_answers):
                        correct += 1
                    else:
                        wrong.append(num)

                total = len(answer_key)
                st.success(f"점수: {correct} / {total}")
                st.write("❌ 틀린 번호:", ", ".join(wrong))
    else:
        st.info("아직 등록된 시험이 없습니다.")
