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
    Habit,
    create_habit,
    calculate_streak,
)
from habits.storage import (
    init_db,
    create_habit_db,
    list_all_habits_db,
    get_completions_db,
    mark_completed_db,
    is_completed_today_db,
)


def format_date_display(d: date) -> str:
    """Formatear una fecha para mostrar al usuario en dd/mm/aaaa (Tarea 6.4).

    Args:
        d: La fecha a formatear.

    Returns:
        La fecha como cadena en formato dd/mm/aaaa.
    """
    return d.strftime("%d/%m/%Y")


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


def main(page: ft.Page):
    """Punto de entrada de la aplicación Flet.

    Crea la ventana principal con navegación entre vistas.
    Tarea 6.1: Infraestructura de UI.
    Tarea 6.2: Conecta el callback de creación.
    Tarea 6.3: Conecta el callback de marcado y refresco de lista.
    """
    page.title = "Habits App"
    page.window_width = 400
    page.window_height = 500

    # Crear vistas
    list_view = ListHabitsView(on_habit_marked=None)
    _list_view_ref["view"] = list_view

    def on_habit_marked():
        """Callback cuando se marca un hábito: refrescar la lista."""
        list_view.refresh_list()

    list_view.on_habit_marked = on_habit_marked

    create_view = CreateHabitView(on_habit_created=None)

    def on_habit_created():
        """Callback cuando se crea un hábito: navegar a la lista."""
        page.navigate("/lista")

    create_view.on_habit_created = on_habit_created

    # Guardar referencias en page para acceso desde vistas
    page.create_view = create_view  # type: ignore
    page.list_view = list_view  # type: ignore

    def route_change(route):
        """Construir las vistas según la ruta actual."""
        page.views.clear()

        def show_create(event):
            page.navigate("/crear")

        def show_list(event):
            page.navigate("/lista")

        main_view = create_main_view(show_create, show_list)

        if page.route == "/crear":
            page.views.append(
                ft.Container(content=create_view, padding=20)
            )
        elif page.route == "/lista":
            page.views.append(
                ft.Container(content=list_view, padding=20)
            )
            # Refrescar la lista al entrar
            list_view.refresh_list()
        else:
            page.views.append(main_view)

        page.update()

    page.on_route_change = route_change
    route_change(page.route)


if __name__ == "__main__":
    ft.run(main)
