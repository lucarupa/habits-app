# spec: 001-habits-mvp
# spec: 003-edit-delete-habits
"""Punto de entrada de Habits App.

Monta la interfaz y conecta estado, persistencia y widgets de `habits.ui`.
"""

from datetime import date, datetime

import flet as ft

from habits.domain.models import Habit
from habits.forms.models import (
    CreateHabitResult,
    UpdateHabitResult,
)
from habits.notifications.models import SCHEDULER_INSTALL_FAILED_MESSAGE
from habits.notifications.notifier import SystemNotifier
from habits.notifications.scheduler import SystemScheduler
from habits.persistence.completions_repo import mark_recovered_days_db
from habits.persistence.habits_repo import delete_habit_db
from habits.persistence.reminders_repo import get_reminder_db, save_reminder_db
from habits.persistence.schema import init_db
from habits.registration import duplicate_warning, register_today
from habits.reminders import effective_date, reminder_message
from habits.state.loader import load_app_state
from habits.ui.delete_dialog import DeleteHabitDialog
from habits.ui.detail_header import HabitDetailHeader
from habits.ui.empty import EmptyDetailPanel
from habits.ui.form_dialog import HabitFormDialog
from habits.ui.heatmap import ActivityHeatmap
from habits.ui.page import configure_page
from habits.ui.recovery_dialog import StreakRecoveryDialog
from habits.ui.registration_panel import TodayRegistrationPanel
from habits.ui.reminder_dialog import ReminderDialog
from habits.ui.sidebar import Sidebar
from habits.ui.stats import HabitStatsCards

REMINDER_ACTIVATION_ERROR = "No se pudo activar el recordatorio."


