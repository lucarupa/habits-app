# spec: 003-edit-delete-habits
from datetime import date, timedelta

import pytest

from habits import core
from habits.core import (
    Habit,
    HabitStats,
    HeatmapDay,
    create_habit,
    reset_id_counter,
    mark_completed,
    calculate_streak,
    calculate_best_streak,
    count_registered_days,
    get_habit_stats,
    build_activity_heatmap,
    list_habits_with_streak,
)

TODAY = date(2026, 10, 26)


class TestHabit:
    """Tests para la clase Habit — Tarea 2.1, RF-1.1, RF-1.2."""

    def test_habit_attributes(self):
        """Un Habit se puede instanciar con id, name y start_date."""
        habit = Habit(id=1, name="Estudiar Python", start_date=date(2024, 1, 15))

        assert habit.id == 1
        assert habit.name == "Estudiar Python"
        assert habit.start_date == date(2024, 1, 15)

    def test_habit_date_type(self):
        """El atributo start_date es del tipo date."""
        habit = Habit(id=1, name="Leer", start_date=date.today())

        assert isinstance(habit.start_date, date)

    def test_habit_default_icon(self):
        """RF-2.6: Un Habit sin icono usa el icono por defecto."""
        habit = Habit(id=1, name="Leer", start_date=date.today())

        assert habit.icon == "book"

    def test_habit_with_icon(self):
        """RF-2.8: Un Habit puede construirse con un icono explícito."""
        habit = Habit(id=1, name="Programar", start_date=date.today(), icon="code")

        assert habit.icon == "code"


class TestCreateHabit:
    """Tests para create_habit — Tarea 2.2, T3.1, RF-1.1 a RF-1.4 y caso límite."""

    def setup_method(self):
        """Reiniciar el contador de IDs antes de cada test."""
        reset_id_counter()

    def test_create_habit_valid_name(self):
        """RF-1.1: Crear hábito con nombre válido retorna un Habit."""
        habit = create_habit("Estudiar Python")

        assert isinstance(habit, Habit)
        assert habit.name == "Estudiar Python"
        assert habit.start_date == date.today()
        assert habit.id == 1

    def test_create_habit_default_start_date(self):
        """RF-1.2: Sin fecha de inicio se asigna la fecha actual."""
        habit = create_habit("Leer")

        assert habit.start_date == date.today()

    def test_create_habit_with_start_date(self):
        """RF-1.1: Con fecha de inicio válida se usa esa fecha."""
        yesterday = date.today().replace(day=1)
        habit = create_habit("Leer", start_date=yesterday)

        assert habit.start_date == yesterday

    def test_create_habit_empty_name(self):
        """RF-1.3: Nombre vacío levanta ValueError."""
        try:
            create_habit("")
            assert False, "Se esperaba ValueError"
        except ValueError as exc:
            assert "obligatorio" in str(exc).lower()

    def test_create_habit_whitespace_name(self):
        """RF-1.3: Nombre con solo espacios levanta ValueError."""
        try:
            create_habit("   ")
            assert False, "Se esperaba ValueError"
        except ValueError as exc:
            assert "obligatorio" in str(exc).lower()

    def test_create_habit_name_too_long(self):
        """RF-1.4: Nombre > 60 caracteres levanta ValueError."""
        long_name = "A" * 61

        try:
            create_habit(long_name)
            assert False, "Se esperaba ValueError"
        except ValueError as exc:
            assert "60" in str(exc)

    def test_create_habit_name_exactly_60(self):
        """RF-1.4: Nombre de exactamente 60 caracteres es válido."""
        name_60 = "A" * 60
        habit = create_habit(name_60)

        assert habit.name == name_60

    def test_create_habit_future_start_date(self):
        """Caso límite: Fecha en futuro se corrige a fecha actual."""
        future = date(2099, 12, 31)
        habit = create_habit("Futuro", start_date=future)

        assert habit.start_date == date.today()

    def test_create_habit_default_icon(self):
        """RF-2.6: Sin icono se asigna el icono por defecto."""
        habit = create_habit("Leer")

        assert habit.icon == "book"

    def test_create_habit_selected_icon(self):
        """RF-2.8: El icono elegido se conserva en el objeto Habit."""
        habit = create_habit("Programar", icon="code")

        assert habit.icon == "code"

    def test_create_habit_invalid_icon(self):
        """RF-2.6: Un icono no válido se sustituye por el icono por defecto."""
        habit = create_habit("Leer", icon="icono-inexistente")

        assert habit.icon == "book"


