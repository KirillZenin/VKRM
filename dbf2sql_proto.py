#!/usr/bin/python3
import dbfread  # main library for project, redacted dbf.py as lines 157-158 been commented
import os  # Library to work with filenames and pathes
from pandas import DataFrame  # used for being mediator from dbf to sql
from sqlalchemy import create_engine  # using to allow creating engine for generating SQLdump
import csv  # library to work with CSV
import io  # used to read and write to files in memory
import zipfile  # for creating zip archives
from flask import Flask  # library to create back-end
from flask import render_template, send_file, request  # importing RT rendering and getting uploaded files
from flask_wtf import FlaskForm  # allows to create form for web page
from wtforms import SubmitField, RadioField, StringField, MultipleFileField  # fields for web page
from wtforms.validators import DataRequired  # validation for  no empty forms been sent
# allows to translate text on rendering web page
from flask_babel import Babel, _
from flask_babel import lazy_gettext as _l

app = Flask(__name__)
# needed for hidden.tag in /templates/index.html
app.config['SECRET_KEY'] = 'Bloodghast'
app.config['LANGUAGES'] = ['en', 'ru']
babel = Babel(app)


@babel.localeselector
def get_locale():  # can translate text on web page if browser language in app.config
    # print(request.accept_languages.best_match(app.config['LANGUAGES']))
    return request.accept_languages.best_match(app.config['LANGUAGES'])
    # return 'ru'


class FileForm(FlaskForm):
    # allows to upload multiple files
    file = MultipleFileField(label=_l('Files'))
    radio = RadioField(label=_l('Output Format'),
                       choices=[("SQL", _l("Export to SQL dump file")),
                                ("CSV", _l("Export to CSV file"))],
                       validators=[DataRequired()])  # requires a choice so no empty form is sent
    # allows to manually choose codec
    codec = StringField(label=_l('Codec (Optional)'))
    submit = SubmitField(_l('Convert'))  # submit convertation


@app.route('/db', methods=['GET', 'POST'])
def index():
    form = FileForm()
    if form.validate_on_submit():
        try:
            if form.file.data[0].filename != '':
                if form.radio.data == 'CSV':  # if "convert to CSV" was chosen
                    memzip = io.BytesIO()  # binary in-memory stream with file-like properties and opening stream for writing to archive
                    with zipfile.ZipFile(memzip, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
                        for item in form.file.data:
                            dbf = None
                            csv_out = io.StringIO()  # string in-memory stream with file-like properties
                            # function of lib/csv to write in CSV files
                            writer = csv.writer(csv_out)
                            if form.codec.data == '':  # using autodetect, if codec not chosen manually
                                dbf = dbfread.DBF(item.stream)
                            else:
                                # using manually specified codec
                                dbf = dbfread.DBF(
                                    item.stream, encoding=form.codec.data)
                            # writing row of headers in CSV
                            writer.writerow(dbf.field_names)
                            for record in dbf:
                                # writing rows of data in CSV
                                writer.writerow(list(record.values()))
                            zipf.writestr(os.path.splitext(item.filename)[0] + '.csv', csv_out.getvalue())  # packing to zip
                    memzip.seek(0)  # moving at beginning of archive file
                    return send_file(memzip, mimetype='application/zip',
                                     attachment_filename='Combined.zip',
                                     as_attachment=True)  # sending an archive with CSVs to user

                if form.radio.data == 'SQL':  # if "convert to SQL dump" was chosen
                    # using on MEMORY engine of SQLite
                    db = create_engine('sqlite:///:memory:')
                    dbc = db.connect()  # connecting to MEMORY engine
                    for item in form.file.data:
                        if form.codec.data == '':  # using autodetect, if codec was not specified
                            dbf = dbfread.DBF(item.stream)
                        else:  # using with specified codec
                            dbf = dbfread.DBF(item.stream, 
                                encoding=form.codec.data)

                        frame = DataFrame(iter(dbf))  # putting DBF data to DataFrame
                        frame.to_sql(os.path.splitext(item.filename)[0], 
                                    dbc, if_exists='replace')  # from DataFrame to SQL

                    cn = db.raw_connection() # return connection without shells
                    res = ''
                    for line in cn.iterdump(): # allows to create SQLdump from DB in memory
                        res += '%s\n' % line  # writing inserts to SQL dump by line
                    proxy = io.BytesIO() # creating byte buffer
                    proxy.write(res.encode('utf-8')) # create utf-8 encoded text
                    proxy.seek(0) # return to start file

                    return send_file(proxy, mimetype='application/sql',
                                     attachment_filename=os.path.splitext(
                                         form.file.data[0].filename)[0] + '.sql',
                                     as_attachment=True)  # sending SQL dump file to user for download
        except UnicodeDecodeError:
            return render_template('index.html', title=_('DB Converter'), form=form,
                                   err=_(
                                       'Error decoding DBF with given codec, or no codec is given and header does not '
                                       'have one'), advice=_('Consider using cp866 for DBs containing Russian'))
       


    # rendering web-page in RT
    return render_template('index.html', title=_('DB Converter'), form=form)


if __name__ == '__main__':
    # do()
    # app.run(host='0.0.0.0')
    # app.run(debug=True)
    app.run()
