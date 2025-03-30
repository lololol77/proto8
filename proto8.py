import streamlit as st
import pandas as pd
import sqlite3

# 데이터베이스 경로
DB_PATH = 'job_seekers.db'

# 데이터베이스 연결 함수
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

# 구직자 정보 저장 함수
def save_job_seeker(name, disability, severity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO job_seekers (name, disability, severity) VALUES (?, ?, ?)", (name, disability, severity))
    conn.commit()
    conn.close()

# 구인자 정보 저장 함수
def save_job_listing(job_name, job_description, required_skills):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO job_listings (job_name, job_description, required_skills) VALUES (?, ?, ?)", (job_name, job_description, required_skills))
    conn.commit()
    conn.close()

# 일자리 목록 조회 함수
def get_job_listings():
    conn = connect_db()
    query = "SELECT * FROM job_listings"
    listings = pd.read_sql_query(query, conn)
    conn.close()
    return listings

# 유료 서비스 질문 함수
def ask_premium_service(user_type):
    if user_type == "구직자":
        choice = st.radio("유료 취업준비 서비스를 이용하시겠습니까?", ("예", "아니오"))
        st.write(f"선택: {choice}")
    elif user_type == "구인자":
        choice = st.radio("유료 직무개발 서비스를 이용하시겠습니까?", ("예", "아니오"))
        st.write(f"선택: {choice}")

# 일자리 매칭 알고리즘
def calculate_match_score(required_skills, disability, severity, ability_df):
    skills = required_skills.split(",")
    score = 0
    for skill in skills:
        skill = skill.strip()
        match = ability_df[(ability_df['능력'] == skill) & (ability_df['정도'] == severity)][disability].values
        if len(match) > 0:
            score += match[0]
        else:
            return -1  # 매칭 불가능
    return score

st.title("장애인 일자리 매칭 플랫폼")

user_type = st.selectbox("사용자 유형을 선택하세요", ["구직자", "구인자"])

if user_type == "구직자":
    st.header("구직자 정보 입력")
    name = st.text_input("이름")
    disability = st.selectbox("장애 유형", ["시각장애", "청각장애", "지체장애", "뇌병변장애", "언어장애", "안면장애", "신장장애", "심장장애", "간장애", "호흡기장애", "장루·요루장애", "뇌전증장애", "지적장애", "자폐성장애", "정신장애"])
    severity = st.selectbox("장애 정도", ["심하지 않은", "심한"])

    if st.button("구직자 등록"):
        save_job_seeker(name, disability, severity)
        st.success("구직자 정보가 저장되었습니다.")

    # 일자리 추천 보기
    if st.button("일자리 추천 보기"):
        listings = get_job_listings()
        ability_df = pd.read_excel("장애유형_직무능력_매칭표 (1).xlsx")
        ability_df['능력'].fillna(method='ffill', inplace=True)
        scores = []
        for _, row in listings.iterrows():
            score = calculate_match_score(row['required_skills'], disability, severity, ability_df)
            if score >= 0:
                scores.append((row['job_name'], score))
        scores.sort(key=lambda x: x[1], reverse=True)
        st.write("적합한 일자리 목록:")
        for job, score in scores:
            st.write(f"{job} (적합도 점수: {score})")

    ask_premium_service("구직자")

if user_type == "구인자":
    st.header("구인자 정보 입력")
    job_name = st.text_input("업무명")
    job_description = st.text_area("업무 설명")
    required_skills = st.text_input("필요 능력 (쉼표로 구분)")

    if st.button("구인자 등록"):
        save_job_listing(job_name, job_description, required_skills)
        st.success("일자리 정보가 저장되었습니다.")

    ask_premium_service("구인자")
