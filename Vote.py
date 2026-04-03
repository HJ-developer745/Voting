from flask import Flask, request, render_template_string, redirect, session
import sqlite3
import qrcode

app = Flask(__name__)
app.secret_key = "supersecret"

ADMIN_PASSWORD = "admin123"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("voting.db")
    c = conn.cursor()
    
    c.execute("CREATE TABLE IF NOT EXISTS votes (student_id TEXT UNIQUE, choice TEXT)")
    
    conn.commit()
    conn.close()

init_db()

# ================= QR GENERATOR =================
def generate_qr(student_id):
    url = f"http://127.0.0.1:5000/?id={student_id}"
    img = qrcode.make(url)
    path = f"qr_{student_id}.png"
    img.save(path)

# ================= HTML =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>QR Voting System</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: Arial; background: linear-gradient(135deg,#667eea,#764ba2); }
.container {
    max-width: 400px;
    margin: auto;
    background: white;
    padding: 20px;
    margin-top: 40px;
    border-radius: 10px;
}
button {
    width: 100%;
    padding: 10px;
    margin-top: 10px;
    background: #667eea;
    color: white;
    border: none;
}
</style>
</head>
<body>

<div class="container">
<h2>📲 QR Voting</h2>

<form method="POST">
<input type="text" name="student_id" value="{{student_id}}" readonly>

<label><input type="radio" name="vote" value="Head Boy" required> Head Boy</label><br>
<label><input type="radio" name="vote" value="Head Girl"> Head Girl</label><br>
<label><input type="radio" name="vote" value="Sports Captain"> Sports Captain</label><br>

<button>Submit Vote</button>
</form>

<p>{{message}}</p>
</div>

</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Admin Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: Arial; background: #f5f6fa; }
.container {
    max-width: 500px;
    margin: auto;
    margin-top: 40px;
    background: white;
    padding: 20px;
}
.bar {
    height: 20px;
    background: #44bd32;
    margin-bottom: 10px;
}
</style>
</head>
<body>

<div class="container">
<h2>📊 Live Results</h2>

{% for option, value in results.items() %}
<p>{{option}} - {{value}} votes ({{percent[option]}}%)</p>
<div class="bar" style="width: {{percent[option]}}%;"></div>
{% endfor %}

<a href="/logout">Logout</a>
</div>

</body>
</html>
"""

LOGIN_HTML = """
<h2>Admin Login</h2>
<form method="POST">
<input type="password" name="password" placeholder="Password">
<button>Login</button>
</form>
<p>{{msg}}</p>
"""

# ================= ROUTES =================
@app.route("/", methods=["GET","POST"])
def home():
    student_id = request.args.get("id","")
    msg = ""

    if request.method == "POST":
        student_id = request.form["student_id"]
        vote = request.form["vote"]

        conn = sqlite3.connect("voting.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO votes VALUES (?,?)",(student_id,vote))
            conn.commit()
            msg = "✅ Vote Submitted!"
        except:
            msg = "❌ Already Voted!"

        conn.close()

    return render_template_string(HTML, student_id=student_id, message=msg)

@app.route("/admin", methods=["GET","POST"])
def admin():
    if "admin" in session:
        conn = sqlite3.connect("voting.db")
        c = conn.cursor()

        options = ["Head Boy","Head Girl","Sports Captain"]
        results = {}

        for opt in options:
            c.execute("SELECT COUNT(*) FROM votes WHERE choice=?",(opt,))
            results[opt] = c.fetchone()[0]

        total = sum(results.values()) or 1
        percent = {k: round((v/total)*100,2) for k,v in results.items()}

        conn.close()

        return render_template_string(ADMIN_HTML, results=results, percent=percent)

    msg = ""
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        else:
            msg = "Wrong Password"

    return render_template_string(LOGIN_HTML, msg=msg)

@app.route("/logout")
def logout():
    session.pop("admin",None)
    return redirect("/admin")

@app.route("/generate_qr")
def generate():
    students = ["STU101","STU102","STU103","STU104"]

    for s in students:
        generate_qr(s)

    return "QR Codes Generated!"

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
