# -*- coding: utf-8 -*-
"""
RTT (Real Time Transfer) Module
pylink를 사용한 RTT 연결 및 통신 기능을 제공하는 순수 Python 모듈
GUI 프레임워크에 의존하지 않음
"""

try:
    import pylink
    PYLINK_AVAILABLE = True
except ImportError:
    PYLINK_AVAILABLE = False
    print("pylink not available. Install with: pip install pylink-square")

import time
import threading
from enum import Enum, auto
from typing import Callable, Optional, Dict, Any

# RTT 관련 상수
RTT_CONNECT_RETRY = 30
RTT_THREAD_TIMER_INTERVAL = 50  # 50ms
RTT_CHK_TIME = 8000  # about 5s

class RTTConnectionState(Enum):
    """RTT 연결 상태"""
    NONE = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()
    DISCONNECTED = auto()

class RTTReadThread(threading.Thread):
    """RTT 데이터 읽기 스레드 (순수 Python threading 사용)"""
    
    def __init__(self, jlink, data_callback=None, disconnect_callback=None, auto_reconnect_enabled=False):
        super().__init__(daemon=True)
        self.jlink = jlink
        self.data_callback = data_callback
        self.disconnect_callback = disconnect_callback
        self.auto_reconnect_enabled = auto_reconnect_enabled
        self.rtt_disconnect = False
        self.cnt_disconnect_chk = 0
        self._stop_event = threading.Event()

    def stop(self):
        """스레드 중지 요청"""
        self.rtt_disconnect = True
        self._stop_event.set()

    def run(self):
        """스레드 실행"""
        self.cnt_disconnect_chk = 0
        self.rtt_disconnect = False
        
        try:
            while self.jlink.connected() and not self._stop_event.is_set():
                # RTT 데이터 읽기
                try:
                    terminal_bytes = self.jlink.rtt_read(0, 1024)
                    if terminal_bytes:
                        str_data = "".join(map(chr, terminal_bytes))
                        if self.data_callback:
                            self.data_callback(str_data)
                except:
                    # RTT 읽기 실패 시 연결 상태 확인
                    if not self.jlink.connected():
                        break

                if self.rtt_disconnect:
                    break

                # 자동 재연결 체크 (기존 소스와 동일한 로직)
                if self.auto_reconnect_enabled:
                    try:
                        if self.jlink.halted():
                            self.cnt_disconnect_chk += 1
                            if self.cnt_disconnect_chk >= RTT_CHK_TIME / RTT_THREAD_TIMER_INTERVAL:
                                break
                        else:
                            self.cnt_disconnect_chk = 0
                    except:
                        # halted() 호출 실패 시 연결 상태 확인
                        try:
                            if not self.jlink.connected():
                                break
                        except:
                            break
                else:
                    self.cnt_disconnect_chk = 0

                # CPU 사용률을 줄이기 위해 적절한 sleep
                time.sleep(RTT_THREAD_TIMER_INTERVAL / 1000)

            if self.disconnect_callback:
                self.disconnect_callback()
                
        except Exception as ex:
            print(f"RTT Thread run Error: {ex}")
            if self.disconnect_callback:
                self.disconnect_callback()

