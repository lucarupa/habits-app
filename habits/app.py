# spec: 001-habits-mvp
"""Interfaz de escritorio para Habits App.

Capa de presentación en Flet 1.0: vistas y navegación, sin lógica de negocio.
Delega toda la lógica a `core.py` y `storage.py`.

Constitución principio 3: la capa de interfaz nunca contiene cálculos ni acceso a datos.
"""

from datetime import date
from typing import Any, Callable

import flet as ft

from habits.core import (
    DEFAULT_ICON,
    Habit,
    create_habit,
    calculate_streak,
)
from habits.app_state import (
    EMPTY_BUTTON_LABEL,
    EMPTY_SIDEBAR_MESSAGE,
    EMPTY_TITLE,
    AppState,
    SidebarItem,
    format_date_label,
    load_app_state,
)
from habits.habit_form import (
    ICON_CATALOG,
    ICON_LABELS,
    MAX_NAME_LENGTH,
    CreateHabitResult,
    HabitFormData,
    create_habit_from_form,
)
from habits.theme import (
    ACCENT_GREEN,
    BACKGROUND,
    SELECTED_BG,
    SIDEBAR_BG,
    SIDEBAR_WIDTH,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from habits.storage import (
    init_db,
    create_habit_db,
    list_all_habits_db,
    get_completions_db,
    mark_completed_db,
    is_completed_today_db,
)

ICON_BY_KEY = {
    "book": ft.Icons.MENU_BOOK,
    "code": ft.Icons.CODE,
    "science": ft.Icons.SCIENCE,
    "language": ft.Icons.TRANSLATE,
    "music": ft.Icons.MUSIC_NOTE,
    "art": ft.Icons.PALETTE,
    "math": ft.Icons.CALCULATE,
    "fitness": ft.Icons.FITNESS_CENTER,
}
DEFAULT_SIDEBAR_ICON = ft.Icons.MENU_BOOK


def icon_for_habit(icon_key: str):
    """Traducir una clave semántica de icono a un icono de Flet.

    Args:
        icon_key: Clave guardada en la base de datos.

    Returns:
        El icono de Flet correspondiente, o el icono por defecto.
    """
    return ICON_BY_KEY.get(icon_key, DEFAULT_SIDEBAR_ICON)


def format_streak_label(streak: int) -> str:
    """Formatear la racha para mostrarla en la barra lateral.

    Args:
        streak: Racha actual en días.

    Returns:
        Texto en español con la racha, o "Sin racha" si es 0.
    """
    if streak == 0:
        return "Sin racha"
    suffix = "s" if streak != 1 else ""
    return f"🔥 {streak} día{suffix}"


def format_date_display(d: date) -> str:
    """Formatear una fecha para mostrar al usuario en dd/mm/aaaa (Tarea 6.4).

    Args:
        d: La fecha a formatear.

    Returns:
        La fecha como cadena en formato dd/mm/aaaa.
    """
    return format_date_label(d)


@ft.control
class Sidebar(ft.Container):
    """Barra lateral con “Mis hábitos”, “+ Nuevo” y la lista de hábitos.

    Tarea 3.2, RF-1.2, RF-1.4, RF-1.6, RF-7.2. Muestra el icono, el nombre y
    la racha de cada hábito; el orden proviene de `AppState`. El hábito
    seleccionado se resalta con fondo y un indicador lateral.
    """

    state: AppState | None = None
    on_select: Callable[[int], None] | None = None
    on_new: Callable[[], None] | None = None
    _items_column: ft.Column | None = None

    def init(self):
        self.width = SIDEBAR_WIDTH
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SIDEBAR_BG
        self._items_column = ft.Column(spacing=4)
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Mis hábitos", size=20, weight="bold"),
                        ft.Container(expand=True),
                        ft.Button(
                            content="+ Nuevo",
                            icon=ft.Icons.ADD,
                            on_click=self._handle_new,
                        ),
                    ],
                    alignment="spaceBetween",
                    vertical_alignment="center",
                ),
                self._items_column,
            ],
            spacing=12,
        )
        self.refresh()

    def refresh(self):
        """Reconstruir la lista de hábitos desde el estado actual."""
        if self._items_column is None:
            return

        items = self.state.sidebar_items() if self.state is not None else []
        if not items:
            self._items_column.controls = [
                ft.Text(
                    EMPTY_SIDEBAR_MESSAGE,
                    size=12,
                    color=TEXT_SECONDARY,
                )
            ]
            return

        self._items_column.controls = [
            self._build_item(item) for item in items
        ]

    def _handle_new(self, event):
        """Notificar que el usuario pidió crear un hábito (RF-1.6)."""
        if self.on_new is not None:
            self.on_new()

    def _select_habit(self, habit_id: int):
        """Seleccionar un hábito y notificar al panel de detalle (RF-1.4)."""
        if self.state is None:
            return

        self.state.select(habit_id)
        self.refresh()
        if self.on_select is not None:
            self.on_select(habit_id)

    def _build_item(self, item: SidebarItem) -> ft.Container:
        """Construir el control de un hábito de la barra lateral (RF-1.2)."""
        selected = item.selected
        indicator_color = ACCENT_GREEN if selected else "transparent"
        text_color = ACCENT_GREEN if selected else TEXT_PRIMARY

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=4,
                        height=40,
                        bgcolor=indicator_color,
                        border_radius=2,
                    ),
                    ft.Icon(
                        icon_for_habit(item.icon),
                        size=18,
                        color=text_color,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                item.name,
                                size=14,
                                weight="medium",
                                color=text_color,
                            ),
                            ft.Text(
                                format_streak_label(item.streak),
                                size=12,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment="center",
            ),
            padding=8,
            border_radius=8,
            bgcolor=SELECTED_BG if selected else None,
            on_click=lambda event, habit_id=item.habit_id: self._select_habit(
                habit_id
            ),
        )


