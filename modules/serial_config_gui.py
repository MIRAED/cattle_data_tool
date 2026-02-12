# -*- coding: utf-8 -*-
"""
Serial Configuration GUI Module
Serial 설정을 위한 GUI 모듈
"""

from PySide6.QtCore import Qt, Signal, Slot, QEvent
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QGridLayout, QVBoxLayout, QPushButton, QComboBox, QApplication
from PySide6.QtGui import QIcon

from .serial_manager import SerialConfig

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


class SerialConfigWindow(DPIAwareMixin, QWidget):
    """Serial 설정 창"""

    config_saved = Signal(object)

    def __init__(self, config=None, icon_path=None):
        super().__init__()
        self.config = config or SerialConfig()
        self.icon_path = icon_path
        self.initUI()
        self._init_dpi_handling()

    def initUI(self):
        vbox = QVBoxLayout()
        gridSerial = QGridLayout()
        vbox.addLayout(gridSerial)

        # Baud Rate
        lblBaud = QLabel('Baud rate', self)
        lblBaud.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboBaud = QComboBox()
        self.comboBaud.currentIndexChanged.connect(self.BaudRateChangeEvent)
        self.comboBaudCustom = QLineEdit()
        self.comboBaudCustom.setEnabled(False)

        # Data Bits
        lblBit = QLabel('Data Bits', self)
        lblBit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboBit = QComboBox()
        
        # Flow Control
        lblFlow = QLabel('Flow Control', self)
        lblFlow.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboFlow = QComboBox()
        
        # Parity
        lblParity = QLabel('Parity', self)
        lblParity.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboParity = QComboBox()
        
        # Stop Bits
        lblStop = QLabel('Stop Bits', self)
        lblStop.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboStop = QComboBox()
        
        # Buttons
        btnsave = QPushButton('Save')
        btnsave.clicked.connect(self.saveconfig)
        btncancel = QPushButton('Cancel')
        btncancel.clicked.connect(self.cancelconfig)

        # Layout 구성
        gridSerial.addWidget(lblBaud, 0, 0)
        gridSerial.addWidget(self.comboBaud, 0, 1)
        gridSerial.addWidget(self.comboBaudCustom, 1, 1)
        gridSerial.addWidget(lblBit, 2, 0)
        gridSerial.addWidget(self.comboBit, 2, 1)
        gridSerial.addWidget(lblFlow, 3, 0)
        gridSerial.addWidget(self.comboFlow, 3, 1)
        gridSerial.addWidget(lblParity, 4, 0)
        gridSerial.addWidget(self.comboParity, 4, 1)
        gridSerial.addWidget(lblStop, 5, 0)
        gridSerial.addWidget(self.comboStop, 5, 1)
        gridSerial.addWidget(btnsave, 6, 0)
        gridSerial.addWidget(btncancel, 6, 1)

        gridSerial.setColumnStretch(0, 1)
        gridSerial.setColumnStretch(1, 1)

        self.serial_init()

        self.setLayout(vbox)
        self.resize(300, 100)
        self.setWindowTitle("Serial config")
        
        if self.icon_path:
            try:
                self.setWindowIcon(QIcon(self.icon_path))
            except:
                pass

    def serial_init(self):
        """Serial 설정 초기화"""
        try:
            # Baud Rate 설정
            self.comboBaud.insertItems(0, [str(x) for x in self.config.BAUDRATES_STR])
            self.comboBaud.setCurrentIndex(self.config.baud_rate_index)
            self.comboBaudCustom.setText(str(self.config.baud_rate_custom))
            
            # Data Bits 설정
            self.comboBit.insertItems(0, [str(x) for x in self.config.DATABITS_STR])
            self.comboBit.setCurrentIndex(self.config.data_bits_index)
            
            # Flow Control 설정
            self.comboFlow.insertItems(0, [str(x) for x in self.config.FLOWCONTROL_STR])
            self.comboFlow.setCurrentIndex(self.config.flow_control_index)
            
            # Parity 설정
            self.comboParity.insertItems(0, [str(x) for x in self.config.PARITY_STR])
            self.comboParity.setCurrentIndex(self.config.parity_index)
            
            # Stop Bits 설정
            self.comboStop.insertItems(0, [str(x) for x in self.config.STOPBITS_STR])
            self.comboStop.setCurrentIndex(self.config.stop_bits_index)
            
        except Exception as ex:
            print(f"serial_init Error: {ex}")

    def BaudRateChangeEvent(self):
        """Baud Rate 변경 이벤트"""
        try:
            index = self.comboBaud.currentIndex()
            if index < len(self.config.BAUDRATES_STR) and self.config.BAUDRATES_STR[index] == "Custom":
                self.comboBaudCustom.setEnabled(True)
            else:
                self.comboBaudCustom.setEnabled(False)
                if index < len(self.config.BAUDRATES):
                    self.comboBaudCustom.setText(str(int(self.config.BAUDRATES[index])))
        except Exception as ex:
            print(f"BaudRateChangeEvent Error: {ex}")

    @Slot()
    def saveconfig(self):
        """설정 저장"""
        try:
            # 설정 업데이트
            self.config.baud_rate_index = self.comboBaud.currentIndex()
            self.config.baud_rate_custom = int(self.comboBaudCustom.text())
            self.config.data_bits_index = self.comboBit.currentIndex()
            self.config.flow_control_index = self.comboFlow.currentIndex()
            self.config.parity_index = self.comboParity.currentIndex()
            self.config.stop_bits_index = self.comboStop.currentIndex()

            # 시그널 발생
            self.config_saved.emit(self.config)
            self.close()

        except Exception as ex:
            print(f"saveconfig Error: {ex}")

    @Slot()
    def cancelconfig(self):
        """설정 취소"""
        try:
            self.close()
        except Exception as ex:
            print(f"cancelconfig Error: {ex}")

    def set_config(self, config):
        """외부에서 설정 업데이트"""
        self.config = config
        self.serial_init()

    def get_config(self):
        """현재 설정 반환"""
        return self.config