class RTTManager:
    """RTT 연결 및 통신 관리 클래스 (순수 Python)"""
    
    # RTT 속도 옵션
    RTT_SPEED_OPTIONS = (
        5, 10, 20, 30, 50, 100, 200, 300, 500, 600, 750, 900, 1000, 1334, 1600, 
        2667, 3200, 4000, 4800, 5334, 6000, 8000, 9600, 12000, 15000, 20000, 
        25000, 30000, 40000, 50000
    )
    
    def __init__(self, config: Dict[str, Any], debug_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.debug_callback = debug_callback or (lambda x: print(x))
        
        # JLink 초기화
        self.jlink = None
        self.jlink_enable = False
        self.init_jlink()
        
        # RTT 상태
        self.connection_state = RTTConnectionState.NONE
        self.rtt_thread = None
        self.try_rtt_recon = False
        self.rtt_recon_signal = False
        self.manual_disconnect = False  # 수동 연결 해제 플래그
        self.last_error = ""  # 마지막 에러 메시지
        
        # 콜백 함수들
        self.data_received_callback = None
        self.connection_changed_callback = None
        self.auto_reconnect_enabled = False

    def init_jlink(self):
        """JLink 초기화"""
        if not PYLINK_AVAILABLE:
            self.jlink = None
            self.jlink_enable = False
            self.debug_callback("pylink not available, JLink disabled")
            return
        try:
            self.jlink = pylink.JLink()
            self.jlink_enable = True
            self.debug_callback("JLink initialized successfully")
        except Exception as ex:
            # Linux에서 라이브러리 경로 지정 시도
            try:
                import platform
                if platform.system() != "Windows":
                    self.jlink = pylink.JLink(lib=pylink.library.Library(dllpath='/opt/SEGGER/JLink/libjlinkarm.so'))
                    self.jlink_enable = True
                    self.debug_callback("JLink initialized with Linux library")
                else:
                    raise ex
            except:
                self.jlink = None
                self.jlink_enable = False
                self.debug_callback(f"JLink initialization failed: {ex}")

    def set_data_received_callback(self, callback: Callable[[str], None]):
        """데이터 수신 콜백 설정"""
        self.data_received_callback = callback

    def set_connection_changed_callback(self, callback: Callable[[RTTConnectionState], None]):
        """연결 상태 변경 콜백 설정"""
        self.connection_changed_callback = callback

    def set_auto_reconnect(self, enabled: bool):
        """자동 재연결 설정"""
        self.auto_reconnect_enabled = enabled
        # 실행 중인 스레드에도 설정 반영
        if self.rtt_thread:
            self.rtt_thread.auto_reconnect_enabled = enabled

    def is_enabled(self) -> bool:
        """JLink 사용 가능 여부"""
        return self.jlink_enable

    def is_connected(self) -> bool:
        """RTT 연결 상태 확인"""
        try:
            # JLink 객체와 연결 상태, RTT 스레드 상태를 모두 확인
            if not self.jlink:
                return False
            
            # JLink 연결 상태 확인
            if not self.jlink.connected():
                return False
                
            # RTT 스레드 상태 확인
            if not self.rtt_thread or not self.rtt_thread.is_alive():
                return False
                
            # 연결 상태 확인
            return self.connection_state == RTTConnectionState.CONNECTED
            
        except Exception as ex:
            self.debug_callback(f"is_connected check error: {ex}")
            return False

    def get_serial_number(self) -> Optional[int]:
        """현재 연결된 JLink 시리얼 번호 반환"""
        if self.jlink and hasattr(self.jlink, 'serial_number'):
            return self.jlink.serial_number
        return None

    def get_connection_info(self) -> Dict[str, Any]:
        """연결 정보 반환"""
        if not self.is_connected():
            return {}
        
        return {
            'serial_number': self.get_serial_number(),
            'speed': getattr(self.jlink, 'speed', None),
            'device_name': self.config.get('device_name', ''),
            'state': self.connection_state
        }

    def connect(self, serial_number: str = "", auto_reconnect: bool = False) -> bool:
        """RTT 연결"""
        if not self.jlink_enable:
            self.debug_callback("JLink not available")
            return False

        try:
            self.connection_state = RTTConnectionState.CONNECTING
            if self.connection_changed_callback:
                self.connection_changed_callback(self.connection_state)

            # 이미 연결된 경우 연결 해제
            if self.is_connected():
                self.disconnect()

            target_device = self.config.get('device_name', '')
            self.debug_callback(f"Target device: {target_device}")
            self.debug_callback(f"Serial number input: '{serial_number}'")
            
            # JLink 열기 - 기존 로직과 동일하게 수정
            try:
                self.jlink.close()
                
                # 시리얼 번호가 있으면 해당 번호로 연결 시도
                if serial_number.strip():
                    try:
                        serial_int = int(serial_number)
                        self.debug_callback(f"Trying to open JLink with serial: {serial_int}")
                        self.jlink.open(serial_int)
                        actual_serial = self.jlink.serial_number
                        self.debug_callback(f"JLink opened with serial: {actual_serial}")
                    except Exception as ex:
                        self.debug_callback(f"JLink open with serial_number Error: {ex}")
                        # 시리얼 번호로 실패하면 자동으로 찾기 시도
                        self.debug_callback("Trying to open JLink automatically...")
                        self.jlink.open()
                        actual_serial = self.jlink.serial_number
                        self.debug_callback(f"JLink opened automatically with serial: {actual_serial}")
                        # 설정 업데이트
                        self.config['rttserialno'] = str(actual_serial)
                else:
                    # 시리얼 번호가 없으면 자동으로 찾기
                    self.debug_callback("No serial number provided, trying to open JLink automatically...")
                    self.jlink.open()
                    actual_serial = self.jlink.serial_number
                    self.debug_callback(f"JLink opened automatically with serial: {actual_serial}")
                    # 설정 업데이트
                    self.config['rttserialno'] = str(actual_serial)
                    
            except Exception as ex:
                self.last_error = f"JLink open error: {ex}"
                self.debug_callback(self.last_error)
                self.connection_state = RTTConnectionState.DISCONNECTED
                if self.connection_changed_callback:
                    self.connection_changed_callback(self.connection_state)
                return False

            # 타겟 연결
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            
            try:
                rtt_speed = self.config.get('rtt_speed', 1000)
                self.jlink.connect(target_device, speed=rtt_speed)
            except Exception as ex:
                self.last_error = f"Target connect error: {ex}"
                self.debug_callback(self.last_error)
                
                # 자동 디바이스 감지 시도
                try:
                    index = self.jlink._dll.JLINKARM_DEVICE_GetIndex(0)
                    if index == -1:
                        self.last_error = "No target device found"
                        self.debug_callback(self.last_error)
                        self.disconnect()
                        return False
                    else:
                        device = self.jlink.supported_device(index)
                        self.config['device_name'] = device.name
                        self.debug_callback(f"Auto-detected device: {device.name}")
                except Exception as detect_ex:
                    self.last_error = f"Device detection failed: {detect_ex}"
                    self.debug_callback(self.last_error)
                    self.disconnect()
                    return False

            if not self.jlink.connected():
                self.last_error = "Target connection failed"
                self.debug_callback(self.last_error)
                self.disconnect()
                return False

            # RTT 시작
            speed = self.jlink.speed
            serial = self.jlink.serial_number
            self.debug_callback(f"Connected to target, Serial: {serial}, Speed: {speed}")
            
            self.jlink.rtt_start()

            # RTT 버퍼 확인
            count = 0
            while count < RTT_CONNECT_RETRY:
                try:
                    num_up = self.jlink.rtt_get_num_up_buffers()
                    num_down = self.jlink.rtt_get_num_down_buffers()
                    if num_up > 0:
                        self.debug_callback(f"RTT started, {num_up} up bufs, {num_down} down bufs")
                        break
                except:
                    pass
                time.sleep(0.1)
                count += 1

            if count >= RTT_CONNECT_RETRY:
                self.last_error = f"RTT buffer not found after {RTT_CONNECT_RETRY} retries"
                self.debug_callback(self.last_error)
                self.disconnect()
                return False

            # RTT 읽기 스레드 시작
            self.auto_reconnect_enabled = auto_reconnect
            self.rtt_thread = RTTReadThread(
                jlink=self.jlink,
                data_callback=self.data_received_callback,
                disconnect_callback=self._on_disconnected,
                auto_reconnect_enabled=self.auto_reconnect_enabled
            )
            self.rtt_thread.start()

            self.connection_state = RTTConnectionState.CONNECTED
            self.last_error = ""  # 연결 성공 시 에러 메시지 초기화
            if self.connection_changed_callback:
                self.connection_changed_callback(self.connection_state)
                
            # 연결 성공 정보 출력
            speed = getattr(self.jlink, 'speed', 'Unknown')
            serial = getattr(self.jlink, 'serial_number', 'Unknown')
            self.debug_callback(f"RTT connected successfully - Serial: {serial}, Speed: {speed}")
            return True

        except Exception as ex:
            self.last_error = f"RTT connect error: {ex}"
            self.debug_callback(self.last_error)
            self.disconnect()
            return False

    def disconnect(self, manual=True):
        """RTT 연결 해제"""
        try:
            self.manual_disconnect = manual  # 수동 연결 해제 여부 설정
            self.connection_state = RTTConnectionState.DISCONNECTING
            if self.connection_changed_callback:
                self.connection_changed_callback(self.connection_state)
            
            # RTT 스레드 종료
            if self.rtt_thread:
                self.rtt_thread.stop()
                # 스레드가 빠르게 종료되도록 더 짧은 timeout 사용
                self.rtt_thread.join(timeout=1.0)
                if self.rtt_thread.is_alive():
                    # 강제 종료가 필요한 경우를 위한 추가 처리
                    pass
                self.rtt_thread = None

            # JLink 연결 해제
            if self.jlink and self.jlink.connected():
                self.jlink.rtt_stop()
                self.jlink.close()

            self.connection_state = RTTConnectionState.DISCONNECTED
            if self.connection_changed_callback:
                self.connection_changed_callback(self.connection_state)
                
            self.debug_callback("RTT disconnected")

        except Exception as ex:
            self.debug_callback(f"RTT disconnect error: {ex}")

    def _on_disconnected(self):
        """연결 해제 콜백 처리"""
        self.manual_disconnect = False  # 자동 연결 해제
        self.connection_state = RTTConnectionState.DISCONNECTED
        if self.connection_changed_callback:
            self.connection_changed_callback(self.connection_state)

    def write_data(self, data) -> bool:
        """RTT 데이터 전송"""
        if not self.is_connected():
            self.debug_callback("RTT write failed: not connected")
            return False
            
        try:
            if isinstance(data, str):
                bytes_data = list(bytearray(data.encode()))
            else:
                bytes_data = list(bytearray(data))
                
            self.jlink.rtt_write(0, bytes_data)
            return True
        except Exception as ex:
            self.debug_callback(f"RTT write error: {ex}")
            
            # 쓰기 실패 시 연결 상태 재확인
            try:
                if not self.jlink.connected():
                    self.debug_callback("RTT write failed: JLink disconnected")
                    # 연결이 끊어진 경우 상태 업데이트
                    if self.connection_state == RTTConnectionState.CONNECTED:
                        self._on_disconnected()
            except:
                pass
                
            return False

    def reconnect(self, serial_number: str = "") -> bool:
        """RTT 재연결"""
        self.debug_callback("RTT reconnecting...")
        self.disconnect(manual=False)  # 재연결은 자동 연결 해제로 처리
        time.sleep(0.1)
        return self.connect(serial_number, self.auto_reconnect_enabled)

    def get_connection_state(self) -> RTTConnectionState:
        """현재 연결 상태 반환"""
        return self.connection_state

    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if key in ['device_name', 'rtt_speed', 'rttserialno']:
                self.config[key] = value

    def get_config(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return {
            'device_name': self.config.get('device_name', ''),
            'rtt_speed': self.config.get('rtt_speed', 1000),
            'rttserialno': self.config.get('rttserialno', ''),
            'rtt_discon_detect': self.config.get('rtt_discon_detect', 8.0)
        }

    def is_manual_disconnect(self) -> bool:
        """수동 연결 해제 여부 반환"""
        return self.manual_disconnect

    def get_last_error(self) -> str:
        """마지막 에러 메시지 반환"""
        return self.last_error

    def cleanup(self):
        """리소스 정리"""
        self.disconnect()

# CLI 사용을 위한 간단한 예제 클래스
class RTTCLIInterface:
    """CLI에서 RTT를 사용하기 위한 간단한 인터페이스"""
    
    def __init__(self, config=None):
        self.config = config or {
            'device_name': '',
            'rtt_speed': 1000,
            'rttserialno': '',
            'rtt_discon_detect': 8.0
        }
        self.rtt_manager = RTTManager(self.config, debug_callback=self.print_debug)
        self.rtt_manager.set_data_received_callback(self.on_data_received)
        self.rtt_manager.set_connection_changed_callback(self.on_connection_changed)
        
    def print_debug(self, message):
        """디버그 메시지 출력"""
        print(f"[RTT] {message}")
        
    def on_data_received(self, data):
        """데이터 수신 처리"""
        print(f"RX: {data}", end='')
        
    def on_connection_changed(self, state):
        """연결 상태 변경 처리"""
        print(f"[RTT] Connection state: {state.name}")
        
    def connect(self, serial_number="", device_name="", speed=1000):
        """RTT 연결"""
        if device_name:
            self.config['device_name'] = device_name
        if speed != 1000:
            self.config['rtt_speed'] = speed
            
        return self.rtt_manager.connect(serial_number)
        
    def disconnect(self):
        """RTT 연결 해제"""
        self.rtt_manager.disconnect()
        
    def send(self, data):
        """데이터 전송"""
        return self.rtt_manager.write_data(data)
        
    def is_connected(self):
        """연결 상태 확인"""
        return self.rtt_manager.is_connected()
        
    def get_info(self):
        """연결 정보 반환"""
        return self.rtt_manager.get_connection_info()

# CLI 사용 예제
if __name__ == "__main__":
    import sys
    
    # 간단한 CLI 예제
    rtt = RTTCLIInterface()
    
    print("RTT CLI Interface")
    print("Commands: connect, disconnect, send <data>, info, quit")
    
    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "connect":
                serial = cmd[1] if len(cmd) > 1 else ""
                if rtt.connect(serial):
                    print("Connected successfully")
                else:
                    print("Connection failed")
                    
            elif cmd[0] == "disconnect":
                rtt.disconnect()
                print("Disconnected")
                
            elif cmd[0] == "send" and len(cmd) > 1:
                data = " ".join(cmd[1:])
                if rtt.send(data + "\n"):
                    print(f"TX: {data}")
                else:
                    print("Send failed - not connected")
                    
            elif cmd[0] == "info":
                info = rtt.get_info()
                if info:
                    for key, value in info.items():
                        print(f"  {key}: {value}")
                else:
                    print("Not connected")
                    
            elif cmd[0] == "quit":
                rtt.disconnect()
                break
                
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            rtt.disconnect()
            break
        except Exception as ex:
            print(f"Error: {ex}")