@ft.control
class HabitDetailHeader(ft.Container):
    """Encabezado del panel de detalle del hábito seleccionado.

    Tarea 3.3, RF-3.1, RF-7.4. Muestra el icono, el nombre, el subtítulo
    “Hábito de estudio” y la fecha de inicio en dd/mm/aaaa.
    """

    state: AppState | None = None
    _body: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._body = ft.Column(spacing=8)
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Reconstruir el encabezado desde el estado actual."""
        if self._body is None:
            return

        header = (
            self.state.detail_header() if self.state is not None else None
        )
        if header is None:
            self._body.controls = []
            return

        self._body.controls = [
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            icon_for_habit(header.icon),
                            size=28,
                            color=ACCENT_GREEN,
                        ),
                        padding=10,
                        border_radius=10,
                        bgcolor=SELECTED_BG,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                header.name,
                                size=24,
                                weight="bold",
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                header.subtitle,
                                size=14,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment="center",
            ),
            ft.Text(
                value=f"Inicio: {header.start_date_label}",
                size=12,
                color=TEXT_SECONDARY,
            ),
        ]


@ft.control
class EmptyDetailPanel(ft.Container):
    """Estado vacío del panel principal cuando no hay hábitos.

    Tarea 3.4, RF-6.2, RF-6.4. Muestra una ilustración, el título de
    bienvenida y el botón “+ Crear hábito”. Se oculta en cuanto existe al
    menos un hábito.
    """

    state: AppState | None = None
    on_create: Callable[[], None] | None = None

    def init(self):
        self.expand = True
        self.padding = 32
        self.content = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.SELF_IMPROVEMENT,
                    size=64,
                    color=ACCENT_GREEN,
                ),
                ft.Text(
                    EMPTY_TITLE,
                    size=20,
                    weight="bold",
                    text_align="center",
                    color=TEXT_PRIMARY,
                ),
                ft.Button(
                    content=EMPTY_BUTTON_LABEL,
                    icon=ft.Icons.ADD,
                    on_click=self._handle_create,
                ),
            ],
            horizontal_alignment="center",
            alignment="center",
            spacing=16,
        )
        self.refresh()

    def refresh(self):
        """Mostrar el estado vacío solo cuando no hay hábitos."""
        empty = (
            self.state.empty_state() if self.state is not None else None
        )
        self.visible = empty is not None

    def _handle_create(self, event):
        """Abrir el diálogo de creación desde el estado vacío (RF-6.3)."""
        if self.on_create is not None:
            self.on_create()


class HabitFormDialog:
    """Diálogo modal para crear un hábito sin abandonar la vista actual.

    Tareas 4.1 a 4.3, RF-2.1 a RF-2.7, RF-2.9 y RF-2.10. Contiene el nombre
    obligatorio, la fecha opcional en dd/mm/aaaa y el selector de icono. La
    validación y la persistencia se delegan en `habit_form.py`; ante un error
    el diálogo permanece abierto y, al guardar correctamente, se cierra y
    notifica el hábito creado.
    """

    def __init__(
        self,
        page: ft.Page,
        on_saved: Callable[[CreateHabitResult], None] | None = None,
        db_path: str = "data/habits.db",
        today: date | None = None,
    ) -> None:
        """Construir el diálogo y sus controles.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_saved: Callback invocado con el hábito recién creado.
            db_path: Ruta a la base de datos SQLite.
            today: Fecha actual; permite fijarla en tests.
        """
        self.page = page
        self.on_saved = on_saved
        self.db_path = db_path
        self.today = today

        self.name_field = ft.TextField(
            label="Nombre del hábito",
            hint_text="Ej: Estudiar Python 30 minutos",
            max_length=MAX_NAME_LENGTH,
            autofocus=True,
            border_radius=8,
        )
        self.date_field = ft.TextField(
            label="Fecha de inicio (opcional)",
            hint_text="dd/mm/aaaa",
            max_length=10,
            border_radius=8,
        )
        self.icon_dropdown = ft.Dropdown(
            label="Icono",
            value=DEFAULT_ICON,
            border_radius=8,
            options=[
                ft.DropdownOption(
                    key=icon,
                    text=ICON_LABELS[icon],
                    leading_icon=icon_for_habit(icon),
                )
                for icon in ICON_CATALOG
            ],
        )
        self.error_text = ft.Text(
            value="",
            size=14,
            color="red",
            visible=False,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo hábito", size=20, weight="bold"),
            content=ft.Column(
                controls=[
                    self.name_field,
                    self.date_field,
                    self.icon_dropdown,
                    self.error_text,
                ],
                spacing=12,
                tight=True,
                width=420,
            ),
            actions=[
                ft.TextButton(
                    content="Cancelar",
                    on_click=self.close,
                ),
                ft.Button(
                    content="Guardar",
                    icon=ft.Icons.CHECK,
                    on_click=self.submit,
                ),
            ],
            actions_alignment="end",
        )

    def open(self) -> None:
        """Abrir el diálogo con un formulario limpio (RF-2.1)."""
        self.name_field.value = ""
        self.date_field.value = ""
        self.icon_dropdown.value = DEFAULT_ICON
        self.error_text.value = ""
        self.error_text.visible = False
        self.page.show_dialog(self.dialog)

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin crear nada."""
        self.page.pop_dialog()

    def submit(self, event=None) -> None:
        """Validar y guardar el hábito.

        Si la validación falla, muestra el mensaje y mantiene el diálogo
        abierto (RF-2.2, RF-2.3, RF-2.10). Si tiene éxito, persiste el hábito,
        cierra el diálogo y notifica el resultado (RF-2.7, RF-2.9).
        """
        data = HabitFormData(
            name=self.name_field.value or "",
            start_date=self.date_field.value or "",
            icon=self.icon_dropdown.value,
        )

        try:
            result = create_habit_from_form(
                data,
                db_path=self.db_path,
                today=self.today,
            )
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self._show_error("")
        self.page.pop_dialog()
        if self.on_saved is not None:
            self.on_saved(result)

    def _show_error(self, message: str) -> None:
        """Mostrar u ocultar el mensaje de error sin cerrar el diálogo."""
        self.error_text.value = message
        self.error_text.visible = bool(message)
        if self.dialog.open:
            self.page.update()


