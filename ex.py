from flask import Flask, render_template, request,url_for,redirect,flash
import os
import sqlite3
import cv2
import pytesseract
import csv
import re
import nltk
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

import numpy as np

app = Flask(__name__)
word_list = ['Shree', 'Mahendra', 'Higher', 'Secondary', 'School', 'Sarthak', 'Walmart', 'Manakamana']
word_needed = ""
APP_ROOT =  os.path.dirname(os.path.abspath(__file__))

pnr_area = [150, 450, 1600, 1150]  # [start_x, start_y, end_x, end_y]

output_dir = ("C:/Users/Nitesh/Desktop/fileupload/test")


def ext_names(string):
    m = re.search('Name:(.+?)C', string)
    if m:
        found = m.group(1)
        return found

def get_names(string):
    named=item_name(string)
    word_needed = ""
    for nam in named:
        for word in word_list:
            Distance = minimumEditDistance(nam, word)
            if Distance <= 2:
                word_needed = word_needed + ' ' + word
                # print(word_needed)
                # word+=word
    return word_needed


def sum(string):
    m = re.search('Sum:(.+?)00', string)
    if m:
        found = m.group(1)
        return found
def phone_no(string):
    r = re.compile(r'(\d{3}-\d{6})')
    p = r.findall(string)
    return p

def invoice_no(string):
    r = re.compile(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})')
    # r = re.compile(r'”(\(0\)|0)((\s∗\−)?\s∗[0−9]){9}”, ')
    # r =re.compile(r'([0−9]\s∗)+[\ ,\.](\s∗[0−9]){2}')
    # r = re.compile(r'(?:\$|RS|Rs|rs|Rupees|rupees|pkr)(\s*?)(\d+(?:\.\d{2}))')
    one_numbers = r.findall(string)
    return [re.sub(r'\D', '', number) for number in one_numbers]


def extract_email_addresses(string):
    r = re.compile(r'[\w\.-]+@[\w\.-]+')
    return r.findall(string)

def prices(string):
    p = re.findall('(\d+[\.,]\d{2})',string)
    max = float(p[0])
    n = len(p)
    for i in range(1, n):
        if float(p[i]) > max:
            max = float(p[i])
    return max
def ie_preprocess(document):
    document = ' '.join([i for i in document.split() if i not in stop])
    sentences = nltk.sent_tokenize(document)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences


def extract_names(document):
    names = []
    sentences = ie_preprocess(document)
    for tagged_sentence in sentences:
        for chunk in nltk.ne_chunk(tagged_sentence):
            if type(chunk) == nltk.tree.Tree:
                if chunk.label() == 'PERSON':
                    names.append(' '.join([c[0] for c in chunk]))
    return names

def item_name(result):
    ssd=re.compile(r'[a-zA-Z]+')
    item_name=ssd.findall(result)
    return item_name

#re to return date
def Date(string):
    r = re.compile("^([1-9] |1[0-9]| 2[0-9]|3[0-1])(.|-)([1-9] |1[0-2])(.|-|)20[0-9][0-9]$")
    m = re.search('(\d{4}[-/]\d{2}[-/]\d{2})', string)
    if m:
        found = m.group(1)
        return found


