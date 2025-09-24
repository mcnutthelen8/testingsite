from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", result=None, error=None, a="", b="", op="add")

@app.route("/calc", methods=["POST"])
def calc():
    a = request.form.get("a", "").strip()
    b = request.form.get("b", "").strip()
    op = request.form.get("op", "add")
    error = None
    result = None

    # basic validation
    try:
        a_val = float(a)
        b_val = float(b)
    except ValueError:
        error = "Please enter valid numbers."
        return render_template("index.html", result=None, error=error, a=a, b=b, op=op)

    try:
        if op == "add":
            result = a_val + b_val
        elif op == "sub":
            result = a_val - b_val
        elif op == "mul":
            result = a_val * b_val
        elif op == "div":
            if b_val == 0:
                raise ZeroDivisionError
            result = a_val / b_val
        else:
            error = "Unknown operation."
    except ZeroDivisionError:
        error = "Division by zero is not allowed."

    return render_template("index.html", result=result, error=error, a=a, b=b, op=op)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