@ft.control
class CreateHabitView(ft.Column):
    """Vista para crear nuevos hábitos (Tarea 6.2, RF-1).

    Formulario con nombre obligatorio y fecha de inicio opcional.
    Valida las entradas y delega la creación a core.py y storage.py.
    """

    on_habit_created: Callable[..., Any] | None = None
    name_field: ft.TextField | None = None
    date_field: ft.TextField | None = None
    status_text: ft.Text | None = None

    def init(self):
        init_db()

        self.name_field = ft.TextField(
            label="Nombre del hábito",
            hint_text="Ej: Estudiar Python 30 minutos",
            max_length=60,
            border_radius=8,
            expand=True,
        )

        self.date_field = ft.TextField(
            label="Fecha de inicio (opcional)",
            hint_text="dd/mm/aaaa",
            max_length=10,
            border_radius=8,
            expand=True,
        )

        self.status_text = ft.Text(value="", size=14)

        self.controls = [
            ft.Row(
                [ft.IconButton(ft.Icons.ARROW_BACK, on_click=self._go_back)],
                alignment="start",
            ),
            ft.Text(value="Crear nuevo hábito", size=24, weight="bold"),
            self.name_field,
            self.date_field,
            ft.Button(
                content="Crear hábito",
                on_click=self._create_habit,
                icon=ft.Icons.PLUS_ONE,
            ),
            self.status_text,
        ]
        self.spacing = 16

    def _go_back(self, e):
        """Navegar de vuelta a la pantalla principal."""
        self.page.navigate("/")

    def _create_habit(self, e):
        """Validar el formulario y crear el hábito (RF-1)."""
        if self.name_field is None or self.status_text is None:
            return

        name = self.name_field.value.strip() if self.name_field.value else ""

        # Validación: nombre vacío (RF-1.3)
        if not name:
            self.status_text.value = "⚠️ El nombre del hábito es obligatorio."
            self.status_text.color = "red"
            return

        # Validación: nombre muy largo (RF-1.4)
        if len(name) > 60:
            self.status_text.value = (
                "⚠️ El nombre no puede superar 60 caracteres."
            )
            self.status_text.color = "red"
            return

        # Parsear fecha opcional (RF-1.2)
        start_date = None
        if self.date_field and self.date_field.value and self.date_field.value.strip():
            date_str = self.date_field.value.strip()
            try:
                day, month, year = date_str.split("/")
                parsed_date = date(int(year), int(month), int(day))
                if parsed_date > date.today():
                    # Caso límite: fecha futura se corrige a hoy
                    start_date = date.today()
                else:
                    start_date = parsed_date
            except ValueError:
                self.status_text.value = (
                    "⚠️ Formato de fecha inválido. Usa dd/mm/aaaa."
                )
                self.status_text.color = "red"
                return

        # Crear el hábito delegando en core.py y storage.py
        try:
            habit = create_habit(name, start_date)
            create_habit_db(
                habit.name,
                habit.start_date.isoformat(),
            )
            start_display = format_date_display(habit.start_date)
            self.status_text.value = (
                f"✅ Hábito «{habit.name}» creado exitosamente. "
                f"Inicio: {start_display}"
            )
            self.status_text.color = "green"
            self.name_field.value = ""
            if self.date_field:
                self.date_field.value = ""

            # Notificar a otras vistas que se creó un hábito
            if self.on_habit_created:
                self.on_habit_created()

        except ValueError as exc:
            self.status_text.value = f"⚠️ {exc}"
            self.status_text.color = "red"
            return


