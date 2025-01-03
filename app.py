from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Fungsi untuk mengambil data dari database
def get_news():
    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row  # Mengembalikan data sebagai dictionary
    cur = conn.cursor()
    cur.execute("SELECT * FROM news")
    rows = cur.fetchall()
    conn.close()
    return rows

# Route untuk halaman utama
@app.route("/")
def index():
    news = get_news()
    return render_template("news.html", news=news)

if __name__ == "__main__":
    app.run(debug=True)
