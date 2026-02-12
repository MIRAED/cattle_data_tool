#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial Manager 사용 예제
"""

import sys
import time

try:
    from PySide2.QtCore import QCoreApplication
    from PySide2.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtWidgets import QApplication

from .serial_manager import SerialManager, SerialConfig, SerialPortScanner, SerialConnectionState


class SerialExample:
    """Serial Manager 사용 예제 클래스"""
    
    def __init__(self):
        self.serial_manager = None
        
    def run_example(self):
        """예제 실행"""
        print("=== Serial Manager 예제 ===")
        
        # 1. 사용 가능한 포트 스캔
        print("\n1. 사용 가능한 포트 스캔:")
        ports = SerialPortScanner.get_available_ports()
        for i, port in enumerate(ports):
            print(f"  {i}: {port}")
        
        if not ports:
            print("  사용 가능한 포트가 없습니다.")
            return
        
        # 2. Serial 설정 생성
        print("\n2. Serial 설정:")
        config = SerialConfig()
        config.baud_rate_index = 3  # 9600
        config.data_bits_index = 3  # 8 bits
        print(f"  Baud Rate: {config.get_baudrate()}")
        print(f"  Data Bits: {config.get_databits()}")
        print(f"  Flow Control: {config.get_flowcontrol()}")
        print(f"  Parity: {config.get_parity()}")
        print(f"  Stop Bits: {config.get_stopbits()}")
        
        # 3. Serial Manager 생성 및 시그널 연결
        print("\n3. Serial Manager 생성:")
        self.serial_manager = SerialManager(config)
        self.serial_manager.data_received.connect(self.on_data_received)
        self.serial_manager.connection_changed.connect(self.on_connection_changed)
        self.serial_manager.error_occurred.connect(self.on_error_occurred)
        
        # 4. 첫 번째 포트에 연결 시도
        print(f"\n4. 포트 연결 시도: {ports[0]}")
        if self.serial_manager.connect_to_port(ports[0]):
            print("  연결 성공!")
            
            # 5. 데이터 전송 테스트
            print("\n5. 데이터 전송 테스트:")
            test_data = "Hello Serial!\r\n"
            if self.serial_manager.write_data(test_data):
                print(f"  전송 성공: {test_data.strip()}")
            else:
                print("  전송 실패")
            
            # 잠시 대기 (데이터 수신 확인)
            time.sleep(1)
            
            # 6. 연결 해제
            print("\n6. 연결 해제:")
            if self.serial_manager.disconnect_port():
                print("  연결 해제 성공")
            else:
                print("  연결 해제 실패")
        else:
            print("  연결 실패")
        
        print("\n=== 예제 완료 ===")
    
    def on_data_received(self, data):
        """데이터 수신 처리"""
        print(f"  수신 데이터: {repr(data)}")
    
    def on_connection_changed(self, state):
        """연결 상태 변경 처리"""
        if state == SerialConnectionState.CONNECTED:
            print("  상태: 연결됨")
        elif state == SerialConnectionState.DISCONNECTED:
            print("  상태: 연결 해제됨")
    
    def on_error_occurred(self, error_msg):
        """에러 발생 처리"""
        print(f"  에러: {error_msg}")


def main():
    """메인 함수"""
    app = QCoreApplication(sys.argv)
    
    example = SerialExample()
    example.run_example()
    
    # 이벤트 루프를 잠시 실행하여 시그널 처리
    app.processEvents()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())