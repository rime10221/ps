# E-daily 입원(step=2) 자동화 - 엘리먼트/로직 참조

대상: `http://new.edaily.plasticsurgery.or.kr/edaily_new/regist.php?step=2&sid=176059`
디버깅 크롬: `127.0.0.1:9222` (selenium `debuggerAddress` 연결)

## 1. 메인 폼
- form action `/edaily_new/handle/proc_step02.php` (POST)
- hidden: `step=2`, `sid=176059`, `search_hid=39`
- 저장 버튼: `input[name=action][value='저장']`, `[value='저장 후 다음']`
- iframe 없음

## 2. 입원 명수 → 환자행 생성
- `#in_cnt` (select 0~200). **change 이벤트** 발생 시:
  - count > 기존행수 → AJAX `/edaily_new/ajax/add_admission.php` → `#admission_box`에 행 추가
  - count < 기존행수 → `#admission_{i}` 제거
- 각 환자행 = `#admission_{n}` (n = 1-base), 내부 sub 테이블 `#admission_sub_{n}`

## 3. 환자행(admission_{n}) 필드
`[]` 배열명 필드는 **id가 없음 → 행 인덱스(순서)로 매칭** 하거나 `#admission_{n}` 스코프 내에서 탐색.

| 항목 | selector | 값/비고 |
|---|---|---|
| 등록번호 | `input[name='a_regnum[]']` | text (id없음) |
| 전입 | `input[name='transfer_in[{n-1}]']` | 0-base index, value=Y |
| 병실 | `input[name='a_room[]']` | text (id없음) |
| 이름 | `input[name='a_name[]']` | text (id없음) |
| 성별 | `#a_sex_{n}_1`(남/M), `#a_sex_{n}_2`(여/F) | radio name=`a_sex_{n}` |
| 나이 | `input[name='a_age[]']` | text (id없음) |
| 보험 | `select[name='a_insurance_{n}[]']` (첫번째) | ''=선택, 1=보험, 2=비보험 |
| 전문의 | `select[name='a_doctor_{n}[]']` (첫번째) | (전문의 이름 목록 — 병원별 상이) |
| 진단코드 | `#a_sick_{n}_0` (readonly) + hidden `#a_sick_sid_{n}_0` | 팝업으로만 입력 |
| 진단메모 | `#a_consult_memo_{n}_0` (textarea) | 선택 시 영문명 자동입력됨 |
| 협진 | `select[name='a_consult_{n}[]']` A~E (class consult_chk) | A/B/C 선택시 옆 sub select 노출 |
| 상병 추가 | `a.add_a_sub[data='{n}']` (텍스트 "추가") | 클릭 → 상병 sub행 추가 |

## 4. 진단코드 입력 (핵심 플로우)
좌표: `v`=환자행번호, `sv`=상병 sub인덱스(0-base), `mode`=a

1. **코드조회 버튼 클릭** → `window.open('/popup/code.php?v={v}&sv={sv}&mode=a', 'code', ...)`
   - 팝업은 실제 window (opener = 메인). selenium은 새 window handle로 전환.
2. 팝업 `#search_keyword`에 **상병명 입력** → **keyup**마다 AJAX `/edaily_new/ajax/make_code.php {keyword}` → `#search_table`에 `tr.search_tr` append
3. 결과행 컬럼: [Code, 영문명칭, 한글명칭, 관리]. 선택 링크 = `a.insert_code`
   - 속성: `data`=내부sid, `code`=ICD(예 S02.121), `data_en`=영문명
4. **`a.insert_code` 클릭** → opener에 기록 후 **window.close()**:
   - `a_sick_{v}_{sv}` = code
   - `a_consult_memo_{v}_{sv}` = data_en
   - `a_sick_sid_{v}_{sv}` = data(sid)
5. **다음 상병 추가**: 메인에서 `a.add_a_sub[data='{v}']` 클릭
   → AJAX `add_a_sub.php {index:v, sub_count:현재sub수, hid:39, sid}` → 새 `admission_sub_tr_{v}` (새 `#a_sick_{v}_{sv+1}` + 새 코드조회 버튼 sv+1)
   → 1번부터 반복

### 매칭 전략 (진단명 텍스트 → 코드)
- 검색은 **영문 상병명**으로만 정확히 걸림 (원본 코드 `S0211`로 검색하면 0건, 실제 코드는 `S02.121`)
- 결과 중 `data_en` == 상병명(정규화: trim/다중공백/대소문자) 인 행 선택
- 교차검증: `code`의 점(.) 제거 == 텍스트의 코드컬럼 (예 `T14.1`→`T141`)

## 5. 입력값
### 입원목록.xls (입력값1) — **구형 OLE2/BIFF, xlrd 필요**
시트 `Page1`. 헤더 4행, 데이터 5행~. 컬럼(위치 기준):
구분 | 등록번호 | 성명 | _ | S/A(성별/나이 예:F/0) | _ | _ | 병실 | 입원예정일 | _ | 진료과 | 주치의 | 입원구분 | _ | 예약구분 | _ | 보험유형 | _ | 진단명/수술명 | _ | 의료진 참고사항
- 예(가상): 입원 | 000000000 | 홍길동 | | F/0 | | | 0000 | 20260712 | | PS | 홍의사 | 일반 | | | | 건강보험 | | [진단명] Example Dx ...
- 보험유형 "건강보험" → 보험(1) / 그외 → 비보험(2) 추정 (확인 필요)

### 진단명 (입력값2) — 프로그램에 붙여넣기(탭 구분, 진단명.txt 형식)
탭 구분 컬럼(0-base): [6]=코드(점없음), [7]=상병명(★=주진단 표시). 나머지 undefined/Y/- 등.
예: `- M undefined C N Y S0211 ★Fracture of frontal sinus, open Y ...`
→ 코드 S0211(=S02.121), 상병명 "Fracture of frontal sinus, open", ★=주진단

## 6. 자동화 주의점
- 진단코드칸 readonly → 반드시 팝업 경유(또는 opener 방식 JS 직접 주입)
- insert_code 클릭 시 팝업 자동 close → 상병마다 팝업 재오픈 필요
- `[]` 필드는 id 없음 → 행 스코프/인덱스 매칭
- 협진 sub는 A/B/C 선택시에만 노출(consult_chk change)
- transfer_in 인덱스는 0-base (`transfer_in[0]`)
