# spec: 002-ui-redesign
# spec: 006-code-organization
"""Tests de iconos, etiquetas y formatos visuales — Tarea 6.2, RF-2.2 y RF-5.4.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
"""

from datetime import date

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.domain.models import ALLOWED_ICONS
from habits.state.models import (
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
)
from habits.ui.common import (
    DEFAULT_SIDEBAR_ICON,
    ICON_BY_KEY,
    STAT_CARD_ICONS,
    WEEKDAY_LABELS,
    format_date_display,
    format_streak_label,
    icon_for_habit,
)


class TestIconMapping:
    """Traducción de claves semánticas a iconos de Flet."""

    def test_icon_map_covers_all_allowed_icons(self):
        """RF-2.2: cada icono permitido tiene un icono visual."""
        assert set(ICON_BY_KEY) == set(ALLOWED_ICONS)

    def test_known_key_returns_its_icon(self):
        """RF-2.2: una clave válida devuelve el icono correspondiente."""
        assert icon_for_habit("code") == ft.Icons.CODE

    def test_unknown_key_returns_default_icon(self):
        """RF-2.2: una clave desconocida cae en el icono por defecto."""
        assert icon_for_habit("unknown") == DEFAULT_SIDEBAR_ICON


class TestStreakLabel:
    """Formato de la racha en la barra lateral."""

    def test_zero_streak_has_no_flame(self):
        """RF-5.4: sin racha se muestra el texto neutro."""
        assert format_streak_label(0) == "Sin racha"

    def test_one_day_is_singular(self):
        """RF-5.4: un día usa singular."""
        assert format_streak_label(1) == "🔥 1 día"

    def test_multiple_days_are_plural(self):
        """RF-5.4: dos o más días usan plural."""
        assert format_streak_label(7) == "🔥 7 días"


class TestDateFormat:
    """Formato visual de fechas."""

    def test_date_is_rendered_as_day_month_year(self):
        """RF-5.4: las fechas visibles usan dd/mm/aaaa."""
        assert format_date_display(date(2024, 10, 24)) == "24/10/2024"


class TestSharedLabels:
    """Etiquetas compartidas por los widgets."""

    def test_weekday_labels_start_on_monday(self):
        """RF-5.4: el heatmap etiqueta las filas de lunes a domingo."""
        assert WEEKDAY_LABELS == ("L", "M", "X", "J", "V", "S", "D")

    def test_stat_cards_have_an_icon_each(self):
        """RF-5.4: cada tarjeta de estadísticas tiene su icono."""
        assert set(STAT_CARD_ICONS) == {
            STAT_CURRENT_STREAK_LABEL,
            STAT_BEST_STREAK_LABEL,
            STAT_REGISTERED_DAYS_LABEL,
        }
