try:
    from PySide2.QtGui import QColor, QPalette
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QApplication
    QT_VERSION = "PySide2"
    print("ThemeManager: PySide2")
except ImportError:
    from PyQt5.QtGui import QColor, QPalette
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    QT_VERSION = "PyQt5"
    print("ThemeManager: PyQt5")

class ThemeManager:
    @staticmethod
    def _set_disabled_colors(palette, is_dark_theme):
        """Disabled 상태의 색상을 설정합니다."""
        if is_dark_theme:
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        else:
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    @staticmethod
    def apply_theme(theme_name):
        app = QApplication.instance()
        if not app:
            return

        # Fusion 스타일 설정 (크로스 플랫폼 일관성)
        app.setStyle("Fusion")

        new_palette = QPalette()
        if theme_name == "Dark":
            new_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            new_palette.setColor(QPalette.WindowText, Qt.white)
            new_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            new_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.white)
            new_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            new_palette.setColor(QPalette.ButtonText, Qt.white)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            new_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            new_palette.setColor(QPalette.HighlightedText, Qt.black)
            ThemeManager._set_disabled_colors(new_palette, True)
        elif theme_name == "Light Gray":
            new_palette.setColor(QPalette.Window, QColor(220, 220, 220))
            new_palette.setColor(QPalette.WindowText, Qt.black)
            new_palette.setColor(QPalette.Base, QColor(200, 200, 200))
            new_palette.setColor(QPalette.AlternateBase, QColor(220, 220, 220))
            new_palette.setColor(QPalette.ToolTipBase, Qt.black)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.black)
            new_palette.setColor(QPalette.Button, QColor(220, 220, 220))
            new_palette.setColor(QPalette.ButtonText, Qt.black)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(0, 102, 204))
            new_palette.setColor(QPalette.Highlight, QColor(51, 153, 255))
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, False)
        elif theme_name == "Gray":
            new_palette.setColor(QPalette.Window, QColor(68, 68, 68))
            new_palette.setColor(QPalette.WindowText, Qt.white)
            new_palette.setColor(QPalette.Base, QColor(45, 45, 45))
            new_palette.setColor(QPalette.AlternateBase, QColor(68, 68, 68))
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.white)
            new_palette.setColor(QPalette.Button, QColor(68, 68, 68))
            new_palette.setColor(QPalette.ButtonText, Qt.white)
            new_palette.setColor(QPalette.BrightText, Qt.yellow)
            new_palette.setColor(QPalette.Link, QColor(0, 122, 255))
            new_palette.setColor(QPalette.Highlight, QColor(0, 122, 255))
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, True)
        elif theme_name == "Light Blue":
            # 테스트 도구용 라이트 블루 - 시원하고 명확한 시인성
            new_palette.setColor(QPalette.Window, QColor(235, 245, 255))       # 연한 블루 배경
            new_palette.setColor(QPalette.WindowText, Qt.black)
            new_palette.setColor(QPalette.Base, QColor(245, 250, 255))         # 밝은 블루 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(225, 240, 255)) # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.black)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.black)
            new_palette.setColor(QPalette.Button, QColor(225, 240, 255))       # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.black)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(20, 80, 180))           # 명확한 블루 링크
            new_palette.setColor(QPalette.Highlight, QColor(80, 140, 220))     # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, False)
        elif theme_name == "Dark Blue":
            # 테스트 도구용 다크 블루 - 전문적이고 명확한 네이비
            new_palette.setColor(QPalette.Window, QColor(35, 45, 70))          # 진한 네이비 배경
            new_palette.setColor(QPalette.WindowText, Qt.white)
            new_palette.setColor(QPalette.Base, QColor(25, 35, 60))            # 어두운 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(45, 55, 80))   # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.white)
            new_palette.setColor(QPalette.Button, QColor(45, 55, 80))          # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.white)
            new_palette.setColor(QPalette.BrightText, Qt.yellow)
            new_palette.setColor(QPalette.Link, QColor(120, 180, 255))         # 명확한 라이트 블루
            new_palette.setColor(QPalette.Highlight, QColor(60, 120, 200))     # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.black)
            ThemeManager._set_disabled_colors(new_palette, True)
        elif theme_name == "Light Green":
            # 테스트 도구용 라이트 그린 - 자연스럽고 명확한 시인성
            new_palette.setColor(QPalette.Window, QColor(240, 250, 240))       # 연한 그린 배경
            new_palette.setColor(QPalette.WindowText, Qt.black)
            new_palette.setColor(QPalette.Base, QColor(248, 255, 248))         # 밝은 그린 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(230, 245, 230)) # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.black)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.black)
            new_palette.setColor(QPalette.Button, QColor(230, 245, 230))       # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.black)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(40, 120, 60))           # 명확한 그린 링크
            new_palette.setColor(QPalette.Highlight, QColor(100, 180, 120))    # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, False)
        elif theme_name == "Dark Green":
            # 테스트 도구용 다크 그린 - 전문적이고 명확한 포레스트
            new_palette.setColor(QPalette.Window, QColor(35, 55, 40))          # 진한 포레스트 그린
            new_palette.setColor(QPalette.WindowText, Qt.white)
            new_palette.setColor(QPalette.Base, QColor(25, 45, 30))            # 어두운 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(45, 65, 50))   # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.white)
            new_palette.setColor(QPalette.Button, QColor(45, 65, 50))          # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.white)
            new_palette.setColor(QPalette.BrightText, Qt.yellow)
            new_palette.setColor(QPalette.Link, QColor(120, 220, 140))         # 명확한 라이트 그린
            new_palette.setColor(QPalette.Highlight, QColor(60, 140, 80))      # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.black)
            ThemeManager._set_disabled_colors(new_palette, True)
        elif theme_name == "Light Red":
            # 테스트 도구용 라이트 레드 - 따뜻하고 명확한 시인성
            new_palette.setColor(QPalette.Window, QColor(255, 240, 240))       # 연한 핑크 배경
            new_palette.setColor(QPalette.WindowText, Qt.black)
            new_palette.setColor(QPalette.Base, QColor(255, 248, 248))         # 밝은 핑크 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(250, 230, 230)) # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.black)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.black)
            new_palette.setColor(QPalette.Button, QColor(250, 230, 230))       # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.black)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(180, 60, 60))           # 명확한 레드 링크
            new_palette.setColor(QPalette.Highlight, QColor(220, 100, 100))    # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, False)
        elif theme_name == "Dark Red":
            # 테스트 도구용 다크 레드 - 전문적이고 명확한 마룬
            new_palette.setColor(QPalette.Window, QColor(70, 35, 35))          # 진한 마룬 배경
            new_palette.setColor(QPalette.WindowText, Qt.white)
            new_palette.setColor(QPalette.Base, QColor(60, 25, 25))            # 어두운 베이스
            new_palette.setColor(QPalette.AlternateBase, QColor(80, 45, 45))   # 명확한 대체 색상
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.white)
            new_palette.setColor(QPalette.Text, Qt.white)
            new_palette.setColor(QPalette.Button, QColor(80, 45, 45))          # 구분되는 버튼
            new_palette.setColor(QPalette.ButtonText, Qt.white)
            new_palette.setColor(QPalette.BrightText, Qt.yellow)
            new_palette.setColor(QPalette.Link, QColor(255, 140, 140))         # 명확한 라이트 레드
            new_palette.setColor(QPalette.Highlight, QColor(160, 80, 80))      # 뚜렷한 하이라이트
            new_palette.setColor(QPalette.HighlightedText, Qt.black)
            ThemeManager._set_disabled_colors(new_palette, True)
        elif theme_name == "White":
            # White (Default) theme - 명시적으로 라이트 테마 설정
            new_palette.setColor(QPalette.Window, Qt.white)
            new_palette.setColor(QPalette.WindowText, Qt.black)
            new_palette.setColor(QPalette.Base, Qt.white)
            new_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
            new_palette.setColor(QPalette.ToolTipBase, Qt.white)
            new_palette.setColor(QPalette.ToolTipText, Qt.black)
            new_palette.setColor(QPalette.Text, Qt.black)
            new_palette.setColor(QPalette.Button, QColor(240, 240, 240))
            new_palette.setColor(QPalette.ButtonText, Qt.black)
            new_palette.setColor(QPalette.BrightText, Qt.red)
            new_palette.setColor(QPalette.Link, QColor(0, 0, 255))
            new_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            new_palette.setColor(QPalette.HighlightedText, Qt.white)
            ThemeManager._set_disabled_colors(new_palette, False)

        # Palette 적용
        app.setPalette(new_palette)

        # 모든 위젯을 강제로 업데이트하여 즉시 테마 적용
        for widget in app.allWidgets():
            widget.setPalette(new_palette)
            widget.update()
