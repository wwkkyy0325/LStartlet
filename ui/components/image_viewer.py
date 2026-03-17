"""
图片显示组件
支持上下结构布局，上部分显示图片，下部分提供图像处理功能
"""

from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QRubberBand, QGraphicsRectItem
)
from PySide6.QtCore import Qt, QRectF, Signal, QPoint, QRect, QSize, QPointF, QSizeF
from PySide6.QtGui import QPixmap, QWheelEvent, QKeyEvent, QMouseEvent, QTransform, QColor, QFont, QPen

from .base_component import BaseComponent
from ..config.ui_config import UIConfig
from ..state.ui_state import UIState


class ImageViewerWidget(QWidget):
    """
    图片查看器组件
    提供图片显示和基本图像处理功能
    """
    
    # 信号定义
    image_loaded = Signal(str)  # 图片加载完成
    image_transformed = Signal()  # 图片变换完成
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._fixed_width = 800
        self._fixed_height = 600
        
        # 设置固定大小
        self.setFixedSize(self._fixed_width, self._fixed_height)
        
        # 当前图片路径和原始pixmap
        self._current_image_path: Optional[str] = None
        self._original_pixmap: Optional[QPixmap] = None
        self._current_pixmap: Optional[QPixmap] = None
        
        # 缩放相关
        self._scale_factor = 1.0
        self._ctrl_pressed = False
        
        # 裁剪相关
        self._rubber_band: Optional[QRubberBand] = None
        self._origin_pos: Optional[QPoint] = None
        self._is_cropping = False
        self._crop_rect_item: Optional[QGraphicsRectItem] = None
        self._confirm_button: Optional[QPushButton] = None
        self._cancel_button: Optional[QPushButton] = None
        self._pending_crop_rect: Optional[QRectF] = None
        
        # 保存按钮
        self._save_btn: Optional[QPushButton] = None
        
        self._setup_ui()
        self._setup_connections()
        
        # 显示无图片状态
        self._show_no_image_state()
        
    def _setup_ui(self):
        """设置UI布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 上部分 - 图片显示区域 (占70%高度)
        image_height = int(self._fixed_height * 0.7)
        self._graphics_view = QGraphicsView()
        self._graphics_view.setFixedSize(self._fixed_width, image_height)
        self._graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._graphics_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._graphics_view.setInteractive(True)
        
        # 创建场景
        self._scene = QGraphicsScene()
        self._graphics_view.setScene(self._scene)
        
        # 图片项
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        
        main_layout.addWidget(self._graphics_view)
        
        # 下部分 - 控制按钮区域 (占30%高度)
        control_height = self._fixed_height - image_height
        control_widget = QWidget()
        control_widget.setFixedHeight(control_height)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(10, 5, 10, 5)
        control_layout.setSpacing(10)
        
        # 图像处理按钮
        self._crop_btn = QPushButton("裁剪")
        self._rotate_left_btn = QPushButton("↺ 左旋转")
        self._rotate_right_btn = QPushButton("↻ 右旋转")
        self._flip_vertical_btn = QPushButton("↕ 垂直翻转")
        self._flip_horizontal_btn = QPushButton("↔ 水平翻转")
        self._reset_btn = QPushButton("复原")
        self._save_btn = QPushButton("保存")
        
        # 设置按钮大小
        button_width = 80
        for btn in [self._crop_btn, self._rotate_left_btn, self._rotate_right_btn, 
                   self._flip_vertical_btn, self._flip_horizontal_btn, self._reset_btn, self._save_btn]:
            btn.setFixedWidth(button_width)
        
        control_layout.addWidget(self._crop_btn)
        control_layout.addWidget(self._rotate_left_btn)
        control_layout.addWidget(self._rotate_right_btn)
        control_layout.addWidget(self._flip_vertical_btn)
        control_layout.addWidget(self._flip_horizontal_btn)
        control_layout.addStretch()
        control_layout.addWidget(self._reset_btn)
        control_layout.addWidget(self._save_btn)
        
        main_layout.addWidget(control_widget)
        
    def _show_no_image_state(self):
        """显示无图片状态"""
        if self._scene is not None:
            # 清空场景中的所有项，但保留_pixmap_item
            items = self._scene.items()
            for item in items:
                if item != self._pixmap_item:
                    self._scene.removeItem(item)
            
            # 清空pixmap
            if self._pixmap_item is not None:
                self._pixmap_item.setPixmap(QPixmap())
            
            # 添加"无图片"文本
            text_item = self._scene.addText("无图片", QFont("Arial", 24))
            text_item.setDefaultTextColor(QColor(150, 150, 150))  # 灰色文字
            
            # 居中显示
            view_rect = self._graphics_view.rect()
            text_rect = text_item.boundingRect()
            text_item.setPos(
                (view_rect.width() - text_rect.width()) / 2,
                (view_rect.height() - text_rect.height()) / 2
            )
            
            # 设置场景矩形
            self._scene.setSceneRect(QRectF(0, 0, view_rect.width(), view_rect.height()))
    
    def _setup_connections(self):
        """设置信号连接"""
        self._crop_btn.clicked.connect(self._on_crop_clicked)
        self._rotate_left_btn.clicked.connect(self._on_rotate_left_clicked)
        self._rotate_right_btn.clicked.connect(self._on_rotate_right_clicked)
        self._flip_vertical_btn.clicked.connect(self._on_flip_vertical_clicked)
        self._flip_horizontal_btn.clicked.connect(self._on_flip_horizontal_clicked)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        self._save_btn.clicked.connect(self._on_save_clicked)
        
        # 连接图形视图的鼠标事件
        self._graphics_view.viewport().installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """事件过滤器，处理裁剪相关的鼠标事件"""
        if obj == self._graphics_view.viewport() and self._is_cropping:
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    # 检查是否点击了确认按钮
                    scene_pos = self._graphics_view.mapToScene(event.pos())
                    if self._handle_crop_confirmation_click(scene_pos):
                        return True
                    
                    # 开始新的裁剪区域选择
                    self._origin_pos = event.pos()
                    if self._rubber_band is None:
                        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self._graphics_view)
                    self._rubber_band.setGeometry(QRect(self._origin_pos, QSize()))
                    self._rubber_band.show()
                    
                    # 移除之前的裁剪矩形和按钮
                    if self._crop_rect_item is not None:
                        self._scene.removeItem(self._crop_rect_item)
                        self._crop_rect_item = None
                    if self._confirm_button is not None:
                        self._scene.removeItem(self._confirm_button)
                        self._confirm_button = None
                    if self._cancel_button is not None:
                        self._scene.removeItem(self._cancel_button)
                        self._cancel_button = None
                        
                    return True
                    
            elif event.type() == QMouseEvent.Type.MouseMove:
                if self._rubber_band is not None and self._origin_pos is not None:
                    self._rubber_band.setGeometry(QRect(self._origin_pos, event.pos()).normalized())
                    return True
                    
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton and self._rubber_band is not None:
                    # 获取裁剪区域
                    rect = self._rubber_band.geometry()
                    self._rubber_band.hide()
                    
                    # 将视口坐标转换为场景坐标
                    scene_rect = self._graphics_view.mapToScene(rect).boundingRect()
                    
                    # 保存待处理的裁剪区域
                    self._pending_crop_rect = scene_rect
                    
                    # 在场景中显示裁剪区域（带边框）
                    if self._crop_rect_item is not None:
                        self._scene.removeItem(self._crop_rect_item)
                    pen = QPen(QColor(255, 0, 0))
                    pen.setWidth(2)
                    self._crop_rect_item = self._scene.addRect(scene_rect, pen)  # 红色边框
                    
                    # 创建确认按钮
                    self._create_crop_confirmation_buttons(scene_rect)
                    
                    return True
        
        return super().eventFilter(obj, event)
        
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘按下事件"""
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pressed = True
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event: QKeyEvent):
        """处理键盘释放事件"""
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pressed = False
        super().keyReleaseEvent(event)
        
    def wheelEvent(self, event: QWheelEvent):
        """处理鼠标滚轮事件 - Ctrl+滚轮缩放"""
        if self._ctrl_pressed and self._current_pixmap is not None:
            # 获取滚轮方向
            delta = event.angleDelta().y()
            if delta > 0:
                # 放大
                self._scale_factor *= 1.1
            else:
                # 缩小
                self._scale_factor *= 0.9
            
            # 限制缩放范围
            self._scale_factor = max(0.1, min(self._scale_factor, 5.0))
            
            self._update_display(fit_to_view=False)
            self.image_transformed.emit()
            event.accept()
        else:
            super().wheelEvent(event)
            
    def set_image(self, image_path: str):
        """设置要显示的图片"""
        if not Path(image_path).exists():
            return
            
        self._current_image_path = image_path
        self._original_pixmap = QPixmap(image_path)
        self._current_pixmap = self._original_pixmap.copy()
        self._scale_factor = 1.0
        
        # 确保_pixmap_item存在
        if self._pixmap_item is None or self._scene is None:
            if self._scene is not None:
                self._pixmap_item = QGraphicsPixmapItem()
                self._scene.addItem(self._pixmap_item)
            else:
                return
        
        self._update_display(fit_to_view=True)
        self.image_loaded.emit(image_path)
        
    def _update_display(self, fit_to_view: bool = False):
        """更新图片显示"""
        if self._current_pixmap is None:
            self._show_no_image_state()
            return
            
        # 应用缩放
        scaled_pixmap = self._current_pixmap.scaled(
            self._current_pixmap.size() * self._scale_factor,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self._pixmap_item.setPixmap(scaled_pixmap)
        
        # 设置场景矩形为图片大小
        self._scene.setSceneRect(QRectF(scaled_pixmap.rect()))
        
        # 只在初始加载或复原时按比例填充到视图中
        if fit_to_view:
            self._graphics_view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def clear(self):
        """清空图片"""
        self._current_image_path = None
        self._original_pixmap = None
        self._current_pixmap = None
        self._scale_factor = 1.0
        self._show_no_image_state()
        
    def _on_crop_clicked(self):
        """处理裁剪按钮点击"""
        if self._current_pixmap is not None:
            if not self._is_cropping:
                # 进入裁剪模式
                self._is_cropping = True
                self._crop_btn.setStyleSheet("background-color: red; color: white;")
                self._ctrl_pressed = False  # 裁剪模式下禁用缩放
            else:
                # 退出裁剪模式
                self._exit_crop_mode()
                
    def _exit_crop_mode(self):
        """退出裁剪模式"""
        self._is_cropping = False
        self._crop_btn.setStyleSheet("")
        if self._rubber_band is not None:
            self._rubber_band.hide()
        if self._crop_rect_item is not None:
            self._scene.removeItem(self._crop_rect_item)
            self._crop_rect_item = None
        self._pending_crop_rect = None
        
    def _create_crop_confirmation_buttons(self, rect: QRectF):
        """创建裁剪确认按钮（红叉和绿勾）"""
        # 移除之前的确认按钮
        if self._confirm_button is not None:
            self._scene.removeItem(self._confirm_button)
        if self._cancel_button is not None:
            self._scene.removeItem(self._cancel_button)
            
        # 创建确认按钮（绿勾）
        confirm_x = rect.right() - 30
        confirm_y = rect.bottom() - 30
        
        # 使用文本项模拟按钮
        self._confirm_button = self._scene.addText("✓", QFont("Arial", 16))
        self._confirm_button.setDefaultTextColor(QColor(0, 255, 0))  # 绿色
        self._confirm_button.setPos(confirm_x, confirm_y)
        self._confirm_button.setData(Qt.ItemDataRole.UserRole, "confirm")
        
        # 创建取消按钮（红叉）
        cancel_x = rect.right() - 60
        cancel_y = rect.bottom() - 30
        
        self._cancel_button = self._scene.addText("✗", QFont("Arial", 16))
        self._cancel_button.setDefaultTextColor(QColor(255, 0, 0))  # 红色
        self._cancel_button.setPos(cancel_x, cancel_y)
        self._cancel_button.setData(Qt.ItemDataRole.UserRole, "cancel")
        
    def _handle_crop_confirmation_click(self, pos: QPointF):
        """处理裁剪确认按钮点击"""
        if self._confirm_button is not None and self._cancel_button is not None:
            # 检查是否点击了确认按钮
            confirm_rect = QRectF(
                self._confirm_button.pos(),
                QSizeF(self._confirm_button.boundingRect().width(), self._confirm_button.boundingRect().height())
            )
            cancel_rect = QRectF(
                self._cancel_button.pos(),
                QSizeF(self._cancel_button.boundingRect().width(), self._cancel_button.boundingRect().height())
            )
            
            if confirm_rect.contains(pos):
                # 执行裁剪
                self._execute_crop()
                return True
            elif cancel_rect.contains(pos):
                # 取消裁剪
                self._exit_crop_mode()
                return True
        return False
        
    def _execute_crop(self):
        """执行裁剪操作"""
        if self._pending_crop_rect is not None and self._current_pixmap is not None:
            # 将场景坐标转换为原始图片坐标
            current_scene_size = self._pixmap_item.pixmap().size()
            original_size = self._current_pixmap.size()
            
            crop_x = int(self._pending_crop_rect.x() * original_size.width() / current_scene_size.width())
            crop_y = int(self._pending_crop_rect.y() * original_size.height() / current_scene_size.height())
            crop_width = int(self._pending_crop_rect.width() * original_size.width() / current_scene_size.width())
            crop_height = int(self._pending_crop_rect.height() * original_size.height() / current_scene_size.height())
            
            # 确保裁剪区域在图片范围内
            crop_x = max(0, min(crop_x, original_size.width() - 1))
            crop_y = max(0, min(crop_y, original_size.height() - 1))
            crop_width = max(1, min(crop_width, original_size.width() - crop_x))
            crop_height = max(1, min(crop_height, original_size.height() - crop_y))
            
            # 执行裁剪
            cropped_pixmap = self._current_pixmap.copy(crop_x, crop_y, crop_width, crop_height)
            if not cropped_pixmap.isNull():
                self._current_pixmap = cropped_pixmap
                self._scale_factor = 1.0
                self._update_display(fit_to_view=True)
                self.image_transformed.emit()
        
        # 退出裁剪模式
        self._exit_crop_mode()
        
    def _on_rotate_left_clicked(self):
        """处理左旋转按钮点击"""
        if self._current_pixmap is not None:
            transform = QTransform()
            transform.rotate(-90)
            self._current_pixmap = self._current_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            self._update_display()
            self.image_transformed.emit()
            
    def _on_rotate_right_clicked(self):
        """处理右旋转按钮点击"""
        if self._current_pixmap is not None:
            transform = QTransform()
            transform.rotate(90)
            self._current_pixmap = self._current_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            self._update_display()
            self.image_transformed.emit()
            
    def _on_flip_vertical_clicked(self):
        """处理垂直翻转按钮点击"""
        if self._current_pixmap is not None:
            transform = QTransform()
            transform.scale(1, -1)
            self._current_pixmap = self._current_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            self._update_display()
            self.image_transformed.emit()
            
    def _on_flip_horizontal_clicked(self):
        """处理水平翻转按钮点击"""
        if self._current_pixmap is not None:
            transform = QTransform()
            transform.scale(-1, 1)
            self._current_pixmap = self._current_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            self._update_display()
            self.image_transformed.emit()
            
    def _on_reset_clicked(self):
        """处理复原按钮点击"""
        if self._original_pixmap is not None:
            self._current_pixmap = self._original_pixmap.copy()
            self._scale_factor = 1.0
            self._update_display(fit_to_view=True)
            self.image_transformed.emit()
            
    def _on_save_clicked(self):
        """处理保存按钮点击"""
        if self._current_pixmap is not None and self._current_image_path is not None:
            # 保存到原路径
            self._current_pixmap.save(self._current_image_path)
            # 也可以添加文件对话框让用户选择保存位置
            from core.logger import info
            info(f"图片已保存到: {self._current_image_path}")
            
    def get_current_image_path(self) -> Optional[str]:
        """获取当前图片路径"""
        return self._current_image_path

class ImageViewerComponent(BaseComponent):
    """图片查看器组件包装类"""
    
    def __init__(self, parent: Optional[QWidget] = None, component_id: Optional[str] = None):
        super().__init__(parent)
        self.component_id = component_id or f"image_viewer_{id(self)}"
        # 使用基类的_widget类型定义，避免类型覆盖问题
        self._widget = ImageViewerWidget(parent)
        
    def create_widget(self) -> QWidget:
        """创建图片查看器组件的widget"""
        if self._widget is None:
            raise RuntimeError("ImageViewerWidget not initialized properly")
        return self._widget
        
    def set_image(self, image_path: str):
        """设置要显示的图片"""
        if self._widget is not None:
            self._widget.set_image(image_path)
            
    def get_current_image_path(self) -> Optional[str]:
        """获取当前图片路径"""
        if self._widget is not None:
            return self._widget.get_current_image_path()
        return None
        
    def clear(self):
        """清空图片"""
        if self._widget is not None:
            self._widget.clear()
            
    def update_config(self, config: UIConfig) -> None:
        """更新组件配置 - 空实现，图片查看器不依赖UI配置"""
        pass
        
    def update_state(self, state: UIState) -> None:
        """更新组件状态 - 空实现，图片查看器不依赖UI状态"""
        pass
