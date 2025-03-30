def 직무_매칭_점수_계산(일자리_제목, 필요한_능력, 장애유형):
    conn = 연결_함수()
    cursor = conn.cursor()
    
    # 구직자의 장애유형에 맞는 disability_id 확인
    cursor.execute("SELECT id FROM disabilities WHERE name=?", (장애유형,))
    disability_id = cursor.fetchone()
    
    if disability_id is None:
        print(f"장애유형 '{장애유형}'에 해당하는 disability_id가 없습니다.")
        return 0  # 장애유형에 해당하는 disability_id가 없으면 0점 처리
    
    disability_id = disability_id[0]  # disability_id 값을 추출
    print(f"구직자의 장애유형 '{장애유형}'에 해당하는 disability_id: {disability_id}")
    
    # 매칭 점수 계산
    매칭_점수 = []
    
    for 능력 in 필요한_능력:
        if 능력 is None or 능력 == "":
            continue  # 능력 값이 유효하지 않으면 넘어감
        
        # 능력 이름으로 매칭 처리 (abilities 테이블에서 id 조회)
        cursor.execute("SELECT id FROM abilities WHERE TRIM(UPPER(name)) = TRIM(UPPER(?))", (능력,))
        능력_id = cursor.fetchone()
        
        if 능력_id is None:
            print(f"능력 '{능력}'에 해당하는 ability_id가 없습니다.")  # 디버깅 메시지
            continue  # 능력 ID가 없다면 넘어감
        
        능력_id = 능력_id[0]  # 능력의 ID 값 추출
        print(f"능력 '{능력}'에 해당하는 ability_id: {능력_id}")
        
        # 장애유형에 맞는 능력 점수 가져오기 (matching 테이블에서)
        cursor.execute("""
            SELECT suitability 
            FROM matching 
            WHERE disability_id=? AND ability_id=?
        """, (disability_id, 능력_id))
        
        적합도 = cursor.fetchone()
        
        if 적합도 is None:
            print(f"장애유형 '{장애유형}'과 능력 '{능력}'에 대한 적합도 값이 없음.")  # 디버깅 메시지
            적합도 = (0,)  # 적합도가 없다면 0으로 처리
        
        적합도 = 적합도[0]
        print(f"장애유형 '{장애유형}'과 능력 '{능력}'의 적합도: {적합도}")  # 디버깅 메시지
        
        매칭_점수.append(적합도)
    
    # 점수 합계 계산
    총점수 = sum(매칭_점수)
    print(f"일자리: {일자리_제목}, 총점수: {총점수}")  # 디버깅용 출력
    
    conn.close()
    
    return 총점수
