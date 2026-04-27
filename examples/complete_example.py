"""
LStartlet 完整示例 - 任务管理系统

这个示例展示了 LStartlet 框架的所有公共 API 的使用方法。
这是一个功能完整的任务管理系统，包含用户管理、任务处理、通知等功能。
"""

from typing import Optional, List
from dataclasses import dataclass
from LStartlet import (
    ApplicationInfo,
    Service,
    Init,
    Start,
    Stop,
    Destroy,
    Event,
    publish_event,
    subscribe_event,
    get_config,
    set_config,
    Config,
    debug,
    info,
    warning,
    error,
    critical,
    start_framework,
    stop_framework,
    Interceptor,
    ValidateParams,
    Timing,
    inject,
    resolve_service,
)


# ============================================================================
# 1. 应用信息定义
# ============================================================================


@ApplicationInfo
class TaskManagerAppInfo:
    def get_directory_name(self) -> str:
        return "task_manager"

    def get_display_name(self) -> Optional[str]:
        return "任务管理系统"

    def get_author(self) -> Optional[str]:
        return "LStartlet Team"

    def get_email(self) -> Optional[str]:
        return "team@lstartlet.com"

    def get_description(self) -> Optional[str]:
        return "一个功能完整的任务管理系统示例"

    def get_version(self) -> Optional[str]:
        return "1.0.0"


# ============================================================================
# 2. 配置定义
# ============================================================================


@Config("app_config", "应用配置")
class AppConfig:
    max_tasks_per_user: int = 100
    task_priority_levels: int = 3
    enable_notifications: bool = True
    database_url: str = "sqlite:///tasks.db"
    log_level: str = "INFO"


@Config("user_config", "用户配置")
class UserConfig:
    max_users: int = 1000
    default_role: str = "user"
    enable_registration: bool = True


# ============================================================================
# 3. 事件定义
# ============================================================================


@dataclass
class UserCreatedEvent(Event):
    user_id: int
    username: str
    email: str


@dataclass
class TaskCreatedEvent(Event):
    task_id: int
    title: str
    user_id: int
    priority: int


@dataclass
class TaskCompletedEvent(Event):
    task_id: int
    user_id: int
    completion_time: float


@dataclass
class NotificationEvent(Event):
    user_id: int
    message: str
    notification_type: str


@dataclass
class SystemErrorEvent(Event):
    error_type: str
    error_message: str
    timestamp: float


# ============================================================================
# 4. 数据库服务
# ============================================================================


@Service(singleton=True)
class DatabaseService:
    def __init__(self):
        self.connected = False
        self.users = {}
        self.tasks = {}
        self.user_counter = 0
        self.task_counter = 0

    @Init(priority=-1)
    def initialize_database(self):
        debug("初始化数据库连接")
        database_url = get_config("database_url")  # 使用正确的键名
        info(f"连接数据库: {database_url}")

    @Start()
    def connect(self):
        info("数据库已连接")
        self.connected = True

    @Stop()
    def disconnect(self):
        info("数据库已断开")
        self.connected = False

    @Destroy()
    def cleanup(self):
        debug("清理数据库资源")

    def create_user(self, username: str, email: str) -> int:
        self.user_counter += 1
        user_id = self.user_counter
        self.users[user_id] = {
            "id": user_id,
            "username": username,
            "email": email,
            "tasks": [],
        }
        debug(f"创建用户: {username} (ID: {user_id})")
        return user_id

    def get_user(self, user_id: int) -> Optional[dict]:
        return self.users.get(user_id)

    def create_task(self, user_id: int, title: str, priority: int = 1) -> int:
        self.task_counter += 1
        task_id = self.task_counter
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "user_id": user_id,
            "priority": priority,
            "completed": False,
        }
        if user_id in self.users:
            self.users[user_id]["tasks"].append(task_id)
        debug(f"创建任务: {title} (ID: {task_id})")
        return task_id

    def get_task(self, task_id: int) -> Optional[dict]:
        return self.tasks.get(task_id)

    def complete_task(self, task_id: int) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id]["completed"] = True
            debug(f"完成任务: {task_id}")
            return True
        return False

    def get_user_tasks(self, user_id: int) -> List[dict]:
        if user_id not in self.users:
            return []
        task_ids = self.users[user_id]["tasks"]
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]


