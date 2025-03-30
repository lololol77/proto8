import sqlite3
import streamlit as st

# DB 연결 함수 (업로드된 DB 파일 사용)
def 연결_함수():
    db_path = 'job_matching_new.db'  # DB 파일 경로
    conn = sqlite3.connect(db_path)  # DB 파일 경로로 연결
    return conn

# 구직자 정보를 DB에 저장하는 함수
def 구직자_정보_저장(이름, 장애유형, 장애정도):
    conn = 연결_함수()  # DB 연결
    cursor = conn.cursor()
    
    # 구직자 정보 'job_seekers' 테이블에 저장
    cursor.execute("INSERT INTO job_seekers (name, disability, severity) VALUES (?, ?, ?)", (이름, 장애유형, 장애정도))
    
    conn.commit()  # 변경 사항 커밋
    conn.close()   # DB 연결 종료

# 구인자가 원하는 직무 정보와 능력 목록을 DB에 저장하는 함수
def 직무_정보_저장(일자리_제목, 필요한_능력):
    conn = 연결_함수()
    cursor = conn.cursor()
    
    # job_postings 테이블에 구인자 정보 저장
    cursor.execute("INSERT INTO job_postings (job_title, abilities) VALUES (?, ?)", (일자리_제목, ", ".join(필요한_능력)))
    
    # 구인자가 원하는 능력도 'abilities' 테이블에 저장
    for 능력 in 필요한_능력:
        cursor.execute("INSERT OR IGNORE INTO abilities (name) VALUES (?)", (능력,))
    
    conn.commit()
    conn.close()

# 매칭 점수 계산 (합계 점수만으로 비교)
def 직무_매칭_점수_계산(일자리_제목, 필요한_능력, 장애유형):
    conn = 연결_함수()
    cursor = conn.cursor()
    
    # 구직자의 장애유형에 맞는 점수 확인
    매칭_점수 = []
    
    # 구인자가 요구하는 능력과 매칭 점수 계산
    for 능력 in 필요한_능력:
        if 능력 is None or 능력 == "":
            continue  # 능력 값이 유효하지 않으면 넘어감
        
        # 능력 이름으로 매칭 처리 (abilities 테이블에서 id 조회)
        cursor.execute("SELECT id FROM abilities WHERE TRIM(UPPER(name)) = TRIM(UPPER(?))", (능력,))
        능력_id = cursor.fetchone()
        
        if 능력_id is None:
            print(f"능력 '{능력}'에 해당하는 ID가 없습니다.")  # 디버깅 메시지
            continue  # 능력 ID가 없다면 넘어감
        
        # 구직자의 장애유형에 맞는 점수 얻기 (disabilities 테이블에서 disability_id 조회)
        cursor.execute("""
            SELECT suitability 
            FROM matching 
            WHERE disability_id=(SELECT id FROM disabilities WHERE name=?)  -- disabilities 테이블에서 id를 찾음
            AND ability_id=?
        """, (장애유형, 능력_id[0]))
        
        적합도 = cursor.fetchone()
        if 적합도:
            적합도 = 적합도[0]
        else:
            적합도 = 0  # 매칭되지 않으면 0으로 처리
        
        매칭_점수.append(적합도)
    
    # 점수 합계 계산
    총점수 = sum(매칭_점수)
    
    print(f"일자리: {일자리_제목}, 총점수: {총점수}")  # 디버깅용 출력
    
    conn.close()
    
    return 총점수

# 구직자 매칭 및 순위 정렬
def 매칭_결과_정렬(필요한_능력, 장애유형):
    conn = sqlite3.connect("job_matching_new.db")  # DB 파일 경로
    cursor = conn.cursor()
    
    # 구인자가 원하는 능력에 맞는 구직자 매칭 처리
    매칭_결과 = []

    cursor.execute("SELECT job_title, abilities FROM job_postings")
    직무_등록 = cursor.fetchall()

    for 직무 in 직무_등록:
        일자리_제목 = 직무[0]
        능력들 = 직무[1].split(", ")

        # 매칭 점수 계산
        총점수 = 직무_매칭_점수_계산(일자리_제목, 능력들, 장애유형)
        
        # 점수가 0 이상인 일자리만 추가
        if 총점수 > 0:
            매칭_결과.append((일자리_제목, 총점수))
    
    # 점수를 기준으로 적합한 일자리 내림차순 정렬
    매칭_결과.sort(key=lambda x: x[1], reverse=True)

    conn.close()
    
    return 매칭_결과

