from typing import Optional, get_origin, get_args


class ServiceResolutionError(Exception):
    """服务解析错误"""
    
    def __init__(self, service_type: type, message: str, inner_exception: Optional[Exception] = None):
        self.service_type = service_type
        self.inner_exception = inner_exception
        
        # 安全地获取类型名称，处理 typing 模块中的类型
        if hasattr(service_type, '__name__'):
            type_name = service_type.__name__
        elif hasattr(service_type, '__origin__'):
            # 处理泛型类型，如 List[str], Dict[str, Any] 等
            origin = get_origin(service_type)
            args = get_args(service_type)
            if origin is not None:
                origin_name = getattr(origin, '__name__', str(origin))
                if args:
                    args_str = ', '.join(str(arg) for arg in args)
                    type_name = f"{origin_name}[{args_str}]"
                else:
                    type_name = str(origin)
            else:
                type_name = str(service_type)
        else:
            type_name = str(service_type)
            
        super().__init__(f"无法解析服务 {type_name}: {message}")


class ServiceRegistrationError(Exception):
    """服务注册错误"""
    
    def __init__(self, service_type: type, message: str):
        self.service_type = service_type
        
        # 安全地获取类型名称，处理 typing 模块中的类型
        if hasattr(service_type, '__name__'):
            type_name = service_type.__name__
        elif hasattr(service_type, '__origin__'):
            # 处理泛型类型，如 List[str], Dict[str, Any] 等
            origin = get_origin(service_type)
            args = get_args(service_type)
            if origin is not None:
                origin_name = getattr(origin, '__name__', str(origin))
                if args:
                    args_str = ', '.join(str(arg) for arg in args)
                    type_name = f"{origin_name}[{args_str}]"
                else:
                    type_name = str(origin)
            else:
                type_name = str(service_type)
        else:
            type_name = str(service_type)
            
        super().__init__(f"服务注册失败 {type_name}: {message}")