# Referencias globales para callbacks entre vistas
_list_view_ref: dict = {"view": None}


@ft.control
class ListHabitsView(ft.Column):
    """Vista para listar hábitos con rachas y botones de marcar (Tarea 6.3).

    Muestra todos los hábitos ordenados por racha descendente (RF-3.1, RF-3.2).
    Cada hábito tiene un botón para marcar como completado hoy (RF-2.1).
    Muestra mensajes cuando no hay hábitos o cuando ya está marcado (RF-2.2).
    """

    on_habit_marked: Callable[..., Any] | None = None
    status_text: ft.Text | None = None
    empty_text: ft.Text | None = None
    _habits_container: ft.Column | None = None

    def init(self):
        init_db()

        self.status_text = ft.Text(value="", size=14)
        self.empty_text = ft.Text(
            value="Aún no hay hábitos. ¡Crea tu primer hábito!",
            size=16,
            color="gray",
        )
        self._habits_container = ft.Column(spacing=8)

        self.controls = [
            ft.Row(
                [ft.IconButton(ft.Icons.ARROW_BACK, on_click=self._go_back)],
                alignment="start",
            ),
            ft.Text(value="Mis hábitos", size=24, weight="bold"),
            self.status_text,
            ft.Text(
                value="Toca el botón ✓ para marcar un hábito como completado hoy.",
                size=12,
                color="gray",
            ),
            self.empty_text,
            self._habits_container,
        ]
        self.spacing = 12

    def _go_back(self, e):
        """Navegar de vuelta a la pantalla principal."""
        self.page.navigate("/")

    def refresh_list(self):
        """Recargar la lista de hábitos con rachas actualizadas (RF-3)."""
        if self.status_text is None or self.empty_text is None or self._habits_container is None:
            return

        # Limpiar items anteriores
        self._habits_container.controls.clear()

        # Obtener todos los hábitos de la BD
        all_habits = list_all_habits_db()

        if not all_habits:
            self.empty_text.visible = True
            self.status_text.value = ""
            return

        self.empty_text.visible = False

        # Construir objetos Habit y sus fechas de completado
        today = date.today()
        habits: list[Habit] = []
        completions_by_habit: dict[int, set[date]] = {}

        for row in all_habits:
            habit = Habit(
                id=row.id,
                name=row.name,
                start_date=date.fromisoformat(row.start_date),
            )
            habits.append(habit)

            # Obtener fechas de completado desde la BD
            completed_dates_str = get_completions_db(row.id)
            completed_dates = set()
            for d_str in completed_dates_str:
                completed_dates.add(date.fromisoformat(d_str))
            completions_by_habit[row.id] = completed_dates

        # Calcular rachas y ordenar (RF-3.1 a RF-3.4)
        ranked = self._list_habits_with_streak(habits, completions_by_habit, today)

        # Crear un item UI por cada hábito
        for habit, streak in ranked:
            item = self._create_habit_item(habit, streak, today)
            self._habits_container.controls.append(item)

        self.status_text.value = ""

    def _list_habits_with_streak(
        self,
        habits: list[Habit],
        completions_by_habit: dict[int, set[date]],
        today: date,
    ) -> list[tuple[Habit, int]]:
        """Ordenar hábitos por racha descendente y nombre alfabético.

        Delega el cálculo de racha a core.py (RF-3.2, RF-3.3).
        """
        result: list[tuple[Habit, int]] = []
        for habit in habits:
            completed_dates = completions_by_habit.get(habit.id, set())
            streak = calculate_streak(completed_dates, today)
            result.append((habit, streak))

        result.sort(key=lambda item: (-item[1], item[0].name))
        return result

    def _create_habit_item(
        self, habit: Habit, streak: int, today: date
    ) -> ft.Container:
        """Crear un widget para un hábito con su racha y botón de marcar.

        Args:
            habit: El hábito a mostrar.
            streak: La racha actual del hábito.
            today: La fecha actual para verificar si ya está marcado.

        Returns:
            Un Container con el nombre, racha y botón del hábito.
        """
        already_done = is_completed_today_db(habit.id, today.isoformat())

        streak_text = f"🔥 {streak} día{'s' if streak != 1 else ''}"
        if streak == 0:
            streak_text = "Sin racha"

        status_icon = "✅" if already_done else "⬜"
        start_display = format_date_display(habit.start_date)

        def mark_habit(event):
            self._mark_habit_completed(habit.id, habit.name)

        mark_button = (
            ft.Button(
                content="Marcar hecho",
                on_click=mark_habit,
                icon=ft.Icons.CHECK,
            )
            if not already_done
            else ft.Text(value="Ya completado hoy", size=12, color="green")
        )

        item = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                value=f"{status_icon} {habit.name}",
                                size=16,
                                weight="medium",
                            ),
                            ft.Container(expand=True),
                            ft.Text(value=streak_text, size=14, color="orange"),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                value=f"Desde: {start_display}",
                                size=12,
                                color="gray",
                            ),
                            ft.Container(expand=True),
                            mark_button,
                        ],
                        alignment="start",
                    ),
                ],
                spacing=8,
            ),
            padding=12,
            border_radius=8,
            bgcolor="#f5f5f5",
        )
        return item

    def _mark_habit_completed(self, habit_id: int, habit_name: str):
        """Marcar un hábito como completado hoy (RF-2.1, RF-2.2).

        Verifica primero si ya está marcado para mostrar advertencia (RF-2.2).
        """
        if self.status_text is None:
            return

        today = date.today()

        # Verificar si ya está marcado hoy (RF-2.2)
        if is_completed_today_db(habit_id, today.isoformat()):
            self.status_text.value = (
                f"⚠️ «{habit_name}» ya está marcado para hoy."
            )
            self.status_text.color = "orange"
            return

        # Marcar como completado (RF-2.1)
        try:
            mark_completed_db(habit_id, today.isoformat())
            self.status_text.value = (
                f"✅ «{habit_name}» marcado como completado."
            )
            self.status_text.color = "green"

            # Refrescar la lista para actualizar rachas
            if self.on_habit_marked:
                self.on_habit_marked()
            else:
                self.refresh_list()

        except Exception as exc:
            self.status_text.value = f"⚠️ Error: {exc}"
            self.status_text.color = "red"


