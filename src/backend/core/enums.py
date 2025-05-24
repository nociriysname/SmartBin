from enum import Enum

__all__ = ("AccessLevel", "ProductType", "ProductStatus", "StopListReason")


class AccessLevel(Enum):
    owner = "owner"
    admin = "admin"
    employee = "employee"
    regional_manager = "regional_manager"
    CEO = "CEO"


class ProductType(Enum):
    box = "box"
    not_box = "not_box"


class ProductStatus(Enum):
    in_warehouse = "in_warehouse"
    stop_list = "stop_list"
    issued = "issued"


class StopListReason(Enum):
    fitting = "fitting"
    acceptance = "acceptance"
