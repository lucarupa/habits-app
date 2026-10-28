# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Diálogo modal de creación y edición de hábitos.

Conserva el comportamiento del diálogo monolítico anterior (RF-2.1, RF-2.2 y
RF-5.4). No accede a datos: delega en `habits.forms`.
"""

from datetime import date, datetime
from typing import Callable

import flet as ft

from habits.domain.models import DEFAULT_ICON, Habit
from habits.forms.models import (
    ICON_CATALOG,
    ICON_LABELS,
    MAX_NAME_LENGTH,
    CreateHabitResult,
    HabitFormData,
    UpdateHabitResult,
)
from habits.forms.service import create_habit_from_form, update_habit_from_form
from habits.ui.common import icon_for_habit


class HabitFormDialog:
    """Diálogo modal para crear o editar un hábito sin abandonar la vista.

    En creación contiene el nombre obligatorio, la fecha de inicio precargada
    con hoy y el selector de icono; en edición precarga los datos del hábito.
    El campo de fecha es de solo lectura y la fecha se elige en un calendario
    en español que bloquea los días futuros. La validación y la persistencia
    se delegan en `habits.forms`; ante un error el diálogo permanece abierto y,
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

        El formulario parte limpio, el campo de fecha muestra hoy y es de solo
        lectura.
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

        El nombre, el icono y la fecha de inicio aparecen precargados, con la
        fecha en formato dd/mm/aaaa.
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

        El calendario parte de la fecha seleccionada y usa hoy como fecha
        actual y como última fecha permitida.
        """
        today = self.today or date.today()
        self.date_picker.value = self.selected_date
        self.date_picker.current_date = today
        self.date_picker.last_date = today
        self.page.show_dialog(self.date_picker)

    def handle_date_change(self, event=None) -> None:
        """Copiar la fecha elegida al campo sin cerrar el formulario.

        Solo la confirmación en el calendario actualiza el campo; cancelar deja
        intacto el valor anterior.
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

        En edición, cancelar deja intactos los datos del hábito.
        """
        self.editing_habit = None
        self.page.pop_dialog()

    def submit(self, event=None) -> None:
        """Validar y guardar la creación o la edición.

        Si la validación falla, muestra el mensaje y mantiene el diálogo
        abierto. Si tiene éxito, persiste los cambios, cierra el diálogo y
        notifica el resultado; en edición conserva el ID del hábito y sus
        registros.
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