class TestUpdateHabit:
    """Tests para update_habit — Tarea 1.1, RF-2.3, RF-2.4, RF-2.7, RF-2.8, RF-2.9, RF-2.12."""

    def _habit(self) -> Habit:
        """Hábito de referencia con fecha de inicio anterior a TODAY."""
        return Habit(
            id=7,
            name="Python",
            start_date=date(2026, 9, 1),
            icon="code",
        )

    def test_update_habit_changes_fields_and_keeps_id(self):
        """RF-2.9, RF-2.12: Devuelve nombre, fecha e icono nuevos con el mismo ID."""
        habit = self._habit()

        updated = core.update_habit(
            habit,
            name="Python avanzado",
            start_date=date(2026, 10, 1),
            icon="science",
            today=TODAY,
        )

        assert updated == Habit(
            id=7,
            name="Python avanzado",
            start_date=date(2026, 10, 1),
            icon="science",
        )
        assert habit == self._habit()

    def test_update_habit_strips_name(self):
        """RF-2.3: El nombre actualizado se guarda sin espacios sobrantes."""
        updated = core.update_habit(
            self._habit(),
            name="  Leer  ",
            start_date=date(2026, 9, 1),
            icon="code",
            today=TODAY,
        )

        assert updated.name == "Leer"

    def test_update_habit_rejects_empty_name(self):
        """RF-2.3: Nombre vacío o solo espacios lanza ValueError."""
        habit = self._habit()

        for name in ("", "   "):
            with pytest.raises(ValueError, match="obligatorio"):
                core.update_habit(
                    habit,
                    name=name,
                    start_date=habit.start_date,
                    icon=habit.icon,
                    today=TODAY,
                )

    def test_update_habit_rejects_long_name(self):
        """RF-2.4: Nombre de más de 60 caracteres lanza ValueError."""
        habit = self._habit()

        with pytest.raises(ValueError, match="60"):
            core.update_habit(
                habit,
                name="A" * 61,
                start_date=habit.start_date,
                icon=habit.icon,
                today=TODAY,
            )

    def test_update_habit_rejects_future_date(self):
        """RF-2.7: Una fecha de inicio futura lanza ValueError."""
        habit = self._habit()

        with pytest.raises(ValueError, match="futura"):
            core.update_habit(
                habit,
                name="Python",
                start_date=TODAY + timedelta(days=1),
                icon=habit.icon,
                today=TODAY,
            )

    def test_update_habit_keeps_current_icon_when_invalid(self):
        """RF-2.8: Una clave de icono ajena al catálogo conserva el icono actual."""
        habit = self._habit()

        updated = core.update_habit(
            habit,
            name="Python",
            start_date=habit.start_date,
            icon="icono-inexistente",
            today=TODAY,
        )

        assert updated.id == habit.id
        assert updated.icon == "code"


class TestMarkCompleted:
    """Tests para mark_completed — Tarea 2.3, RF-2.1 a RF-2.3."""

    def test_mark_completed_success(self):
        """RF-2.1: Marcar un hábito como completado retorna éxito."""
        today = date.today()
        completed = set()
        result = mark_completed(1, completed, today)

        assert result["success"] is True
        assert today in completed

    def test_mark_completed_already_today(self):
        """RF-2.2: Marcar ya completado hoy retorna mensaje de advertencia."""
        today = date.today()
        completed = {today}
        result = mark_completed(1, completed, today)

        assert result["success"] is False
        assert "advertencia" in result["message"].lower() or "ya" in result["message"].lower()

    def test_mark_completed_different_date(self):
        """RF-2.3: Intentar marcar con fecha distinta a hoy levanta ValueError."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        completed = set()

        try:
            mark_completed(1, completed, yesterday)
            assert False, "Se esperaba ValueError"
        except ValueError as exc:
            assert "hoy" in str(exc).lower() or "actual" in str(exc).lower()

    def test_mark_completed_adds_to_set(self):
        """RF-2.1: La fecha se agrega al conjunto de completados."""
        today = date.today()
        completed = set()
        mark_completed(1, completed, today)

        assert len(completed) == 1
        assert today in completed

    def test_mark_completed_multiple_habits(self):
        """RF-2.1: Diferentes hábitos pueden marcarse el mismo día."""
        today = date.today()
        completed = {}  # dict: habit_id -> set of dates

        # Simular múltiples hábitos
        completed[1] = set()
        completed[2] = set()

        mark_completed(1, completed[1], today)
        mark_completed(2, completed[2], today)

        assert today in completed[1]
        assert today in completed[2]


class TestCalculateStreak:
    """Tests para calculate_streak — Tarea 2.4, RF-4.1 a RF-4.4."""

    def test_calculate_streak_today(self):
        """RF-4.1: Racha cuenta hacia atrás desde hoy cuando hay días consecutivos."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        completed = {today, yesterday, two_days_ago}

        streak = calculate_streak(completed, today)

        assert streak == 3

    def test_calculate_streak_not_today(self):
        """RF-4.2: Si el último día registrado no es hoy, la racha es 0."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        completed = {yesterday}

        streak = calculate_streak(completed, today)

        assert streak == 0

    def test_calculate_streak_single_day(self):
        """RF-4.3: Un solo día registrado y es hoy, la racha es 1."""
        today = date.today()
        completed = {today}

        streak = calculate_streak(completed, today)

        assert streak == 1

    def test_calculate_streak_with_gap(self):
        """RF-4.4: Un hueco en los registros detiene el conteo."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        three_days_ago = today - timedelta(days=3)
        completed = {today, yesterday, three_days_ago}

        streak = calculate_streak(completed, today)

        assert streak == 2

    def test_calculate_streak_empty(self):
        """RF-4: Sin registros, la racha es 0."""
        today = date.today()
        completed = set()

        streak = calculate_streak(completed, today)

        assert streak == 0