# ============================================================================
# 5. 用户服务
# ============================================================================


@Service(singleton=True)
class UserService:
    _db: DatabaseService = inject(DatabaseService)  # 类级别注入，框架会自动注入

    def __init__(self):
        pass

    @ValidateParams()
    @Timing(log_threshold=0.1)
    @Interceptor(
        intercept_params=lambda *args, **kwargs: (
            args,
            {k: v.strip() if isinstance(v, str) else v for k, v in kwargs.items()},
        )
    )
    def create_user(self, username: str, email: str) -> int:
        info(f"创建用户请求: {username}")

        max_users = get_config("max_users")  # 使用正确的键名
        if len(self._db.users) >= max_users:
            warning("用户数量已达上限")
            raise ValueError("用户数量已达上限")

        user_id = self._db.create_user(username, email)

        publish_event(UserCreatedEvent(user_id=user_id, username=username, email=email))

        return user_id

    @ValidateParams()
    def get_user(self, user_id: int) -> Optional[dict]:
        return self._db.get_user(user_id)

    @Interceptor(intercept_result=lambda result: result or None)
    def get_all_users(self) -> List[dict]:
        return list(self._db.users.values())


# ============================================================================
# 6. 任务服务
# ============================================================================


@Service(singleton=True)
class TaskService:
    def __init__(self):
        self._db: DatabaseService = inject(DatabaseService)

    @ValidateParams()
    @Timing(log_threshold=0.1)
    def create_task(self, user_id: int, title: str, priority: int = 1) -> int:
        info(f"创建任务请求: {title}")

        user = self._db.get_user(user_id)
        if not user:
            error(f"用户不存在: {user_id}")
            raise ValueError("用户不存在")

        max_priority = get_config("task_priority_levels")  # 使用正确的键名
        if priority < 1 or priority > max_priority:
            warning(f"任务优先级无效: {priority}")
            raise ValueError(f"任务优先级必须在 1-{max_priority} 之间")

        task_id = self._db.create_task(user_id, title, priority)

        publish_event(
            TaskCreatedEvent(
                task_id=task_id, title=title, user_id=user_id, priority=priority
            )
        )

        return task_id

    @ValidateParams()
    def complete_task(self, task_id: int) -> bool:
        info(f"完成任务请求: {task_id}")

        task = self._db.get_task(task_id)
        if not task:
            error(f"任务不存在: {task_id}")
            return False

        if task["completed"]:
            warning(f"任务已完成: {task_id}")
            return True

        success = self._db.complete_task(task_id)
        if success:
            import time

            publish_event(
                TaskCompletedEvent(
                    task_id=task_id,
                    user_id=task["user_id"],
                    completion_time=time.time(),
                )
            )

        return success

    @ValidateParams()
    def get_task(self, task_id: int) -> Optional[dict]:
        return self._db.get_task(task_id)

    @ValidateParams()
    def get_user_tasks(self, user_id: int) -> List[dict]:
        return self._db.get_user_tasks(user_id)

    @Interceptor(
        intercept_result=lambda result: sorted(
            result, key=lambda x: x["priority"], reverse=True
        )
    )
    def get_pending_tasks(self, user_id: int) -> List[dict]:
        tasks = self._db.get_user_tasks(user_id)
        return [t for t in tasks if not t["completed"]]


# ============================================================================
# 7. 通知服务
# ============================================================================


@Service(singleton=True)
class NotificationService:
    def __init__(self):
        self.notifications = []
        self.enable_notifications = True

    @Init()
    def initialize_notifications(self):
        self.enable_notifications = get_config("enable_notifications")  # 使用正确的键名
        debug(f"通知服务初始化: {'启用' if self.enable_notifications else '禁用'}")

    @ValidateParams()
    def send_notification(
        self, user_id: int, message: str, notification_type: str = "info"
    ) -> bool:
        if not self.enable_notifications:
            debug("通知已禁用")
            return False

        info(f"发送通知给用户 {user_id}: {message}")

        notification = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "read": False,
        }
        self.notifications.append(notification)

        publish_event(
            NotificationEvent(
                user_id=user_id, message=message, notification_type=notification_type
            )
        )

        return True

    @ValidateParams()
    def get_user_notifications(self, user_id: int) -> List[dict]:
        return [n for n in self.notifications if n["user_id"] == user_id]

    @Interceptor(intercept_exception=lambda e: (error(f"通知发送失败: {e}"), False)[1])
    def send_bulk_notification(self, user_ids: List[int], message: str) -> int:
        success_count = 0
        for user_id in user_ids:
            if self.send_notification(user_id, message):
                success_count += 1
        return success_count


