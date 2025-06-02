from flask import Blueprint, jsonify, send_file
from extensions import mongo
from collections import Counter
from wordcloud import WordCloud
import os
import datetime
import re
import string


# Custom ballet-related vocabulary (feel free to expand this)
ballet_vocabulary = {
    'ballet', 'dancer', 'dance', 'performance', 'rehearsal', 'choreography', 'balletic', 'pirouette',
    'ballerina', 'balletschool', 'balletcompany', 'pas', 'tendu', 'arabesque', 'pointe', 'pas de deux',
    'balletdance', 'balletperformance', 'balletclass', 'danceacademy', 'danceday', 'balletshow',
    'balet', 'penari', 'tari', 'pertunjukan', 'latihan', 'koreografi', 'gerakan balet', 'putaran',
    'ballerina', 'sekolah balet', 'perusahaan balet', 'langkah', 'tendu', 'arabesque', 'ujung jari',
    'pas de deux', 'tari balet', 'pertunjukan balet', 'kelas balet', 'akademi tari', 'hari tari', 'pertunjukan balet',
    'ballet klasik', 'pentas balet', 'gerak balet', 'tarian balet', 'komunitas balet', 'pembelajaran balet',
    'pas ballerina', 'karya balet'
}

# Additional stopwords (standard plus any other words you don't want to include)
additional_stop_words = {
    'yang', 'di', 'ke', 'dari', 'pada', 'dalam', 'untuk', 'dengan', 'dan', 'atau',
    'ini', 'itu', 'juga', 'sudah', 'saya', 'anda', 'dia', 'mereka', 'kita', 'akan',
    'bisa', 'ada', 'tidak', 'saat', 'oleh', 'setelah', 'para', 'seperti', 'saat',
    'bagi', 'serta', 'tapi', 'lain', 'sebuah', 'karena', 'ketika', 'jika', 'apa',
    'seorang', 'tentang', 'dalam', 'bisa', 'sementara', 'dilakukan', 'setelah',
    'yakni', 'menurut', 'hampir', 'dimana', 'bagaimana', 'selama', 'sebelum', 
    'hingga', 'kepada', 'sebagai', 'masih', 'hal', 'sempat', 'sedang', 'selain',
    'sembari', 'mendapat', 'sedangkan', 'tetapi', 'membuat', 'namun', 'gimana'
}


def clean_text(text):
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    words = text.split()
    return [word for word in words if word not in additional_stop_words and len(word) > 2]

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/api/wordcloud', methods=['GET'])
def generate_wordcloud():
    articles = list(mongo.db.big_data.find())
    all_text = ' '.join([a['title'] for a in articles if 'title' in a])
    words = clean_text(all_text)

    # Gunakan hanya kata-kata dari vocabulary
    filtered_words = [word for word in words if word in ballet_vocabulary]
    text_for_cloud = ' '.join(filtered_words)

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_for_cloud)

    os.makedirs("static", exist_ok=True)
    path = os.path.join("static", "wordcloud.png")
    wordcloud.to_file(path)
    return send_file(path, mimetype='image/png')


@analysis_bp.route('/api/topwords', methods=['GET'])
def top_words():
    articles = list(mongo.db.big_data.find())
    all_text = ' '.join([a['title'] for a in articles if 'title' in a])
    words = all_text.lower().split()
    word_counts = Counter(words)
    return jsonify(word_counts.most_common(10))

@analysis_bp.route('/api/trend', methods=['GET'])
def trend():
    articles = list(mongo.db.big_data.find())
    monthly_counts = Counter()
    for a in articles:
        try:
            date_obj = datetime.datetime.strptime(a["date"], "%d %b %Y")
            key = f"{date_obj.year}-{date_obj.month:02d}"
            monthly_counts[key] += 1
        except:
            continue
    return jsonify(dict(sorted(monthly_counts.items())))

@analysis_bp.route('/api/yearly_trends', methods=['GET'])
def yearly_trends():
    articles = list(mongo.db.big_data.find())

    counts_by_year = {}
    for a in articles:
        try:
            date_obj = datetime.datetime.strptime(a["date"], "%d %b %Y")
            year = date_obj.year
            counts_by_year[year] = counts_by_year.get(year, 0) + 1
        except:
            continue

    sorted_counts = dict(sorted(counts_by_year.items()))
    return jsonify(sorted_counts)


@analysis_bp.route('/api/monthly_trends/<int:year>', methods=['GET'])
def monthly_trends(year):
    articles = list(mongo.db.big_data.find())

    counts_by_month_source = {}
    for a in articles:
        try:
            date_obj = datetime.datetime.strptime(a["date"], "%d %b %Y")
            if date_obj.year == year:
                month = date_obj.strftime("%B")  # eg: January
                source = a.get("source", "Unknown")
                key = (month, source)
                counts_by_month_source[key] = counts_by_month_source.get(key, 0) + 1
        except:
            continue

    # Format JSON for Flutter
    result = []
    for (month, source), count in counts_by_month_source.items():
        result.append({"month": month, "source": source, "count": count})

    return jsonify(result)

