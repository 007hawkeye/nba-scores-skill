import sys
import os
import ctypes # 引入 ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                             QFrame, QDesktopWidget, QSystemTrayIcon, QMenu, QAction,
                             QGraphicsDropShadowEffect, QGraphicsBlurEffect, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QLinearGradient, QBrush, QPixmap, QPainter, QPainterPath, QPen
from nba_api import NBAApi
from datetime import datetime

# NBA 球队中英文对照表
NBA_TEAMS_CN = {
    'ATL': '老鹰', 'BOS': '凯尔特人', 'BKN': '篮网', 'CHA': '黄蜂', 'CHI': '公牛',
    'CLE': '骑士', 'DAL': '独行侠', 'DEN': '掘金', 'DET': '活塞', 'GSW': '勇士',
    'HOU': '火箭', 'IND': '步行者', 'LAC': '快船', 'LAL': '湖人', 'MEM': '灰熊',
    'MIA': '热火', 'MIL': '雄鹿', 'MIN': '森林狼', 'NOP': '鹈鹕', 'NYK': '尼克斯',
    'OKC': '雷霆', 'ORL': '魔术', 'PHI': '76人', 'PHX': '太阳', 'POR': '开拓者',
    'SAC': '国王', 'SAS': '马刺', 'TOR': '猛龙', 'UTA': '爵士', 'WAS': '奇才'
}

