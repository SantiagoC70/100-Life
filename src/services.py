"""Reglas de negocio puras y operaciones seguras por usuario."""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import date, datetime, time, timedelta
from typing import Iterable
from uuid import uuid4

from .db import connect, init_db

KINDS = ("clase", "tarea", "examen", "entrenamiento", "personal", "estudio")


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000).hex()


def register(username: str, password: str, path=None) -> tuple[bool, str]:
    username = username.strip()
    if len(username) < 3 or len(password) < 8:
        return False, "Usa un usuario de 3 caracteres y una contraseña de al menos 8."
    init_db(path)
    salt = os.urandom(16)
    try:
        with connect(path) as db:
            db.execute("INSERT INTO users(username,password_hash,password_salt,created_at) VALUES(?,?,?,?)",
                       (username, _hash(password, salt), salt.hex(), datetime.now().isoformat(timespec="seconds")))
        return True, "Cuenta creada. Ya puedes iniciar sesión."
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return False, "Ese nombre de usuario ya existe."
        return False, "No fue posible crear la cuenta."


def authenticate(username: str, password: str, path=None):
    init_db(path)
    with connect(path) as db:
        row = db.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE", (username.strip(),)).fetchone()
    if row and hmac.compare_digest(row["password_hash"], _hash(password, bytes.fromhex(row["password_salt"]))):
        return {"id": row["id"], "username": row["username"]}
    return None


def get_profile(user_id: int, path=None):
    with connect(path) as db:
        row = db.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def save_profile(user_id: int, data: dict, path=None) -> None:
    if data["student_type"] not in ("general", "atleta"):
        raise ValueError("Tipo de estudiante inválido")
    goal = int(data["water_goal_ml"])
    if not 250 <= goal <= 10_000:
        raise ValueError("Meta de hidratación inválida")
    with connect(path) as db:
        db.execute("""INSERT INTO profiles VALUES(?,?,?,?,?,?,?,?)
          ON CONFLICT(user_id) DO UPDATE SET student_type=excluded.student_type,
          study_preference=excluded.study_preference,sleep_start=excluded.sleep_start,
          sleep_end=excluded.sleep_end,dietary_preferences=excluded.dietary_preferences,
          dietary_restrictions=excluded.dietary_restrictions,water_goal_ml=excluded.water_goal_ml""",
          (user_id, data["student_type"], data["study_preference"].strip(), data["sleep_start"],
           data["sleep_end"], data.get("dietary_preferences", "").strip(),
           data.get("dietary_restrictions", "").strip(), goal))


def _parse(value: str | datetime) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


def conflicts(user_id: int, start, end, exclude_id=None, path=None) -> list[dict]:
    start, end = _parse(start), _parse(end)
    if end <= start:
        raise ValueError("La hora final debe ser posterior a la inicial.")
    query = "SELECT * FROM activities WHERE user_id=? AND starts_at < ? AND ends_at > ?"
    params: list = [user_id, end.isoformat(timespec="minutes"), start.isoformat(timespec="minutes")]
    if exclude_id is not None:
        query += " AND id<>?"; params.append(exclude_id)
    with connect(path) as db:
        return [dict(r) for r in db.execute(query, params).fetchall()]


