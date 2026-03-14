import os
import secrets
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    _secret_key = secrets.token_hex(32)
app.secret_key = _secret_key

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "fungi")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "fungi_db")


def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )


def init_db():
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fungi (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scientific_name VARCHAR(255) NOT NULL,
                    common_name VARCHAR(255),
                    family VARCHAR(255),
                    habitat TEXT,
                    edibility ENUM('edible', 'poisonous', 'inedible', 'unknown') NOT NULL DEFAULT 'unknown',
                    description TEXT,
                    notes TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()


@app.route("/")
def index():
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, scientific_name, common_name, family, edibility, date_added "
                "FROM fungi ORDER BY date_added DESC"
            )
            fungi_list = cursor.fetchall()
    return render_template("index.html", fungi_list=fungi_list)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        scientific_name = request.form.get("scientific_name", "").strip()
        if not scientific_name:
            flash("Scientific name is required.", "error")
            return render_template("form.html", action="Add", entry=request.form)

        conn = get_db()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO fungi
                        (scientific_name, common_name, family, habitat, edibility, description, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        scientific_name,
                        request.form.get("common_name", "").strip() or None,
                        request.form.get("family", "").strip() or None,
                        request.form.get("habitat", "").strip() or None,
                        request.form.get("edibility", "unknown"),
                        request.form.get("description", "").strip() or None,
                        request.form.get("notes", "").strip() or None,
                    ),
                )
            conn.commit()
        flash(f"'{scientific_name}' added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", action="Add", entry={})


@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
def edit(entry_id):
    conn = get_db()
    if request.method == "POST":
        scientific_name = request.form.get("scientific_name", "").strip()
        if not scientific_name:
            flash("Scientific name is required.", "error")
            return render_template("form.html", action="Edit", entry=request.form, entry_id=entry_id)

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE fungi
                    SET scientific_name=%s, common_name=%s, family=%s,
                        habitat=%s, edibility=%s, description=%s, notes=%s
                    WHERE id=%s
                    """,
                    (
                        scientific_name,
                        request.form.get("common_name", "").strip() or None,
                        request.form.get("family", "").strip() or None,
                        request.form.get("habitat", "").strip() or None,
                        request.form.get("edibility", "unknown"),
                        request.form.get("description", "").strip() or None,
                        request.form.get("notes", "").strip() or None,
                        entry_id,
                    ),
                )
            conn.commit()
        flash(f"'{scientific_name}' updated successfully.", "success")
        return redirect(url_for("index"))

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM fungi WHERE id=%s", (entry_id,))
            entry = cursor.fetchone()

    if entry is None:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    return render_template("form.html", action="Edit", entry=entry, entry_id=entry_id)


@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete(entry_id):
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT scientific_name FROM fungi WHERE id=%s", (entry_id,))
            entry = cursor.fetchone()
            if entry:
                cursor.execute("DELETE FROM fungi WHERE id=%s", (entry_id,))
        conn.commit()

    if entry:
        flash(f"'{entry['scientific_name']}' deleted.", "success")
    else:
        flash("Entry not found.", "error")

    return redirect(url_for("index"))


@app.route("/view/<int:entry_id>")
def view_entry(entry_id):
    conn = get_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM fungi WHERE id=%s", (entry_id,))
            entry = cursor.fetchone()

    if entry is None:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    return render_template("detail.html", entry=entry)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