class GameWidget(QFrame):
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data
        self.setup_ui()
        self.setup_animation()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.NoFrame)
        
        # 极简深色玻璃风格配色
        if self.game_data['is_live']:
            # 进行中：深邃黑底 + 霓虹绿光晕
            self.bg_color = "rgba(30, 41, 59, 0.7)"
            self.border_color = "rgba(74, 222, 128, 0.3)"
            self.text_primary = "#ffffff"
            self.text_secondary = "#94a3b8"
            self.accent_color = "#4ade80" # 亮绿
            self.status_bg = "rgba(74, 222, 128, 0.15)"
        elif self.game_data['is_finished']:
            # 已结束：低调深灰
            self.bg_color = "rgba(30, 41, 59, 0.4)"
            self.border_color = "rgba(255, 255, 255, 0.05)"
            self.text_primary = "#cbd5e1"
            self.text_secondary = "#64748b"
            self.accent_color = "#94a3b8"
            self.status_bg = "rgba(148, 163, 184, 0.1)"
        else:
            # 未开始：温暖琥珀
            self.bg_color = "rgba(30, 41, 59, 0.7)"
            self.border_color = "rgba(251, 191, 36, 0.2)"
            self.text_primary = "#ffffff"
            self.text_secondary = "#94a3b8"
            self.accent_color = "#fbbf24" # 琥珀色
            self.status_bg = "rgba(251, 191, 36, 0.15)"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: 1px solid {self.border_color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: rgba(51, 65, 85, 0.8);
                border: 1px solid {self.accent_color};
            }}
        """)
        
        # 主布局 - 紧凑型
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(16, 12, 16, 12)
        
        # 1. 顶部信息栏 (状态 | 时间)
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 8)
        
        # 状态指示 (胶囊) - 汉化处理
        status_text = self.game_data['game_status_text']
        if "Final" in status_text: 
            status_text = "已结束"
        elif "pm" in status_text.lower():
            time_str = status_text.lower().replace(" et", "").replace("pm", "").strip()
            status_text = f"比赛时间 {time_str}"
        elif "am" in status_text.lower():
            time_str = status_text.lower().replace(" et", "").replace("am", "").strip()
            status_text = f"比赛时间 {time_str}"
        
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        status_label.setStyleSheet(f"""
            color: {self.accent_color}; 
            background-color: {self.status_bg}; 
            border-radius: 4px; 
            padding: 2px 8px;
            border: none;
        """)
        status_label.setFixedHeight(22)
        
        info_layout.addWidget(status_label)
        info_layout.addStretch()
        
        # 2. 比赛数据网格 (客队 - 比分 - 主队)
        game_grid = QHBoxLayout()
        game_grid.setSpacing(0)
        
        # 左侧：客队 (Logo/Code + Name)
        away_widget = self.create_team_info(self.game_data['away_team'], Qt.AlignLeft)
        
        # 中间：比分
        score_widget = QWidget()
        score_widget.setStyleSheet("background: transparent; border: none;")
        score_layout = QHBoxLayout(score_widget)
        score_layout.setContentsMargins(10, 0, 10, 0)
        score_layout.setSpacing(12)
        
        score_font = QFont("Segoe UI", 20, QFont.Bold)
        score_font.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        
        away_score = QLabel(str(self.game_data['away_team']['score']))
        away_score.setFont(score_font)
        away_score.setStyleSheet(f"color: {self.text_primary}; border: none;")
        
        divider = QLabel(":")
        divider.setFont(QFont("Segoe UI", 16))
        divider.setStyleSheet(f"color: {self.text_secondary}; margin-bottom: 2px; border: none;")
        
        home_score = QLabel(str(self.game_data['home_team']['score']))
        home_score.setFont(score_font)
        home_score.setStyleSheet(f"color: {self.text_primary}; border: none;")
        
        score_layout.addWidget(away_score)
        score_layout.addWidget(divider)
        score_layout.addWidget(home_score)
        
        # 右侧：主队
        home_widget = self.create_team_info(self.game_data['home_team'], Qt.AlignRight)
        
        game_grid.addWidget(away_widget, 1)
        game_grid.addWidget(score_widget, 0)
        game_grid.addWidget(home_widget, 1)
        
        main_layout.addLayout(info_layout)
        main_layout.addLayout(game_grid)
        
        self.setLayout(main_layout)
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)

    def create_team_info(self, team_data, align):
        widget = QWidget()
        widget.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 汉化球队名称
        tricode = team_data['team_tricode']
        team_name_cn = NBA_TEAMS_CN.get(tricode, tricode)
        
        # 球队名
        name_label = QLabel(team_name_cn)
        name_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        name_label.setStyleSheet(f"color: {self.text_primary};")
        name_label.setAlignment(align)
        
        # 英文缩写 (辅助显示)
        code_label = QLabel(tricode) 
        code_label.setFont(QFont("Segoe UI", 8))
        code_label.setStyleSheet(f"color: {self.text_secondary};")
        code_label.setAlignment(align)
        
        layout.addWidget(name_label)
        layout.addWidget(code_label)
        layout.addStretch()
        
        return widget
    
    def setup_animation(self):
        self.color_animation = QPropertyAnimation(self, b"styleSheet")
        self.color_animation.setDuration(200)
        self.color_animation.setEasingCurve(QEasingCurve.OutQuad)

class NBAScoresPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = NBAApi()
        self.games = []
        self.is_hidden = False
        self.hidden_edge = None
        self.edge_threshold = 30
        self.drag_position = None
        self.screen_geometry = None # 缓存屏幕几何信息
        self.is_expanded = True # 默认展开状态
        self.expanded_height = 620 # 展开高度
        self.collapsed_height = 360 # 折叠高度 (增加高度以完全显示两个卡片)
        
        self.notified_games = set() # 记录已通知结束的比赛ID
        self.first_load = True # 标记首次加载
        
        self.setup_ui()
        self.setup_system_tray()
        self.load_games()
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)
        
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_panel)
        
        self.show_timer = QTimer()
        self.show_timer.setSingleShot(True)
        self.show_timer.timeout.connect(self.show_panel)
    
    def setup_ui(self):
        self.setWindowTitle("NBA Tracker")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.central_widget = QWidget()
        self.central_widget.setAttribute(Qt.WA_TranslucentBackground) # 确保背景透明
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 20, 20, 20) # 增加边距，防止圆角被截断
        
        # 容器：深色磨砂玻璃背景
        self.container = QFrame()
        self.container.setObjectName("MainContainer") # 设置ID以便区分
        self.container.setStyleSheet("""
            QFrame#MainContainer { 
                background-color: rgba(15, 23, 42, 0.95); 
                border-radius: 16px; 
                border: 1px solid rgba(255, 255, 255, 0.1); 
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180)) # 更深的阴影
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout()
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("background: transparent; border-bottom: 1px solid rgba(255, 255, 255, 0.05);")
        title_bar.setFixedHeight(50)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 16, 0)
        
        title_label = QLabel("NBA实时比分")
        title_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #e2e8f0; letter-spacing: 1px;")
        
        # 按钮样式：统一圆角背景
        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 14px;
                color: #94a3b8;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
                color: #cbd5e1;
            }
        """
        
        # 按钮容器，确保对齐
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setFixedSize(28, 28)
        self.refresh_button.setStyleSheet(btn_style)
        self.refresh_button.clicked.connect(self.manual_refresh)
        
        self.minimize_button = QPushButton("－")
        self.minimize_button.setFixedSize(28, 28)
        self.minimize_button.setStyleSheet(btn_style)
        self.minimize_button.clicked.connect(self.minimize_to_tray) # 修改连接槽函数
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(28, 28)
        self.close_button.setStyleSheet(btn_style)
        self.close_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.minimize_button)
        buttons_layout.addWidget(self.close_button)
        
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addLayout(buttons_layout)
        
        # 统计栏 (极简)
        stats_bar = QWidget()
        stats_bar.setStyleSheet("background: transparent;")
        stats_bar.setFixedHeight(30)
        # 将整个统计栏设置为可点击，通过事件过滤器或覆盖 mousePressEvent
        stats_bar.setCursor(Qt.PointingHandCursor)
        stats_bar.mousePressEvent = self.on_stats_bar_click
        
        stats_bar_layout = QHBoxLayout(stats_bar)
        stats_bar_layout.setContentsMargins(16, 0, 16, 0)
        
        self.stats_label = QLabel("正在更新...")
        self.stats_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.stats_label.setStyleSheet("color: #64748b;")
        self.stats_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 展开/收起按钮
        self.expand_button = QPushButton("▼") # 初始为展开状态，显示向下箭头表示可收起？或者向上收起？
        # 逻辑：当前是展开状态，按钮应显示“收起”（向上箭头 ▲）；当前是折叠状态，显示“展开”（向下箭头 ▼）
        # 题目要求默认“缩短至仅能呈现两个比赛卡片”，所以默认应该是折叠状态。
        # 但我上面的 init 设置了 self.is_expanded = True，这里需要调整一下逻辑。
        # 让我们按照题目要求：默认缩短。
        
        self.expand_button.setFixedSize(20, 20) # 缩小尺寸
        self.expand_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 10px; /* 缩小字号 */
            }
            QPushButton:hover {
                color: #94a3b8;
            }
        """)
        self.expand_button.clicked.connect(self.toggle_expand)
        
        # 将 stats_label 和 expand_button 的点击事件也穿透到 stats_bar，或者它们自己也触发展开
        # 简单做法：让它们不拦截鼠标事件，或者给它们也绑定 toggle_expand
        # QLabel 默认不处理点击，QWidget 默认不处理。QPushButton 会处理。
        # 所以点击 Label 应该会穿透到 stats_bar (如果 label 没有设置鼠标追踪等)
        # 为了保险，我们可以给 label 也加上 mousePressEvent 或者直接让 stats_bar 覆盖在最上层？不行，按钮要能点。
        # 其实只要点击 stats_bar 的空白处能触发就行，用户通常会点空白处。
        # 如果用户点 label，最好也能触发。
        # 我们给 label 安装事件过滤器，或者简单的子类化。
        # 最简单：直接给 stats_bar 安装事件过滤器，拦截所有子控件的点击？
        # 不，expand_button 已经绑定了。label 需要处理。
        
        # 让 label 也能点击
        self.stats_label.mousePressEvent = self.on_stats_bar_click
        
        stats_bar_layout.addWidget(self.stats_label)
        stats_bar_layout.addStretch()
        stats_bar_layout.addWidget(self.expand_button)
        
        # 内容区
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 10)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.1);
                width: 6px;
                margin: 0px 0px 0px 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        self.games_container = QWidget()
        self.games_container.setStyleSheet("background: transparent;")
        self.games_layout = QVBoxLayout(self.games_container)
        self.games_layout.setSpacing(8) # 卡片间距
        self.games_layout.setContentsMargins(12, 0, 12, 12)
        self.games_layout.addStretch()
        
        self.scroll_area.setWidget(self.games_container)
        content_layout.addWidget(self.scroll_area)
        
        container_layout.addWidget(title_bar)
        container_layout.addWidget(content_widget)
        container_layout.addWidget(stats_bar) # 统计栏放底部
        
        self.container.setLayout(container_layout)
        main_layout.addWidget(self.container)
        
        self.central_widget.setLayout(main_layout)
        
        # 初始设置为折叠状态
        self.is_expanded = False
        self.expand_button.setText("▼") # 显示展开图标
        self.setFixedSize(400, self.collapsed_height) # 默认折叠高度
        
        screen = QDesktopWidget().screenGeometry()
        x = screen.width() - 420
        y = 100
        self.move(x, y)
    
    def on_stats_bar_click(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_expand()

    def toggle_expand(self):
        start_height = self.height()
        
        if self.is_expanded:
            # 执行收起
            end_height = self.collapsed_height
            self.expand_button.setText("▼")
            self.is_expanded = False
        else:
            # 执行展开
            end_height = self.expanded_height
            self.expand_button.setText("▲")
            self.is_expanded = True
            
        # 高度变化动画
        self.height_animation = QPropertyAnimation(self, b"size")
        self.height_animation.setDuration(300)
        self.height_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.height_animation.setStartValue(self.size())
        self.height_animation.setEndValue(self.size().transposed().expandedTo(self.minimumSize()).transposed()) # 保持宽度不变
        # QPropertyAnimation 对 size 的动画需要 QSize 对象
        # 我们直接用 setFixedSize 可能会冲突，最好是用 geometry 或者 minimumHeight/maximumHeight
        # 这里为了简单有效，我们用 QPropertyAnimation 动画 geometry 或者直接用 QTimer 模拟
        
        # 更简单的方法：使用 geometry 动画，只改变高度
        current_geo = self.geometry()
        target_geo = QRect(current_geo.x(), current_geo.y(), current_geo.width(), end_height)
        
        self.geo_animation = QPropertyAnimation(self, b"geometry")
        self.geo_animation.setDuration(300)
        self.geo_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.geo_animation.setStartValue(current_geo)
        self.geo_animation.setEndValue(target_geo)
        self.geo_animation.start()
        
        # 动画结束后更新 fixed size，防止被意外改变
        self.geo_animation.finished.connect(lambda: self.setFixedSize(400, end_height))

    def setup_animation(self):
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(400)
        self.show_animation.setEasingCurve(QEasingCurve.OutElastic)
    
    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # 动态绘制图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. 绘制背景圆 (使用路径数据中的灰色 #696065)
        path1 = QPainterPath()
        # SVG path 1: M198.692801 198.692801...
        # 这是一个圆形背景，我们可以直接画一个圆，或者简化路径。
        # 为了最佳效果，我们直接画一个圆，颜色取自 SVG 第一个 path 的 fill
        painter.setBrush(QBrush(QColor("#696065")))
        painter.setPen(Qt.NoPen)
        # 原始 SVG viewBox 是 1024x1024，这里缩放到 64x64
        # 1024 / 64 = 16
        # 圆心大概在 512, 512，半径大概是 443 (根据 path 数据估算)
        # 简单起见，我们画满整个 64x64
        painter.drawEllipse(0, 0, 64, 64)
        
        # 2. 绘制奖杯图案 (黄色 #FBB01F)
        # 由于 SVG path 比较复杂，手动转换很繁琐且易错。
        # 我们用一个简化的奖杯形状来代替，或者尝试绘制核心部分。
        # 这里为了稳定性和效率，我们绘制一个风格化的奖杯。
        
        painter.setBrush(QBrush(QColor("#FBB01F")))
        
        # 奖杯底座
        painter.drawRect(20, 48, 24, 6)
        painter.drawRect(26, 42, 12, 6)
        
        # 奖杯杯身 (倒梯形 + 半圆)
        path_cup = QPainterPath()
        path_cup.moveTo(16, 16)
        path_cup.lineTo(48, 16)
        path_cup.lineTo(40, 36)
        path_cup.lineTo(24, 36)
        path_cup.closeSubpath()
        painter.drawPath(path_cup)
        
        # 奖杯把手 (左右圆弧)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("#FBB01F"), 3))
        painter.drawArc(12, 18, 10, 10, 90*16, 180*16)
        painter.drawArc(42, 18, 10, 10, -90*16, 180*16)
        
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("NBA实时比分")
        
        menu = QMenu()
        # 设置菜单样式
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                border: 1px solid #475569;
                color: #e2e8f0;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #334155;
            }
        """)
        
        show_action = QAction("显示主面板", self)
        show_action.triggered.connect(self.restore_window)
        menu.addAction(show_action)
        
        refresh_action = QAction("刷新数据", self)
        refresh_action.triggered.connect(self.manual_refresh)
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        exit_action = QAction("退出程序", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
        else:
            print("系统托盘不可用")

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.minimize_to_tray()
            else:
                self.restore_window()
                
    def restore_window(self):
        # 1. 如果窗口完全隐藏（最小化到托盘），先显示出来
        if not self.isVisible():
            self.showNormal()
            
        # 2. 如果窗口是最小化状态，恢复正常
        if self.isMinimized():
            self.showNormal()
            
        # 3. 如果窗口处于边缘隐藏状态，执行滑出动画
        if self.is_hidden:
            self.show_panel()
            
        # 4. 激活窗口并置顶
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()
    
    def load_games(self):
        success, result = self.api.fetch_games()
        
        if success:
            self.games = result
            self.update_ui()
            self.check_finished_games() # 检查是否有新结束的比赛
            self.first_load = False
        else:
            self.stats_label.setText(f"错误: {result}")

    def check_finished_games(self):
        for game in self.games:
            if game['is_finished']:
                game_id = game['game_id']
                if game_id not in self.notified_games:
                    # 如果不是首次加载，且窗口处于最小化或隐藏状态，则发送通知
                    if not self.first_load and (self.isMinimized() or not self.isVisible()):
                        away_team = game['away_team']
                        home_team = game['home_team']
                        
                        away_name = NBA_TEAMS_CN.get(away_team['team_tricode'], away_team['team_tricode'])
                        home_name = NBA_TEAMS_CN.get(home_team['team_tricode'], home_team['team_tricode'])
                        
                        away_score = away_team['score']
                        home_score = home_team['score']
                        
                        msg = f"比赛结束：{away_name} {away_score} vs {home_name} {home_score}"
                        
                        self.tray_icon.showMessage(
                            "NBA实时比分",
                            msg,
                            QSystemTrayIcon.Information,
                            3000
                        )
                    
                    # 记录已处理的比赛，避免重复通知
                    self.notified_games.add(game_id)
    
    def update_ui(self):
        for i in reversed(range(self.games_layout.count())):
            widget = self.games_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        if not self.games:
            no_games_label = QLabel("今日暂无比赛")
            no_games_label.setFont(QFont("Segoe UI", 15))
            no_games_label.setAlignment(Qt.AlignCenter)
            no_games_label.setStyleSheet("color: #8e8e93; padding: 50px;")
            self.games_layout.insertWidget(0, no_games_label)
        else:
            live_games = [g for g in self.games if g['is_live']]
            finished_games = [g for g in self.games if g['is_finished']]
            other_games = [g for g in self.games if not g['is_live'] and not g['is_finished']]
            
            for game in live_games + other_games + finished_games:
                game_widget = GameWidget(game)
                self.games_layout.insertWidget(self.games_layout.count() - 1, game_widget)
        
        total_games = self.api.get_total_games()
        live_count = self.api.get_live_games_count()
        finished_count = self.api.get_finished_games_count()
        
        self.stats_label.setText(f"今日 {total_games} 场比赛 · 进行中 {live_count} · 已结束 {finished_count}")
    
    def manual_refresh(self):
        # 1. 隐藏现有卡片
        self.scroll_area.setVisible(False)
        
        # 2. 显示加载动画
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("background: transparent;")
        
        # 创建垂直布局来放置图标和文字
        loading_layout = QVBoxLayout(self.loading_label)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        # 刷新图标
        icon_label = QLabel("⟳")
        icon_label.setFont(QFont("Segoe UI", 32))
        icon_label.setStyleSheet("color: #4ade80;") # 霓虹绿
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 旋转动画
        self.rotate_anim = QPropertyAnimation(icon_label, b"windowOpacity") # 临时替代，实际旋转需要更复杂实现
        # 这里简化处理，直接显示图标
        
        # 文字
        text_label = QLabel("正在刷新中...")
        text_label.setFont(QFont("Microsoft YaHei UI", 10))
        text_label.setStyleSheet("color: #94a3b8; margin-top: 10px;")
        text_label.setAlignment(Qt.AlignCenter)
        
        loading_layout.addWidget(icon_label)
        loading_layout.addWidget(text_label)
        
        self.container.layout().insertWidget(1, self.loading_label)
        
        # 3. 禁用刷新按钮防止重复点击
        self.refresh_button.setEnabled(False)
        
        # 4. 延迟执行刷新，模拟网络请求并展示动画
        QTimer.singleShot(800, self.perform_refresh)

    def perform_refresh(self):
        self.load_games()
        
        # 移除加载动画
        self.loading_label.deleteLater()
        self.scroll_area.setVisible(True)
        
        # 恢复按钮
        self.refresh_button.setEnabled(True)
    
    def reset_refresh_button(self):
        pass # 不再需要这个函数，样式保持一致

    def auto_refresh(self):
        self.load_games()
    
    def minimize_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "别忘了关注比赛~",
            "程序已最小化到托盘，点击图标恢复显示",
            QSystemTrayIcon.Information,
            2000
        )

    def hide_panel(self):
        if not self.is_hidden:
            screen = QDesktopWidget().screenGeometry()
            panel_rect = self.geometry()
            
            self.hide_animation = QPropertyAnimation(self, b"geometry")
            self.hide_animation.setDuration(300)
            self.hide_animation.setEasingCurve(QEasingCurve.OutCubic)
            
            if panel_rect.right() >= screen.width() - self.edge_threshold:
                self.hidden_edge = 'right'
                target_x = screen.width() - 15
                target_y = panel_rect.y()
            elif panel_rect.left() <= self.edge_threshold:
                self.hidden_edge = 'left'
                target_x = -self.width() + 15
                target_y = panel_rect.y()
            elif panel_rect.top() <= self.edge_threshold:
                self.hidden_edge = 'top'
                target_x = panel_rect.x()
                target_y = -self.height() + 15
            elif panel_rect.bottom() >= screen.height() - self.edge_threshold:
                self.hidden_edge = 'bottom'
                target_x = panel_rect.x()
                target_y = screen.height() - 15
            else:
                return
            
            self.hide_animation.setStartValue(panel_rect)
            self.hide_animation.setEndValue(QRect(target_x, target_y, self.width(), self.height()))
            self.hide_animation.start()
            self.is_hidden = True
    
    def show_panel(self):
        if self.is_hidden and self.hidden_edge:
            screen = QDesktopWidget().screenGeometry()
            panel_rect = self.geometry()
            
            self.show_animation = QPropertyAnimation(self, b"geometry")
            self.show_animation.setDuration(400)
            self.show_animation.setEasingCurve(QEasingCurve.OutElastic)
            
            if self.hidden_edge == 'right':
                target_x = screen.width() - self.width() - 40
                target_y = panel_rect.y()
            elif self.hidden_edge == 'left':
                target_x = 40
                target_y = panel_rect.y()
            elif self.hidden_edge == 'top':
                target_x = panel_rect.x()
                target_y = 40
            elif self.hidden_edge == 'bottom':
                target_x = panel_rect.x()
                target_y = screen.height() - self.height() - 40
            else:
                return
            
            self.show_animation.setStartValue(panel_rect)
            self.show_animation.setEndValue(QRect(target_x, target_y, self.width(), self.height()))
            self.show_animation.start()
            self.is_hidden = False
            self.hidden_edge = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.screen_geometry = QDesktopWidget().screenGeometry() # 缓存屏幕信息
            
            # 拖拽开始时暂时移除阴影特效以提升性能
            self.container.setGraphicsEffect(None)
            # 拖拽时停止任何隐藏计时器
            self.hide_timer.stop()
            
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            # 移除所有复杂的逻辑，只保留移动，确保最流畅
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        
        # 拖拽结束，恢复阴影特效
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)
        
        # 拖拽结束后，检查是否停靠在边缘
        if not self.is_hidden:
            screen_width = self.screen_geometry.width()
            screen_height = self.screen_geometry.height()
            panel_rect = self.geometry()
            
            if (panel_rect.right() >= screen_width - self.edge_threshold or
                panel_rect.left() <= self.edge_threshold or
                panel_rect.top() <= self.edge_threshold or
                panel_rect.bottom() >= screen_height - self.edge_threshold):
                # 如果在边缘释放鼠标，启动隐藏计时器
                self.hide_timer.start(1200)
        
        if self.is_hidden:
            self.show_timer.start(100)
    
    def enterEvent(self, event):
        if self.is_hidden:
            self.show_panel()
        event.accept()
    
    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()

def main():
    # 设置 AUMID 以确保通知标题显示正确
    # 注意：在 Windows 上，AUMID 必须与快捷方式的 AUMID 匹配，或者对于未打包的应用，
    # 只要设置了唯一的 ID，系统通常会使用 setApplicationName 设置的名称作为通知标题。
    # 但有时直接显示 ID 可能是因为系统缓存或未正确识别。
    # 我们尝试使用一个更符合规范的格式。
    myappid = u'NBAScores.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setApplicationName("NBAScores.1.0")
    app.setApplicationDisplayName("NBAScores.1.0") # 显式设置显示名称
    
    # 动态创建并设置应用图标，确保通知栏有图标显示
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 1. 绘制背景圆 (使用路径数据中的灰色 #696065)
    painter.setBrush(QBrush(QColor("#696065")))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, 64, 64)
    
    # 2. 绘制奖杯图案 (黄色 #FBB01F)
    painter.setBrush(QBrush(QColor("#FBB01F")))
    
    # 奖杯底座
    painter.drawRect(20, 48, 24, 6)
    painter.drawRect(26, 42, 12, 6)
    
    # 奖杯杯身 (倒梯形 + 半圆)
    path_cup = QPainterPath()
    path_cup.moveTo(16, 16)
    path_cup.lineTo(48, 16)
    path_cup.lineTo(40, 36)
    path_cup.lineTo(24, 36)
    path_cup.closeSubpath()
    painter.drawPath(path_cup)
    
    # 奖杯把手 (左右圆弧)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor("#FBB01F"), 3))
    painter.drawArc(12, 18, 10, 10, 90*16, 180*16)
    painter.drawArc(42, 18, 10, 10, -90*16, 180*16)
    
    painter.end()
    app_icon = QIcon(pixmap)
    app.setWindowIcon(app_icon)
    
    app.setQuitOnLastWindowClosed(False)
    
    panel = NBAScoresPanel()
    panel.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
