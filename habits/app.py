# spec: 001-habits-mvp
# spec: 003-edit-delete-habits
"""Interfaz de escritorio para Habits App.

Capa de presentación en Flet 1.0: vistas y navegación, sin lógica de negocio.
Delega toda la lógica a `core.py` y `storage.py`.

Constitución principio 3: la capa de interfaz nunca contiene cálculos ni acceso a datos.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import flet as ft
from flet.controls.base_control import skip_field

from habits.core import (
    DEFAULT_ICON,
    Habit,
    HeatmapDay,
    create_habit,
    calculate_streak,
)
from habits.app_state import (
    EMPTY_BUTTON_LABEL,
    EMPTY_SIDEBAR_MESSAGE,
    EMPTY_TITLE,
    HEATMAP_COMPLETED_LABEL,
    HEATMAP_NOT_COMPLETED_LABEL,
    HEATMAP_TITLE,
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
    AppState,
    SidebarItem,
    StatCard,
    format_date_label,
    load_app_state,
)
from habits.habit_form import (
    ICON_CATALOG,
    ICON_LABELS,
    MAX_NAME_LENGTH,
    CreateHabitResult,
    HabitFormData,
    UpdateHabitResult,
    create_habit_from_form,
    update_habit_from_form,
)
from habits.registration import (
    REGISTRATION_BUTTON_LABEL,
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_TITLE,
    register_today,
)
from habits.theme import (
    ACCENT_GREEN,
    BACKGROUND,
    HEATMAP_EMPTY,
    HEATMAP_FUTURE,
    HEATMAP_TODAY_BORDER,
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
    delete_habit_db,
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

STAT_CARD_ICONS = {
    STAT_CURRENT_STREAK_LABEL: ft.Icons.LOCAL_FIRE_DEPARTMENT,
    STAT_BEST_STREAK_LABEL: ft.Icons.STAR,
    STAT_REGISTERED_DAYS_LABEL: ft.Icons.CALENDAR_MONTH,
}

WEEKDAY_LABELS = ("L", "M", "X", "J", "V", "S", "D")

APP_ICON_PATH = Path(__file__).resolve().parent.parent / "img" / "icon.ico"


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

    state: AppState | None = skip_field()
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
                        ft.FilledButton(
                            content="+ Nuevo",
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
                    ft.Text(
                        item.name,
                        size=14,
                        weight="medium",
                        color=text_color,
                        expand=True,
                    ),
                    ft.Text(
                        format_streak_label(item.streak),
                        size=12,
                        color=TEXT_SECONDARY,
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

    Tareas 3.3 y 5.2, RF-1.1 a RF-1.5, RF-3.1 y RF-7.4. Muestra el icono, el
    nombre, el subtítulo “Hábito de estudio”, la fecha de inicio en dd/mm/aaaa
    y las acciones “Editar” y “Eliminar”, que solo aparecen con un hábito
    seleccionado y notifican su ID mediante callbacks.
    """

    state: AppState | None = skip_field()
    on_edit: Callable[[int], None] | None = None
    on_delete: Callable[[int], None] | None = None
    edit_button: ft.TextButton | None = skip_field()
    delete_button: ft.TextButton | None = skip_field()
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
        self.visible = header is not None
        if header is None:
            self.edit_button = None
            self.delete_button = None
            self._body.controls = []
            return

        self.edit_button = ft.TextButton(
            content="Editar",
            icon=ft.Icons.EDIT,
            on_click=self._handle_edit,
        )
        self.delete_button = ft.TextButton(
            content="Eliminar",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_delete,
        )

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
                    self.edit_button,
                    self.delete_button,
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

    def _handle_edit(self, event=None) -> None:
        """Notificar la edición del hábito seleccionado (RF-1.3)."""
        selected = self.state.selected if self.state is not None else None
        if selected is not None and self.on_edit is not None:
            self.on_edit(selected.habit.id)

    def _handle_delete(self, event=None) -> None:
        """Notificar la eliminación del hábito seleccionado (RF-1.4)."""
        selected = self.state.selected if self.state is not None else None
        if selected is not None and self.on_delete is not None:
            self.on_delete(selected.habit.id)


