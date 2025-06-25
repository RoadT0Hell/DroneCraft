from typing import Dict, List

class DroneWorkbenchSystem:
    """
    Хранит статичную конфигурацию верстака и рецептов.
    """
    def __init__(self):
        # Схема верстака 3x3: ID ячейки -> (ряд, колонка)
        self.workbench_layout = {
            0: (0, 0), 1: (0, 1), 2: (0, 2),
            3: (1, 0), 4: (1, 1), 5: (1, 2),
            6: (2, 0), 7: (2, 1), 8: (2, 2),
        }

        # Рецепты крафта. Для каждого ID прописано, какой дрон куда летит.
        # Это то, что будет возвращать get_idx_inside_workbench.
        self.craft_recipes = {
            0: {"name": "Кирка", "assignments": {"drone5": 1, "drone6": 4, "drone11": 7}},
            1: {"name": "Топор", "assignments": {"drone5": 0, "drone6": 1, "drone11": 3, "drone13": 4}},
            2: {"name": "Меч", "assignments": {"drone5": 4, "drone6": 5, "drone11": 3, "drone13": 6}},
            3: {"name": "Мотыга", "assignments": {"drone5": 0, "drone6": 1, "drone11": 4, "drone13": 7}}
        }

        # Физические размеры в метрах
        self.cell_size = 0.15  # 15 см между центрами ячеек
        self.hover_height = 0.3  # Высота зависания над ячейкой

# Создаем один экземпляр системы, чтобы не инициализировать его каждый раз
system = DroneWorkbenchSystem()

def get_idx_inside_workbench(craft_id: int, aruco_idx: int) -> Dict[str, int]:
    """
    Определяет, какие дроны должны лететь к каким позициям для указанного крафта.
    
    Args:
        craft_id: ID предмета для крафта (0-3).
        aruco_idx: ID ArUco маркера, который был обнаружен (используется для контекста).

    Returns:
        Словарь вида {"имя_дрона": номер_позиции}, например:
        {"drone5": 4, "drone6": 5, "drone11": 3, "drone13": 6}
    """
    if craft_id in system.craft_recipes:
        # Просто находим нужный рецепт и возвращаем предопределенные назначения
        recipe = system.craft_recipes[craft_id]
        print(f"INFO: Запрошен крафт '{recipe['name']}' (ID: {craft_id}). Назначения найдены.")
        return recipe["assignments"]
    else:
        print(f"ERROR: Рецепт для craft_id={craft_id} не найден.")
        return {}

def get_coords_to_fly(aruco_coords: list, aruco_idx: int, drone_idx: dict) -> Dict[str, list]:
    """
    Вычисляет физические XYZ координаты для полета каждого дрона.

    Args:
        aruco_coords: [x, y, z] координаты обнаруженного ArUco маркера.
        aruco_idx: ID этого ArUco маркера (например, 3).
        drone_idx: Словарь с назначениями дронов, полученный от get_idx_inside_workbench.

    Returns:
        Словарь вида {"имя_дрона": [x, y, z]}, например:
        {"drone5": [2.65, 1.8, 0.8], "drone6": [2.80, 1.8, 0.8], ...}
    """
    if aruco_idx not in system.workbench_layout:
        print(f"ERROR: Обнаруженный ArUco маркер с ID={aruco_idx} не является частью верстака.")
        return {}

    flight_coordinates = {}
    base_x, base_y, base_z = aruco_coords

    # Шаг 1: Получаем позицию (ряд, колонка) нашего опорного маркера
    base_row, base_col = system.workbench_layout[aruco_idx]

    # Шаг 2: Проходим по каждому дрону в списке задач
    for drone_name, target_pos_idx in drone_idx.items():
        if target_pos_idx not in system.workbench_layout:
            print(f"WARN: Для дрона {drone_name} указана неверная позиция {target_pos_idx}.")
            continue

        # Шаг 3: Получаем целевую позицию (ряд, колонка) для этого дрона
        target_row, target_col = system.workbench_layout[target_pos_idx]

        # Шаг 4: Вычисляем разницу в шагах по сетке
        # от опорного маркера до целевой ячейки
        col_diff = target_col - base_col
        row_diff = target_row - base_row

        # Шаг 5: Рассчитываем физические координаты
        # Ось Y часто инвертирована (положительное Y - "вперед", что соответствует уменьшению номера ряда)
        target_x = base_x + col_diff * system.cell_size
        target_y = base_y - row_diff * system.cell_size
        target_z = base_z + system.hover_height

        flight_coordinates[drone_name] = [round(target_x, 3), round(target_y, 3), round(target_z, 3)]
    
    return flight_coordinates

# --- Демонстрация работы ---
if __name__ == "__main__":
    print("--- Демонстрация работы системы планирования полетов ---")

    # Входные данные, как в вашем примере
    CRAFT_ID = 2  # Хотим скрафтить "Меч"
    
    # Предположим, камера обнаружила маркер с ID=3 в этих координатах
    ARUCO_IDX = 3
    ARUCO_COORDS = [2.5, 1.8, 0.5]  # [x, y, z] в метрах

    print(f"\n1. Получение назначений для крафта ID={CRAFT_ID}...")
    drone_assignments = get_idx_inside_workbench(craft_id=CRAFT_ID, aruco_idx=ARUCO_IDX)
    print(f"   Результат: {drone_assignments}")

    if drone_assignments:
        print(f"\n2. Расчет координат полета относительно маркера ID={ARUCO_IDX} в точке {ARUCO_COORDS}...")
        flight_plan = get_coords_to_fly(
            aruco_coords=ARUCO_COORDS,
            aruco_idx=ARUCO_IDX,
            drone_idx=drone_assignments
        )
        
        print("\n--- ИТОГОВЫЙ ПЛАН ПОЛЕТА ---")
        for drone, coords in flight_plan.items():
            print(f"  - Дрон {drone} летит в точку: [x={coords[0]}, y={coords[1]}, z={coords[2]}]")
        print("----------------------------")