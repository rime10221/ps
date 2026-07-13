# E-daily 입원/응급 자동화

대한성형외과학회 E-daily 작성 화면을 Selenium으로 자동 입력하는 GUI 도구.
디버깅 포트로 띄운 Chrome에 attach 하여, 엑셀/텍스트 입력을 폼에 채운다.

> ⚠️ 이 저장소에는 환자 개인정보(입원목록.xls, ER.xls, 진단명.txt 등)가 **포함되어 있지 않습니다.**
> 해당 파일들은 `.gitignore` 로 제외됩니다. 실제 환자 데이터를 커밋하지 마세요.

## 구성
- `edaily_core.py` — 파싱 + Selenium 로직 (xls 파싱, 진단명 매칭, 폼 입력)
- `edaily_gui.py` — tkinter GUI
- `open_chrome_debug.py` — 디버깅 포트로 Chrome 실행 예제
- `ELEMENTS_REFERENCE.md` — 대상 페이지 엘리먼트/AJAX 구조 참조

## 기능
- **⓪ 크롬 디버깅 모드로 열기** — 포트 9222로 Chrome 실행 후 E-daily 접속
- **① 기본정보** — `입원목록.xls` → 입원 명수 설정 + 환자별 등록번호/병실/이름/성별/나이/보험/전문의 입력
- **② 진단명** — 화면에서 환자 1명 선택 + 진단명 텍스트 붙여넣기 → 코드조회 자동 매칭 입력
- **③ EMERGENCY ROOM** — `ER.xls` → 03 페이지에 병실 ER·전원 퇴원 고정으로 입력

저장(제출)은 자동으로 누르지 않으며, 사용자가 브라우저에서 검토 후 직접 저장한다.

## 실행
```bash
pip install -r requirements.txt
python edaily_gui.py
```

## exe 빌드
```bash
python -m PyInstaller --onefile --noconsole --name edaily_auto \
  --collect-all selenium --collect-all xlrd edaily_gui.py
```