# ============================================================================
# 8. 统计服务
# ============================================================================


@Service(singleton=True)
class TaskStatisticsService:
    def __init__(self):
        self._db: DatabaseService = inject(DatabaseService)
        self.stats = {
            "total_users": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "pending_tasks": 0,
        }

    @Start()
    def start_statistics(self):
        info("统计服务已启动")
        self.update_statistics()

    @Timing(log_threshold=0.05)
    def update_statistics(self):
        self.stats["total_users"] = len(self._db.users)
        self.stats["total_tasks"] = len(self._db.tasks)
        self.stats["completed_tasks"] = sum(
            1 for t in self._db.tasks.values() if t["completed"]
        )
        self.stats["pending_tasks"] = sum(
            1 for t in self._db.tasks.values() if not t["completed"]
        )
        debug(f"统计信息已更新: {self.stats}")

    def get_statistics(self) -> dict:
        return self.stats.copy()

    @Interceptor(
        intercept_result=lambda result: {
            "completion_rate": (
                (result["completed_tasks"] / result["total_tasks"] * 100)
                if result["total_tasks"] > 0
                else 0
            ),
            **result,
        }
    )
    def get_statistics_with_rate(self) -> dict:
        return self.get_statistics()


# ============================================================================
# 9. 事件处理器
# ============================================================================


def setup_event_handlers():
    def handle_user_created(event: UserCreatedEvent):
        info(f"用户创建事件: {event.username}")
        notification_service = NotificationService()
        notification_service.send_notification(
            event.user_id, f"欢迎 {event.username}！您的账户已创建成功。", "welcome"
        )

    def handle_task_created(event: TaskCreatedEvent):
        info(f"任务创建事件: {event.title}")
        notification_service = NotificationService()
        notification_service.send_notification(
            event.user_id,
            f"任务 '{event.title}' 已创建，优先级: {event.priority}",
            "task",
        )

    def handle_task_completed(event: TaskCompletedEvent):
        info(f"任务完成事件: {event.task_id}")
        notification_service = NotificationService()
        notification_service.send_notification(
            event.user_id, f"任务 {event.task_id} 已完成！", "success"
        )

    def handle_notification_event(event: NotificationEvent):
        debug(f"通知事件: {event.message}")

    def handle_system_error(event: SystemErrorEvent):
        error(f"系统错误: {event.error_type} - {event.error_message}")

    subscribe_event(UserCreatedEvent, handle_user_created)
    subscribe_event(TaskCreatedEvent, handle_task_created)
    subscribe_event(TaskCompletedEvent, handle_task_completed)
    subscribe_event(NotificationEvent, handle_notification_event)
    subscribe_event(SystemErrorEvent, handle_system_error)


# ============================================================================
# 10. 错误处理和监控
# ============================================================================