@ft.control
class HabitStatsCards(ft.Container):
    """Tarjetas de estadísticas del hábito seleccionado.

    Tarea 5.1, RF-3.2 a RF-3.6. Muestra “Racha actual”, “Mejor racha” y
    “Días registrados” a partir de `AppState.stat_cards()`; un hábito sin
    registros muestra 0 en las tres.
    """

    state: AppState | None = skip_field()
    cards: list[StatCard] | None = skip_field()
    _cards_row: ft.Row | None = None

    def init(self):
        self._cards_row = ft.Row(spacing=12)
        self.content = self._cards_row
        self.refresh()

    def refresh(self):
        """Reconstruir las tarjetas desde el estado actual."""
        if self._cards_row is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.cards = []
            self._cards_row.controls = []
            return

        self.cards = self.state.stat_cards()
        self._cards_row.controls = [
            self._build_card(card) for card in self.cards
        ]

    def _build_card(self, card: StatCard) -> ft.Container:
        """Construir una tarjeta con su icono, título y valor."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                card.label,
                                size=12,
                                color=TEXT_SECONDARY,
                                expand=True,
                            ),
                            ft.Icon(
                                STAT_CARD_ICONS.get(
                                    card.label, ft.Icons.INSIGHTS
                                ),
                                size=16,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        vertical_alignment="center",
                    ),
                    ft.Text(
                        str(card.value),
                        size=28,
                        weight="bold",
                        color=TEXT_PRIMARY,
                    ),
                ],
                spacing=4,
            ),
            padding=16,
            border_radius=12,
            bgcolor=SURFACE,
            expand=True,
        )


@ft.control
class ActivityHeatmap(ft.Container):
    """Heatmap binario de actividad de las últimas cinco semanas.

    Tarea 5.2, RF-4.1 a RF-4.6. Pinta una cuadrícula de 7 filas de lunes a
    domingo por 5 columnas de semanas. Los días completados usan el acento
    verde, hoy lleva borde destacado y los días futuros se ven como no
    disponibles. Incluye la leyenda “No completado / Completado”.
    """

    state: AppState | None = skip_field()
    rows: list[list[HeatmapDay]] | None = skip_field()
    _body: ft.Column | None = None
    _grid: ft.Column | None = None
    _weekday_labels: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._body = ft.Column(spacing=12)
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Reconstruir la cuadrícula y la leyenda desde el estado actual."""
        if self._body is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.rows = []
            self._body.controls = []
            return

        self.rows = self.state.heatmap_rows()
        self._grid = ft.Column(
            controls=[
                ft.Row(
                    controls=[self._build_cell(cell) for cell in row],
                    spacing=4,
                )
                for row in self.rows
            ],
            spacing=4,
        )
        self._weekday_labels = ft.Column(
            controls=[
                ft.Text(
                    label,
                    size=11,
                    color=TEXT_SECONDARY,
                    height=22,
                )
                for label in WEEKDAY_LABELS
            ],
            spacing=4,
        )
        self._body.controls = [
            ft.Text(
                HEATMAP_TITLE,
                size=16,
                weight="bold",
                color=TEXT_PRIMARY,
            ),
            ft.Row(
                controls=[self._weekday_labels, self._grid],
                spacing=8,
                vertical_alignment="start",
            ),
            self._build_legend(),
        ]

    def _build_cell(self, cell: HeatmapDay) -> ft.Container:
        """Construir una celda con el color y el borde que le corresponden."""
        if cell.is_future:
            bgcolor = HEATMAP_FUTURE
        elif cell.completed:
            bgcolor = ACCENT_GREEN
        else:
            bgcolor = HEATMAP_EMPTY

        border = (
            ft.Border.all(2, HEATMAP_TODAY_BORDER)
            if cell.is_today
            else None
        )

        return ft.Container(
            width=22,
            height=22,
            border_radius=4,
            bgcolor=bgcolor,
            border=border,
            tooltip=self._cell_tooltip(cell),
        )

    def _cell_tooltip(self, cell: HeatmapDay) -> str:
        """Describir la fecha y el estado de una celda."""
        if cell.is_future:
            status = HEATMAP_NOT_COMPLETED_LABEL
        elif cell.completed:
            status = HEATMAP_COMPLETED_LABEL
        else:
            status = HEATMAP_NOT_COMPLETED_LABEL
        return f"{format_date_label(cell.date)} · {status}"

    def _build_legend(self) -> ft.Row:
        """Construir la leyenda “No completado / Completado”."""
        return ft.Row(
            controls=[
                self._legend_item(
                    HEATMAP_NOT_COMPLETED_LABEL, HEATMAP_EMPTY
                ),
                self._legend_item(HEATMAP_COMPLETED_LABEL, ACCENT_GREEN),
            ],
            spacing=16,
        )

    def _legend_item(self, label: str, color: str) -> ft.Row:
        """Construir un elemento de la leyenda con su muestra de color."""
        return ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(label, size=12, color=TEXT_SECONDARY),
            ],
            spacing=6,
            vertical_alignment="center",
        )


