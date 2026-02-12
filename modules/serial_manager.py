# -*- coding: utf-8 -*-
"""
Serial Manager Module
Serial 통신 관련 기능들을 관리하는 모듈
GUI 의존성 없이 순수한 Serial 통신 기능만 제공
"""

from PySide6.QtCore import QIODevice, Signal, QObject
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from ast import List
from enum import Enum, auto


class SerialConnectionState(Enum):
    """Serial 연결 상태"""
    NONE = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


class SerialConfig:
    """Serial 포트 설정 클래스"""
    
    # 시리얼포트 상수 값
    BAUDRATES = (
        QSerialPort.Baud1200,
        QSerialPort.Baud2400,
        QSerialPort.Baud4800,
        QSerialPort.Baud9600,
        QSerialPort.Baud19200,
        QSerialPort.Baud38400,
        QSerialPort.Baud57600,
        QSerialPort.Baud115200,
    )
    
    BAUDRATES_STR = (
        "1200", "2400", "4800", "9600", "19200", 
        "38400", "57600", "115200", "Custom"
    )

    DATABITS = (
        QSerialPort.Data5,
        QSerialPort.Data6,
        QSerialPort.Data7,
        QSerialPort.Data8,
    )

    DATABITS_STR = ("5", "6", "7", "8")

    FLOWCONTROL = (
        QSerialPort.NoFlowControl,
        QSerialPort.HardwareControl,
        QSerialPort.SoftwareControl,
    )

    FLOWCONTROL_STR = ("None", "Hardware", "Software")

    PARITY = (
        QSerialPort.NoParity,
        QSerialPort.EvenParity,
        QSerialPort.OddParity,
        QSerialPort.SpaceParity,
        QSerialPort.MarkParity,
    )

    PARITY_STR = ("None", "Even", "Odd", "Space", "Mark")

    STOPBITS = (
        QSerialPort.OneStop,
        QSerialPort.OneAndHalfStop,
        QSerialPort.TwoStop,
    )

    STOPBITS_STR = ("1", "1.5", "2")

    def __init__(self):
        self.baud_rate_index = 3  # 9600 기본값
        self.baud_rate_custom = 9600
        self.data_bits_index = 3  # Data8 기본값
        self.flow_control_index = 0  # NoFlowControl 기본값
        self.parity_index = 0  # NoParity 기본값
        self.stop_bits_index = 0  # OneStop 기본값

    def get_baudrate(self):
        """현재 설정된 Baud Rate 반환"""
        if self.baud_rate_index >= len(self.BAUDRATES):
            return self.baud_rate_custom
        return self.BAUDRATES[self.baud_rate_index]

    def get_databits(self):
        """현재 설정된 Data Bits 반환"""
        return self.DATABITS[self.data_bits_index]

    def get_flowcontrol(self):
        """현재 설정된 Flow Control 반환"""
        return self.FLOWCONTROL[self.flow_control_index]

    def get_parity(self):
        """현재 설정된 Parity 반환"""
        return self.PARITY[self.parity_index]

    def get_stopbits(self):
        """현재 설정된 Stop Bits 반환"""
        return self.STOPBITS[self.stop_bits_index]


