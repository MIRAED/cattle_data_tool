# -*- coding: utf-8 -*-
"""
RTT GUI Components
RTT 모듈을 위한 GUI 컴포넌트들 (PySide2/PyQt5 지원)
"""

try:
    from PySide2.QtCore import Qt, QThread, Signal, Slot, QEvent
    from PySide2.QtWidgets import (QWidget, QLabel, QLineEdit, QGridLayout,
                                   QVBoxLayout, QPushButton, QComboBox,
                                   QCheckBox, QMessageBox, QHBoxLayout, QApplication)
    from PySide2.QtGui import QIcon
    print("RTT GUI: PySide2")
except ImportError:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal as Signal, pyqtSlot as Slot, QEvent
    from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QGridLayout,
                                 QVBoxLayout, QPushButton, QComboBox,
                                 QCheckBox, QMessageBox, QHBoxLayout, QApplication)
    from PyQt5.QtGui import QIcon
    print("RTT GUI: PyQt5")

import os
from .rtt_module import RTTManager, RTTConnectionState

class DPIAwareMixin:
  """DPI 변경을 감지하고 폰트를 재조정하는 믹스인 클래스"""

  def _init_dpi_handling(self):
    """DPI 처리를 위한 초기화 (서브클래스의 __init__에서 호출)"""
    self._current_dpi = None
    self._base_font_size = None

    # 화면 변경 시그널 연결
    try:
      app = QApplication.instance()
      if app:
        app.primaryScreen().logicalDotsPerInchChanged.connect(self._on_dpi_changed)
        # 모든 화면의 DPI 변경 감지
        for screen in app.screens():
          screen.logicalDotsPerInchChanged.connect(self._on_dpi_changed)
    except:
      pass

    # 초기 DPI 저장
    self._update_current_dpi()

  def _update_current_dpi(self):
    """현재 DPI를 저장합니다."""
    try:
      app = QApplication.instance()
      if app:
        screen = app.screenAt(self.pos())
        if not screen:
          screen = app.primaryScreen()
        self._current_dpi = screen.logicalDotsPerInch()
    except:
      pass

  def _on_dpi_changed(self, dpi=None):
    """DPI 변경 시 폰트 크기를 재조정합니다."""
    try:
      old_dpi = self._current_dpi
      self._update_current_dpi()

      if old_dpi and self._current_dpi and old_dpi != self._current_dpi:
        # DPI가 변경되면 폰트 크기 재조정
        self._adjust_fonts_for_dpi()
    except:
      pass

  def _adjust_fonts_for_dpi(self):
    """현재 DPI에 맞게 폰트 크기를 조정합니다. (서브클래스에서 오버라이드)"""
    try:
      # 기본 구현: 모든 자식 위젯의 폰트 업데이트
      self.update()

      # 자식 위젯들도 업데이트
      for child in self.findChildren(QWidget):
        child.update()
    except:
      pass

  def changeEvent(self, event):
    """위젯 상태 변경 이벤트를 처리합니다."""
    try:
      super().changeEvent(event)
    except:
      pass

    try:
      # 화면 변경 감지
      if event.type() == QEvent.ScreenChangeEvent:
        self._on_dpi_changed()
    except:
      pass