@ft.control
class TodayRegistrationPanel(ft.Container):
    """Panel “Registrar hoy” del hábito seleccionado.

    Tarea 6.1, RF-5.1, RF-5.2, RF-5.5 y RF-5.6. Muestra la fecha actual en
    dd/mm/aaaa y un botón “Guardar”; no incluye selector de fecha, minutos ni
    “Quitar registro”. Si el hábito ya está completado hoy muestra el mensaje
    “Ya registrado hoy” (RF-5.4).
    """

    state: AppState | None = skip_field()
    on_save: Callable[[], None] | None = None
    message: str = ""
    _date_text: ft.Text | None = None
    _save_button: ft.Button | None = None
    _message_text: ft.Text | None = None
    _body: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._date_text = ft.Text(size=14, color=TEXT_PRIMARY)
        self._save_button = ft.Button(
            content=REGISTRATION_BUTTON_LABEL,
            on_click=self._handle_save,
        )
        self._message_text = ft.Text(
            value="",
            size=14,
            color=TEXT_SECONDARY,
            visible=False,
        )
        self._body = ft.Column(
            controls=[
                ft.Text(
                    REGISTRATION_TITLE,
                    size=16,
                    weight="bold",
                    color=TEXT_PRIMARY,
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Fecha",
                            size=12,
                            color=TEXT_SECONDARY,
                        ),
                        self._date_text,
                        self._save_button,
                    ],
                    spacing=12,
                    vertical_alignment="center",
                ),
                self._message_text,
            ],
            spacing=8,
        )
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Actualizar fecha, botón y mensaje desde el estado actual."""
        if self._body is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.message = ""
            self._message_text.value = ""
            self._message_text.visible = False
            return

        self._date_text.value = format_date_label(self.state.today)
        if not self.state.is_completed_today:
            self.message = ""
        elif not self.message:
            self.message = REGISTRATION_DUPLICATE_MESSAGE

        self._message_text.value = self.message
        self._message_text.visible = bool(self.message)

    def _handle_save(self, event):
        """Delegar el guardado en la vista principal (RF-5.3)."""
        if self.on_save is not None:
            self.on_save()


@ft.control
class EmptyDetailPanel(ft.Container):
    """Estado vacío del panel principal cuando no hay hábitos.

    Tarea 3.4, RF-6.2, RF-6.4. Muestra una ilustración, el título de
    bienvenida y el botón “+ Crear hábito”. Se oculta en cuanto existe al
    menos un hábito.
    """

    state: AppState | None = skip_field()
    on_create: Callable[[], None] | None = None

    def init(self):
        self.expand = True
        self.padding = 32
        self.alignment = ft.Alignment.CENTER
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
                ft.FilledButton(
                    content=EMPTY_BUTTON_LABEL,
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
    """Diálogo modal para crear o editar un hábito sin abandonar la vista.

    Tareas 4.1 a 4.4, RF-1.3, RF-2.1 a RF-2.10 y RF-5.1 a RF-5.8. En creación
    contiene el nombre obligatorio, la fecha de inicio precargada con hoy y el
    selector de icono; en edición precarga los datos del hábito. El campo de
    fecha es de solo lectura y la fecha se elige en un calendario en español
    que bloquea los días futuros (RF-5). La validación y la persistencia se
    delegan en `habit_form.py`; ante un error el diálogo permanece abierto y,
    al guardar correctamente, se cierra y notifica el resultado.
    """

    def __init__(
        self,
        page: ft.Page,
        on_saved: Callable[[CreateHabitResult], None] | None = None,
        on_updated: Callable[[UpdateHabitResult], None] | None = None,
        db_path: str = "data/habits.db",
        today: date | None = None,
    ) -> None:
        """Construir el diálogo y sus controles.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_saved: Callback invocado con el hábito recién creado.
            on_updated: Callback invocado con el hábito editado.
            db_path: Ruta a la base de datos SQLite.
            today: Fecha actual; permite fijarla en tests.
        """
        self.page = page
        self.on_saved = on_saved
        self.on_updated = on_updated
        self.db_path = db_path
        self.today = today
        self.selected_date = today or date.today()
        self.editing_habit: Habit | None = None

        self.name_field = ft.TextField(
            label="Nombre del hábito",
            hint_text="Ej: Estudiar Python",
            max_length=MAX_NAME_LENGTH,
            autofocus=True,
            border_radius=8,
        )
        self.date_field = ft.TextField(
            label="Fecha de inicio",
            hint_text="dd/mm/aaaa",
            max_length=10,
            read_only=True,
            border_radius=8,
            on_click=self.open_date_picker,
        )
        self.date_picker = ft.DatePicker(
            value=self.selected_date,
            current_date=self.today or date.today(),
            last_date=self.today or date.today(),
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
            locale=ft.Locale(language_code="es", country_code="ES"),
            help_text="Selecciona la fecha de inicio",
            cancel_text="Cancelar",
            confirm_text="Aceptar",
            on_change=self.handle_date_change,
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
        """Abrir el diálogo de creación con la fecha de hoy precargada.

        RF-2.1, RF-5.1 y RF-5.8: el formulario parte limpio, el campo de fecha
        muestra hoy y es de solo lectura.
        """
        today = self.today or date.today()
        self.editing_habit = None
        self.dialog.title.value = "Nuevo hábito"
        self.selected_date = today
        self.name_field.value = ""
        self.date_field.value = today.strftime("%d/%m/%Y")
        self.icon_dropdown.value = DEFAULT_ICON
        self.error_text.value = ""
        self.error_text.visible = False
        self.date_picker.value = today
        self.date_picker.current_date = today
        self.date_picker.last_date = today
        self.page.show_dialog(self.dialog)

    def open_edit(self, habit: Habit) -> None:
        """Abrir el diálogo de edición con los datos actuales del hábito.

        RF-1.3, RF-2.1, RF-2.2 y RF-5.2: el nombre, el icono y la fecha de
        inicio aparecen precargados, con la fecha en formato dd/mm/aaaa.
        """
        today = self.today or date.today()
        self.editing_habit = habit
        self.dialog.title.value = "Editar hábito"
        self.selected_date = habit.start_date
        self.name_field.value = habit.name
        self.date_field.value = habit.start_date.strftime("%d/%m/%Y")
        self.icon_dropdown.value = habit.icon
        self.error_text.value = ""
        self.error_text.visible = False
        self.date_picker.value = habit.start_date
        self.date_picker.current_date = today
        self.date_picker.last_date = today
        self.page.show_dialog(self.dialog)

    def open_date_picker(self, event=None) -> None:
        """Abrir el calendario con los días futuros deshabilitados.

        RF-5.3 y RF-5.6: el calendario parte de la fecha seleccionada y usa
        hoy como fecha actual y como última fecha permitida.
        """
        today = self.today or date.today()
        self.date_picker.value = self.selected_date
        self.date_picker.current_date = today
        self.date_picker.last_date = today
        self.page.show_dialog(self.date_picker)

    def handle_date_change(self, event=None) -> None:
        """Copiar la fecha elegida al campo sin cerrar el formulario.

        RF-5.4 y RF-5.5: solo la confirmación en el calendario actualiza el
        campo; cancelar deja intacto el valor anterior.
        """
        value = self.date_picker.value
        if value is None:
            return
        self.selected_date = (
            value.date() if isinstance(value, datetime) else value
        )
        self.date_field.value = self.selected_date.strftime("%d/%m/%Y")
        if self.dialog.open:
            self.page.update()

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin crear ni modificar nada.

        RF-2.10: en edición, cancelar deja intactos los datos del hábito.
        """
        self.editing_habit = None
        self.page.pop_dialog()

    def submit(self, event=None) -> None:
        """Validar y guardar la creación o la edición.

        Si la validación falla, muestra el mensaje y mantiene el diálogo
        abierto (RF-2.3, RF-2.4). Si tiene éxito, persiste los cambios, cierra
        el diálogo y notifica el resultado (RF-2.9); en edición conserva el ID
        del hábito y sus registros (RF-2.12).
        """
        data = HabitFormData(
            name=self.name_field.value or "",
            start_date=self.date_field.value or "",
            icon=self.icon_dropdown.value,
        )
        habit = self.editing_habit

        try:
            if habit is None:
                result = create_habit_from_form(
                    data,
                    db_path=self.db_path,
                    today=self.today,
                )
            else:
                result = update_habit_from_form(
                    habit,
                    data,
                    db_path=self.db_path,
                    today=self.today,
                )
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self._show_error("")
        self.page.pop_dialog()

        if habit is None:
            if self.on_saved is not None:
                self.on_saved(result)
            return

        self.editing_habit = None
        if self.on_updated is not None:
            self.on_updated(result)

    def _show_error(self, message: str) -> None:
        """Mostrar u ocultar el mensaje de error sin cerrar el diálogo."""
        self.error_text.value = message
        self.error_text.visible = bool(message)
        if self.dialog.open:
            self.page.update()


