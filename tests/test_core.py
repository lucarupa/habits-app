from datetime import date, timedelta

from habits.core import Habit, create_habit, reset_id_counter, mark_completed, calculate_streak, list_habits_with_streak


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