# Streamlit UI 예시
st.title("장애인 일자리 매칭 시스템")

역할 = st.selectbox("사용자 역할 선택", ["구직자", "구인자"])

# 구직자 기능
if 역할 == "구직자":
    이름 = st.text_input("이름 입력")
    장애유형 = st.selectbox("장애유형", ["시각장애", "청각장애", "지체장애", "뇌병변장애", "언어장애", "안면장애", "신장장애", "심장장애", "간장애", "호흡기장애", "장루·요루장애", "뇌전증장애", "지적장애", "자폐성장애", "정신장애"])
    장애정도 = st.selectbox("장애 정도", ["심하지 않은", "심한"])
    
    if st.button("매칭 결과 보기"):  # 구직자 매칭 버튼
        # 구직자 정보 저장
        구직자_정보_저장(이름, 장애유형, 장애정도)
        
        st.write(f"구직자 정보가 저장되었습니다: {이름}, {장애유형}, {장애정도}")
        
        # 구인자가 등록한 능력 자동 불러오기
        필요한_능력 = []
        conn = 연결_함수()
        cursor = conn.cursor()
        
        # 구인자가 등록한 직무 정보 가져오기
        cursor.execute("SELECT abilities FROM job_postings")
        직무_등록 = cursor.fetchall()
        for 직무 in 직무_등록:
            필요한_능력 = 직무[0].split(", ")  # 구인자가 등록한 능력 목록
        
        conn.close()

        # 매칭 결과 출력
        매칭_결과 = 매칭_결과_정렬(필요한_능력, 장애유형)

        st.write("### 적합한 일자리 목록:")
        for 일자리_제목, 점수 in 매칭_결과:
            st.write(f"- {일자리_제목}: {점수}점")
        
        # **유료 서비스 관련 추가 질문 자동 표시**
        유료_서비스 = st.radio("유료 취업준비 서비스 이용하시겠습니까?", ["네", "아니요"])
        if 유료_서비스 == "네":
            st.write("유료 서비스 이용해주셔서 감사합니다!")
        else:
            st.write("유료 서비스 이용을 하지 않으셨습니다.")

        # 대화 종료 버튼 표시
        if st.button("대화 종료"):
            st.write("대화를 종료합니다.")

# 구인자 기능
elif 역할 == "구인자":
    일자리_제목 = st.text_input("일자리 제목 입력")
    능력들 = st.multiselect("필요한 능력 선택", ["주의력", "아이디어 발상 및 논리적 사고", "기억력", "지각능력", "수리능력", "공간능력", "언어능력", "지구력", "유연성 · 균형 및 조정", "체력", "움직임 통제능력", "정밀한 조작능력", "반응시간 및 속도", "청각 및 언어능력", "시각능력"])
    
    if st.button("등록"):  # 구인자 등록 버튼
        # 구인자 정보 저장
        직무_정보_저장(일자리_제목, 능력들)
        st.success("구인자 정보가 저장되었습니다!")
        st.write("일자리 제목:", 일자리_제목)
        st.write("필요 능력:", ", ".join(능력들))  # 능력 리스트를 쉼표로 구분해서 표시

        # **유료 서비스 관련 추가 질문 자동 표시**
        유료_서비스 = st.radio("유료 직무개발 서비스 이용하시겠습니까?", ["네", "아니요"])
        if 유료_서비스 == "네":
            st.write("유료 직무개발 서비스 이용해주셔서 감사합니다!")
        else:
            st.write("유료 직무개발 서비스를 이용하지 않으셨습니다.")

        # 대화 종료 버튼 표시
        if st.button("대화 종료"):
            st.write("대화를 종료합니다.")

