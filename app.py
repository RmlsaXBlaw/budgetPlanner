from flask import Flask, request, render_template
#request enable form handling
#render_template enable rendering html templates

app = Flask(__name__) #create flask app

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, request received"
    return render_template('loginForm.html')

@app.route('/registration', methods=['GET', 'POST']) 
def registration():
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, request received"
    return render_template('regForm.html')

if __name__ == '__main__':
    app.run(debug=True)