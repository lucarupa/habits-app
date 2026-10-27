# spec: 004-duplicate-warning-streak-recovery
"""Tests de detección del hueco recuperable — Tarea 1.1.

Fijan el contrato de `RecoverableGap` y `find_recoverable_gap`: solo se
recupera el hueco más reciente cuando tiene uno o dos días. No requieren Flet.
"""

from datetime import date, timedelta

from habits import core

TODAY = date(2026, 10, 26)


def days_ago(count: int) -> date:
    """Devolver la fecha situada `count` días antes de TODAY."""
    return TODAY - timedelta(days=count)


def gap_dates(completed_dates: set[date]) -> tuple[date, ...]:
    """Obtener las fechas del hueco recuperable, comprobando su tipo."""
    gap = core.find_recoverable_gap(completed_dates, TODAY)
    assert isinstance(gap, core.RecoverableGap)
    return gap.dates


class TestFindRecoverableGap:
    """Detección del hueco más reciente — Tarea 1.1, RF-2.1 a RF-2.3, RF-2.18."""

    def test_without_dates_returns_none(self):
        """RF-2.3: un hábito sin registros no tiene nada que recuperar."""
        assert core.find_recoverable_gap(set(), TODAY) is None

    def test_one_day_between_records(self):
        """RF-2.1: un día faltante entre dos registros es recuperable."""
        completed = {days_ago(2), TODAY}

        assert gap_dates(completed) == (days_ago(1),)

    def test_two_days_between_records(self):
        """RF-2.1: dos días faltantes entre dos registros son recuperables."""
        completed = {days_ago(3), TODAY}

        assert gap_dates(completed) == (days_ago(2), days_ago(1))

    def test_three_days_between_records_returns_none(self):
        """RF-2.2: un hueco de tres días entre registros no es recuperable."""
        completed = {days_ago(4), TODAY}

        assert core.find_recoverable_gap(completed, TODAY) is None

    def test_one_day_before_today(self):
        """RF-2.1: el hueco de cola de un día es recuperable."""
        completed = {days_ago(2)}

        assert gap_dates(completed) == (days_ago(1),)

    def test_two_days_before_today(self):
        """RF-2.1: el hueco de cola de dos días es recuperable."""
        completed = {days_ago(3)}

        assert gap_dates(completed) == (days_ago(2), days_ago(1))

    def test_three_days_before_today_returns_none(self):
        """RF-2.2: el hueco de cola de tres días no es recuperable."""
        completed = {days_ago(4)}

        assert core.find_recoverable_gap(completed, TODAY) is None

    def test_today_completed_with_two_day_gap(self):
        """RF-2.1: hoy registrado y un hueco anterior de dos días es recuperable."""
        completed = {days_ago(3), TODAY}

        assert gap_dates(completed) == (days_ago(2), days_ago(1))

    def test_today_and_yesterday_registered_returns_none(self):
        """RF-2.1: sin días faltantes recientes no hay nada que recuperar."""
        completed = {days_ago(2), days_ago(1), TODAY}

        assert core.find_recoverable_gap(completed, TODAY) is None

    def test_ignores_older_gap_when_latest_is_large(self):
        """RF-2.2, RF-2.18: manda el hueco más reciente, aunque sea largo."""
        completed = {days_ago(10), days_ago(8), days_ago(4), TODAY}

        assert core.find_recoverable_gap(completed, TODAY) is None

    def test_returns_latest_small_gap(self):
        """RF-2.18: se devuelve el hueco pequeño más reciente."""
        completed = {days_ago(10), days_ago(6), days_ago(2), TODAY}

        assert gap_dates(completed) == (days_ago(1),)

    def test_gap_never_includes_today(self):
        """RF-2.1: el día de hoy no forma parte del hueco recuperable."""
        completed = {days_ago(3)}

        assert TODAY not in gap_dates(completed)


class TestRecoveredDaysStatsAndHeatmap:
    """Estadísticas y heatmap con días recuperados — Tareas 1.3 y 1.4."""

    def test_stats_include_recovered_days_in_streaks(self):
        """RF-2.9: la racha actual y la mejor racha incluyen recuperados."""
        completed = {days_ago(2), days_ago(1), TODAY}
        recovered = {days_ago(1)}

        stats = core.get_habit_stats(
            completed,
            TODAY,
            recovered_dates=recovered,
        )

        assert stats.current_streak == 3
        assert stats.best_streak == 3

    def test_registered_days_exclude_recovered_days(self):
        """RF-2.10: “Días registrados” no cuenta los recuperados."""
        completed = {days_ago(3), days_ago(2), days_ago(1), TODAY}
        recovered = {days_ago(2), days_ago(1)}

        assert core.count_registered_days(
            completed,
            recovered_dates=recovered,
        ) == 2
        assert core.count_registered_days(completed) == 4

    def test_heatmap_marks_recovered_days(self):
        """RF-2.11: el heatmap distingue los días recuperados."""
        completed = {days_ago(2), days_ago(1), TODAY}
        recovered = {days_ago(1)}

        cells = core.build_activity_heatmap(
            completed,
            TODAY,
            recovered_dates=recovered,
        )
        by_date = {cell.date: cell for cell in cells}

        assert by_date[days_ago(1)].completed is True
        assert by_date[days_ago(1)].recovered is True
        assert by_date[days_ago(2)].completed is True
        assert by_date[days_ago(2)].recovered is False
        assert by_date[days_ago(3)].completed is False
        assert by_date[days_ago(3)].recovered is False

    def test_heatmap_defaults_recovered_to_false(self):
        """RF-2.11: sin fechas recuperadas, ninguna celda es recuperada."""
        cells = core.build_activity_heatmap({TODAY}, TODAY)

        assert all(cell.recovered is False for cell in cells)
