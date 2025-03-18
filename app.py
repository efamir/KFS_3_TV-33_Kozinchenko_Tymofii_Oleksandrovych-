import shutil

from flask import Flask, render_template, request
import os
from graphs import generate_plots, cities


app = Flask(__name__)
image_dir = "static/img"


@app.route('/', methods=['GET'])
def index():
    selected_location = request.args.get('location')
    imgs=None
    if selected_location:
        # Очищаємо теку перед генерацією нових зображень
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir)
        os.makedirs(image_dir, exist_ok=True)

        # Генеруємо нові графіки
        imgs = generate_plots(selected_location if selected_location != "ALL" else None)

    return render_template('index.html', imgs=imgs, selected_location=selected_location, cities=cities)


if __name__ == '__main__':
    app.run(debug=True)