def create_connection(result):
    # email=extract_email_addresses(result)
    date = Date(result)
    phone='123123123'
    name= get_names(result)
    print("phone no:",phone)
    print(date)
    price = prices(result)
    print("Total amount: ", price)
    connection = sqlite3.connect('oogello.db')
    c = connection.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS Invoice_table (id INTEGER PRIMARY KEY, name text NOT NULL,Date text,Price text NOT NULL)''')
    c.execute('''INSERT INTO Invoice_table VALUES(null,?,?,?);''', (name,date,price))

    # a=c.execute('''CREATE TRIGGER Display AFTER INSERT ON Invoice_table  BEGIN SELECT * FROM Invoice_table WHERE   row_id = (SELECT MAX(row_id)  FROM Invoice_table) ''')
    # a=c.execute('''CREATE TRIGGER Display AFTER INSERT ON Invoice_table  BEGIN row_id = (SELECT MAX(row_id)  FROM Invoice_table ''')

    connection.commit()
    for row in c.execute('''SELECT * FROM Invoice_table where id=(SELECT max(id) FROM Invoice_table)'''):
        print(row)

    # for row in c.execute('''SELECT * FROM Invoice_table'''):
    #   print(row)
    c.close()
    connection.close()

#re to return name of vendor
# def ext_names(string):
#     m = re.search('', string)
#     if m:
#         found = m.group(1)
#         return found

def minimumEditDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for index2, char2 in enumerate(s2):
        newDistances = [index2 + 1]
        for index1, char1 in enumerate(s1):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1],
                                             distances[index1 + 1],
                                             newDistances[-1])))
        distances = newDistances
    return distances[-1]

def apply_threshold(img, argument):
    switcher = {
        1: cv2.threshold(cv2.GaussianBlur(img, (9, 9), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        2: cv2.threshold(cv2.GaussianBlur(img, (7, 7), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        3: cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        4: cv2.threshold(cv2.medianBlur(img, 5), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        5: cv2.threshold(cv2.medianBlur(img, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        6: cv2.adaptiveThreshold(cv2.GaussianBlur(img, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2),
        7: cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2),
    }
    return switcher.get(argument, "Invalid method")



class ArticleForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=200)])
    date = TextAreaField('Date', [validators.Length(min=30)])
    price = TextAreaField('Price', [validators.Length(min=1)])

#homepage route
@app.route('/')
def main():
    return render_template('newupload.html')

@app.route('/upload', methods = ['POST'])
def upload():
    target = os.path.join(APP_ROOT, 'image/')
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        #to tell where to store file w/ filename
        destination = "/".join([target, filename])
        print(destination)
        file.save(destination)

    # print("again " + destination)
    img = cv2.imread(destination)

    file_name = os.path.basename(destination).split('.')[0]
    file_name = file_name.split()[0]

    output_path = os.path.join(output_dir, file_name)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Crop the areas where provision number is more likely present
    imgr = crop_image(img, pnr_area[0], pnr_area[1], pnr_area[2], pnr_area[3])
    imgr = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    #
      # Convert to gray
    imgr = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #
    # Apply dilation and erosion to remove some noise
    kernel = np.ones((1, 1), np.uint8)
    imgr = cv2.dilate(img, kernel, iterations=1)
    imgr = cv2.erode(img, kernel, iterations=1)
    #
    #  Apply threshold to get image with only black and white
    # imgr = apply_threshold(img, method)
    # save_path = os.path.join(output_path, file_name + "_filter_" + str(method) + ".jpg")
    # cv2.imwrite(save_path, imgr)
    #
    # Recognize text with tesseract for python
    result = pytesseract.image_to_string(img, lang="eng")
    print(result)
    named= item_name(result)
    # print(nam)
    # word_list = ['Shree', 'Mahendra', 'Higher', 'Secondary', 'School', 'Sarthak', 'Walmart', 'Manakamana']
    # word_needed = "."
    # for nam in named:
    #     for word in word_list:
    #         Distance = minimumEditDistance(nam, word)
    #         if Distance <= 2:
    #             word_needed = word_needed + ' ' + word
    #             # print(word_needed)
    #             # word+=word
    # print(word_needed)
    email=extract_email_addresses(result)
    print("E-mail=",email)
    date=Date(result)
    print(date)
    price=prices(result)
    print("Total amount: ",price)

    create_connection(result)
    # info=cursor.execute

    # DATAbase connection
    return render_template('newupload.html')

@app.route('/details')
def detail():
    con = sqlite3.connect("oogello.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    cur.execute("select * from Invoice_table")

    rows= cur.fetchall()
    search = False
    q = request.args.get('q')
    if q:
        search =True

    return render_template('detail.html', rows=rows)

#Edit details
@app.route('/edit_detail/<int:id>', methods=['GET', 'POST'])
def edit_detail(id):
    # Create cursor

    con = sqlite3.connect("oogello.db")
    con.row_factory = sqlite3.Row

    cur = con.cursor()
    # Get article by id
    res = cur.execute("SELECT * FROM Invoice_table WHERE id =%d" %id)

    detail = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate details form fields
    form.name.data = detail['name']
    form.date.data = detail['date']
    form.price.data = detail['price']

    if request.method == 'POST' and form.validate():
        name = request.form['name']
        date = request.form['date']
        price = request.form['price']
        cur = con.cursor()
        cur.execute("UPDATE Invoice_table SET name=%s, date=%s, price=%d WHERE id=%d", (name, date, price, id))
        con.commit()
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('detail.html'))

@app.route('/new_detail/1',methods=['POST', 'GET'])
def new_detail():
    return render_template('addnew.html')


#edit_detail_2
@app.route('/addrec/1', methods=['POST', 'GET'])
def addrec():
    if request.method == 'POST':
        nm = request.form['nm']
        dat = request.form['date']
        price = request.form['price']

        con = sqlite3.connect("oogello.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("UPDATE Invoice_table SET name='Anil Basnet', date='2072/02/02', price='5000' WHERE id=1" )

        # cur.execute("INSERT INTO Invoice_table (name,date,price) VALUES(?, ?, ?)",(nm,dat,price) )

        con.commit()
        con.close()
        return render_template("detail.html")

    @app.route('/addrec/1', methods=['POST', 'GET'])
    def addrec():
        if request.method == 'POST':
            nm = request.form['nm']
            dat = request.form['date']
            price = request.form['price']

            con = sqlite3.connect("oogello.db")
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("UPDATE Invoice_table SET name='%s', date='%s', price='%d' WHERE id=1")

            # cur.execute("INSERT INTO Invoice_table (name,date,price) VALUES(?, ?, ?)",(nm,dat,price) )

            con.commit()
            con.close()
            return render_template("detail.html")

# Delete Article
@app.route('/delete_detail/<int:id>', methods=['POST'])
def delete_detail(id):
    # Create cursor
    con = sqlite3.connect("oogello.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Execute
    cur.execute("DELETE FROM Invoice_table WHERE id = %d" %id)

    # Commit to DB
    con.commit()
    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('detail'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)

    date=Date(result)
