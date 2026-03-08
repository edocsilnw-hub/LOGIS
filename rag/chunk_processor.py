import os
import numpy as np

from core.ai_engine import call_ollama
from core.config import VECTORS_DIR, SUMMARIES_DIR, CHUNKBLOCKS_DIR
from core.ai_engine import get_embedding

def split_into_chunks(session_id, text, source_path, chunk_size=1200, overlap=200):
    chunks=[]
    start=0
    chunk_index=1
    base_filename=os.path.basename(source_path).replace(".txt","")

    os.makedirs(CHUNKBLOCKS_DIR,exist_ok=True)

    while start<len(text):
        end=start+chunk_size
        chunk_text=text[start:end]

        chunk_name=f"{base_filename}_chunk_{chunk_index:03d}"
        chunk_file=chunk_name+".txt"
        block_path=os.path.join(CHUNKBLOCKS_DIR,chunk_file)

        with open(block_path,"w",encoding="utf-8") as f:
            f.write(chunk_text)

        process_chunk(chunk_name,chunk_text)

        chunks.append(chunk_file)
        start+=max(chunk_size-overlap,200)
        chunk_index+=1

    print(f"[CHUNKER] Created {len(chunks)} chunks for session {session_id}")
    return chunks

def process_chunk(chunk_name,chunk_text):
    try:
        os.makedirs(VECTORS_DIR,exist_ok=True)
        os.makedirs(SUMMARIES_DIR,exist_ok=True)

        vector_path=os.path.join(VECTORS_DIR,chunk_name+".npy")
        summary_path=os.path.join(SUMMARIES_DIR,chunk_name+"_summary.txt")

        vector=get_embedding(chunk_text)

        if vector is not None:
            np.save(vector_path,np.array(vector))
            print(f"[VECTOR] Saved {chunk_name}")

        summary_prompt=(
            "Summarize this development log chunk.\n"
            "Extract goals, problems, solutions, and code changes.\n\n"
            +chunk_text
        )

        summary,_=call_ollama(summary_prompt)

        with open(summary_path,"w",encoding="utf-8") as f:
            f.write(summary)

    except Exception as e:
        print(f"[CHUNK ERROR] {e}")

def chunk_script(text, chunk_size=1200, overlap=200):
    """
    Lightweight chunker used during vector retrieval.
    Does not save files — only returns chunks.
    """

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start += max(chunk_size - overlap, 200)

    return chunks