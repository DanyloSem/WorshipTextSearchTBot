from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh import highlight
import os

# Створення індексу
schema = Schema(content=TEXT(stored=True))
if not os.path.exists("index"):
    os.mkdir("index")
index = create_in("index", schema)

# Додавання документів
writer = index.writer()
writer.add_document(content="This document is a test document with some text.")
writer.add_document(content="Another document is here for testing purposes.")
writer.add_document(content="Searching text in Whoosh is very flexible for test.")
writer.commit()

# Пошук
with index.searcher() as searcher:
    parser = QueryParser("content", index.schema)
    query = parser.parse("test")
    results = searcher.search(query)

    # Обрізаємо до 50 символів навколо знайденого
    results.fragmenter = highlight.ContextFragmenter(maxchars=5)
    print("Fragments with maxchars=50 for 'test':")
    for result in results:
        fragment = result.highlights("content")
        print(fragment)