def save_activity(user_id: int, data: dict, activity_id=None, path=None) -> int:
    title = data.get("title", "").strip()
    kind = data.get("kind")
    start, end = _parse(data["starts_at"]), _parse(data["ends_at"])
    if not title or kind not in KINDS or end <= start:
        raise ValueError("Completa un título, tipo y horario válidos.")
    deadline = data.get("deadline")
    values = (kind, title, start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes"),
              int(data.get("priority", 2)), deadline.isoformat(timespec="minutes") if isinstance(deadline, datetime) else deadline,
              int(bool(data.get("completed"))), data.get("notes", "").strip(), data.get("perceived_intensity"),
              data.get("fatigue"), int(bool(data.get("pain"))))
    with connect(path) as db:
        if activity_id:
            cur = db.execute("""UPDATE activities SET kind=?,title=?,starts_at=?,ends_at=?,priority=?,deadline=?,
             completed=?,notes=?,perceived_intensity=?,fatigue=?,pain=? WHERE id=? AND user_id=?""", values + (activity_id, user_id))
            if not cur.rowcount: raise ValueError("Actividad no encontrada.")
            return int(activity_id)
        return db.execute("""INSERT INTO activities(kind,title,starts_at,ends_at,priority,deadline,completed,
          notes,perceived_intensity,fatigue,pain,user_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", values + (user_id,)).lastrowid


def list_activities(user_id: int, path=None) -> list[dict]:
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM activities WHERE user_id=? ORDER BY starts_at", (user_id,))]


def delete_activity(user_id: int, activity_id: int, path=None) -> bool:
    with connect(path) as db:
        return bool(db.execute("DELETE FROM activities WHERE id=? AND user_id=?", (activity_id, user_id)).rowcount)


def set_completed(user_id: int, activity_id: int, completed: bool, path=None) -> None:
    with connect(path) as db:
        db.execute("UPDATE activities SET completed=? WHERE id=? AND user_id=?", (int(completed), activity_id, user_id))


def add_water(user_id: int, amount_ml: int, consumed_at: datetime, path=None) -> int:
    if not 1 <= int(amount_ml) <= 5000: raise ValueError("La cantidad debe estar entre 1 y 5000 ml.")
    with connect(path) as db:
        return db.execute("INSERT INTO hydration(user_id,consumed_at,amount_ml) VALUES(?,?,?)",
                          (user_id, consumed_at.isoformat(timespec="minutes"), int(amount_ml))).lastrowid


def update_water(user_id: int, entry_id: int, amount_ml: int, consumed_at: datetime, path=None) -> None:
    if not 1 <= int(amount_ml) <= 5000: raise ValueError("Cantidad inválida.")
    with connect(path) as db:
        if not db.execute("UPDATE hydration SET amount_ml=?,consumed_at=? WHERE id=? AND user_id=?",
                          (int(amount_ml), consumed_at.isoformat(timespec="minutes"), entry_id, user_id)).rowcount:
            raise ValueError("Registro no encontrado.")


def delete_water(user_id: int, entry_id: int, path=None) -> bool:
    with connect(path) as db:
        return bool(db.execute("DELETE FROM hydration WHERE id=? AND user_id=?", (entry_id, user_id)).rowcount)


def water_history(user_id: int, path=None) -> list[dict]:
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM hydration WHERE user_id=? ORDER BY consumed_at DESC", (user_id,))]


def water_total(user_id: int, day: date, path=None) -> int:
    with connect(path) as db:
        row = db.execute("SELECT COALESCE(SUM(amount_ml),0) total FROM hydration WHERE user_id=? AND date(consumed_at)=?",
                         (user_id, day.isoformat())).fetchone()
    return int(row["total"])


def recommend_study_blocks(user_id: int, task_id: int, path=None, now: datetime | None = None) -> dict:
    """Busca huecos de 30-90 min, respeta sueño y divide el trabajo restante."""
    profile = get_profile(user_id, path)
    activities = list_activities(user_id, path)
    task = next((a for a in activities if a["id"] == task_id and a["kind"] in ("tarea", "examen")), None)
    if not profile or not task: raise ValueError("Selecciona una tarea/examen y completa el perfil.")
    now = (now or datetime.now()).replace(second=0, microsecond=0)
    deadline = _parse(task["deadline"]) if task["deadline"] else _parse(task["starts_at"])
    needed = max(30, int((_parse(task["ends_at"]) - _parse(task["starts_at"])).total_seconds() // 60))
    busy = [(_parse(a["starts_at"]), _parse(a["ends_at"])) for a in activities if a["id"] != task_id]
    blocks, cursor = [], now
    cursor += timedelta(minutes=(30 - cursor.minute % 30) % 30)
    while cursor < deadline and needed > 0:
        awake_start = datetime.combine(cursor.date(), time.fromisoformat(profile["sleep_end"]))
        awake_end = datetime.combine(cursor.date(), time.fromisoformat(profile["sleep_start"]))
        if awake_end <= awake_start: awake_end += timedelta(days=1)
        if cursor < awake_start: cursor = awake_start
        if cursor >= awake_end: cursor = datetime.combine(cursor.date() + timedelta(days=1), time.fromisoformat(profile["sleep_end"])); continue
        length = min(90, needed)
        end = min(cursor + timedelta(minutes=length), awake_end, deadline)
        collision = next(((s, e) for s, e in busy if cursor < e and end > s), None)
        if collision: cursor = collision[1]; continue
        minutes = int((end-cursor).total_seconds()//60)
        if minutes >= 30:
            blocks.append({"start": cursor, "end": end, "minutes": minutes,
                           "reason": f"Bloque libre antes de la fecha límite; prioridad {task['priority']}/3."})
            needed -= minutes
        cursor = end + timedelta(minutes=15)
    return {"task": task, "blocks": blocks, "missing_minutes": max(0, needed),
            "message": "No hay tiempo suficiente; mueve actividades flexibles o amplía la fecha límite." if needed else "Se encontraron bloques sin superposición y fuera del horario de sueño."}


def wellbeing_advice(profile: dict, workouts: Iterable[dict]) -> dict:
    athlete = profile.get("student_type") == "atleta"
    latest = next(iter(workouts), {})
    pain = bool(latest.get("pain"))
    recovery = ("No hagas ejercicios ante dolor o síntomas preocupantes; informa a una persona adulta y busca valoración profesional."
                if pain else "Tras una sesión exigente, prioriza descanso, comida habitual suficiente y movilidad suave si resulta cómoda.")
    return {
      "salud": "Mantén horarios de sueño regulares y pausas durante el estudio. Son consejos generales, no una evaluación médica.",
      "nutricion": f"Organiza comidas variadas y regulares respetando tus preferencias ({profile.get('dietary_preferences') or 'ninguna declarada'}) y restricciones ({profile.get('dietary_restrictions') or 'ninguna declarada'}). No se indican dietas restrictivas ni suplementos.",
      "recuperacion": recovery if athlete else "Para estudiantes que no entrenan: alterna estudio con pausas breves y movimiento cotidiano cómodo.",
      "hidratacion": "Usa tu meta personal como referencia flexible y registra lo que bebes; las necesidades varían y no conviene forzar un consumo excesivo."
    }
