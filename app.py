from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
        <head>
            <title>Nasze wesele</title>
        </head>
        <body>
            <h1>Nasze wesele</h1>
            <p>Planner organizacji wesela</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