class TestCalculateBestStreak:
    """Tests para calculate_best_streak — Tarea 1.2, RF-3.3."""

    def test_calculate_best_streak_empty(self):
        """RF-3.3: Sin registros, la mejor racha es 0."""
        assert calculate_best_streak(set()) == 0

    def test_calculate_best_streak_single(self):
        """RF-3.3: Un solo día registrado da mejor racha 1."""
        today = date.today()

        assert calculate_best_streak({today}) == 1

    def test_calculate_best_streak_consecutive(self):
        """RF-3.3: Varios días consecutivos se cuentan completos."""
        today = date.today()
        completed = {
            today,
            today - timedelta(days=1),
            today - timedelta(days=2),
        }

        assert calculate_best_streak(completed) == 3

    def test_calculate_best_streak_with_gaps(self):
        """RF-3.3: Los huecos separan bloques y se toma el mayor."""
        today = date.today()
        completed = {
            today,
            today - timedelta(days=1),
            today - timedelta(days=4),
            today - timedelta(days=5),
            today - timedelta(days=6),
        }

        assert calculate_best_streak(completed) == 3

    def test_calculate_best_streak_includes_current(self):
        """RF-3.3: La racha actual puede ser la mejor racha."""
        today = date.today()
        completed = {
            today,
            today - timedelta(days=1),
            today - timedelta(days=2),
            today - timedelta(days=3),
            today - timedelta(days=10),
        }

        assert calculate_best_streak(completed) == 4


class TestCountRegisteredDays:
    """Tests para count_registered_days — Tarea 1.3, RF-3.4."""

    def test_count_registered_days_empty(self):
        """RF-3.4: Sin registros, los días registrados son 0."""
        assert count_registered_days(set()) == 0

    def test_count_registered_days_distinct(self):
        """RF-3.4: Se cuentan fechas distintas, no repeticiones."""
        today = date.today()
        completed = {
            today,
            today - timedelta(days=1),
            today - timedelta(days=3),
        }

        assert count_registered_days(completed) == 3


class TestGetHabitStats:
    """Tests para HabitStats y get_habit_stats — Tarea 1.3, RF-3.2, RF-3.4, RF-3.5."""

    def test_get_habit_stats_empty(self):
        """RF-3.5: Sin registros, las tres estadísticas son 0."""
        stats = get_habit_stats(set(), date.today())

        assert stats == HabitStats(
            current_streak=0,
            best_streak=0,
            registered_days=0,
        )

    def test_get_habit_stats_active(self):
        """RF-3.2, RF-3.3, RF-3.4: Un hábito activo devuelve valores correctos."""
        today = date.today()
        completed = {
            today,
            today - timedelta(days=1),
            today - timedelta(days=3),
            today - timedelta(days=4),
            today - timedelta(days=5),
        }

        stats = get_habit_stats(completed, today)

        assert stats.current_streak == 2
        assert stats.best_streak == 3
        assert stats.registered_days == 5

    def test_get_habit_stats_inactive(self):
        """RF-3.2: Si el último día no es hoy, la racha actual es 0."""
        today = date.today()
        completed = {
            today - timedelta(days=1),
            today - timedelta(days=2),
            today - timedelta(days=3),
        }

        stats = get_habit_stats(completed, today)

        assert stats.current_streak == 0
        assert stats.best_streak == 3
        assert stats.registered_days == 3


