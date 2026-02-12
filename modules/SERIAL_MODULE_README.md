# Serial 모듈화 작업 완료

Term.py의 Serial 관련 기능들을 별도 모듈로 분리하여 모듈화를 완료했습니다.

## 생성된 파일들

### 1. `serial_manager.py`
- **목적**: Serial 통신 관련 핵심 기능 제공
- **GUI 의존성**: 없음 (순수한 Serial 통신 기능만 제공)
- **주요 클래스**:
  - `SerialConfig`: Serial 포트 설정 관리
  - `SerialPortScanner`: 사용 가능한 포트 스캔
  - `SerialManager`: 단일 Serial 포트 관리
  - `DualSerialManager`: 두 개의 Serial 포트 동시 관리

### 2. `serial_config_gui.py`
- **목적**: Serial 설정을 위한 GUI 제공
- **주요 클래스**:
  - `SerialConfigWindow`: Serial 설정 창

### 3. `serial_example.py`
- **목적**: Serial Manager 사용 예제
- **기능**: 포트 스캔, 연결, 데이터 송수신 예제

## 주요 변경사항

### Term.py에서 제거된 부분
1. `serial_window` 클래스 → `serial_config_gui.py`로 이동
2. Serial 관련 상수들 (`BAUDRATES`, `DATABITS` 등) → `SerialConfig` 클래스로 이동
3. `getAvailablePort()` 메서드 → `SerialPortScanner.get_available_ports()`로 대체
4. `_open()`, `_open2()` 메서드 → `SerialManager.connect_to_port()`로 대체
5. 직접적인 `QSerialPort` 사용 → `SerialManager`를 통한 추상화

### Term.py에서 수정된 부분
1. Serial Manager 초기화 및 시그널 연결
2. `connect_serial()`, `disconnect_serial()` 메서드를 새로운 모듈 사용하도록 수정
3. `fillSerialInfo()` 메서드를 `SerialPortScanner` 사용하도록 수정
4. Serial 연결 상태 확인을 `SerialManager.is_connected()` 사용하도록 수정

## 사용 방법

### 기본 사용법
```python
from serial_manager import SerialManager, SerialConfig, SerialPortScanner

# 1. 포트 스캔
ports = SerialPortScanner.get_available_ports()

# 2. 설정 생성
config = SerialConfig()
config.baud_rate_index = 3  # 9600

# 3. Serial Manager 생성
serial_manager = SerialManager(config)

# 4. 시그널 연결
serial_manager.data_received.connect(on_data_received)
serial_manager.connection_changed.connect(on_connection_changed)

# 5. 연결
serial_manager.connect_to_port(ports[0])

# 6. 데이터 전송
serial_manager.write_data("Hello World!\r\n")

# 7. 연결 해제
serial_manager.disconnect_port()
```

### GUI 설정 창 사용법
```python
from serial_config_gui import SerialConfigWindow

config_window = SerialConfigWindow(config, icon_path)
config_window.config_saved.connect(on_config_saved)
config_window.show()
```

## 장점

1. **모듈화**: Serial 기능이 독립적인 모듈로 분리됨
2. **재사용성**: 다른 프로젝트에서도 쉽게 사용 가능
3. **유지보수성**: Serial 관련 코드가 한 곳에 집중됨
4. **테스트 용이성**: GUI와 분리되어 단위 테스트 가능
5. **확장성**: 새로운 Serial 기능 추가가 용이함

## 호환성

- 기존 Term.py의 기능은 그대로 유지됨
- 기존 설정 파일과 호환됨
- PySide2/PyQt5 모두 지원

## 테스트

```bash
python serial_example.py
```

위 명령으로 Serial Manager의 기본 기능을 테스트할 수 있습니다.