class RTTConfigWindow(DPIAwareMixin, QWidget):
    """RTT 설정 창"""

    def __init__(self, config, save_callback):
        super().__init__()
        self.config = config
        self.save_callback = save_callback
        self.initUI()
        self._init_dpi_handling()

    def initUI(self):
        vbox = QVBoxLayout()
        gridRTT = QGridLayout()
        vbox.addLayout(gridRTT)

        # Device Type
        lblType = QLabel('Board type')
        lblType.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lnType = QLineEdit(self.config.get('device_name', ''))
        self.lnType.setMinimumWidth(1)

        # Speed
        lblSpeed = QLabel('Speed')
        lblSpeed.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboSpeed = QComboBox()
        self.comboSpeed.setMinimumWidth(1)

        # Buttons
        btnsave = QPushButton('Save')
        btnsave.setMinimumWidth(1)
        btnsave.clicked.connect(self.saveconfig)
        btncancel = QPushButton('Cancel')
        btncancel.setMinimumWidth(1)
        btncancel.clicked.connect(self.cancelconfig)

        gridRTT.addWidget(lblType, 0, 0)
        gridRTT.addWidget(self.lnType, 0, 1)
        gridRTT.addWidget(lblSpeed, 1, 0)
        gridRTT.addWidget(self.comboSpeed, 1, 1)
        gridRTT.addWidget(btnsave, 3, 0)
        gridRTT.addWidget(btncancel, 3, 1)

        gridRTT.setColumnStretch(0, 1)
        gridRTT.setColumnStretch(1, 1)

        # RTT 속도 옵션 추가
        self.comboSpeed.insertItems(0, [str(x) for x in RTTManager.RTT_SPEED_OPTIONS])

        try:
            current_speed = self.config.get('rtt_speed', 1000)
            self.comboSpeed.setCurrentIndex(RTTManager.RTT_SPEED_OPTIONS.index(current_speed))
        except:
            self.config['rtt_speed'] = 1000
            self.comboSpeed.setCurrentIndex(RTTManager.RTT_SPEED_OPTIONS.index(1000))

        self.setLayout(vbox)
        self.resize(300, 100)
        self.setWindowTitle("RTT Config")
        
        # 아이콘 설정 (옵션)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'Term_icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

    def showmodel(self):
        """모달 창으로 표시"""
        return super().exec_()

    @Slot()
    def saveconfig(self):
        """설정 저장"""
        try:
            self.config['device_name'] = self.lnType.text()
            self.config['rtt_speed'] = int(self.comboSpeed.currentText())
            
            if self.save_callback:
                self.save_callback()
            self.close()
        except Exception as ex:
            print(f"RTT Config save error: {ex}")

    @Slot()
    def cancelconfig(self):
        """설정 취소"""
        try:
            self.close()
        except Exception as ex:
            print(f"RTT Config cancel error: {ex}")

