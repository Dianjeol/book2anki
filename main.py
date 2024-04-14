from flask import Flask, request, render_template, send_file
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import re
import genanki
import os

# Stellen Sie sicher, dass die NLTK-Ressourcen heruntergeladen werden
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('omw-1.4')

app = Flask(__name__)

# Definieren Sie eine Funktion zum Lemmatisieren von Wörtern mit mindestens 3 Zeichen
def lemmatize_words(words):
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = []
    for word, tag in nltk.pos_tag(words):
        if len(word) >= 3:  # Nur Wörter mit mindestens 3 Zeichen lemmatisieren
            pos = {'NN': wordnet.NOUN, 'VB': wordnet.VERB, 'JJ': wordnet.ADJ, 'RB': wordnet.ADV}.get(tag[:2], wordnet.NOUN)
            lemmatized_words.append(lemmatizer.lemmatize(word.lower(), pos))  # In Kleinbuchstaben konvertieren
    return lemmatized_words

# Definieren Sie eine Funktion zum Laden des Basiswortschatzes
def load_base_vocabulary(base_vocab_size):
    with open('eng.txt', 'r') as file:
        base_vocab = file.read().splitlines()
    return set(word.lower() for word in base_vocab[:base_vocab_size])  # In Kleinbuchstaben konvertieren

# Definieren Sie eine Funktion, um Definitionen und Beispiele zu erhalten
def get_definitions_examples(words):
    definitions_examples = {}
    for word in words:
        synsets = wordnet.synsets(word)
        if synsets:
            definitions_examples[word] = {
                'definition': synsets[0].definition(),
                'example': synsets[0].examples()[0] if synsets[0].examples() else ''
            }
    return definitions_examples

# Definieren Sie eine Funktion zur Verarbeitung der Benutzerwortschatzliste
def process_user_vocab(vocab_file):
    if vocab_file:
        vocab_text = vocab_file.read().decode('utf-8')
        # Teilen Sie den Wortschatztext durch jedes Nicht-Wort-Zeichen (einschließlich Leerzeichen, Zeilenumbrüche usw.)
        user_vocab = set(re.findall(r'\b\w+\b', vocab_text.lower()))  # In Kleinbuchstaben konvertieren
    else:
        user_vocab = set()
    return user_vocab

# Definieren Sie eine Funktion zum Erstellen eines Anki-Decks
def create_anki_deck(unknown_words_defs_examps):
    my_deck = genanki.Deck(
        2059400110,
        'Vocabulary Deck'
    )

    my_model = genanki.Model(
        1607392319,
        'Simple Model',
        fields=[
            {'name': 'Word'},
            {'name': 'Definition'},
            {'name': 'Example'}
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Word}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Definition}}<br><em>{{Example}}</em>',
            },
        ]
    )

    for word, defs_examps in unknown_words_defs_examps.items():
        my_note = genanki.Note(
            model=my_model,
            fields=[word, defs_examps['definition'], defs_examps['example']]
        )
        my_deck.add_note(my_note)

    # Erstellen Sie eine temporäre Datei für das Anki-Paket
    deck_filename = 'vocabulary_deck.apkg'
    genanki.Package(my_deck).write_to_file(deck_filename)
    return deck_filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    book_file = request.files['book']
    vocab_file = request.files.get('vocab')
    base_vocab_size = int(request.form['base_vocab_size'])

    book_text = book_file.read().decode('utf-8')
    book_words = nltk.word_tokenize(book_text)
    book_words_lemmatized = lemmatize_words(book_words)
    book_root_words = set(book_words_lemmatized)

    user_vocab = process_user_vocab(vocab_file)
    base_vocab = load_base_vocabulary(base_vocab_size)
    combined_vocab = user_vocab.union(base_vocab)
    unknown_words = book_root_words.difference(combined_vocab)
    unknown_words_defs_examps = get_definitions_examples(unknown_words)

    # Erstellen Sie das Anki-Deck und erhalten Sie den Dateinamen
    deck_filename = create_anki_deck(unknown_words_defs_examps)

    return render_template('result.html',

            original_words_count=len(book_words),
                           root_words_count=len(book_root_words),
                           user_vocab_count=len(user_vocab),
                           base_vocab_count=len(base_vocab),
                           combined_vocab_count=len(combined_vocab),
                           unknown_words_count=len(unknown_words),
                           unknown_words_defs_examps=unknown_words_defs_examps,
                           deck_filename=deck_filename)

@app.route('/download/<deck_filename>', methods=['GET'])
def download(deck_filename):
    # Stellen Sie sicher, dass der Dateiname sicher ist und keine relativen Pfade enthält
    if os.path.basename(deck_filename) == deck_filename:
        path = os.path.join(app.root_path, deck_filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
     app.run(host="localhost", port=8080, debug=True)
   # app.run(debug=True)
