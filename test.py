from google.cloud import translate_v2 as translate
import nltk
import re

def translate_sentence(project_id, credentials_path, words_file, file_paths):
    client = translate.Client.from_service_account_json(credentials_path)
    results = []

    with open(words_file, 'r', encoding='utf-8') as f:
        words = [word.strip() for word in f.readlines()]
        k=0

    for word in words:
        print(k)
        k+=1
        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                sentences = nltk.sent_tokenize(text, language='french')
                for sentence in sentences:
                    if any(re.search(rf'\b{variant}\b', sentence) for variant in word.split('/')):
                        sentence_fr = re.sub(r':[^a-zA-Z]*', ': ', sentence).strip()
                        translation = client.translate(sentence_fr, target_language='de')
                        results.append((sentence_fr, translation['translatedText']))
                        break
                else:
                    continue
                break

    return results

project_id = 'booming-argon-419917'
credentials_path = 'test.json'
words_file = 'words.txt'
file_paths = ['p.txt', 'm.txt']

results = translate_sentence(project_id, credentials_path, words_file, file_paths)

for sentence_fr, translated_sentence in results:
    print(f"Französischer Satz: {sentence_fr}")
    print(f"Übersetzter Satz: {translated_sentence}")