def create_main_view(
    on_create_click: Callable[..., Any], on_list_click: Callable[..., Any]
) -> ft.Container:
    """Crear la vista principal de navegación."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(value="Habits App", size=32, weight="bold", text_align="center"),
                ft.Container(expand=True),
                ft.Button(content="Crear hábito", on_click=on_create_click),
                ft.Button(content="Mis hábitos", on_click=on_list_click),
                ft.Container(height=20),
                ft.Text(
                    value="Registra tus hábitos y sigue tus rachas",
                    text_align="center",
                    color="gray",
                ),
            ],
            expand=True,
            horizontal_alignment="center",
        ),
        padding=20,
    )


def configure_page(page: ft.Page) -> None:
    """Aplicar el tema claro y el tamaño de ventana de escritorio.

    Tarea 3.5, RF-7.1, RF-7.3. Usa fondo crema, superficies claras y acentos
    verdes, y abre la ventana con espacio suficiente para la barra lateral y
    el panel de detalle.
    """
    page.title = "Habits App"
    page.bgcolor = BACKGROUND
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ACCENT_GREEN)
    page.padding = 0
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT


def main(page: ft.Page, db_path: str = "data/habits.db"):
    """Punto de entrada de la aplicación Flet.

    Tareas 3.5 y 4.1 a 4.4: aplica el tema, monta el layout de dos zonas y
    conecta el botón “+ Nuevo” y el CTA del estado vacío con el mismo diálogo
    modal de creación. Al guardar, recarga el estado, actualiza la barra
    lateral y selecciona el hábito recién creado.

    Args:
        page: Página Flet proporcionada por `ft.run`.
        db_path: Ruta a la base de datos SQLite.
    """
    configure_page(page)
    init_db(db_path)

    state = load_app_state(db_path)
    sidebar = Sidebar(state=state)
    header = HabitDetailHeader(state=state)
    empty_panel = EmptyDetailPanel(state=state)

    detail_column = ft.Column(
        controls=[header, empty_panel],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
    layout = ft.Row(
        controls=[sidebar, detail_column],
        spacing=16,
        expand=True,
        vertical_alignment="start",
    )

    def refresh_views(selected_id: int | None = None) -> None:
        """Recargar el estado y repintar la barra lateral y el detalle.

        Args:
            selected_id: Hábito que debe quedar seleccionado; si se omite,
                se conserva la selección inicial del cargador de estado.
        """
        nonlocal state
        state = load_app_state(db_path)
        if selected_id is not None:
            try:
                state.select(selected_id)
            except ValueError:
                pass

        sidebar.state = state
        header.state = state
        empty_panel.state = state
        sidebar.refresh()
        header.refresh()
        empty_panel.refresh()
        page.update()

    def on_select(_habit_id: int) -> None:
        """Actualizar el detalle al cambiar de hábito (RF-1.4)."""
        header.refresh()
        empty_panel.refresh()
        page.update()

    def on_habit_created(result: CreateHabitResult) -> None:
        """Refrescar la interfaz y seleccionar el hábito creado (RF-2.9)."""
        refresh_views(selected_id=result.habit_id)

    form_dialog = HabitFormDialog(
        page,
        on_saved=on_habit_created,
        db_path=db_path,
    )

    def open_create_dialog() -> None:
        """Abrir el mismo modal desde “+ Nuevo” y el estado vacío."""
        form_dialog.open()

    sidebar.on_select = on_select
    sidebar.on_new = open_create_dialog
    empty_panel.on_create = open_create_dialog

    page.views.clear()
    page.views.append(ft.Container(content=layout, padding=16, expand=True))
    page.update()


if __name__ == "__main__":
    ft.run(main)