def main(
    page: ft.Page, db_path: str = "data/habits.db", *,
    scheduler: SystemScheduler | None = None,
    notifier: SystemNotifier | None = None,
):
    """Montar la interfaz y conectar estado, persistencia y widgets."""
    scheduler = scheduler if scheduler is not None else SystemScheduler()
    notifier = notifier if notifier is not None else SystemNotifier()
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
        spacing=16, expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        scroll=None if state.is_empty else ft.ScrollMode.AUTO,
    )
    layout = ft.Row(
        controls=[sidebar, detail_column], spacing=16,
        expand=True, vertical_alignment="start",
    )

    def refresh_views(selected_id: int | None = None) -> None:
        """Recargar el estado y repintar todos los widgets."""
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
        detail_column.scroll = None if state.is_empty else ft.ScrollMode.AUTO
        sidebar.refresh()
        header.refresh()
        stats_cards.refresh()
        heatmap.refresh()
        registration.refresh()
        empty_panel.refresh()
        page.update()

    def on_select(_habit_id: int) -> None:
        """Actualizar el detalle al cambiar de hábito."""
        header.refresh()
        stats_cards.refresh()
        heatmap.refresh()
        registration.refresh()
        empty_panel.refresh()
        page.update()

    def on_register_today() -> None:
        """Registrar el día actual y refrescar la interfaz."""
        selected = state.selected
        if selected is None:
            return

        result = register_today(selected.habit.id, state.today, db_path=db_path)
        if not result.success:
            page.show_dialog(
                ft.SnackBar(content=duplicate_warning(selected.habit.name))
            )
        registration.message = result.message
        refresh_views(selected_id=selected.habit.id)

    def on_habit_created(result: CreateHabitResult) -> None:
        """Refrescar la interfaz y seleccionar el hábito creado."""
        refresh_views(selected_id=result.habit_id)

    def on_habit_updated(result: UpdateHabitResult) -> None:
        """Refrescar la vista conservando el hábito editado."""
        refresh_views(selected_id=result.habit_id)

    def on_habit_deleted(habit_id: int) -> None:
        """Borrar el hábito y recargar la selección restante."""
        try:
            delete_habit_db(habit_id, db_path=db_path)
        except Exception as exc:
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f"⚠️ No se pudo eliminar el hábito: {exc}")
            ))
            return

        refresh_views()
        sync_result = scheduler.sync(
            db_path, has_active_reminders=has_active_reminders())
        if not sync_result.ok:
            show_warning(sync_result.message or SCHEDULER_INSTALL_FAILED_MESSAGE)

    def show_warning(message: str) -> None:
        """Mostrar un aviso en español sin cerrar la aplicación."""
        page.show_dialog(ft.SnackBar(content=ft.Text(f"⚠️ {message}")))

    def has_active_reminders() -> bool:
        """Indicar si el estado actual tiene algún recordatorio activo."""
        return any(habit_state.reminder_enabled for habit_state in state.habits)

    def has_active_after(habit_id: int, enabled: bool) -> bool:
        """Calcular si quedará algún recordatorio activo tras el cambio."""
        if enabled:
            return True
        return any(
            habit_state.reminder_enabled and habit_state.habit.id != habit_id
            for habit_state in state.habits
        )

    def sync_scheduler() -> None:
        """Sincronizar la tarea periódica y avisar de los fallos."""
        result = scheduler.sync(
            db_path, has_active_reminders=has_active_reminders()
        )
        if not result.ok:
            show_warning(result.message or SCHEDULER_INSTALL_FAILED_MESSAGE)

    def on_reminder_saved(
        habit_id: int, enabled: bool, reminder_time: str | None
    ) -> None:
        """Guardar la configuración y sincronizar la tarea periódica."""
        habit = find_habit(habit_id)
        if habit is None:
            return

        if enabled and reminder_time is None:
            show_warning(REMINDER_ACTIVATION_ERROR)
            return

        if enabled:
            notification = notifier.notify(reminder_message(habit.name))
            if not notification.ok:
                show_warning(notification.message or REMINDER_ACTIVATION_ERROR)
                return

        previous = get_reminder_db(habit_id, db_path=db_path)
        if enabled:
            if (
                previous is not None
                and previous.enabled
                and previous.reminder_time == reminder_time
            ):
                effective_from = previous.effective_from
            else:
                effective_from = effective_date(
                    datetime.now(), reminder_time
                ).isoformat()
        elif previous is not None:
            effective_from = previous.effective_from
        else:
            effective_from = date.today().isoformat()

        sync_result = scheduler.sync(
            db_path, has_active_reminders=has_active_after(habit_id, enabled))
        if not sync_result.ok:
            show_warning(sync_result.message or SCHEDULER_INSTALL_FAILED_MESSAGE)
            return

        save_reminder_db(habit_id, enabled, reminder_time,
                         effective_from, db_path=db_path)
        refresh_views(selected_id=habit_id)

    def on_streak_recovered(habit: Habit, dates: tuple[date, ...]) -> None:
        """Persistir los días recuperados y recargar la vista."""
        try:
            mark_recovered_days_db(
                habit.id, [day.isoformat() for day in dates], db_path=db_path
            )
        except Exception as exc:
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f"⚠️ No se pudo recuperar la racha: {exc}")
            ))
            return

        refresh_views(selected_id=habit.id)

    form_dialog = HabitFormDialog(
        page, on_saved=on_habit_created,
        on_updated=on_habit_updated, db_path=db_path,
    )
    delete_dialog = DeleteHabitDialog(page, on_confirm=on_habit_deleted)
    recovery_dialog = StreakRecoveryDialog(
        page, on_confirm=on_streak_recovered)
    reminder_dialog = ReminderDialog(page, on_save=on_reminder_saved)

    def find_habit(habit_id: int) -> Habit | None:
        for habit_state in state.habits:
            if habit_state.habit.id == habit_id:
                return habit_state.habit
        return None

    def open_create_dialog() -> None:
        form_dialog.open()

    def open_edit_dialog(habit_id: int) -> None:
        habit = find_habit(habit_id)
        if habit is not None:
            form_dialog.open_edit(habit)

    def open_delete_dialog(habit_id: int) -> None:
        habit = find_habit(habit_id)
        if habit is not None:
            delete_dialog.open(habit)

    def open_recovery_dialog() -> None:
        selected = state.selected
        gap = state.recoverable_gap
        if selected is not None and gap is not None:
            recovery_dialog.open(selected.habit, gap.dates)

    def open_reminder_dialog(habit_id: int) -> None:
        habit = find_habit(habit_id)
        if habit is None:
            return
        reminder = get_reminder_db(habit_id, db_path=db_path)
        reminder_dialog.open(
            habit,
            enabled=bool(reminder.enabled) if reminder is not None else False,
            reminder_time=(
                reminder.reminder_time if reminder is not None else None
            ),
        )

    sidebar.on_select = on_select
    sidebar.on_new = open_create_dialog
    registration.on_save = on_register_today
    registration.on_recover = open_recovery_dialog
    empty_panel.on_create = open_create_dialog
    header.on_edit = open_edit_dialog
    header.on_delete = open_delete_dialog
    header.on_reminder = open_reminder_dialog

    sync_scheduler()
    page.add(ft.Container(content=layout, padding=16, expand=True))


if __name__ == "__main__":
    ft.run(main)
