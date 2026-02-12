import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg

class DualAxisPlot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이중 Y축 그래프 예제")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 첫 번째 PlotWidget 생성 (왼쪽 y축용)
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        
        # 두 번째 ViewBox 생성 (오른쪽 y축용)
        self.viewbox2 = pg.ViewBox()
        self.plot_widget.scene().addItem(self.viewbox2)
        
        # 두 번째 축을 오른쪽에 배치
        self.plot_widget.getAxis('right').linkToView(self.viewbox2)
        self.viewbox2.setXLink(self.plot_widget)
        
        # 오른쪽 축 보이기
        self.plot_widget.showAxis('right')
        
        # 그래프 설정
        self.setup_plot()
        
        # 데이터 플롯
        self.plot_data()
        
        # ViewBox 크기 동기화 함수 연결
        self.plot_widget.getViewBox().sigResized.connect(self.update_views)
        
    def setup_plot(self):
        """그래프 기본 설정"""
        # 제목과 레이블 설정
        self.plot_widget.setLabel('left', '온도 (°C)', color='red')
        self.plot_widget.setLabel('right', '습도 (%)', color='blue')
        self.plot_widget.setLabel('bottom', '시간 (초)')
        self.plot_widget.setTitle('온도와 습도 변화')
        
        # 격자 표시
        self.plot_widget.showGrid(x=True, y=True)
        
    def plot_data(self):
        """데이터 플롯"""
        # 샘플 데이터 생성
        x = np.linspace(0, 10, 100)
        
        # 첫 번째 데이터 (온도): 범위 20-30°C
        temperature = 25 + 5 * np.sin(x) + np.random.normal(0, 0.5, 100)
        
        # 두 번째 데이터 (습도): 범위 40-80%
        humidity = 60 + 20 * np.cos(x * 0.5) + np.random.normal(0, 2, 100)
        
        # 첫 번째 데이터를 왼쪽 축에 플롯 (빨간색)
        self.plot_widget.plot(x, temperature, pen=pg.mkPen('red', width=2), name='온도 (°C)')
        
        # 두 번째 데이터를 오른쪽 축에 플롯 (파란색)
        self.curve2 = pg.PlotCurveItem(x, humidity, pen=pg.mkPen('blue', width=2))
        self.viewbox2.addItem(self.curve2)
        
        # 범례 추가
        self.add_legend()
        
        # 축 범위 설정
        self.set_axis_ranges(temperature, humidity)
        
    def add_legend(self):
        """범례 추가"""
        # 수동으로 범례 텍스트 추가
        legend = pg.LegendItem(offset=(70, 30))
        legend.setParentItem(self.plot_widget.getPlotItem())
        
        # 범례 항목 추가
        legend.addItem(pg.PlotCurveItem(pen=pg.mkPen('red', width=2)), '온도 (°C)')
        legend.addItem(pg.PlotCurveItem(pen=pg.mkPen('blue', width=2)), '습도 (%)')
        
    def set_axis_ranges(self, temp_data, humidity_data):
        """각 축의 범위 설정"""
        # 왼쪽 축 (온도) 범위 설정
        temp_min, temp_max = np.min(temp_data), np.max(temp_data)
        temp_margin = (temp_max - temp_min) * 0.1
        self.plot_widget.setYRange(temp_min - temp_margin, temp_max + temp_margin)
        
        # 오른쪽 축 (습도) 범위 설정
        humidity_min, humidity_max = np.min(humidity_data), np.max(humidity_data)
        humidity_margin = (humidity_max - humidity_min) * 0.1
        self.viewbox2.setYRange(humidity_min - humidity_margin, humidity_max + humidity_margin)
        
        # 축 범위를 텍스트로 표시
        self.show_axis_ranges(temp_min, temp_max, humidity_min, humidity_max)
        
    def show_axis_ranges(self, temp_min, temp_max, humidity_min, humidity_max):
        """축 범위 정보를 텍스트로 표시"""
        # 범위 정보 텍스트
        range_text = pg.TextItem(
            f"온도 범위: {temp_min:.1f}°C ~ {temp_max:.1f}°C\n습도 범위: {humidity_min:.1f}% ~ {humidity_max:.1f}%",
            anchor=(0, 1)
        )
        range_text.setPos(0.5, temp_max - 1)
        self.plot_widget.addItem(range_text)
        
    def update_views(self):
        """ViewBox 크기 동기화"""
        self.viewbox2.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
        self.viewbox2.linkedViewChanged(self.plot_widget.getViewBox(), self.viewbox2.XAxis)

def main():
    app = QApplication(sys.argv)
    
    # 다크 테마 설정 (선택사항)
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    
    window = DualAxisPlot()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()