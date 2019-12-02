from flask import *
import sqlite3
from wtforms import Form,validators,TextAreaField,StringField
app = Flask(__name__)


class EmployeeForm(Form):
    name = StringField('Name')
    email = TextAreaField('email')
    address = TextAreaField('Address')


@app.route("/")
def index():
    return render_template("index.html");


@app.route("/add")
def add():
    return render_template("add.html")


@app.route("/savedetails", methods=["POST", "GET"])
def saveDetails():
    msg = "msg"
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        address = request.form["address"]
        with sqlite3.connect("employee.db") as con:
            cur = con.cursor()
            cur.execute("INSERT into Employees (name, email, address) values (?,?,?)", (name, email, address))
            con.commit()
            msg = "Employee successfully Added"


        return render_template("success.html", msg=msg)
        con.close()


@app.route("/view")
def view():
    con = sqlite3.connect("employee.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("select * from Employees")
    rows = cur.fetchall()
    return render_template("view.html", rows=rows)


@app.route("/delete")
def delete():
    return render_template("delete.html")

@app.route("/update")
def update():
    return render_template(("update.html"))
@app.route("/updaterecord/<int:id>", methods=["POST","GET"])
def updaterecord():
    id = request.form["id"]
    with sqlite3.connect("employee.db") as con:
        cur = con.cursor()
        res = cur.execute("SELECT * FROM Employees WHERE id =%d" % id)
        detail = cur.fetchone(res)
        # cur.close()
        # # Get form
        form = EmployeeForm(request.form)
        #
        # # Populate details form fields
        form.name.data = detail['name']
        form.email.data = detail['email']
        form.address.data = detail['address']
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            address = request.form['address']
            cur = con.cursor()
            cur.execute("UPDATE Employees SET name=%s, email=%s, address=%s WHERE id=%d", (name, email, address, id))
            con.commit()
            cur.close()
            msg = "record successfully updated"

        return render_template("update_record.html", msg=msg)
@app.route("/deleterecord", methods=["POST"])
def deleterecord():
    id = request.form["id"]
    with sqlite3.connect("employee.db") as con:

        cur = con.cursor()
        cur.execute("delete from Employees where id = ?", id)
        msg = "record successfully deleted"


        return render_template("delete_record.html", msg=msg)


if __name__ == "__main__":
    app.run(debug=True)