@Service(singleton=True)
class ErrorHandlingService:
    def __init__(self):
        self.error_count = 0
        self.last_error = None

    @Interceptor(
        intercept_exception=lambda e: (
            error(f"捕获异常: {type(e).__name__}: {e}"),
            publish_event(
                SystemErrorEvent(
                    error_type=type(e).__name__, error_message=str(e), timestamp=0.0
                )
            ),
            None,
        )[2]
    )
    def safe_execute(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def report_error(self, error_type: str, error_message: str):
        self.error_count += 1
        self.last_error = error_message
        critical(f"错误报告: {error_type} - {error_message}")

    def get_error_stats(self) -> dict:
        return {"error_count": self.error_count, "last_error": self.last_error}


# ============================================================================
# 11. 主应用
# ============================================================================


class TaskManagerApp:
    def __init__(self):
        pass

    @Timing(log_threshold=0.2)
    def create_user(self, username: str, email: str) -> int:
        user_service = resolve_service(UserService)
        return user_service.create_user(username, email)

    @Timing(log_threshold=0.2)
    def create_task(self, user_id: int, title: str, priority: int = 1) -> int:
        task_service = resolve_service(TaskService)
        return task_service.create_task(user_id, title, priority)

    @Timing(log_threshold=0.1)
    def complete_task(self, task_id: int) -> bool:
        task_service = resolve_service(TaskService)
        return task_service.complete_task(task_id)

    def get_user_tasks(self, user_id: int) -> List[dict]:
        task_service = resolve_service(TaskService)
        return task_service.get_user_tasks(user_id)

    def get_statistics(self) -> dict:
        statistics_service = resolve_service(TaskStatisticsService)
        return statistics_service.get_statistics_with_rate()

    def get_user_notifications(self, user_id: int) -> List[dict]:
        notification_service = resolve_service(NotificationService)
        return notification_service.get_user_notifications(user_id)

    @ValidateParams()
    def update_config(self, key: str, value):
        info(f"更新配置: {key} = {value}")
        set_config(key, value)


# ============================================================================
# 12. 示例运行
# ============================================================================


def run_example():
    info("=" * 60)
    info("任务管理系统示例")
    info("=" * 60)

    app = TaskManagerApp()

    try:
        info("\n1. 创建用户")
        user1_id = app.create_user("Alice", "alice@example.com")
        user2_id = app.create_user("Bob", "bob@example.com")
        user3_id = app.create_user("Charlie", "charlie@example.com")
        info(f"已创建用户: {user1_id}, {user2_id}, {user3_id}")

        info("\n2. 创建任务")
        task1_id = app.create_task(user1_id, "完成项目文档", 3)
        task2_id = app.create_task(user1_id, "代码审查", 2)
        task3_id = app.create_task(user2_id, "修复 Bug", 3)
        task4_id = app.create_task(user3_id, "编写测试", 1)
        info(f"已创建任务: {task1_id}, {task2_id}, {task3_id}, {task4_id}")

        info("\n3. 查看用户任务")
        alice_tasks = app.get_user_tasks(user1_id)
        info(f"Alice 的任务: {len(alice_tasks)} 个")
        for task in alice_tasks:
            status = "已完成" if task["completed"] else "待处理"
            info(f"  - {task['title']} (优先级: {task['priority']}, 状态: {status})")

        info("\n4. 完成任务")
        app.complete_task(task1_id)
        app.complete_task(task3_id)
        info(f"已完成任务: {task1_id}, {task3_id}")

        info("\n5. 查看统计信息")
        stats = app.get_statistics()
        info(f"统计信息:")
        info(f"  - 总用户数: {stats['total_users']}")
        info(f"  - 总任务数: {stats['total_tasks']}")
        info(f"  - 已完成任务: {stats['completed_tasks']}")
        info(f"  - 待处理任务: {stats['pending_tasks']}")
        info(f"  - 完成率: {stats['completion_rate']:.2f}%")

        info("\n6. 查看用户通知")
        notifications = app.get_user_notifications(user1_id)
        info(f"Alice 的通知: {len(notifications)} 条")
        for notif in notifications:
            info(f"  - [{notif['type']}] {notif['message']}")

        info("\n7. 更新配置")
        app.update_config("enable_notifications", False)  # 使用正确的键名
        app.update_config("task_priority_levels", 5)  # 使用正确的键名
        info("配置已更新")

        info("\n8. 测试参数验证")
        try:
            app.create_task(user1_id, "新任务", 10)
        except ValueError as e:
            warning(f"参数验证生效: {e}")

        info("\n9. 测试错误处理")
        try:
            app.complete_task(9999)
        except Exception as e:
            error(f"错误处理: {e}")

        info("\n" + "=" * 60)
        info("示例运行完成")
        info("=" * 60)

    except Exception as e:
        critical(f"示例运行失败: {e}")
        raise


# ============================================================================
# 13. 主程序入口
# ============================================================================


def main():
    debug("启动任务管理系统")

    setup_event_handlers()

    start_framework(app_info=TaskManagerAppInfo)

    try:
        run_example()
    except KeyboardInterrupt:
        info("用户中断")
    except Exception as e:
        critical(f"发生错误: {e}")
    finally:
        info("正在停止框架...")
        stop_framework()
        info("框架已停止")


if __name__ == "__main__":
    main()
