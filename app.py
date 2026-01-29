import streamlit as st
import json
import os
from PIL import Image
import pytesseract

st.set_page_config(page_title="사진 단어시험 자동채점기", layout="centered")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")
ANSWERS_FILE = os.path.join(DATA_DIR, "answers.json")

if not os.path.exists(TEMPLATES_FILE):
    with open(TEMPLATES_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(ANSWERS_FILE):
    with open(ANSWERS_FILE, "w") as f:
        json.dump({}, f)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
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

st.title("📸 단어시험 사진 자동채점기")

tab1, tab2, tab3 = st.tabs(["1️⃣ 시험지 등록", "2️⃣ 답지 등록", "3️⃣ 학생 답안 채점"])

# -----------------------
# 1. 시험지 등록
# -----------------------
with tab1:
    st.subheader("시험지 양식 등록")
    test_name = st.text_input("시험 이름 (예: 1월 29일 단어시험)")
    template_img = st.file_uploader("빈 시험지 사진 업로드", type=["jpg", "png", "jpeg"])

    if st.button("시험지 저장"):
        if not test_name or not template_img:
            st.error("시험 이름과 시험지 사진을 모두 입력하세요.")
        else:
            templates = load_json(TEMPLATES_FILE)
            templates[test_name] = {"template_image": template_img.name}
            save_json(TEMPLATES_FILE, templates)
            st.success("시험지가 저장되었습니다! (현재는 구조 저장 단계만 구현됨)")

# -----------------------
# 2. 답지 등록
# -----------------------
with tab2:
    st.subheader("답지 등록")
    answers_test_name = st.text_input("연결할 시험 이름")
    answer_img = st.file_uploader("답지 사진 업로드", type=["jpg", "png", "jpeg"])

    if st.button("답지 저장"):
        if not answers_test_name or not answer_img:
            st.error("시험 이름과 답지 사진을 모두 입력하세요.")
        else:
            img = Image.open(answer_img)
            text = pytesseract.image_to_string(img, lang="kor+eng")

            lines = text.split("\n")
            answers = {}
            for line in lines:
                if "." in line:
                    try:
                        num, rest = line.split(".", 1)
                        num = num.strip()
                        meaning = rest.strip()
                        if num.isdigit():
                            meanings = [m.strip() for m in meaning.replace("(", "").replace(")", "").split(",")]
                            answers[num] = meanings
                    except:
                        pass

            all_answers = load_json(ANSWERS_FILE)
            all_answers[answers_test_name] = answers
            save_json(ANSWERS_FILE, all_answers)

            st.success("답지가 저장되었습니다!")

# -----------------------
# 3. 학생 답안 채점
# -----------------------
with tab3:
    st.subheader("학생 답안 채점")
    tests = load_json(ANSWERS_FILE)
    if tests:
        selected_test = st.selectbox("시험 선택", list(tests.keys()))
        student_img = st.file_uploader("학생 시험지 사진 업로드", type=["jpg", "png", "jpeg"])

        if st.button("채점하기"):
            if not student_img:
                st.error("학생 시험지 사진을 업로드하세요.")
            else:
                img = Image.open(student_img)
                text = pytesseract.image_to_string(img, lang="kor+eng")
                lines = text.split("\n")

                student_answers = {}
                for line in lines:
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