class SerialPortScanner:
    """Serial 포트 스캔 기능"""

    @staticmethod
    def debug_port_info():
        """포트 정보 디버그 출력 - 개발용"""
        try:
            # pyserial의 list_ports import
            try:
                from serial.tools import list_ports
                has_pyserial = True
            except ImportError:
                has_pyserial = False
                print("Warning: pyserial not available. Some details will be missing.")

            # QSerialPortInfo로 포트 목록 가져오기
            qt_ports = QSerialPortInfo.availablePorts()

            # pyserial로 포트 목록 가져오기 (더 상세한 정보)
            if has_pyserial:
                serial_ports = list(list_ports.comports())
            else:
                serial_ports = []

            print("\n" + "=" * 70)
            print("=== Serial Port Debug Info ===")
            print("=" * 70)

            for idx, port_info in enumerate(qt_ports, 1):
                port_name = port_info.portName()
                print(f"\n[{idx}] Port: {port_name}")
                print(f"  Description: {port_info.description()}")
                print(f"  Manufacturer: {port_info.manufacturer()}")
                print(f"  Serial Number: {port_info.serialNumber()}")
                print(f"  System Location: {port_info.systemLocation()}")
                print(f"  Is Null: {port_info.isNull()}")
                print(f"  Is Busy: {port_info.isBusy()}")

                if port_info.hasVendorIdentifier():
                    print(f"  Vendor ID: 0x{port_info.vendorIdentifier():04X}")
                else:
                    print(f"  Vendor ID: N/A")

                if port_info.hasProductIdentifier():
                    print(f"  Product ID: 0x{port_info.productIdentifier():04X}")
                else:
                    print(f"  Product ID: N/A")

                # pyserial 추가 정보와 매칭
                if has_pyserial:
                    for sp in serial_ports:
                        if sp.device == port_name:
                            print(f"\n  === pyserial 추가 정보 ===")
                            print(f"  hwid: {sp.hwid}")
                            print(f"  vid: 0x{sp.vid:04X}" if sp.vid else "  vid: N/A")
                            print(f"  pid: 0x{sp.pid:04X}" if sp.pid else "  pid: N/A")
                            print(f"  serial_number: {sp.serial_number}")
                            print(f"  location: {sp.location}")
                            print(f"  interface: {sp.interface}")  # ★ USB Interface Number!
                            print(f"  manufacturer: {sp.manufacturer}")
                            print(f"  product: {sp.product}")
                            print(f"  description: {sp.description}")
                            break

                print("-" * 70)

            print("=" * 70 + "\n")

            # Standard Baud Rates 출력
            print("Standard Baud Rates:")
            print(f"  {QSerialPortInfo.standardBaudRates()}")
            print("=" * 70 + "\n")

        except Exception as ex:
            print(f"debug_port_info Error: {ex}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def get_available_ports():
        """사용 가능한 Serial 포트 목록 반환"""
        try:
            available_ports = []
            info = QSerialPortInfo.availablePorts()

            # JLink 디바이스의 Serial Number별로 포트를 그룹화
            jlink_ports = {}  # {serial_number: [port_info1, port_info2, ...]}

            for port_info in info:
                port_description = f"{port_info.portName()} - {port_info.description()}"

                # JLink 포트인 경우
                if "JLink CDC UART Port" in port_info.description() or "J-Link" in port_info.description():
                    serial_number = port_info.serialNumber()

                    if serial_number:
                        # Serial Number별로 그룹화
                        if serial_number not in jlink_ports:
                            jlink_ports[serial_number] = []
                        jlink_ports[serial_number].append(port_info)

            # 최종 포트 목록 생성
            for port_info in info:
                port_description = f"{port_info.portName()} - {port_info.description()}"

                # JLink 포트 처리
                if "JLink CDC UART Port" in port_info.description() or "J-Link" in port_info.description():
                    serial_number = port_info.serialNumber()

                    if serial_number:
                        port_description += f" (SN: {serial_number})"

                available_ports.append(port_description)

            return available_ports
        except Exception as ex:
            print(f"get_available_ports Error: {ex}")
            return []

    @staticmethod
    def get_nordic_ports():
        """Nordic 개발보드용 포트 필터링 - JLink CDC UART Port는 location: None만"""
        try:
            # pyserial로 상세 정보 확인
            try:
                from serial.tools import list_ports
                has_pyserial = True
            except ImportError:
                has_pyserial = False

            all_ports = SerialPortScanner.get_available_ports()
            nordic_ports = []

            if has_pyserial:
                # pyserial로 location 정보 확인
                serial_ports = list(list_ports.comports())

                for port_name in all_ports:
                    # 실제 포트명 추출 (COM3 - JLink... 에서 COM3만)
                    actual_port_name = port_name.split(' ')[0]

                    # JLink CDC UART Port인 경우 - location: None만 필터링
                    if "JLink CDC UART Port" in port_name:
                        # pyserial에서 해당 포트의 location 확인
                        for sp in serial_ports:
                            if sp.device == actual_port_name:
                                # location이 None인 경우만 추가
                                if sp.location is None:
                                    nordic_ports.append(port_name)
                                break
                    # 다른 Nordic 관련 포트는 그대로 추가
                    elif any(keyword in port_name for keyword in ["J-Link", "CH340"]):
                        nordic_ports.append(port_name)
            else:
                # pyserial이 없으면 기존 방식대로
                for port_name in all_ports:
                    if any(keyword in port_name for keyword in ["JLink CDC UART Port", "J-Link", "CH340"]):
                        nordic_ports.append(port_name)

            return nordic_ports
        except Exception as ex:
            print(f"get_nordic_ports Error: {ex}")
            return []

    @staticmethod
    def get_filter_ports(filter_list: List) -> List:
        try:
            all_ports = SerialPortScanner.get_available_ports()
            filter_ports = []
            
            for port_name in all_ports:
                if any(keyword in port_name for keyword in filter_list):
                    filter_ports.append(port_name)
            
            return filter_ports
        except Exception as ex:
            print(f"get_filter_ports Error: {ex}")
            return []

class SerialManager(QObject):
    """Serial 통신 관리 클래스"""
    
    # 시그널 정의
    data_received = Signal(str)
    connection_changed = Signal(SerialConnectionState)
    error_occurred = Signal(str)
    
    def __init__(self, config=None, debug_callback=None):
        super().__init__()
        self.serial_port = QSerialPort()
        self.config = config or SerialConfig()
        self.debug_log = debug_callback if debug_callback else lambda msg: None
        self.connection_state = SerialConnectionState.NONE
        self.current_port_name = ""
        
        # 데이터 수신 시그널 연결
        self.serial_port.readyRead.connect(self._on_data_ready)
        self.debug_log("[SerialManager] Initialized")
        
    def connect_to_port(self, port_name):
        """지정된 포트에 연결"""
        self.debug_log(f"[SerialManager] Attempting to connect to {port_name}")
        try:
            if self.is_connected():
                self.debug_log(f"[SerialManager] Port already connected. Disconnecting first.")
                self.disconnect_port()
            
            actual_port_name = port_name.split(' ')[0]
            self.debug_log(f"[SerialManager] Actual port name: {actual_port_name}")
            
            port_info = QSerialPortInfo(actual_port_name)
            self.serial_port.setPort(port_info)
            
            baud_rate = self.config.get_baudrate()
            self.debug_log(f"[SerialManager] Setting BaudRate: {baud_rate}")
            if not self.serial_port.setBaudRate(baud_rate):
                raise Exception(f"Failed to set baud rate: {baud_rate}")
                
            self.debug_log(f"[SerialManager] Setting DataBits: {self.config.get_databits()}")
            self.serial_port.setDataBits(self.config.get_databits())
            self.debug_log(f"[SerialManager] Setting FlowControl: {self.config.get_flowcontrol()}")
            self.serial_port.setFlowControl(self.config.get_flowcontrol())
            self.debug_log(f"[SerialManager] Setting Parity: {self.config.get_parity()}")
            self.serial_port.setParity(self.config.get_parity())
            self.debug_log(f"[SerialManager] Setting StopBits: {self.config.get_stopbits()}")
            self.serial_port.setStopBits(self.config.get_stopbits())
            
            self.debug_log(f"[SerialManager] Opening port {actual_port_name}")
            if self.serial_port.open(QIODevice.ReadWrite):
                self.serial_port.setDataTerminalReady(True)
                self.connection_state = SerialConnectionState.CONNECTED
                self.current_port_name = actual_port_name
                self.debug_log(f"[SerialManager] Port {actual_port_name} opened successfully.")
                self.connection_changed.emit(self.connection_state)
                return True
            else:
                error_str = self.serial_port.errorString()
                raise Exception(f"Failed to open port: {actual_port_name}. Error: {error_str}")
                
        except Exception as ex:
            error_msg = f"[SerialManager] connect_to_port Error: {ex}"
            self.debug_log(error_msg)
            self.error_occurred.emit(str(ex))
            return False
    
    def disconnect_port(self):
        """포트 연결 해제"""
        self.debug_log(f"[SerialManager] Disconnecting from {self.current_port_name}")
        try:
            if self.serial_port.isOpen():
                self.serial_port.close()
                self.debug_log(f"[SerialManager] Port {self.current_port_name} closed.")
            
            self.connection_state = SerialConnectionState.DISCONNECTED
            self.current_port_name = ""
            self.connection_changed.emit(self.connection_state)
            return True
            
        except Exception as ex:
            error_msg = f"[SerialManager] disconnect_port Error: {ex}"
            self.debug_log(error_msg)
            self.error_occurred.emit(str(ex))
            return False
    
    def write_data(self, data):
        """데이터 전송"""
        try:
            if not self.is_connected():
                raise Exception("Port is not connected")
            
            if isinstance(data, str):
                data_to_write = data.encode('utf-8')
            else:
                data_to_write = data

            self.debug_log(f"[SerialManager] Writing data: {data_to_write!r}")
            bytes_written = self.serial_port.write(data_to_write)
            if bytes_written == -1:
                raise Exception("Write error")
            self.debug_log(f"[SerialManager] Wrote {bytes_written} bytes.")
            return bytes_written > 0
            
        except Exception as ex:
            error_msg = f"[SerialManager] write_data Error: {ex}"
            self.debug_log(error_msg)
            self.error_occurred.emit(str(ex))
            return False
    
    def _on_data_ready(self):
        """데이터 수신 처리"""
        try:
            bytes_available = self.serial_port.bytesAvailable()
            if bytes_available > 0:
                self.debug_log(f"[SerialManager] _on_data_ready: {bytes_available} bytes available.")
                data = self.serial_port.readAll()
                self.debug_log(f"[SerialManager] Raw data read: {bytes(data)!r}")
                decoded_data = bytes(data).decode('utf-8', errors='replace')
                self.debug_log(f"[SerialManager] Decoded data: {decoded_data!r}")

                cleaned_data = decoded_data.replace('\x00', '')
                if cleaned_data != decoded_data:
                    self.debug_log(f"[SerialManager] Null characters removed. Cleaned data: {cleaned_data!r}")

                self.data_received.emit(cleaned_data)
                
        except Exception as ex:
            error_msg = f"[SerialManager] _on_data_ready Error: {ex}"
            self.debug_log(error_msg)
            self.error_occurred.emit(str(ex))
    
    def is_connected(self):
        """연결 상태 확인"""
        return self.serial_port.isOpen() and self.connection_state == SerialConnectionState.CONNECTED
    
    def get_current_port(self):
        """현재 연결된 포트명 반환"""
        return self.current_port_name
    
    def get_connection_state(self):
        """현재 연결 상태 반환"""
        return self.connection_state
    
    def update_config(self, config):
        """설정 업데이트"""
        self.config = config
        
        # 연결된 상태라면 재연결
        if self.is_connected():
            current_port = self.current_port_name
            self.disconnect_port()
            self.connect_to_port(current_port)


class DualSerialManager:
    """두 개의 Serial 포트를 동시에 관리하는 클래스"""
    
    def __init__(self, config=None):
        self.serial1 = SerialManager(config)
        self.serial2 = SerialManager(config)
        
        # 각 포트의 시그널을 구분하여 전달
        self.serial1.data_received.connect(lambda data: self.on_serial1_data_received(data))
        self.serial2.data_received.connect(lambda data: self.on_serial2_data_received(data))
        
        self.serial1.connection_changed.connect(lambda state: self.on_serial1_connection_changed(state))
        self.serial2.connection_changed.connect(lambda state: self.on_serial2_connection_changed(state))
    
    def on_serial1_data_received(self, data):
        """Serial1 데이터 수신 처리 - 오버라이드하여 사용"""
        pass
    
    def on_serial2_data_received(self, data):
        """Serial2 데이터 수신 처리 - 오버라이드하여 사용"""
        pass
    
    def on_serial1_connection_changed(self, state):
        """Serial1 연결 상태 변경 처리 - 오버라이드하여 사용"""
        pass
    
    def on_serial2_connection_changed(self, state):
        """Serial2 연결 상태 변경 처리 - 오버라이드하여 사용"""
        pass
    
    def connect_serial1(self, port_name):
        """Serial1 연결"""
        return self.serial1.connect_to_port(port_name)
    
    def connect_serial2(self, port_name):
        """Serial2 연결"""
        return self.serial2.connect_to_port(port_name)
    
    def disconnect_serial1(self):
        """Serial1 연결 해제"""
        return self.serial1.disconnect_port()
    
    def disconnect_serial2(self):
        """Serial2 연결 해제"""
        return self.serial2.disconnect_port()
    
    def write_to_serial1(self, data):
        """Serial1에 데이터 전송"""
        return self.serial1.write_data(data)
    
    def write_to_serial2(self, data):
        """Serial2에 데이터 전송"""
        return self.serial2.write_data(data)
    
    def is_serial1_connected(self):
        """Serial1 연결 상태 확인"""
        return self.serial1.is_connected()
    
    def is_serial2_connected(self):
        """Serial2 연결 상태 확인"""
        return self.serial2.is_connected()