DELETE_DIALOG_TITLE = "Eliminar hábito"
DELETE_WARNING = (
    "⚠️ Esta acción es permanente y eliminará el hábito junto con todos "
    "sus registros diarios."
)


class DeleteHabitDialog:
    """Diálogo modal de confirmación para eliminar un hábito.

    Tarea 5.4, RF-3.1 a RF-3.5. Muestra el nombre del hábito y advierte de
    que el borrado es permanente e incluye sus registros, ofrece “Cancelar” y
    “Eliminar”, y solo notifica el ID al confirmar. No accede a datos: la
    persistencia queda en `main` (Constitución, principio 3).
    """

    def __init__(
        self,
        page: ft.Page,
        on_confirm: Callable[[int], None] | None = None,
    ) -> None:
        """Construir el diálogo de confirmación.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_confirm: Callback invocado con el ID del hábito confirmado.
        """
        self.page = page
        self.on_confirm = on_confirm
        self.habit: Habit | None = None

        self.name_text = ft.Text(
            value="",
            size=16,
            weight="bold",
            color=TEXT_PRIMARY,
        )
        self.warning_text = ft.Text(
            value=DELETE_WARNING,
            size=14,
            color=TEXT_SECONDARY,
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(DELETE_DIALOG_TITLE, size=20, weight="bold"),
            content=ft.Column(
                controls=[self.name_text, self.warning_text],
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
                    content="Eliminar",
                    icon=ft.Icons.DELETE,
                    on_click=self.confirm,
                ),
            ],
            actions_alignment="end",
        )

    def open(self, habit: Habit) -> None:
        """Abrir el diálogo con el nombre del hábito a eliminar (RF-3.1)."""
        self.habit = habit
        self.name_text.value = habit.name
        self.page.show_dialog(self.dialog)

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin eliminar nada (RF-3.3)."""
        self.habit = None
        self.page.pop_dialog()

    def confirm(self, event=None) -> None:
        """Cerrar el diálogo y notificar la confirmación (RF-3.4, RF-3.5)."""
        habit = self.habit
        if habit is None:
            return
        self.close()
        if self.on_confirm is not None:
            self.on_confirm(habit.id)


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
            hint_text="Ej: Estudiar Python",
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
    if APP_ICON_PATH.exists():
        page.window.icon = str(APP_ICON_PATH)


def main(page: ft.Page, db_path: str = "data/habits.db"):
    """Punto de entrada de la aplicación Flet.

    Tareas 3.5, 4.1 a 4.4, 5.1 a 5.4 y 6.1 a 6.3: aplica el tema, monta el
    layout de dos zonas, conecta la creación modal, la edición y la eliminación
    con confirmación, y muestra las estadísticas, el heatmap y el panel
    “Registrar hoy” del hábito seleccionado. Al registrar el día actual, todas
    las zonas se actualizan sin reiniciar la aplicación y los duplicados se
    rechazan.

    Args:
        page: Página Flet proporcionada por `ft.run`.
        db_path: Ruta a la base de datos SQLite.
    """
    configure_page(page)
    init_db(db_path)

    state = load_app_state(db_path)
    sidebar = Sidebar(state=state)
    header = HabitDetailHeader(state=state)
    stats_cards = HabitStatsCards(state=state)
    heatmap = ActivityHeatmap(state=state)
    registration = TodayRegistrationPanel(state=state)
    empty_panel = EmptyDetailPanel(state=state)

    detail_column = ft.Column(
        controls=[header, stats_cards, heatmap, registration, empty_panel],
        spacing=16,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        scroll=None if state.is_empty else ft.ScrollMode.AUTO,
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
        stats_cards.state = state
        heatmap.state = state
        registration.state = state
        empty_panel.state = state
        detail_column.scroll = (
            None if state.is_empty else ft.ScrollMode.AUTO
        )
        sidebar.refresh()
        header.refresh()
        stats_cards.refresh()
        heatmap.refresh()
        registration.refresh()
        empty_panel.refresh()
        page.update()

    def on_select(_habit_id: int) -> None:
        """Actualizar el detalle al cambiar de hábito (RF-1.4, RF-3, RF-4)."""
        header.refresh()
        stats_cards.refresh()
        heatmap.refresh()
        registration.refresh()
        empty_panel.refresh()
        page.update()

    def on_register_today() -> None:
        """Registrar el día actual y refrescar la interfaz (RF-5.3, RF-5.4)."""
        selected = state.selected
        if selected is None:
            return

        result = register_today(
            selected.habit.id, state.today, db_path=db_path
        )
        registration.message = result.message
        refresh_views(selected_id=selected.habit.id)

    def on_habit_created(result: CreateHabitResult) -> None:
        """Refrescar la interfaz y seleccionar el hábito creado (RF-2.9)."""
        refresh_views(selected_id=result.habit_id)

    def on_habit_updated(result: UpdateHabitResult) -> None:
        """Refrescar la vista conservando el hábito editado (RF-4.1 a RF-4.4)."""
        refresh_views(selected_id=result.habit_id)

    def on_habit_deleted(habit_id: int) -> None:
        """Borrar el hábito y recargar la selección restante.

        RF-3.4, RF-3.6, RF-3.7 y RF-3.8: el borrado es transaccional; si falla,
        se conserva el hábito y se muestra un aviso sin recargar la vista.
        """
        try:
            delete_habit_db(habit_id, db_path=db_path)
        except Exception as exc:
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"⚠️ No se pudo eliminar el hábito: {exc}")
                )
            )
            return

        refresh_views()

    form_dialog = HabitFormDialog(
        page,
        on_saved=on_habit_created,
        on_updated=on_habit_updated,
        db_path=db_path,
    )
    delete_dialog = DeleteHabitDialog(page, on_confirm=on_habit_deleted)

    def find_habit(habit_id: int) -> Habit | None:
        """Buscar un hábito del estado actual por su ID."""
        for habit_state in state.habits:
            if habit_state.habit.id == habit_id:
                return habit_state.habit
        return None

    def open_create_dialog() -> None:
        """Abrir el mismo modal desde “+ Nuevo” y el estado vacío."""
        form_dialog.open()

    def open_edit_dialog(habit_id: int) -> None:
        """Abrir el modal de edición con los datos actuales (RF-1.3)."""
        habit = find_habit(habit_id)
        if habit is not None:
            form_dialog.open_edit(habit)

    def open_delete_dialog(habit_id: int) -> None:
        """Abrir la confirmación antes de borrar (RF-1.4, RF-3.1)."""
        habit = find_habit(habit_id)
        if habit is not None:
            delete_dialog.open(habit)

    sidebar.on_select = on_select
    sidebar.on_new = open_create_dialog
    registration.on_save = on_register_today
    empty_panel.on_create = open_create_dialog
    header.on_edit = open_edit_dialog
    header.on_delete = open_delete_dialog

    page.add(ft.Container(content=layout, padding=16, expand=True))


if __name__ == "__main__":
    ft.run(main)