class RTTWidget(QWidget):
    """RTT 탭 위젯"""
    
    def __init__(self, config, rtt_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.rtt_manager = rtt_manager
        self.parent_window = parent
        self.initUI()
        
    def initUI(self):
        """RTT 탭 UI 초기화"""
        vbox = QVBoxLayout()
        vbox.setContentsMargins(3, 3, 3, 3)
        
        # RTT 연결 컨트롤
        grid_rtt = QGridLayout()
        
        # RTT 연결 버튼들
        self.btnRTTCon = QPushButton('RTT Con(F1)')
        self.btnRTTCon.setMinimumWidth(1)
        self.btnRTTCon.setShortcut("F1")
        
        self.btnRTTReCon = QPushButton('RTT Recon(F4)')
        self.btnRTTReCon.setMinimumWidth(1)
        self.btnRTTReCon.setShortcut("F4")
        
        # RTT 설정 버튼
        self.btnRTTConfig = QPushButton('RTT Config')
        self.btnRTTConfig.setMinimumWidth(1)
        
        # RTT 시리얼 번호 입력
        self.lineRTTSN = QLineEdit(self.config.get('rttserialno', ''))
        self.lineRTTSN.setMinimumWidth(1)
        
        # RTT 강제 연결 해제 버튼
        self.btnForceDiscon = QPushButton('Force discon')
        self.btnForceDiscon.setMinimumWidth(1)
        
        # 자동 재연결 체크박스
        lbl_rtt_auto_recon = QLabel('Connect repeat')
        lbl_rtt_auto_recon.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.chkbox_rtt_auto_recon = QCheckBox()
        
        # 그리드에 위젯 배치
        grid_rtt.addWidget(self.btnRTTCon, 0, 0)
        grid_rtt.addWidget(self.btnRTTReCon, 0, 1)
        grid_rtt.addWidget(self.btnRTTConfig, 0, 2)
        grid_rtt.addWidget(self.lineRTTSN, 0, 3)
        grid_rtt.addWidget(self.btnForceDiscon, 0, 4)
        grid_rtt.addWidget(lbl_rtt_auto_recon, 0, 5)
        grid_rtt.addWidget(self.chkbox_rtt_auto_recon, 0, 5, Qt.AlignRight)
        
        # 컬럼 스트레치 설정
        for i in range(6):
            grid_rtt.setColumnStretch(i, 1)
            
        vbox.addLayout(grid_rtt)
        self.setLayout(vbox)
        
        # 시그널 연결
        self.connect_signals()
        
    def connect_signals(self):
        """시그널 연결"""
        if self.parent_window:
            self.btnRTTCon.clicked.connect(self.parent_window.RTTConnect)
            self.btnRTTReCon.clicked.connect(self.parent_window.reconRTT)
            self.btnRTTConfig.clicked.connect(self.parent_window.RTTConfig)
            self.btnForceDiscon.clicked.connect(self.parent_window.RTTDisconnect)
            self.lineRTTSN.editingFinished.connect(self.save_serial_number)
            
    def save_serial_number(self):
        """시리얼 번호 저장"""
        self.config['rttserialno'] = self.lineRTTSN.text()
        if hasattr(self.parent_window, 'saveenv'):
            self.parent_window.saveenv()
            
    def set_enabled(self, enabled):
        """RTT 위젯 활성화/비활성화"""
        self.btnRTTCon.setEnabled(enabled)
        self.btnRTTReCon.setEnabled(enabled)
        self.btnRTTConfig.setEnabled(enabled)
        self.lineRTTSN.setEnabled(enabled)
        self.btnForceDiscon.setEnabled(enabled)
        self.chkbox_rtt_auto_recon.setEnabled(enabled)
        
    def update_connection_state(self, connected):
        """연결 상태에 따른 UI 업데이트"""
        if connected:
            self.btnRTTCon.setText('RTT Discon(F3)')
            self.btnRTTCon.setShortcut("F3")
        else:
            self.btnRTTCon.setText('RTT Con(F1)')
            self.btnRTTCon.setShortcut("F1")

class RTTConnectionWorker(QThread):
    """RTT 연결 작업을 비동기로 처리하는 워커 스레드"""
    connection_success = Signal(dict)  # 연결 성공 시 연결 정보 전달
    connection_failed = Signal(str)  # 연결 실패 시 에러 메시지 전달
    connection_progress = Signal(str)  # 연결 진행 상태 메시지

    def __init__(self, rtt_manager, serial_number="", auto_reconnect=False, is_reconnect=False):
        super().__init__()
        self.rtt_manager = rtt_manager
        self.serial_number = serial_number
        self.auto_reconnect = auto_reconnect
        self.is_reconnect = is_reconnect

    def run(self):
        """연결 작업 실행"""
        try:
            # 재연결인 경우 먼저 연결 해제
            if self.is_reconnect:
                self.connection_progress.emit("Disconnecting...")
                self.rtt_manager.disconnect(manual=False)
                import time
                time.sleep(0.1)

            self.connection_progress.emit("Connecting to JLink...")

            # RTT 연결 시도
            if self.rtt_manager.connect(self.serial_number, self.auto_reconnect):
                # 연결 성공 - 연결 정보 수집
                info = self.rtt_manager.get_connection_info()
                self.connection_success.emit(info)
            else:
                # 연결 실패 - 에러 메시지 전달
                error_msg = self.rtt_manager.get_last_error()
                self.connection_failed.emit(error_msg)

        except Exception as ex:
            # 예외 발생 시 실패 처리
            self.connection_failed.emit(f"Connection error: {ex}")

class RTTSignalAdapter(QThread):
    """RTT 모듈의 콜백을 Qt 시그널로 변환하는 어댑터"""
    data_received = Signal(str)
    connection_changed = Signal(object)  # RTTConnectionState

    def __init__(self, rtt_manager):
        super().__init__()
        self.rtt_manager = rtt_manager

        # RTT 매니저의 콜백을 시그널로 연결
        self.rtt_manager.set_data_received_callback(self._on_data_received)
        self.rtt_manager.set_connection_changed_callback(self._on_connection_changed)

    def _on_data_received(self, data):
        """데이터 수신 콜백"""
        cleaned_data = data.replace('\x00', '')
        self.data_received.emit(cleaned_data)

    def _on_connection_changed(self, state):
        """연결 상태 변경 콜백"""
        self.connection_changed.emit(state)