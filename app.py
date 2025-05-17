from flask import Flask, render_template, request, send_file
import pandas as pd
import re
import os

app = Flask(__name__)

# Load kamus
def load_kamus():
    with open("kata_positif.txt", encoding='utf-8') as f:
        pos = [line.strip() for line in f if line.strip()]
    with open("kata_negatif.txt", encoding='utf-8') as f:
        neg = [line.strip() for line in f if line.strip()]
    with open("frasa_positif.txt", encoding='utf-8') as f:
        fpos = [line.strip() for line in f if line.strip()]
    with open("frasa_negatif.txt", encoding='utf-8') as f:
        fneg = [line.strip() for line in f if line.strip()]
    norm = {}
    with open("normalisasi_kata.txt", encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                a,b = line.strip().split('=')
                norm[a] = b
    return pos, neg, fpos, fneg, norm

positive_words, negative_words, frasa_positif, frasa_negatif, normalisasi_dict = load_kamus()
negasi_words = ['tidak', 'gak', 'nggak', 'tak', 'bukan', 'kurang', 'belum']
intensifier = ['sangat', 'banget', 'amat', 'sekali']

# Proses teks
def preprocess(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\d+", "", text)
    words = text.split()
    words = [normalisasi_dict.get(w, w) for w in words]
    return ' '.join(words)

# Deteksi sentimen
def analisis_sentimen(text):
    text = preprocess(text)
    skor = 0
    intensify = 1

    for frasa in frasa_positif:
        if frasa in text:
            skor += 2
            text = text.replace(frasa, '')
    for frasa in frasa_negatif:
        if frasa in text:
            skor -= 2
            text = text.replace(frasa, '')

    words = text.split()
    skip = False
    for i, word in enumerate(words):
        if skip:
            skip = False
            continue
        if word in intensifier:
            intensify = 2
            continue
        if word in negasi_words and i+1 < len(words):
            next_word = words[i+1]
            if next_word in positive_words:
                skor -= 1 * intensify
                skip = True
            elif next_word in negative_words:
                skor += 1 * intensify
                skip = True
            intensify = 1
        else:
            if word in positive_words:
                skor += 1 * intensify
            elif word in negative_words:
                skor -= 1 * intensify
            intensify = 1

    if skor > 0:
        return 'Positif'
    elif skor < 0:
        return 'Negatif'
    else:
        return 'Netral'

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/hasil', methods=['POST'])
def hasil():
    file = request.files['csvfile']
    if not file:
        return "Silakan unggah file CSV"
    df = pd.read_csv(file)
    if 'komentar' not in df.columns:
        return "Kolom 'komentar' tidak ditemukan di file CSV"

    df['sentimen'] = df['komentar'].apply(analisis_sentimen)

    # Simpan hasil
    output_file = 'static/hasil_sentimen.csv'
    df.to_csv(output_file, index=False)

    # Hitung distribusi
    distribusi = df['sentimen'].value_counts()
    jumlah_positif = distribusi.get('Positif', 0)
    jumlah_negatif = distribusi.get('Negatif', 0)
    jumlah_netral = distribusi.get('Netral', 0)

    # Untuk Pie Chart
    labels = distribusi.index.tolist()
    values = distribusi.values.tolist()

    # Tabel
    tabel = df.to_html(classes='table table-bordered', index=False)

    return render_template('hasil.html',
                           tabel=tabel,
                           file_download=output_file,
                           labels=labels,
                           values=values,
                           jumlah_positif=jumlah_positif,
                           jumlah_negatif=jumlah_negatif,
                           jumlah_netral=jumlah_netral)



@app.route('/download')
def download():
    return send_file('static/hasil_sentimen.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
