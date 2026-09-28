# MacroV1

Windows에서 마우스 클릭 좌표를 등록하고, 서버 시간에 맞춰 클릭을 실행하는 Tkinter 앱입니다.

## Windows 실행 파일 만들기

빌드하는 PC에는 Python이 필요합니다. 완성된 `.exe`를 실행하는 PC에는 Python이나 VS Code가 필요하지 않습니다. PowerShell에서 이 저장소의 루트 폴더(`main.py`가 보이는 위치)를 열고 차례로 실행하세요.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name MacroV1 main.py
```

완료되면 `dist\MacroV1.exe`가 생성됩니다. 이 파일을 더블클릭하면 됩니다. 빌드는 Windows에서 실행해야 Windows용 `.exe`가 나옵니다.

설정을 저장하거나 앱을 정상 종료하면 `.exe`와 같은 폴더에 `data\settings.json`이 생성됩니다. 설정을 저장할 수 있는 폴더(예: 바탕화면의 별도 폴더)에 `.exe`를 두세요. 기존 설정과 클릭 좌표를 이어서 사용하려면 저장소의 `data\settings.json`을 `.exe` 옆의 `data\settings.json`으로 복사하면 됩니다. 다른 사람에게 배포할 때 개인 좌표나 URL이 담긴 설정 파일은 필요한 경우에만 함께 보내세요.

`--windowed` 빌드에서 창이 즉시 닫히거나 오류가 보이지 않으면, 아래처럼 콘솔이 보이는 버전을 다시 빌드하고 PowerShell에서 실행해 오류를 확인하세요.

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --console --name MacroV1 main.py
.\dist\MacroV1.exe
```

서버 시간 동기화에는 인터넷 연결이 필요하며, 전역 단축키와 자동 클릭은 Windows 권한 및 대상 프로그램의 권한에 영향을 받을 수 있습니다.