class TestBuildActivityHeatmap:
    """Tests para build_activity_heatmap — Tarea 1.4, RF-4.1 a RF-4.6."""

    def test_build_activity_heatmap_dimensions(self):
        """RF-4.1, RF-4.2: Devuelve 35 celdas en 5 semanas y 7 días."""
        today = date(2024, 10, 24)  # Jueves

        cells = build_activity_heatmap(set(), today)

        assert len(cells) == 35
        assert all(isinstance(cell, HeatmapDay) for cell in cells)
        assert cells[0].date == date(2024, 9, 23)  # Lunes inicial
        assert cells[-1].date == date(2024, 10, 27)  # Domingo final
        assert cells[0].weekday == 0
        assert cells[-1].weekday == 6
        assert {cell.week for cell in cells} == {0, 1, 2, 3, 4}
        assert all(
            sum(1 for cell in cells if cell.week == week) == 7
            for week in range(5)
        )

    def test_build_activity_heatmap_marks_completed(self):
        """RF-4.3: Las fechas completadas se marcan como completadas."""
        today = date(2024, 10, 24)
        completed = {
            date(2024, 10, 21),
            date(2024, 10, 22),
            date(2024, 10, 24),
        }

        cells = build_activity_heatmap(completed, today)
        by_date = {cell.date: cell for cell in cells}

        assert by_date[date(2024, 10, 21)].completed is True
        assert by_date[date(2024, 10, 22)].completed is True
        assert by_date[date(2024, 10, 24)].completed is True
        assert by_date[date(2024, 10, 23)].completed is False

    def test_build_activity_heatmap_today(self):
        """RF-4.4: La celda de hoy se marca con is_today."""
        today = date(2024, 10, 24)

        cells = build_activity_heatmap({today}, today)
        today_cells = [cell for cell in cells if cell.is_today]

        assert len(today_cells) == 1
        assert today_cells[0].date == today
        assert today_cells[0].completed is True
        assert today_cells[0].is_future is False

    def test_build_activity_heatmap_future_days(self):
        """RF-4.3: Los días posteriores a hoy se marcan como futuros."""
        today = date(2024, 10, 24)

        cells = build_activity_heatmap(set(), today)
        future_dates = [cell.date for cell in cells if cell.is_future]

        assert future_dates == [
            date(2024, 10, 25),
            date(2024, 10, 26),
            date(2024, 10, 27),
        ]
        assert all(
            not cell.is_future for cell in cells if cell.date <= today
        )

    def test_build_activity_heatmap_empty(self):
        """RF-4.6: Sin registros, ninguna celda está completada."""
        today = date(2024, 10, 24)

        cells = build_activity_heatmap(set(), today)

        assert all(cell.completed is False for cell in cells)


class TestListHabitsWithStreak:
    """Tests para list_habits_with_streak — Tarea 2.5, RF-3.1 a RF-3.4."""

    def test_list_habits_sorted_by_streak(self):
        """RF-3.2: La lista se ordena por racha descendente."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        habit_a = Habit(id=1, name="Zebra", start_date=today)
        habit_b = Habit(id=2, name="Alpha", start_date=today)

        completions = {
            1: {today},  # racha 1
            2: {today, yesterday, two_days_ago}  # racha 3
        }

        result = list_habits_with_streak([habit_a, habit_b], completions, today)

        assert len(result) == 2
        assert result[0][0].name == "Alpha"
        assert result[0][1] == 3
        assert result[1][0].name == "Zebra"
        assert result[1][1] == 1

    def test_list_habits_alpha_tiebreak(self):
        """RF-3.3: Misma racha, orden alfabético secundario."""
        today = date.today()

        habit_a = Habit(id=1, name="Zebra", start_date=today)
        habit_b = Habit(id=2, name="Alpha", start_date=today)
        habit_c = Habit(id=3, name="Middle", start_date=today)

        completions = {
            1: {today},
            2: {today},
            3: {today}
        }

        result = list_habits_with_streak([habit_a, habit_b, habit_c], completions, today)

        assert len(result) == 3
        assert result[0][0].name == "Alpha"
        assert result[1][0].name == "Middle"
        assert result[2][0].name == "Zebra"

    def test_list_habits_empty(self):
        """RF-3.4: Sin hábitos, retorna lista vacía."""
        today = date.today()

        result = list_habits_with_streak([], {}, today)

        assert result == []
