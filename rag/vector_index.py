import os
import numpy as np
import json

from core.config import VECTORS_DIR

class VectorIndex:
    def __init__(self, vector_dir=VECTORS_DIR):
        self.vector_dir = vector_dir
        self.vectors = []
        self.metadata = []
        self.vector_map = self.load_vector_map()
        self.load_vectors()

    def load_vector_map(self):
        map_path = os.path.join(self.vector_dir, "vector_map.json")
        if not os.path.exists(map_path):
            return {}
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def load_vectors(self):
        self.vectors = []
        self.metadata = []

        for root, dirs, files in os.walk(self.vector_dir):
            for file in files:
                if file.endswith(".npy"):
                    path = os.path.join(root, file)

                    try:
                        vec = np.load(path)
                        self.vectors.append(vec)

                        meta = self.vector_map.get(file, {"vector_file": file})
                        self.metadata.append(meta)

                    except:
                        continue

    def reload(self):
        """Reload vector map and vectors from disk (call after re-indexing)."""
        self.vector_map = self.load_vector_map()
        self.load_vectors()

    def search(self, query_vector, top_k=5):
        if len(self.vectors) == 0:
            self.reload()
        if len(self.vectors) == 0:
            return []

        scores = []

        for i, vec in enumerate(self.vectors):
            score = np.dot(query_vector, vec) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vec)
            )
            scores.append((score, self.metadata[i]))

        scores.sort(reverse=True, key=lambda x: x[0])
        return scores[:top_k]
    

vector_index = VectorIndex()
