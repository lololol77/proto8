import sqlite3
import streamlit as st

# DB 연결 함수 (업로드된 DB 파일 사용)
def connect_db():
    db_path = 'job_matching_new.db'  # DB 파일 경로
    conn = sqlite3.connect(db_path)  # DB 파일 경로로 연결
    return conn

# 구직자 정보를 DB에 저장하는 함수
def save_job_seeker(name, disability, severity):
    conn = connect_db()  # DB 연결
    cursor = conn.cursor()
    
    # 구직자 정보 'job_seekers' 테이블에 저장
    cursor.execute("INSERT INTO job_seekers (name, disability, severity) VALUES (?, ?, ?)", (name, disability, severity))
    
    conn.commit()  # 변경 사항 커밋
    conn.close()   # DB 연결 종료

# 구인자가 원하는 직무 정보와 능력 목록을 DB에 저장하는 함수
def save_job_posting(job_title, abilities_required):
    conn = connect_db()
    cursor = conn.cursor()
    
    # job_postings 테이블에 구인자 정보 저장
    cursor.execute("INSERT INTO job_postings (job_title, abilities) VALUES (?, ?)", (job_title, ", ".join(abilities_required)))
    
    # 구인자가 원하는 능력도 'abilities' 테이블에 저장
    for ability in abilities_required:
        cursor.execute("INSERT OR IGNORE INTO abilities (name) VALUES (?)", (ability,))
    
    conn.commit()
    conn.close()

# 매칭 점수 계산 (합계 점수만으로 비교)
def match_jobs(job_title, abilities_required, disability_type):
    conn = connect_db()
    cursor = conn.cursor()
    
    # 구직자의 장애유형에 맞는 점수 확인
    matching_scores = []
    
    # 구인자가 요구하는 능력과 매칭 점수 계산
    for ability in abilities_required:
        # 능력 ID 얻기
        cursor.execute("SELECT ability_id FROM abilities WHERE name=?", (ability,))
        ability_id = cursor.fetchone()
        
        if ability_id is None:
            continue  # 능력 ID가 없다면 넘어감
        
        # 구직자의 장애유형에 맞는 점수 얻기
        cursor.execute("""
            SELECT suitability 
            FROM matching 
            WHERE disability_id=(SELECT disability_id FROM disabilities WHERE name=?) 
            AND ability_id=?
        """, (disability_type, ability_id[0]))
        
        suitability = cursor.fetchone()
        if suitability:
            suitability = suitability[0]
        else:
            suitability = 0  # 매칭되지 않으면 0으로 처리
        
        matching_scores.append(suitability)
    
    # 점수 합계 계산
    total_score = sum(matching_scores)
    
    conn.close()
    
    return total_score

# 구직자 매칭 및 순위 정렬
def get_sorted_matching_jobs(abilities_required, disability_type):
    conn = sqlite3.connect("job_matching_new.db")  # DB 파일 경로
    cursor = conn.cursor()
    
    # 구인자가 원하는 능력에 맞는 구직자 매칭 처리
    matching_results = []

    cursor.execute("SELECT job_title, abilities FROM job_postings")
    job_postings = cursor.fetchall()

    for job_posting in job_postings:
        job_title = job_posting[0]
        abilities = job_posting[1].split(", ")

        # 매칭 점수 계산
        total_score = match_jobs(job_title, abilities_required, disability_type)
        
        if total_score >= 1:  # 적합한 일자리 점수만 표시
            matching_results.append((job_title, total_score))
    
    # 점수를 기준으로 적합한 일자리 내림차순 정렬
    matching_results.sort(key=lambda x: x[1], reverse=True)

    conn.close()
    
    return matching_results

# Streamlit UI 예시
st.title("장애인 일자리 매칭 시스템")

role = st.selectbox("사용자 역할 선택", ["구직자", "구인자"])

# 구직자 기능
if role == "구직자":
    name = st.text_input("이름 입력")
    disability = st.selectbox("장애유형", ["시각장애", "청각장애", "지체장애", "뇌병변장애", "언어장애", "안면장애", "신장장애", "심장장애", "간장애", "호흡기장애", "장루·요루장애", "뇌전증장애", "지적장애", "자폐성장애", "정신장애"])
    severity = st.selectbox("장애 정도", ["심하지 않은", "심한"])
    
    if st.button("매칭 결과 보기"):  # 구직자 매칭 버튼
        # 구직자 정보 저장
        save_job_seeker(name, disability, severity)
        
        st.write(f"구직자 정보가 저장되었습니다: {name}, {disability}, {severity}")
        
        # 구인자가 등록한 능력 자동 불러오기
        abilities_required = []
        conn = connect_db()
        cursor = conn.cursor()
        
        # 구인자가 등록한 직무 정보 가져오기
        cursor.execute("SELECT abilities FROM job_postings")
        job_postings = cursor.fetchall()
        for job_posting in job_postings:
            abilities_required = job_posting[0].split(", ")  # 구인자가 등록한 능력 목록
        
        conn.close()

        # 매칭 결과 출력
        matching_results = get_sorted_matching_jobs(abilities_required, disability)

        st.write("### 적합한 일자리 목록:")
        for job_title, score in matching_results:
            st.write(f"- {job_title}: {score}점")

# 구인자 기능
elif role == "구인자":
    job_title = st.text_input("일자리 제목 입력")
    abilities = st.multiselect("필요한 능력 선택", ["주의력", "아이디어 발상 및 논리적 사고", "기억력", "지각능력", "수리능력", "공간능력", "언어능력", "지구력", "유연성 · 균형 및 조정", "체력", "움직임 통제능력", "정밀한 조작능력", "반응시간 및 속도", "청각 및 언어능력", "시각능력"])
    
    if st.button("등록"):  # 구인자 등록 버튼
        # 구인자 정보 저장
        save_job_posting(job_title, abilities)
        st.success("구인자 정보가 저장되었습니다!")
        st.write("일자리 제목:", job_title)
        st.write("필요 능력:", ", ".join(abilities))  # 능력 리스트를 쉼표로 구분해서 표시

# 유료 서비스 여부 확인
if st.button("대화 종료"):
    if role == "구직자":
        use_service = st.radio("유료 취업준비 서비스 이용하시겠습니까?", ["네", "아니요"])
    else:
        use_service = st.radio("유료 직무개발 서비스 이용하시겠습니까?", ["네", "아니요"])
    if use_service == "네":
        st.write("서비스를 이용해 주셔서 감사합니다!")
    else:
        st.write("대화를 종료합니다.")

