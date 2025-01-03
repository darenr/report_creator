import sqlite3

def create_fts_table(conn):
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
            content, 
            tokenize = 'porter'  -- Optional: Use a tokenizer for better search results
        );
    ''')

def index_documents(conn, documents):
    for doc_id, content in documents.items():
        conn.execute("INSERT INTO documents (rowid, content) VALUES (?, ?)", (doc_id, content))

def search_documents(conn, query):
    results = conn.execute('''
        SELECT rowid, rank, content
        FROM documents
        WHERE documents MATCH ?
        ORDER BY RANK
    ''', (query,)).fetchall()
    return results

# Create an in-memory database
conn = sqlite3.connect(':memory:')

# Create the FTS5 table
create_fts_table(conn)

# Index some documents
documents = {
    1: "This is a document about time, but not about dilation",
    2: "Another document about dilation.",
    3: "A document about Time Dilation."
}
index_documents(conn, documents)

# Search the documents
qs = ("time dilation",)
query = "NEAR(" +

results = search_documents(conn, f"""NEAR(' '.join([f'"{q}"' for q in"{q}", 10)""")

for doc_id, rank, content in results:
    print(f"Document ID: {doc_id}, [{rank:.8f}]: Content: {content}")

# Close the connection
conn.close()
