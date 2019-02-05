from flask import Flask, Response, request, render_template, url_for, redirect, flash, session, send_file
from functools import wraps
from app import *
from config import IMPORT_FOLDER, allowed_file_import, con
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import xlrd
import os
import numpy as np
import sys
import pdfkit
import time

BASE_lap = os.path.dirname(os.path.realpath(__file__))
LAPORAN_FOLDER = os.path.join(os.path.join(BASE_lap, 'static'), 'laporan')

IMG = os.path.join(os.path.join(BASE_lap,'static'), 'img')

def read_session(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        session.permanent = True
        try:
            if session['id'] is False:
                flash('TEST is invailid')
                return redirect(url_for('save_test'))
            return f(*args, **kwargs)
        except KeyError:
            flash('gk ada id test')
            return redirect(url_for('save_test'))
    return wrap

def admin_session(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        session.permanent = True
        try:
            if session['admin'] is False:
                flash('login is invailid')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        except KeyError:
            flash('Your Session is time out, login first')
            return redirect(url_for('index'))
    return wrap


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/', methods=['POST','GET'])
def index():
    if request.method=='POST':
        user = "admin"
        passw = "admin"
        user_input = request.form['user']
        pass_input = request.form['pass']

        if user == user_input:
            print "username ditemukan"
            if pass_input == passw:
                session['admin'] = user
                return redirect(url_for('save_test'))
            else:
                return redirect(url_for('index'))
        else:
            print "username tidak di temukan"

    return render_template('login.html')



@app.route('/imdata', methods=['POST','GET'])
@read_session
@admin_session
def imdata():
    if request.method == 'POST':
        file = request.files['file-input']
        if file and allowed_file_import(file.filename):
            #simpan file baru
            filename=secure_filename(file.filename)
            path = os.path.join(IMPORT_FOLDER,filename)
            file.save(path)
            #open the workbook and define the worksheet
            book = xlrd.open_workbook(path)
            nm_latih = book.sheet_names()

            try:
                for i in range(len(nm_latih)):
                    if nm_latih[i] == "Daftar Mustahik":
                        sheet = book.sheet_by_name("Daftar Mustahik")
                        #cek excel format
                        if sheet.cell(4,1).value == "Nama" and sheet.cell(4,2).value == "Usia" and sheet.cell(4,3).value == "Penghasilan" and sheet.cell(4,4).value == "Jumlah Tanggungan" and sheet.cell(4,5).value == "Jenis Rumah" and sheet.cell(4,6).value == "Pendidikan" and sheet.cell(4,7).value == "Fasilitas Kesehatan" and sheet.cell(4,8).value == "Ya/Tidak":
                            print "format sesuai "
                            importdata(sheet)
                            return redirect(url_for('view_data_latih_asli'))
                            flash("Format file yang anda upload sesuai","succes")
                        else :
                            print "format tidak sesuai"
                            #print ""+sheet.cell(4,1).value+" "+sheet.cell(4,2).value+" "+sheet.cell(4,3).value+" "+sheet.cell(4,4).value+" "+sheet.cell(4,5).value+" "+sheet.cell(4,6).value+" "+sheet.cell(4,7).value+" "+sheet.cell(4,8).value+""
                            flash("Format file yang anda upload tidak sesuai, silakan cek format file","error")
                            return redirect(url_for('save_test'))
                    else:
                        flash("Format file yang anda upload salah,tidak ditemukan sheet dengan nama : Daftar Mustahik","error")

            except Exception as e:
                 print e
            #hapusfile(IMPORT_FOLDER, filename)
    return render_template('/importdata.html')

@read_session
def importdata(booksheet):
    query = "INSERT INTO tbl_mustahik (id_test,nama_mustahik,x1,x2,x3,x4,x5,x6,c1,c2,k1,k2,k3,k4,k5,k6) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    jml_input = 0
    cc = con
    cursor = cc.cursor()
    id_test = session['id']
    x1_min = 27.0
    x1_max = 80.0
    x2_min = 450000.0
    x2_max = 5000000.0
    x3_min = 1.0
    x3_max = 5.0
    x4_min = 150000000.0
    x4_max = 503000000.0
    x5_min = 1.0
    x5_max = 18.0
    x6_min = 1000000.0
    x6_max = 2500000.0

    #create a loop to iterate through each row in the XLS file
    for r in range(5, booksheet.nrows):
        try:
            nama_mustahik = booksheet.cell(r,1).value,
            a = float(booksheet.cell(r,2).value,)
            b = float(booksheet.cell(r,3).value,)
            c = float(booksheet.cell(r,4).value,)
            d = float(booksheet.cell(r,5).value,)
            e = float(booksheet.cell(r,6).value,)
            f = float(booksheet.cell(r,7).value,)

            c1= "1" if booksheet.cell(r,8).value == "YA" else "0",
            c2= "1" if booksheet.cell(r,8).value == "TIDAK" else "0",
            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            x3= (float(c) - x3_min) / (x3_max-x3_min)
            x4= (x4_max - float(d)) / (x4_max-x4_min)
            x5= (x5_max - float(e)) / (x5_max-x5_min)
            x6= (x6_max - float(f)) / (x6_max-x6_min)


            cursor.execute(query,(str(id_test),nama_mustahik,str(x1),str(x2),str(x3),str(x4),str(x5),str(x6),c1,c2,str(a),str(b),str(c),str(d),str(e),str(f) ))
            cc.commit()

            jml_input += 1

        except Exception as e:
            print e
            print jml_input
    flash(""+str(jml_input)+" Data Mustahik Berhasil Disimpan", "success")




@app.route('/save_test', methods=['POST','GET'])
@admin_session
def save_test():
    c = con
    cursor = c.cursor()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts=0,1,null))'jumlah_latih',count(if(stts=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik on tbl_test.id_test = tbl_mustahik.id_test where status_test='0' group by id_test"
    cursor.execute(query)
    post = cursor.fetchall()
    if request.method == 'POST':
        nama = request.form['name']
        i = 0
        query = "INSERT INTO tbl_test (nama_test,max_iterasi, error, status_test) VALUES (%s,%s,%s,%s)"
        c = con
        cursor = c.cursor()
        print nama
        try:
            cursor.execute(query,(nama,i,i,i))
            c.commit()

            query = "SELECT * from tbl_test WHERE nama_test = '%s'" %(nama)
            cursor.execute(query)
            data = cursor.fetchall()

            if len(data)is 0:
             print "TEST belum terdaftar"
             flash('TEST belum terdaftar','danger')
            else :
                for i in data:
                    if i[1] != "" :
                        session['id']=i[0]
                        print "session ok"
                        return redirect(url_for('imdata'))
                    else:
                        print "session null"
                        return redirect(url_for('save_test'))


            return redirect(url_for('imdata'))

        except Exception as e:
            flash(e,'danger')
            print e

    return render_template('/test.html', post = post)

@app.route('/view_data_latih_asli', methods=['POST','GET'])
@admin_session
@read_session
def view_data_latih_asli():
    cc=con
    cursor = cc.cursor()
    id_test=session['id']
    print session['id']

    qu= "select * from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()

    return render_template('/data_latih_asli.html', post=post)

@app.route('/tambah_data_latih_asli', methods=['POST','GET'])
@admin_session
@read_session
def tambah_data_latih_asli():
    try:
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id']
            print session['id']
            nama= request.form['nama']
            a = request.form['x1']
            b = request.form['x2']
            c = request.form['x3']
            d = request.form['x4']
            e = request.form['x5']
            f = request.form['x6']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
            x2_min = 450000.0
            x2_max = 5000000.0
            x3_min = 1.0
            x3_max = 5.0
            x4_min = 150000000.0
            x4_max = 503000000.0
            x5_min = 1.0
            x5_max = 18.0
            x6_min = 1000000.0
            x6_max = 2500000.0

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            x3= (float(c) - x3_min) / (x3_max-x3_min)
            x4= (x4_max - float(d)) / (x4_max-x4_min)
            x5= (x5_max - float(e)) / (x5_max-x5_min)
            x6= (x6_max - float(f)) / (x6_max-x6_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=0
            query = "INSERT INTO tbl_mustahik (id_test,nama_mustahik,x1,x2,x3,x4,x5,x6,c1,c2,stts,k1,k2,k3,k4,k5,k6) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            print a,b,c,d,e,f, cc
            print x1,x2,x3,x4,x5,x6,c1,c2
            cursor.execute(query,(str(id_test),str(nama),str(x1),str(x2),str(x3),str(x4),str(x5),str(x6),c1,c2,stts,a,b,c,d,e,f))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_latih_asli'))



@app.route('/edit_data_latih_asli/<id>', methods=['POST','GET'])
@admin_session
@read_session
def edit_data_latih_asli(id):
    try:
        id =id
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id']
            print session['id']
            a = request.form['x1']
            b = request.form['x2']
            c = request.form['x3']
            d = request.form['x4']
            e = request.form['x5']
            f = request.form['x6']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
            x2_min = 450000.0
            x2_max = 5000000.0
            x3_min = 1.0
            x3_max = 5.0
            x4_min = 150000000.0
            x4_max = 503000000.0
            x5_min = 1.0
            x5_max = 18.0
            x6_min = 1000000.0
            x6_max = 2500000.0

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            x3= (float(c) - x3_min) / (x3_max-x3_min)
            x4= (x4_max - float(d)) / (x4_max-x4_min)
            x5= (x5_max - float(e)) / (x5_max-x5_min)
            x6= (x6_max - float(f)) / (x6_max-x6_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=0
            query = "Update tbl_mustahik set x1=%s,x2=%s,x3=%s,x4=%s,x5=%s,x6=%s,c1=%s,c2=%s,stts=%s,k1=%s,k2=%s,k3=%s,k4=%s,k5=%s,k6=%s where id_mustahik = %s"
            print a,b,c,d,e,f, cc
            print x1,x2,x3,x4,x5,x6,c1,c2
            cursor.execute(query,(str(x1),str(x2),str(x3),str(x4),str(x5),str(x6),c1,c2,stts,a,b,c,d,e,f, id))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_latih_asli'))


@app.route('/delete_data_latih_asli/<id>', methods=['POST','GET'])
@admin_session
@read_session
def delete_data_latih_asli(id):
    if request.method == 'POST':
        cc=con
        cursor = cc.cursor()
        id=id
        print id

        qu= "delete from tbl_mustahik where id_mustahik = '%s' and stts='0' " %(id)
        cursor.execute(qu)
        cc.commit()

        return redirect(url_for('view_data_latih_asli'))

@app.route('/count_data', methods=['POST','GET'])
@admin_session
@read_session
def count_data():
    cc=con
    cursor = cc.cursor()
    id_test=session['id']
    print session['id']

    qu= "select * from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()


    if request.method=='POST':
        c = con
        cursor = c.cursor()
        id_test = session['id']
        w_input = request.form['w_input']
        iterasi_input = request.form['iterasi_input']
        error_input = request.form['error_input']
        # print id_test
        query = "Select count(id_mustahik) from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
        try:
            cursor.execute(query)
            data = cursor.fetchall()
            for i in data:
                count_data = i[0]

        except Exception as e:
            print e

        c = 2
        #4 angka d blakang koma
        n_rounded = 4
        #make a random number array [a,b]
        miu = np.random.rand(count_data,c)
        #pembulatan 4 angka blakang koma
        x = np.around(miu,n_rounded)
        print "Random Miu"
        print x
        #call def p_cluster
        hitung_fcm(x, iterasi_input, error_input, w_input)
        return redirect(url_for('view_result'))
    return render_template('/data_latih.html', post=post)



@read_session
def hitung_fcm(x, iterasi_input, error_input, w_input):
    c = con
    cursor = c.cursor()
    id_test = session['id']
    #print id_test
    query = "Select x1,x2,x3,x4,x5,x6 from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        #initial list
        att = [1,2,3,4,5,6]
        cluster = [1,2]
        w = int(w_input)
        iterasi = int(iterasi_input)
        error = float(error_input)
        k = 0
        j = 0
        i = 0
        po = 0

        it = 1
        miu = x

        #convert tuple to numpy array
        mus = np.asarray(data)
        p_objecktif = []
        list_mus = mus.tolist()
        print "========================================="
        print "Mustahik"
        a = np.asarray(list_mus)
        # print len(list_mus)
        print a
        for it in range(iterasi+1):
            if it == 0:
                p_objecktif.append(0)
                it+=1
            else:
                print "Iterasi ke-",it
                #mengkuadratkan numpy X ^ w
                miu2 = np.power(miu,w)
                #convert numpy to list
                list_miu2 = miu2.tolist()
                #initial a list
                s=[[] for i in range(len(list_mus))]
                ss=[[] for i in range(len(att))]
                print "========================================="
                print "Miu "
                print "========================================="
                print miu
                print "========================================="
                print "Miu^2"
                print "========================================="
                b = np.asarray(list_miu2)
                # print len(b)
                print b


                #procces
                for i in range(len(list_mus)):
                    for k in range(len(cluster)):
                        for j in range(len(att)):
                            s[i].append(list_mus[i][j] * list_miu2[i][k])
                    #         j=j+1
                    #     k+=1
                    # i+=1
                #back to numpy
                ss = np.asarray(s)
                #sum per colom
                vx = np.sum(ss, axis=0)
                vmiu = np.sum(miu2, axis=0)
                print "========================================="
                #print setiap element x dengan setiap miu
                print " Sum X"
                print "========================================="
                print vx
                print "========================================="
                print " Sum Miu^2"
                print "========================================="
                print vmiu

                vkj = []
                for i in range(len(vmiu)):
                    for j in range(len(vx)):
                        if i == 0 and j <= 5:
                           vkj.append(vx[j] / vmiu[i])
                        elif i == 1 and j>5:
                           vkj.append(vx[j] / vmiu[i])
                cc = np.asarray(vkj)
                new_vkj = cc.reshape(2,6)

                print "========================================="
                print "Pusat Cluster"
                print "========================================="
                ccc = np.asarray(new_vkj)
                print ccc

                p=[[] for i in range(len(list_mus))]

                for i in range(len(list_mus)):
                    for j in range(len(cluster)):
                        for k in range(len(att)):
                            #proses data dikurangi pusat cluster di kuadratkan
                            p[i].append(pow(list_mus[i][k] - new_vkj[j][k], 2))

                aa = len(list_mus*2)
                pp = np.asarray(p)
                ppp = pp.reshape(aa,6)
                p1 = np.around(ppp,4)
                print "========================================="
                print "Hasil F objektif per Cluster"
                print "========================================="
                #sum perbaris
                sum_p1 = np.sum(p1, axis=1)
                sum_p2 = sum_p1.reshape(len(list_mus),2)
                #perkalian c dgn miu2
                fo = np.multiply(sum_p2, b)
                print fo
                print "========================================="
                fo_1 = np.sum(fo, axis=1)
                #sum of fungsi objektif
                fo_2 = np.sum(fo_1, axis=0)
                print "Total fungsi Objectif = ",fo_2
                print "========================================="
                print "Menghitung MIU baru"
                print "========================================="
                print "L"
                print sum_p2
                lt = np.sum(sum_p2, axis=1)
                print "\nLT"
                print lt

                #pembagian antar tiap L dgn LT masing2
                new_miu=[[] for i in range(len(list_mus))]
                for i in range(len(list_mus)):
                    for j in range(len(cluster)):
                        new_miu[i].append(sum_p2[i][j] / lt[i])

                new_miu_2 = np.asarray(new_miu)
                print "========================================="
                print "\n Pembaruan Miu"
                print "========================================="
                print new_miu_2
                res = fo_2 - po
                print "========================================="
                print "Error"
                print "========================================="
                print abs(res)
                print "========================================="
                po = fo_2
                p_objecktif.append(fo_2)
                miu = new_miu_2
                if abs(res) <= error:
                    break
                it+=1
        error = abs(res)
        max_iterasi =len(p_objecktif)
        print max_iterasi
        c_hasil = np.around(miu,0)

        vtvt = ccc.reshape(1,12)
        print vtvt

        #cek sukses
        benar = 0.0
        salah = 0.0
        query="select c1,c2 from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
        cursor.execute(query)
        c.commit()
        cek = cursor.fetchall()
        for j in range(len(list_mus)):
            if c_hasil[j][0] == cek[j][0] and c_hasil[j][1] == cek[j][1]:
                benar +=1.0
            else:
                salah +=1.0
        print benar
        print salah
        print len(list_mus)
        persen = ((benar/float(len(list_mus)))*100.0)
        print persen
        #save result
        query = "UPDATE tbl_test SET max_iterasi = %s, error = %s, sukses=%s, pangkat =%s where id_test = %s"
        cursor.execute(query,((max_iterasi - 1), error,persen, w,  id_test))
        c.commit()

        #save pusat Cluster
        q = "select * from tbl_cluster where id_test=%s" %(id_test)
        cursor.execute(q)
        cluster = cursor.fetchall()
        if cluster == ():
            for i in range(1):
                inp_clus = "insert into tbl_cluster (id_test, v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12) values (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(inp_clus,(id_test, vtvt[i][0],vtvt[i][1],vtvt[i][2],vtvt[i][3],vtvt[i][4],vtvt[i][5],vtvt[i][6],vtvt[i][7],vtvt[i][8],vtvt[i][9],vtvt[i][10],vtvt[i][11]))
                c.commit()

        if cluster != ():
            for i in range(1):
                inp_clus = "update tbl_cluster set v1=%s,v2=%s,v3=%s,v4=%s,v5=%s,v6=%s,v7=%s,v8=%s,v9=%s,v10=%s,v11=%s,v12=%s where id_test = %s"
                cursor.execute(inp_clus,(vtvt[i][0],vtvt[i][1],vtvt[i][2],vtvt[i][3],vtvt[i][4],vtvt[i][5],vtvt[i][6],vtvt[i][7],vtvt[i][8],vtvt[i][9],vtvt[i][10],vtvt[i][11], id_test))
                c.commit()

        #save cluster per mustahik
        query = "select id_mustahik from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
        cursor.execute(query)
        data = cursor.fetchall()

        sql = "select id_mustahik from all_hasil where id_test = '%s' and stts='0' " %(id_test)
        cursor.execute(sql)
        data1 = cursor.fetchall()
        jml = 0
        if data1 == ():
            for i in range(len(list_mus)):
                id_mus = data[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                query = "insert into tbl_hasil (id_mustahik, h_c1, h_c2, miu1, miu2) values (%s, %s, %s, %s, %s)"
                cursor.execute(query,(id_mus, c1,c2,m1,m2))
                c.commit()
                jml+=1
            print jml, "save done"
        elif data1 != ():

            for i in range(len(list_mus)):
                id_mus = data[i]
                id_h_mus = data1[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                if id_mus == id_h_mus:
                    query = "update tbl_hasil set h_c1 =%s, h_c2=%s, miu1=%s, miu2=%s where id_mustahik = %s"
                    cursor.execute(query,( c1,c2,m1, m2, id_mus))
                    c.commit()

                    jml+=1
            print jml, "update done"


    except Exception as e:
        print e


@app.route('/view_result', methods=['POST','GET'])
@read_session
@admin_session
def view_result():
    try:
        id_test = session['id']
        c =con
        cursor = c.cursor()
        query = "SELECT * from all_hasil where id_test = '%s' and stts='0' " %(id_test)
        cursor.execute(query)
        post =  cursor.fetchall()
        print id_test
        sql = "select * from tbl_test where id_test = '"+str(id_test)+"' "
        cursor1 = c.cursor()
        cursor1.execute(sql)
        data = cursor1.fetchall()

        sql = "select * from tbl_test where id_test = '"+str(id_test)+"' "
        cursor1 = c.cursor()
        cursor1.execute(sql)
        data = cursor1.fetchall()


        qu1= "select count(if(stts=0,1,null)) 'datalatih', count(if(stts=1,1,null)) 'datauji' from tbl_mustahik where id_test = '%s' " %(id_test)
        cursor.execute(qu1)
        post1 = cursor.fetchall()

        qu2= "select id_test,stts, count(if(c1=1,1,null)) 'YA', count(if(c2=1,1,null)) 'TIDAK', count(if(h_c1=1,1,null)) 'Program_YA', count(if(h_c2=1,1,null)) 'Program_TIDAK' from all_hasil where id_test = '%s' and stts='0' group by id_test " %(id_test)
        cursor.execute(qu2)
        post2 = cursor.fetchall()

        qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
        cursor.execute(qu3)
        post3 = cursor.fetchall()

        qu4= "select id_test,stts, count(if(c1=1,1,null)) 'YA', count(if(c2=1,1,null)) 'TIDAK', count(if(h_c1=1,1,null)) 'Program_YA', count(if(h_c2=1,1,null)) 'Program_TIDAK' from all_hasil where id_test = '%s' and stts='1' group by id_test " %(id_test)
        cursor.execute(qu4)
        post4 = cursor.fetchall()
        return render_template('/hasil.html',data= data, post = post,post1=post1,post2=post2,post3=post3,post4=post4)

    except Exception as e:
        print e

@app.route('/e_test/<id_test>', methods=['POST','GET'])
@read_session
def e_test(id_test):
    cc=con
    cursor = cc.cursor()
    session['id'] = id_test
    print session['id']
    qu= "select * from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    if post == ():
        return redirect(url_for('imdata'))
    if request.method=='POST':
        id_test=id_test
        session.pop('id', None)
        session['id'] = id_test
        print session['id']
        qu= "select * from tbl_mustahik where id_test = '%s' and stts='0' " %(id_test)
        cursor.execute(qu)
        post = cursor.fetchall()

    return render_template('/data_latih_asli.html', post = post)


@app.route('/delete_test/<id_test>', methods=['POST','GET'])
@read_session
def delete_test(id_test):
    cc=con
    cursor= cc.cursor()
    if request.method=='POST':
        query = "delete from tbl_test where id_test =%s" %(id_test)
        cursor.execute(query)
        cc.commit()
        return redirect(url_for('save_test'))


#UJI DATA
@app.route('/imdata_uji', methods=['POST','GET'])
@read_session
@admin_session
def imdata_uji():
    id_test = session['id']
    c = con
    cursor = c.cursor()
    query ="select * from tbl_test where id_test = %s" %(id_test)
    cursor.execute(query)
    data = cursor.fetchall()

    if request.method == 'POST':
        file = request.files['file-input']
        if file and allowed_file_import(file.filename):
            #simpan file baru
            filename=secure_filename(file.filename)
            path = os.path.join(IMPORT_FOLDER,filename)
            file.save(path)
            #open the workbook and define the worksheet
            book = xlrd.open_workbook(path)
            nm = book.sheet_names()
            print nm[0]
            try:
                for i in range(len(nm)):
                    if nm[i] == "Daftar Uji Mustahik":
                        sheet = book.sheet_by_name("Daftar Uji Mustahik")
                        #cek excel format
                        if sheet.cell(4,1).value == "Nama" and sheet.cell(4,2).value == "Usia" and sheet.cell(4,3).value == "Penghasilan" and sheet.cell(4,4).value == "Jumlah Tanggungan" and sheet.cell(4,5).value == "Jenis Rumah" and sheet.cell(4,6).value == "Pendidikan" and sheet.cell(4,7).value == "Fasilitas Kesehatan" and sheet.cell(4,8).value == "Ya/Tidak":
                            print " format sesuai "
                            qu = "select max_iterasi from tbl_test where id_test = '%s'"%(id_test)
                            cursor1 = c.cursor()
                            cursor1.execute(qu)
                            data1 = cursor1.fetchall()
                            print "data1 adalah",data1[0][0]
                            if data1[0][0] == 0:
                                flash("Data Latih Belum Dilakukan","error")
                            elif data1[0][0] != 0:
                                que = "select count(id_mustahik) from tbl_mustahik where id_test = '%s' and stts = '1' "%(id_test)
                                cursor2 = c.cursor()
                                cursor2.execute(que)
                                data2 = cursor2.fetchall()
                                print "banyak data mustahik", data2[0][0]
                                for i in range(int(data2[0][0])):
                                    quer = "delete from tbl_mustahik where id_test = '%s' and stts = '1'"%(id_test)
                                    cursor3 = c.cursor()
                                    cursor3.execute(quer)
                                    c.commit()

                                importdata_uji(sheet)
                                id = session['id']
                                return redirect(url_for('view_data_uji_asli'))

                                flash("Format file yang anda upload sesuai","succes")
                        else:
                            print "format tidak sesuai"
                            #print ""+sheet.cell(4,1).value+" "+sheet.cell(4,2).value+" "+sheet.cell(4,3).value+" "+sheet.cell(4,4).value+" "+sheet.cell(4,5).value+" "+sheet.cell(4,6).value+" "+sheet.cell(4,7).value+" "+sheet.cell(4,8).value+""
                            flash("Format file yang anda upload tidak sesuai, silakan cek format file","error")
                    else:
                        flash("Format file yang anda upload salah,tidak ditemukan sheet dengan nama : Daftar Mustahik Uji","error")


            except Exception as e:
                print e

            #hapusfile(IMPORT_FOLDER, filename)
    return render_template('/importdatauji.html', post = data)


@read_session
def importdata_uji(booksheet):
    query = "INSERT INTO tbl_mustahik (id_test,nama_mustahik, x1,x2,x3,x4,x5,x6,c1,c2, stts, k1, k2,k3, k4, k5, k6) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    jml_input = 0
    c = con
    cursor = c.cursor()
    id_test = session['id']
    x1_min = 27.0
    x1_max = 80.0
    x2_min = 450000.0
    x2_max = 5000000.0
    x3_min = 1.0
    x3_max = 5.0
    x4_min = 150000000.0
    x4_max = 503000000.0
    x5_min = 1.0
    x5_max = 18.0
    x6_min = 1000000.0
    x6_max = 2500000.0
    #create a loop to iterate through each row in the XLS file
    for r in range(5, booksheet.nrows):
        try:
            nama_mustahik = booksheet.cell(r,1).value,
            x1= float((booksheet.cell(r,2).value) - x1_min) / (x1_max-x1_min),
            x2= float(x2_max - (booksheet.cell(r,3).value)) / (x2_max-x2_min),
            x3= float((booksheet.cell(r,4).value) - x3_min) / (x3_max-x3_min),
            x4= float(x4_max - (booksheet.cell(r,5).value)) / (x4_max-x4_min),
            x5= float(x5_max - (booksheet.cell(r,6).value)) / (x5_max-x5_min),
            x6= float(x6_max - (booksheet.cell(r,7).value)) / (x6_max-x6_min),
            c1= "1" if booksheet.cell(r,8).value == "YA" else "0",
            c2= "1" if booksheet.cell(r,8).value == "TIDAK" else "0",
            status = 1

            cursor.execute(query,(id_test,nama_mustahik,x1,x2,x3,x4,x5,x6,c1,c2,status,booksheet.cell(r,2).value,booksheet.cell(r,3).value,booksheet.cell(r,4).value,booksheet.cell(r,5).value,booksheet.cell(r,6).value,booksheet.cell(r,7).value))
            c.commit()

            jml_input += 1

        except Exception as e:
            print e
            print jml_input
    flash(""+str(jml_input)+" Data Uji Mustahik Berhasil Disimpan", "success")

@app.route('/view_data_uji_asli', methods=['POST','GET'])
@admin_session
@read_session
def view_data_uji_asli():
    cc=con
    cursor = cc.cursor()
    id_test=session['id']
    print session['id']

    qu= "select * from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()



    return render_template('/data_uji_asli.html', post=post)


@app.route('/tambah_data_uji_asli', methods=['POST','GET'])
@admin_session
@read_session
def tambah_data_uji_asli():
    try:
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id']
            print session['id']
            nama= request.form['nama']
            a = request.form['x1']
            b = request.form['x2']
            c = request.form['x3']
            d = request.form['x4']
            e = request.form['x5']
            f = request.form['x6']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
            x2_min = 450000.0
            x2_max = 5000000.0
            x3_min = 1.0
            x3_max = 5.0
            x4_min = 150000000.0
            x4_max = 503000000.0
            x5_min = 1.0
            x5_max = 18.0
            x6_min = 1000000.0
            x6_max = 2500000.0

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            x3= (float(c) - x3_min) / (x3_max-x3_min)
            x4= (x4_max - float(d)) / (x4_max-x4_min)
            x5= (x5_max - float(e)) / (x5_max-x5_min)
            x6= (x6_max - float(f)) / (x6_max-x6_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=1
            query = "INSERT INTO tbl_mustahik (id_test,nama_mustahik,x1,x2,x3,x4,x5,x6,c1,c2,stts,k1,k2,k3,k4,k5,k6) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            print a,b,c,d,e,f, cc
            print x1,x2,x3,x4,x5,x6,c1,c2
            cursor.execute(query,(str(id_test),str(nama),str(x1),str(x2),str(x3),str(x4),str(x5),str(x6),c1,c2,stts,a,b,c,d,e,f))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_uji_asli'))



@app.route('/edit_data_uji_asli/<id>', methods=['POST','GET'])
@admin_session
@read_session
def edit_data_uji_asli(id):
    try:
        id =id
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id']
            print session['id']
            a = request.form['x1']
            b = request.form['x2']
            c = request.form['x3']
            d = request.form['x4']
            e = request.form['x5']
            f = request.form['x6']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
            x2_min = 450000.0
            x2_max = 5000000.0
            x3_min = 1.0
            x3_max = 5.0
            x4_min = 150000000.0
            x4_max = 503000000.0
            x5_min = 1.0
            x5_max = 18.0
            x6_min = 1000000.0
            x6_max = 2500000.0

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            x3= (float(c) - x3_min) / (x3_max-x3_min)
            x4= (x4_max - float(d)) / (x4_max-x4_min)
            x5= (x5_max - float(e)) / (x5_max-x5_min)
            x6= (x6_max - float(f)) / (x6_max-x6_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=1
            query = "Update tbl_mustahik set x1=%s,x2=%s,x3=%s,x4=%s,x5=%s,x6=%s,c1=%s,c2=%s,stts=%s,k1=%s,k2=%s,k3=%s,k4=%s,k5=%s,k6=%s where id_mustahik = %s"
            print a,b,c,d,e,f, cc
            print x1,x2,x3,x4,x5,x6,c1,c2
            cursor.execute(query,(str(x1),str(x2),str(x3),str(x4),str(x5),str(x6),c1,c2,stts,a,b,c,d,e,f, id))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_uji_asli'))


@app.route('/delete_data_uji_asli/<id>', methods=['POST','GET'])
@admin_session
@read_session
def delete_data_uji_asli(id):
    if request.method == 'POST':
        cc=con
        cursor = cc.cursor()
        id=id
        print id

        qu= "delete from tbl_mustahik where id_mustahik = '%s' and stts='1' " %(id)
        cursor.execute(qu)
        cc.commit()

        return redirect(url_for('view_data_uji_asli'))


@app.route('/count_data_uji', methods=['POST','GET'])
@read_session
@admin_session
def count_data_uji():
    cc=con
    cursor = cc.cursor()
    id_test = session['id']
    print session['id']
    qu1= "select count(if(stts=0,1,null)) 'datalatih', count(if(stts=1,1,null)) 'datauji' from tbl_mustahik where id_test = '%s' " %(id_test)
    cursor.execute(qu1)
    post1 = cursor.fetchall()

    qu2= "select id_test,stts, count(if(c1=1,1,null)) 'YA', count(if(c2=1,1,null)) 'TIDAK', count(if(h_c1=1,1,null)) 'Program_YA', count(if(h_c2=1,1,null)) 'Program_TIDAK' from all_hasil where id_test = '%s' and stts='0' group by id_test " %(id_test)
    cursor.execute(qu2)
    post2 = cursor.fetchall()

    qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
    cursor.execute(qu3)
    post3 = cursor.fetchall()




    qu= "select * from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    if post == ():
        flash("Mohon maaf,, Data Uji anda kosong....","error")
    elif post != ():
        try:
           if request.method=='POST':
                query = "Select count(id_mustahik) from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
                try:
                    cursor.execute(query)
                    data = cursor.fetchall()
                    for i in data:
                        count_data = i[0]

                except Exception as e:
                    print e

                c = 2
                #4 angka d blakang koma
                n_rounded = 4
                #make a random number array [a,b]
                miu = np.random.rand(count_data,c)
                #pembulatan 4 angka blakang koma
                x = np.around(miu,n_rounded)

                #select pusat cluster data latih
                sql="select v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_cluster where id_test = '%s' " %(id_test)
                cursor.execute(sql)
                miu = cursor.fetchall()
                bts = np.asarray(miu)
                list_bts = []
                for i in range(1):
                    list_bts.insert(i, bts[i])

                np_v = np.asarray(list_bts)
                vkj = np_v.reshape(2,6)
                print vkj
                p_cluster_uji(x, vkj)
                return redirect(url_for('view_result_uji'))
        except Exception as e:
            print e

    return render_template('/data_uji.html',post1=post1,post2=post2, post3=post3, post = post)



@read_session
def p_cluster_uji(x, vkj):
    c = con
    cursor = c.cursor()
    id_test = session['id']
    #print id_test
    query = "Select x1,x2,x3,x4,x5,x6 from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        #initial list
        att = [1,2,3,4,5,6]
        cluster = [1,2]
        qu = " select pangkat from tbl_test where id_test=%s" %(id_test)
        cursor.execute(qu)
        pngkt = cursor.fetchall()
        print "pangkat",pngkt[0][0]
        w = pngkt[0][0]
        k = 0
        j = 0
        i = 0
        po = 0

        miu = x

        #convert tuple to numpy array
        mus = np.asarray(data)
        p_objecktif = []
        list_mus = mus.tolist()
        print "========================================="
        print "Mustahik"
        a = np.asarray(list_mus)
        # print len(list_mus)
        print a
        #mengkuadratkan numpy X ^ w
        miu2 = np.power(miu,w)
        #convert numpy to list
        list_miu2 = miu2.tolist()
        #initial a list
        s=[[] for i in range(len(list_mus))]
        ss=[[] for i in range(len(att))]
        print "========================================="
        print "Miu "
        print "========================================="
        print miu
        print "========================================="
        print "Miu^2"
        print "========================================="
        b = np.asarray(list_miu2)
        # print len(b)
        print b


        #procces
        for i in range(len(list_mus)):
            for k in range(len(cluster)):
                for j in range(len(att)):
                    s[i].append(list_mus[i][j] * list_miu2[i][k])
            #         j=j+1
            #     k+=1
            # i+=1
        #back to numpy
        ss = np.asarray(s)
        #sum per colom
        vx = np.sum(ss, axis=0)
        vmiu = np.sum(miu2, axis=0)
        print "========================================="
        #print setiap element x dengan setiap miu
        print " Sum X"
        print "========================================="
        print vx
        print "========================================="
        print " Sum Miu^2"
        print "========================================="
        print vmiu
        #print setiap element x dengan setiap miu
        print "========================================="
        print "Pusat Cluster dari Data latih"
        print "========================================="
        new_vkj = vkj
        ccc = np.asarray(new_vkj)
        print ccc
        print "========================================="
        print "Hasil F objektif per Cluster"
        print "========================================="

        p=[[] for i in range(len(list_mus))]

        for i in range(len(list_mus)):
            for j in range(len(cluster)):
                for k in range(len(att)):
                    #proses data dikurangi pusat cluster di kuadratkan
                    p[i].append(pow(list_mus[i][k] - new_vkj[j][k], 2))

        aa = len(list_mus*2)
        pp = np.asarray(p)
        ppp = pp.reshape(aa,6)
        p1 = np.around(ppp,4)
        #sum perbaris
        sum_p1 = np.sum(p1, axis=1)
        sum_p2 = sum_p1.reshape(len(list_mus),2)
        #perkalian c dgn miu2
        fo = np.multiply(sum_p2, b)
        print fo
        print "========================================="
        fo_1 = np.sum(fo, axis=1)
        #sum of fungsi objektif
        fo_2 = np.sum(fo_1, axis=0)
        print "Total fungsi Objectif = ",fo_2
        print "========================================="
        print "Menghitung MIU baru"
        print "========================================="
        print "L"
        print sum_p2
        lt = np.sum(sum_p2, axis=1)
        print "\nLT"
        print lt

        #pembagian antar tiap L dgn LT masing2
        new_miu=[[] for i in range(len(list_mus))]
        for i in range(len(list_mus)):
            for j in range(len(cluster)):
                new_miu[i].append(sum_p2[i][j] / lt[i])

        new_miu_2 = np.asarray(new_miu)
        print "========================================="
        print "\n Pembaruan Miu"
        print "========================================="
        print new_miu_2
        res = fo_2 - po
        print "========================================="
        print "Error"
        print "========================================="
        print abs(res)
        print "========================================="
        po = fo_2
        p_objecktif.append(fo_2)
        error = abs(res)
        max_iterasi =len(p_objecktif)
        print max_iterasi
        c_hasil = np.around(new_miu_2,0)

        #cek sukses
        benar = 0.0
        query="select c1 from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
        cursor.execute(query)
        c.commit()
        cek = cursor.fetchall()
        #cek satu2 sesuai antara manual dan program
        for j in range(len(list_mus)):
            if c_hasil[j][0] == cek[j]:
                benar +=1.0
        print benar
        print len(list_mus)
        persen = ((benar/float(len(list_mus)))*100.0)
        print persen
        #save result
        query = "UPDATE tbl_test SET  error_uji = %s, sukses_uji=%s where id_test = %s"
        cursor.execute(query,(error,persen, id_test))
        c.commit()



        #save cluster per mustahik
        query = "select id_mustahik from tbl_mustahik where id_test = '%s' and stts='1' " %(id_test)
        cursor.execute(query)
        data = cursor.fetchall()

        sql = "select id_mustahik from all_hasil where id_test = '%s' and stts='1' " %(id_test)
        cursor.execute(sql)
        data1 = cursor.fetchall()
        jml = 0
        if data1 == ():
            for i in range(len(list_mus)):
                id_mus = data[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                if (c1>=c2):
                    c1=1
                    c2=0
                elif(c2>=c1):
                    c1=0
                    c2=1
                m1 = miu[i][0]
                m2 = miu[i][1]
                query = "insert into tbl_hasil (id_mustahik, h_c1, h_c2, miu1, miu2) values (%s, %s, %s, %s, %s)"
                cursor.execute(query,(id_mus, c1,c2,m1,m2))
                c.commit()
                jml+=1
            print jml, "save done"
        elif data1 != ():

            for i in range(len(list_mus)):
                id_mus = data[i]
                id_h_mus = data1[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                if id_mus == id_h_mus:
                    query = "update tbl_hasil set h_c1 =%s, h_c2=%s, miu1=%s, miu2=%s where id_mustahik = %s"
                    cursor.execute(query,( c1,c2,m1, m2, id_mus))
                    c.commit()

                    jml+=1
            print jml, "update done"


    except Exception as e:
        print e

@app.route('/view_result_uji', methods=['POST','GET'])
@read_session
@admin_session
def view_result_uji():
    try:
        id_test = session['id']
        c =con
        cursor = c.cursor()
        query = "SELECT * from all_hasil where id_test = '%s' and stts='1' " %(id_test)
        cursor.execute(query)
        post =  cursor.fetchall()
        print id_test
        sql = "select * from tbl_test where id_test = '"+str(id_test)+"' "
        cursor1 = c.cursor()
        cursor1.execute(sql)
        data = cursor1.fetchall()


        qu1= "select count(if(stts=0,1,null)) 'datalatih', count(if(stts=1,1,null)) 'datauji' from tbl_mustahik where id_test = '%s' " %(id_test)
        cursor.execute(qu1)
        post1 = cursor.fetchall()

        qu2= "select id_test,stts, count(if(c1=1,1,null)) 'YA', count(if(c2=1,1,null)) 'TIDAK', count(if(h_c1=1,1,null)) 'Program_YA', count(if(h_c2=1,1,null)) 'Program_TIDAK' from all_hasil where id_test = '%s' and stts='0' group by id_test " %(id_test)
        cursor.execute(qu2)
        post2 = cursor.fetchall()

        qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
        cursor.execute(qu3)
        post3 = cursor.fetchall()

        qu4= "select id_test,stts, count(if(c1=1,1,null)) 'YA', count(if(c2=1,1,null)) 'TIDAK', count(if(h_c1=1,1,null)) 'Program_YA', count(if(h_c2=1,1,null)) 'Program_TIDAK' from all_hasil where id_test = '%s' and stts='1' group by id_test " %(id_test)
        cursor.execute(qu4)
        post4 = cursor.fetchall()

        return render_template('/hasil_uji.html',post1 =post1, post2=post2, post3=post3,post4=post4, data= data, post = post)

    except Exception as e:
        print e






#weka

def read_session_weka(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        session.permanent = True
        try:

            if session['id_weka'] is False:
                flash('TEST is invalid')
                return redirect(url_for('save_test_weka'))
            return f(*args, **kwargs)
        except KeyError:
            flash('Your Session is time out, login first')
            return redirect(url_for('save_test_weka'))
    return wrap


@app.route('/weka', methods=['POST','GET'])
@read_session_weka
def weka():

    return render_template('/weka/homepage_weka.html')



@app.route('/imdata_weka', methods=['POST','GET'])
@read_session_weka
def imdata_weka():
    if request.method == 'POST':
        file = request.files['file-input']
        if file and allowed_file_import(file.filename):
            #simpan file baru
            filename=secure_filename(file.filename)
            path = os.path.join(IMPORT_FOLDER,filename)
            file.save(path)
            #open the workbook and define the worksheet
            book = xlrd.open_workbook(path)
            nm_latih = book.sheet_names()

            try:
                for i in range(len(nm_latih)):
                    if nm_latih[i] == "Daftar Mustahik Weka":
                        sheet = book.sheet_by_name("Daftar Mustahik Weka")
                        #cek excel format
                        if sheet.cell(4,1).value == "Nama" and sheet.cell(4,2).value == "Usia" and sheet.cell(4,3).value == "Penghasilan" and sheet.cell(4,4).value == "Ya/Tidak":
                            print " format sesuai "
                            importdata_weka(sheet)
                            return redirect(url_for('view_data_latih_asli_weka'))
                            flash("Format file yang anda upload sesuai","succes")
                        else :
                            print "format tidak sesuai"
                            #print ""+sheet.cell(4,1).value+" "+sheet.cell(4,2).value+" "+sheet.cell(4,3).value+" "+sheet.cell(4,4).value+" "+sheet.cell(4,5).value+" "+sheet.cell(4,6).value+" "+sheet.cell(4,7).value+" "+sheet.cell(4,8).value+""
                            flash("Format file yang anda upload tidak sesuai, silakan cek format file","error")
                            return redirect(url_for('save_test_weka'))
                    else:
                        flash("Format file yang anda upload salah,tidak ditemukan sheet dengan nama : Daftar Mustahik Weka","error")

            except Exception as e:
                 print e
            #hapusfile(IMPORT_FOLDER, filename)
    return render_template('/weka/importdata_weka.html')

@read_session_weka
def importdata_weka(booksheet):
    query = "INSERT INTO tbl_mustahik_weka (id_test,nama_mustahik_weka, x1_weka,x2_weka,c1_weka,c2_weka,k1_weka,k2_weka) VALUE (%s,%s,%s,%s,%s,%s,%s,%s)"
    jml_input = 0
    c = con
    cursor = c.cursor()
    id_test = session['id_weka']
    x1_min = 27.0
    x1_max = 80.0
    x2_min = 450000.0
    x2_max = 5000000.0
    #create a loop to iterate through each row in the XLS file
    for r in range(5, booksheet.nrows):
        try:
            nama_mustahik = booksheet.cell(r,1).value,
            a = float(booksheet.cell(r,2).value,)
            b = float(booksheet.cell(r,3).value,)
            c1= "1" if booksheet.cell(r,4).value == "YA" else "0",
            c2= "1" if booksheet.cell(r,4).value == "TIDAK" else "0",

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)

            cursor.execute(query,(str(id_test),nama_mustahik, str(x1),str(x2),c1,c2,str(a),str(b)))
            c.commit()

            jml_input += 1

        except Exception as e:
            print e
            print jml_input
    flash(""+str(jml_input)+" Data Mustahik Berhasil Disimpan", "success")




@app.route('/save_test_weka', methods=['POST','GET'])
def save_test_weka():
    c = con
    cursor = c.cursor()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts_weka=0,1,null))'jumlah_latih',count(if(stts_weka=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik_weka on tbl_test.id_test = tbl_mustahik_weka.id_test where status_test='1' group by id_test"
    cursor.execute(query)
    post = cursor.fetchall()
    if request.method == 'POST':
        nama = request.form['name']
        i = 0
        j = 1
        query = "INSERT INTO tbl_test (nama_test,max_iterasi, error, status_test) VALUES (%s,%s,%s,%s)"
        c = con
        cursor = c.cursor()
        print nama
        try:
            cursor.execute(query,(nama,i,i,j))
            c.commit()

            query = "SELECT * from tbl_test WHERE nama_test = '%s'" %(nama)
            cursor.execute(query)
            data = cursor.fetchall()

            if len(data)is 0:
             print "TEST belum terdaftar"
             flash('TEST belum terdaftar','danger')
            else :
                for i in data:
                    if i[1] != "" :
                        session['id_weka']=i[0]
                        print "session ok"
                        return redirect(url_for('imdata_weka'))
                    else:
                        print "session null"
                        return redirect(url_for('save_test_weka'))


            return redirect(url_for('imdata_weka'))

        except Exception as e:
            flash(e,'danger')
            print e

    return render_template('/weka/test_weka.html', post = post)


@app.route('/view_data_latih_asli_weka', methods=['POST','GET'])
@admin_session
@read_session_weka
def view_data_latih_asli_weka():
    cc=con
    cursor = cc.cursor()
    id_test=session['id_weka']
    print session['id_weka']

    qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    return render_template('/weka/data_asli_weka.html', post=post)

@app.route('/tambah_data_latih_asli_weka', methods=['POST','GET'])
@admin_session
@read_session_weka
def tambah_data_latih_asli_weka():
    try:
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id_weka']
            print session['id_weka']
            nama= request.form['nama']
            a = request.form['x1']
            b = request.form['x2']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
            x2_min = 450000.0
<<<<<<< HEAD
            x2_max = 3200000.0

=======
            x2_max = 5000000.0
        
>>>>>>> df9bf9b411b8adb66db02e897e702a74892163df
            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=0
            query = "INSERT INTO tbl_mustahik_weka (id_test,nama_mustahik_weka,x1_weka,x2_weka,c1_weka,c2_weka,stts_weka,k1_weka,k2_weka) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            print a,b, cc
            print x1,x2,c1,c2
            cursor.execute(query,(str(id_test),str(nama),str(x1),str(x2),c1,c2,stts,a,b,))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_latih_asli_weka'))



@app.route('/edit_data_latih_asli_weka/<id>', methods=['POST','GET'])
@admin_session
@read_session_weka
def edit_data_latih_asli_weka(id):
    try:
        id =id
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id_weka']
            print session['id_weka']
            a = request.form['x1']
            b = request.form['x2']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
<<<<<<< HEAD
            x2_min = 700000.0
            x2_max = 3200000.0

=======
            x2_min = 450000.0
            x2_max = 5000000.0
        
>>>>>>> df9bf9b411b8adb66db02e897e702a74892163df
            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=0
            query = "Update tbl_mustahik_weka set x1_weka=%s,x2_weka=%s,c1_weka=%s,c2_weka=%s,stts_weka=%s,k1_weka=%s,k2_weka=%s where id_mustahik_weka = %s"
            print a,b, cc
            print x1,x2,c1,c2
            cursor.execute(query,(str(x1),str(x2),c1,c2,stts,a,b, id))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_latih_asli_weka'))


@app.route('/delete_data_latih_asli_weka/<id>', methods=['POST','GET'])
@admin_session
@read_session_weka
def delete_data_latih_asli_weka(id):
    if request.method == 'POST':
        cc=con
        cursor = cc.cursor()
        id=id
        print id

        qu= "delete from tbl_mustahik_weka where id_mustahik_weka = '%s' and stts_weka='0' " %(id)
        cursor.execute(qu)
        cc.commit()

        return redirect(url_for('view_data_latih_asli_weka'))


@app.route('/count_data_weka', methods=['POST','GET'])
@read_session_weka
def count_data_weka():
    cc=con
    cursor = cc.cursor()
    id_test=session['id_weka']
    print session['id_weka']
    qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    if request.method=='POST':
        c = con
        cursor = c.cursor()
        id_test = session['id_weka']
        w_input = request.form['w_input']
        iterasi_input = request.form['iterasi_input']
        error_input = request.form['error_input']
        # print id_test
        query = "Select count(id_mustahik_weka) from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        try:
            cursor.execute(query)
            data = cursor.fetchall()
            for i in data:
                count_data = i[0]

        except Exception as e:
            print e

        c = 2
        #4 angka d blakang koma
        n_rounded = 4
        #make a random number array [a,b]
        miu = np.random.rand(count_data,c)
        #pembulatan 4 angka blakang koma
        x = np.around(miu,n_rounded)
        print "Random Miu"
        print x
        #call def p_cluster
        p_cluster_weka(x, iterasi_input, error_input, w_input)
        return redirect(url_for('view_result_weka'))
    return render_template('/weka/data_latih_weka.html', post=post)



@read_session_weka
def p_cluster_weka(x, iterasi_input, error_input, w_input):
    c = con
    cursor = c.cursor()
    id_test = session['id_weka']
    #print id_test
    query = "Select x1_weka,x2_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        #initial list
        att = [1,2]
        cluster = [1,2]
        k = 0
        j = 0
        i = 0
        po = 0
        w = int(w_input)
        iterasi = int(iterasi_input)
        error = float(error_input)
        it = 1
        miu = x

        #convert tuple to numpy array
        mus = np.asarray(data)
        p_objecktif = []
        list_mus = mus.tolist()
        print "========================================="
        print "Mustahik"
        a = np.asarray(list_mus)
        # print len(list_mus)
        print a
        for it in range(iterasi+1):
            if it == 0:
                p_objecktif.append(0)
                it+=1
            else:
                print "Iterasi ke-",it
                #mengkuadratkan numpy X ^ w
                miu2 = np.power(miu,w)
                #convert numpy to list
                list_miu2 = miu2.tolist()
                #initial a list
                s=[[] for i in range(len(list_mus))]
                ss=[[] for i in range(len(att))]
                print "========================================="
                print "Miu "
                print "========================================="
                print miu
                print "========================================="
                print "Miu^2"
                print "========================================="
                b = np.asarray(list_miu2)
                # print len(b)
                print b


                #procces
                for i in range(len(list_mus)):
                    for k in range(len(cluster)):
                        for j in range(len(att)):
                            s[i].append(list_mus[i][j] * list_miu2[i][k])
                    #         j=j+1
                    #     k+=1
                    # i+=1
                #back to numpy
                ss = np.asarray(s)
                #sum per colom
                vx = np.sum(ss, axis=0)
                vmiu = np.sum(miu2, axis=0)
                print "========================================="
                #print setiap element x dengan setiap miu
                print " Sum X"
                print "========================================="
                print vx
                print "========================================="
                print " Sum Miu^2"
                print "========================================="
                print vmiu

                vkj = []
                for i in range(len(vmiu)):
                    for j in range(len(vx)):
                        if i == 0 and j <= 1:
                           vkj.append(vx[j] / vmiu[i])
                        elif i == 1 and j>1:
                           vkj.append(vx[j] / vmiu[i])
                cc = np.asarray(vkj)
                new_vkj = cc.reshape(2,2)

                print "========================================="
                print "Pusat Cluster"
                print "========================================="
                ccc = np.asarray(new_vkj)
                print ccc

                p=[[] for i in range(len(list_mus))]

                for i in range(len(list_mus)):
                    for j in range(len(cluster)):
                        for k in range(len(att)):
                            #proses data dikurangi pusat cluster di kuadratkan
                            p[i].append(pow(list_mus[i][k] - new_vkj[j][k], 2))

                aa = len(list_mus*2)
                pp = np.asarray(p)
                ppp = pp.reshape(aa,2)
                p1 = np.around(ppp,4)
                print "========================================="
                print "Hasil F objektif per Cluster"
                print "========================================="
                #sum perbaris
                sum_p1 = np.sum(p1, axis=1)
                sum_p2 = sum_p1.reshape(len(list_mus),2)
                #perkalian c dgn miu2
                fo = np.multiply(sum_p2, b)
                print fo
                print "========================================="
                fo_1 = np.sum(fo, axis=1)
                #sum of fungsi objektif
                fo_2 = np.sum(fo_1, axis=0)
                print "Total fungsi Objectif = ",fo_2
                print "========================================="
                print "Menghitung MIU baru"
                print "========================================="
                print "L"
                print sum_p2
                lt = np.sum(sum_p2, axis=1)
                print "\nLT"
                print lt

                #pembagian antar tiap L dgn LT masing2
                new_miu=[[] for i in range(len(list_mus))]
                for i in range(len(list_mus)):
                    for j in range(len(cluster)):
                        new_miu[i].append(sum_p2[i][j] / lt[i])

                new_miu_2 = np.asarray(new_miu)
                print "========================================="
                print "\n Pembaruan Miu"
                print "========================================="
                print new_miu_2
                res = fo_2 - po
                print "========================================="
                print "Error"
                print "========================================="
                print abs(res)
                print "========================================="
                po = fo_2
                p_objecktif.append(fo_2)
                miu = new_miu_2
                if abs(res) <= error:
                    break
                it+=1
        error = abs(res)
        max_iterasi =len(p_objecktif)
        print max_iterasi
        c_hasil = np.around(miu,0)
        vtvt = ccc.reshape(1,4)
        print vtvt

        #cek sukses
        benar = 0.0
        query="select c1_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        cursor.execute(query)
        c.commit()
        cek = cursor.fetchall()
        for j in range(len(list_mus)):
            if c_hasil[j][0] == cek[j]:
                benar +=1.0
        print benar
        print len(list_mus)
        persen = ((benar/float(len(list_mus)))*100.0)
        print persen
        #save result
        query = "UPDATE tbl_test SET max_iterasi = %s, error = %s, sukses=%s, pangkat=%s where id_test = %s"
        cursor.execute(query,((max_iterasi - 1), error,persen, w, id_test))
        c.commit()

        #save pusat Cluster
        q = "select * from tbl_cluster where id_test=%s" %(id_test)
        cursor.execute(q)
        cluster = cursor.fetchall()
        print cluster
        nn=0.0
        if cluster == ():
            for i in range(1):
                inp_clus = "insert into tbl_cluster (id_test, v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12) values (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(inp_clus,(id_test, vtvt[i][0],vtvt[i][1],vtvt[i][2],vtvt[i][3],nn,nn,nn,nn,nn,nn,nn,nn))
                c.commit()

        if cluster != ():
            for i in range(1):
                inp_clus = "update tbl_cluster set v1=%s,v2=%s,v3=%s,v4=%s,v5=%s,v6=%s,v7=%s,v8=%s,v9=%s,v10=%s,v11=%s,v12=%s where id_test = %s"
                cursor.execute(inp_clus,(vtvt[i][0],vtvt[i][1],vtvt[i][2],vtvt[i][3],nn,nn,nn,nn,nn,nn,nn,nn, id_test))
                c.commit()



        #save cluster per mustahik
        query = "select id_mustahik_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        cursor.execute(query)
        data = cursor.fetchall()

        sql = "select id_mustahik_weka from all_hasil_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        cursor.execute(sql)
        data1 = cursor.fetchall()
        jml = 0
        if data1 == ():
            for i in range(len(list_mus)):
                id_mus = data[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                query = "insert into tbl_hasil_weka (id_mustahik_weka, h_c1_weka, h_c2_weka, miu1_weka, miu2_weka) values (%s, %s, %s, %s, %s)"
                cursor.execute(query,(id_mus, c1,c2,m1,m2))
                c.commit()
                jml+=1
            print jml, "save done"
        elif data1 != ():

            for i in range(len(list_mus)):
                id_mus = data[i]
                id_h_mus = data1[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                if id_mus == id_h_mus:
                    query = "update tbl_hasil_weka set h_c1_weka =%s, h_c2_weka=%s, miu1_weka=%s, miu2_weka=%s where id_mustahik_weka = %s"
                    cursor.execute(query,( c1,c2,m1, m2, id_mus))
                    c.commit()

                    jml+=1
            print jml, "update done"


    except Exception as e:
        print e


@app.route('/view_result_weka', methods=['POST','GET'])
@read_session_weka
def view_result_weka():
    try:
        id_test = session['id_weka']
        c =con
        cursor = c.cursor()
        query = "SELECT * from all_hasil_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        cursor.execute(query)
        post =  cursor.fetchall()
        print id_test
        sql = "select * from tbl_test where id_test = '"+str(id_test)+"' "
        cursor1 = c.cursor()
        cursor1.execute(sql)
        data = cursor1.fetchall()


        qu1= "select count(if(stts_weka=0,1,null)) 'datalatih', count(if(stts_weka=1,1,null)) 'datauji' from tbl_mustahik_weka where id_test = '%s' " %(id_test)
        cursor.execute(qu1)
        post1 = cursor.fetchall()

        qu2= "select id_test,stts_weka, count(if(c1_weka=1,1,null)) 'YA', count(if(c2_weka=1,1,null)) 'TIDAK', count(if(h_c1_weka=1,1,null)) 'Program_YA', count(if(h_c2_weka=1,1,null)) 'Program_TIDAK' from all_hasil_weka where id_test = '%s' and stts_weka='0' group by id_test " %(id_test)
        cursor.execute(qu2)
        post2 = cursor.fetchall()

        qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
        cursor.execute(qu3)
        post3 = cursor.fetchall()

        qu4= "select id_test,stts_weka, count(if(c1_weka=1,1,null)) 'YA', count(if(c2_weka=1,1,null)) 'TIDAK', count(if(h_c1_weka=1,1,null)) 'Program_YA', count(if(h_c2_weka=1,1,null)) 'Program_TIDAK' from all_hasil_weka where id_test = '%s' and stts_weka='1' group by id_test " %(id_test)
        cursor.execute(qu4)
        post4 = cursor.fetchall()
        return render_template('/weka/hasil_weka.html',post1=post1, post2=post2, post3 =post3,post4= post4,data= data, post = post)

    except Exception as e:
        print e

@app.route('/e_test_weka/<id_test>', methods=['POST','GET'])
@read_session_weka
def e_test_weka(id_test):
    cc=con
    cursor = cc.cursor()
    session['id_weka'] = id_test
    print session['id_weka']
    qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    if post == ():
        return redirect(url_for('imdata_weka'))
    if request.method=='POST':
        id_test=id_test
        session.pop('id_weka', None)
        session['id_weka'] = id_test
        print session['id_weka']
        qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='0' " %(id_test)
        cursor.execute(qu)
        post = cursor.fetchall()

    return render_template('/weka/data_asli_weka.html', post = post)



#UJI DATA
@app.route('/imdata_uji_weka', methods=['POST','GET'])
@read_session_weka
def imdata_uji_weka():
    id_test = session['id_weka']
    c = con
    cursor = c.cursor()
    query ="select * from tbl_test where id_test = %s" %(id_test)
    cursor.execute(query)
    data = cursor.fetchall()

    if request.method == 'POST':
        file = request.files['file-input']
        if file and allowed_file_import(file.filename):
            #simpan file baru
            filename=secure_filename(file.filename)
            path = os.path.join(IMPORT_FOLDER,filename)
            file.save(path)
            #open the workbook and define the worksheet
            book = xlrd.open_workbook(path)
            nm = book.sheet_names()
            #print nm[0]
            try:
                for i in range(len(nm)):
                    if nm[i] == "Daftar Uji Mustahik Weka":
                        sheet = book.sheet_by_name("Daftar Uji Mustahik Weka")
                        #cek excel format
                        if sheet.cell(4,1).value == "Nama" and sheet.cell(4,2).value == "Usia" and sheet.cell(4,3).value == "Penghasilan" and sheet.cell(4,4).value == "Ya/Tidak":
                            print " format sesuai "
                            qu = "select max_iterasi from tbl_test where id_test = '%s'"%(id_test)
                            cursor1 = c.cursor()
                            cursor1.execute(qu)
                            data1 = cursor1.fetchall()
                            print "data1 adalah",data1[0][0]
                            if data1[0][0] == 0:
                                flash("Data Latih Belum Dilakukan","error")
                            elif data1[0][0] != 0:
                                que = "select count(id_mustahik_weka) from tbl_mustahik_weka where id_test = '%s' and stts_weka = '1' "%(id_test)
                                cursor2 = c.cursor()
                                cursor2.execute(que)
                                data2 = cursor2.fetchall()
                                print "banyak data mustahik", data2[0][0]
                                for i in range(int(data2[0][0])):
                                    quer = "delete from tbl_mustahik_weka where id_test = '%s' and stts_weka = '1'"%(id_test)
                                    cursor3 = c.cursor()
                                    cursor3.execute(quer)
                                    c.commit()

                                importdata_uji_weka(sheet)
                                id = session['id_weka']
                                return redirect(url_for('view_data_uji_asli_weka'))
                                flash("Format file yang anda upload sesuai","succes")
                        else:
                            print "format tidak sesuai"
                            #print ""+sheet.cell(4,1).value+" "+sheet.cell(4,2).value+" "+sheet.cell(4,3).value+" "+sheet.cell(4,4).value+" "+sheet.cell(4,5).value+" "+sheet.cell(4,6).value+" "+sheet.cell(4,7).value+" "+sheet.cell(4,8).value+""
                            flash("Format file yang anda upload tidak sesuai, silakan cek format file","error")
                    else:
                        flash("Format file yang anda upload salah,tidak ditemukan sheet dengan nama : Daftar Mustahik Uji Weka","error")


            except Exception as e:
                print e
                flash(e, "error")

            #hapusfile(IMPORT_FOLDER, filename)
    return render_template('/weka/importdatauji_weka.html', post = data)


@read_session_weka
def importdata_uji_weka(booksheet):
    query = "INSERT INTO tbl_mustahik_weka (id_test,nama_mustahik_weka, x1_weka,x2_weka,c1_weka,c2_weka, stts_weka, k1_weka,k2_weka) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    jml_input = 0
    c = con
    cursor = c.cursor()
    id_test = session['id_weka']
    x1_min = 27.0
    x1_max = 80.0
    x2_min = 450000.0
    x2_max = 5000000.0
    #create a loop to iterate through each row in the XLS file
    for r in range(5, booksheet.nrows):
        try:
            nama_mustahik = booksheet.cell(r,1).value,
            a = float(booksheet.cell(r,2).value,)
            b = float(booksheet.cell(r,3).value,)
            c1= "1" if booksheet.cell(r,4).value == "YA" else "0",
            c2= "1" if booksheet.cell(r,4).value == "TIDAK" else "0",

            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            stts = 1
            cursor.execute(query,(str(id_test),nama_mustahik, str(x1),str(x2),c1,c2,stts,str(a),str(b)))
            c.commit()

            jml_input += 1

        except Exception as e:
            print e
            print jml_input
    flash(""+str(jml_input)+" Data Uji Mustahik Berhasil Disimpan", "success")

@app.route('/view_data_uji_asli_weka', methods=['POST','GET'])
@admin_session
@read_session_weka
def view_data_uji_asli_weka():
    cc=con
    cursor = cc.cursor()
    id_test=session['id_weka']
    print session['id_weka']

    qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
    cursor.execute(qu)
    cc.commit()
    post = cursor.fetchall()
    return render_template('/weka/data_asli_uji_weka.html', post=post)

@app.route('/tambah_data_uji_asli_weka', methods=['POST','GET'])
@admin_session
@read_session_weka
def tambah_data_uji_asli_weka():
    try:
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id_weka']
            print session['id_weka']
            nama= request.form['nama']
            a = request.form['x1']
            b = request.form['x2']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
<<<<<<< HEAD
            x2_min = 0.0
            x2_max = 3200000.0

=======
            x2_min = 450000.0
            x2_max = 5000000.0
        
>>>>>>> df9bf9b411b8adb66db02e897e702a74892163df
            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=1
            query = "INSERT INTO tbl_mustahik_weka (id_test,nama_mustahik_weka,x1_weka,x2_weka,c1_weka,c2_weka,stts_weka,k1_weka,k2_weka) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            print a,b, cc
            print x1,x2,c1,c2
            cursor.execute(query,(str(id_test),str(nama),str(x1),str(x2),c1,c2,stts,a,b,))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_uji_asli_weka'))



@app.route('/edit_data_uji_asli_weka/<id>', methods=['POST','GET'])
@admin_session
@read_session_weka
def edit_data_uji_asli_weka(id):
    try:
        id =id
        if request.method=='POST':
            ccc=con
            cursor = ccc.cursor()
            id_test=session['id_weka']
            print session['id_weka']
            a = request.form['x1']
            b = request.form['x2']
            cc = request.form['c']
            x1_min = 27.0
            x1_max = 80.0
<<<<<<< HEAD
            x2_min = 700000.0
            x2_max = 3200000.0

=======
            x2_min = 450000.0
            x2_max = 5000000.0
        
>>>>>>> df9bf9b411b8adb66db02e897e702a74892163df
            x1= (float(a) - x1_min) / (x1_max-x1_min)
            x2= (x2_max - float(b)) / (x2_max-x2_min)
            if cc == "YA":
                c1="1"
                c2="0"
            elif cc=="TIDAK":
                c1="0"
                c2="1"
            stts=1
            query = "Update tbl_mustahik_weka set x1_weka=%s,x2_weka=%s,c1_weka=%s,c2_weka=%s,stts_weka=%s,k1_weka=%s,k2_weka=%s where id_mustahik_weka = %s"
            print a,b, cc
            print x1,x2,c1,c2
            cursor.execute(query,(str(x1),str(x2),c1,c2,stts,a,b, id))
            ccc.commit()
    except Exception as e:
        print e
    return redirect(url_for('view_data_uji_asli_weka'))


@app.route('/delete_data_uji_asli_weka/<id>', methods=['POST','GET'])
@admin_session
@read_session_weka
def delete_data_uji_asli_weka(id):
    if request.method == 'POST':
        cc=con
        cursor = cc.cursor()
        id=id
        print id

        qu= "delete from tbl_mustahik_weka where id_mustahik_weka = '%s' and stts_weka='1' " %(id)
        cursor.execute(qu)
        cc.commit()

        return redirect(url_for('view_data_uji_asli_weka'))



@app.route('/count_data_uji_weka', methods=['POST','GET'])
@read_session_weka
def count_data_uji_weka():
    cc=con
    cursor = cc.cursor()
    id_test = session['id_weka']
    print session['id_weka']
    qu1= "select count(if(stts_weka=0,1,null)) 'datalatih', count(if(stts_weka=1,1,null)) 'datauji' from tbl_mustahik_weka where id_test = '%s' " %(id_test)
    cursor.execute(qu1)
    post1 = cursor.fetchall()

    qu2= "select id_test,stts_weka, count(if(c1_weka=1,1,null)) 'YA', count(if(c2_weka=1,1,null)) 'TIDAK', count(if(h_c1_weka=1,1,null)) 'Program_YA', count(if(h_c2_weka=1,1,null)) 'Program_TIDAK' from all_hasil_weka where id_test = '%s' and stts_weka='0' group by id_test " %(id_test)
    cursor.execute(qu2)
    post2 = cursor.fetchall()

    qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
    cursor.execute(qu3)
    post3 = cursor.fetchall()


    qu= "select * from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
    cursor.execute(qu)
    post = cursor.fetchall()
    if post == ():
        flash("Mohon maaf,, Data Uji anda kosong....","error")
    elif post != ():
        try:
            if request.method=='POST':
                query = "Select count(id_mustahik_weka) from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
                try:
                    cursor.execute(query)
                    data = cursor.fetchall()
                    for i in data:
                        count_data = i[0]

                except Exception as e:
                    print e

                c = 2
                #4 angka d blakang koma
                n_rounded = 4
                #make a random number array [a,b]
                miu = np.random.rand(count_data,c)
                #pembulatan 4 angka blakang koma
                x = np.around(miu,n_rounded)

                #select pusat cluster data latih
                sql="select v1,v2,v3,v4 from tbl_cluster where id_test = '%s' " %(id_test)
                cursor.execute(sql)
                miu = cursor.fetchall()
                bts = np.asarray(miu)
                list_bts = []
                for i in range(1):
                    list_bts.insert(i, bts[i])

                np_v = np.asarray(list_bts)
                vkj = np_v.reshape(2,2)
                print vkj
                p_cluster_uji_weka(x, vkj)
                return redirect(url_for('view_result_uji_weka'))

        except Exception as e:
            print e

    return render_template('/weka/data_uji_weka.html',post1=post1,post2=post2, post3=post3, post = post)



@read_session_weka
def p_cluster_uji_weka(x, vkj):
    c = con
    cursor = c.cursor()
    id_test = session['id_weka']
    #print id_test
    query = "Select x1_weka,x2_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        #initial list
        att = [1,2]
        cluster = [1,2]
        w = 2
        k = 0
        j = 0
        i = 0
        po = 0

        miu = x

        #convert tuple to numpy array
        mus = np.asarray(data)
        p_objecktif = []
        list_mus = mus.tolist()
        print "========================================="
        print "Mustahik"
        a = np.asarray(list_mus)
        # print len(list_mus)
        print a
        #mengkuadratkan numpy X ^ w
        miu2 = np.power(miu,w)
        #convert numpy to list
        list_miu2 = miu2.tolist()
        #initial a list
        s=[[] for i in range(len(list_mus))]
        ss=[[] for i in range(len(att))]
        print "========================================="
        print "Miu "
        print "========================================="
        print miu
        print "========================================="
        print "Miu^2"
        print "========================================="
        b = np.asarray(list_miu2)
        # print len(b)
        print b


        #procces
        for i in range(len(list_mus)):
            for k in range(len(cluster)):
                for j in range(len(att)):
                    s[i].append(list_mus[i][j] * list_miu2[i][k])
            #         j=j+1
            #     k+=1
            # i+=1
        #back to numpy
        ss = np.asarray(s)
        #sum per colom
        vx = np.sum(ss, axis=0)
        vmiu = np.sum(miu2, axis=0)
        print "========================================="
        #print setiap element x dengan setiap miu
        print " Sum X"
        print "========================================="
        print vx
        print "========================================="
        print " Sum Miu^2"
        print "========================================="
        print vmiu

        new_vkj = vkj

        print "========================================="
        print "Pusat Cluster"
        print "========================================="
        ccc = np.asarray(new_vkj)
        print ccc

        p=[[] for i in range(len(list_mus))]

        for i in range(len(list_mus)):
            for j in range(len(cluster)):
                for k in range(len(att)):
                    #proses data dikurangi pusat cluster di kuadratkan
                    p[i].append(pow(list_mus[i][k] - new_vkj[j][k], 2))

        aa = len(list_mus*2)
        pp = np.asarray(p)
        ppp = pp.reshape(aa,2)
        p1 = np.around(ppp,4)
        print "========================================="
        print "Hasil F objektif per Cluster"
        print "========================================="
        #sum perbaris
        sum_p1 = np.sum(p1, axis=1)
        sum_p2 = sum_p1.reshape(len(list_mus),2)
        #perkalian c dgn miu2
        fo = np.multiply(sum_p2, b)
        print fo
        print "========================================="
        fo_1 = np.sum(fo, axis=1)
        #sum of fungsi objektif
        fo_2 = np.sum(fo_1, axis=0)
        print "Total fungsi Objectif = ",fo_2
        print "========================================="
        print "Menghitung MIU baru"
        print "========================================="
        print "L"
        print sum_p2
        lt = np.sum(sum_p2, axis=1)
        print "\nLT"
        print lt

        #pembagian antar tiap L dgn LT masing2
        new_miu=[[] for i in range(len(list_mus))]
        for i in range(len(list_mus)):
            for j in range(len(cluster)):
                new_miu[i].append(sum_p2[i][j] / lt[i])

        new_miu_2 = np.asarray(new_miu)
        print "========================================="
        print "\n Pembaruan Miu"
        print "========================================="
        print new_miu_2
        res = fo_2 - po
        print "========================================="
        print "Error"
        print "========================================="
        print abs(res)
        print "========================================="
        po = fo_2
        p_objecktif.append(fo_2)
        error = abs(res)
        max_iterasi =len(p_objecktif)
        print max_iterasi
        c_hasil = np.around(new_miu_2,0)

        #cek sukses
        benar = 0.0
        query="select c1_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
        cursor.execute(query)
        c.commit()
        cek = cursor.fetchall()
        #cek satu2 sesuai antara manual dan program
        for j in range(len(list_mus)):
            if c_hasil[j][0] == cek[j]:
                benar +=1.0
        print benar
        print len(list_mus)
        persen = ((benar/float(len(list_mus)))*100.0)
        print persen
        #save result
        query = "UPDATE tbl_test SET  error_uji = %s, sukses_uji=%s where id_test = %s"
        cursor.execute(query,(error,persen, id_test))
        c.commit()



        #save cluster per mustahik
        query = "select id_mustahik_weka from tbl_mustahik_weka where id_test = '%s' and stts_weka='1' " %(id_test)
        cursor.execute(query)
        data = cursor.fetchall()

        sql = "select id_mustahik_weka from all_hasil_weka where id_test = '%s' and stts_weka='1' " %(id_test)
        cursor.execute(sql)
        data1 = cursor.fetchall()
        jml = 0
        if data1 == ():
            for i in range(len(list_mus)):
                id_mus = data[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                query = "insert into tbl_hasil_weka (id_mustahik_weka, h_c1_weka, h_c2_weka, miu1_weka, miu2_weka) values (%s, %s, %s, %s, %s)"
                cursor.execute(query,(id_mus, c1,c2,m1,m2))
                c.commit()
                jml+=1
            print jml, "save done"
        elif data1 != ():
            for i in range(len(list_mus)):
                id_mus = data[i]
                id_h_mus = data1[i]
                c1 = c_hasil[i][0]
                c2 = c_hasil[i][1]
                m1 = miu[i][0]
                m2 = miu[i][1]
                if id_mus == id_h_mus:
                    query = "update tbl_hasil_weka set h_c1_weka =%s, h_c2_weka=%s, miu1_weka=%s, miu2_weka=%s where id_mustahik_weka = %s"
                    cursor.execute(query,( c1,c2,m1, m2, id_mus))
                    c.commit()

                    jml+=1
            print jml, "update done"


    except Exception as e:
        print e

@app.route('/view_result_uji_weka', methods=['POST','GET'])
@read_session_weka
def view_result_uji_weka():
    try:
        id_test = session['id_weka']
        c =con
        cursor = c.cursor()
        query = "SELECT * from all_hasil_weka where id_test = '%s' and stts_weka='1' " %(id_test)
        cursor.execute(query)
        post =  cursor.fetchall()
        print id_test
        sql = "select * from tbl_test where id_test = '"+str(id_test)+"' "
        cursor1 = c.cursor()
        cursor1.execute(sql)
        data = cursor1.fetchall()




        qu1= "select count(if(stts_weka=0,1,null)) 'datalatih', count(if(stts_weka=1,1,null)) 'datauji' from tbl_mustahik_weka where id_test = '%s' " %(id_test)
        cursor.execute(qu1)
        post1 = cursor.fetchall()

        qu2= "select id_test,stts_weka, count(if(c1_weka=1,1,null)) 'YA', count(if(c2_weka=1,1,null)) 'TIDAK', count(if(h_c1_weka=1,1,null)) 'Program_YA', count(if(h_c2_weka=1,1,null)) 'Program_TIDAK' from all_hasil_weka where id_test = '%s' and stts_weka='0' group by id_test " %(id_test)
        cursor.execute(qu2)
        post2 = cursor.fetchall()

        qu3= "select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat,v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,v11,v12 from tbl_test inner join tbl_cluster on tbl_test.id_test = tbl_cluster.id_test where tbl_test.id_test = '%s' " %(id_test)
        cursor.execute(qu3)
        post3 = cursor.fetchall()

        qu4= "select id_test,stts_weka, count(if(c1_weka=1,1,null)) 'YA', count(if(c2_weka=1,1,null)) 'TIDAK', count(if(h_c1_weka=1,1,null)) 'Program_YA', count(if(h_c2_weka=1,1,null)) 'Program_TIDAK' from all_hasil_weka where id_test = '%s' and stts_weka='1' group by id_test " %(id_test)
        cursor.execute(qu4)
        post4 = cursor.fetchall()

        return render_template('/weka/hasil_uji_weka.html',post1 =post1, post2=post2, post3=post3,post4=post4,data= data, post = post)

    except Exception as e:
        print e


@app.route('/delete_test_weka/<id_test>', methods=['POST','GET'])
@read_session_weka
def delete_test_weka(id_test):
    cc=con
    cursor= cc.cursor()
    if request.method=='POST':
        query = "delete from tbl_test where id_test =%s" %(id_test)
        cursor.execute(query)
        cc.commit()
        return redirect(url_for('save_test_weka'))



#laporan
@app.route('/laporan', methods=['GET', 'POST'])
@read_session
def laporan():
    c = con
    cursor = c.cursor()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts=0,1,null))'jumlah_latih',count(if(stts=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik on tbl_test.id_test = tbl_mustahik.id_test where status_test='0' group by id_test"
    cursor.execute(query)
    post = cursor.fetchall()
    return render_template('laporan/pilihlaporan.html', post=post)

@app.route('/laporan_weka', methods=['GET', 'POST'])
@read_session_weka
def laporan_weka():
    c = con
    cursor = c.cursor()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts_weka=0,1,null))'jumlah_latih',count(if(stts_weka=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik_weka on tbl_test.id_test = tbl_mustahik_weka.id_test where status_test='1' group by id_test"
    cursor.execute(query)
    post = cursor.fetchall()
    return render_template('laporan/pilihlaporanweka.html', post=post)


@app.route('/laporan_data/<id>', methods=['GET', 'POST'])
@read_session
def laporan_data(id):
    id=id
    c = con
    cursor = c.cursor()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts=0,1,null))'jumlah_latih',count(if(stts=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik on tbl_test.id_test = tbl_mustahik.id_test where status_test='0' and tbl_test.id_test=%s " %(id)
    cursor.execute(query)
    post = cursor.fetchall()
    if request.method == 'POST':
        options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'orientation': 'landscape',
        }
        id = id
        sql  ="select * from all_hasil_laporan where id_test = %s"%(id)
        c =con
        cursor = c.cursor()
        cursor.execute(sql)
        post = cursor.fetchall()
        query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts=0,1,null))'jumlah_latih',count(if(stts=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik on tbl_test.id_test = tbl_mustahik.id_test where status_test='0'  and tbl_test.id_test=%s " %(id)
        cursor.execute(query)
        post1 = cursor.fetchall()
        waktu = time.asctime( time.localtime(time.time()) )
        logo = os.path.join(IMG, '21.jpg')
        page = render_template('laporan/lap_data.html',post1=post1, post=post, waktu=waktu, logo=logo)
        pdfkit.from_string(page, os.path.join(LAPORAN_FOLDER, "data_mustahik.pdf"), options=options)
        return send_file(os.path.join(LAPORAN_FOLDER, "data_mustahik.pdf"), mimetype='application/pdf')


@app.route('/laporan_data_weka/<id>', methods=['GET', 'POST'])
@read_session_weka
def laporan_data_weka(id):
    options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'orientation': 'landscape',
    }
    id=id
    sql  ="select * from all_hasil_weka_laporan where id_test = %s"%(id)
    c =con
    cursor = c.cursor()
    cursor.execute(sql)
    post = cursor.fetchall()
    query = " select tbl_test.id_test, nama_test, max_iterasi, error, sukses, error_uji, sukses_uji, status_test, pangkat, count(if(stts_weka=0,1,null))'jumlah_latih',count(if(stts_weka=1,1,null))'jumlah_uji' from tbl_test inner join tbl_mustahik_weka on tbl_test.id_test = tbl_mustahik_weka.id_test where status_test='1' and tbl_test.id_test=%s " %(id)
    cursor.execute(query)
    post1 = cursor.fetchall()
    waktu = time.asctime( time.localtime(time.time()) )
    logo = os.path.join(IMG, '21.jpg')
    page = render_template('laporan/laporan_data_weka.html',post1=post1, post=post, waktu=waktu, logo=logo)
    pdfkit.from_string(page, os.path.join(LAPORAN_FOLDER, "data_mustahik_weka.pdf"), options=options)
    return send_file(os.path.join(LAPORAN_FOLDER, "data_mustahik_weka.pdf"), mimetype='application/pdf')

