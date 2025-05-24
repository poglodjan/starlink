from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    cameras = ['cam0.mp4', 'cam1.mp4', 'cam2.mp4', 'cam3.mp4']
    return render_template('index.html', videos=cameras)

if __name__ == '__main__':
    app.run(debug=True)