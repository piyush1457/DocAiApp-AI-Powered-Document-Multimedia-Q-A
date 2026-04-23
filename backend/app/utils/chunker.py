from typing import List, Dict, Any
from dataclasses import dataclass
import tiktoken


@dataclass
class Chunk:
    text: str
    metadata: Dict[str, Any]
    token_count: int


class RecursiveCharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: List[str] = ["\n\n", "\n", " ", ""],
        encoding_name: str = "cl100k_base",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def _get_token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def split_text(self, text: str) -> List[str]:
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        Implementation of recursive splitting logic.
        """
        final_chunks = []

        # If text is small enough, return it
        if self._get_token_count(text) <= self.chunk_size:
            return [text]

        # Find the best separator
        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                new_separators = separators[i + 1 :]
                break

        # Split by separator
        if separator != "":
            splits = text.split(separator)
        else:
            # Hard split if no separator works
            splits = list(text)

        # Merge splits into chunks
        current_chunk_parts = []
        current_token_count = 0

        for split in splits:
            split_token_count = self._get_token_count(split)

            if split_token_count > self.chunk_size:
                # If a single split is too large, recurse on it
                if current_chunk_parts:
                    final_chunks.append(separator.join(current_chunk_parts))
                    current_chunk_parts = []
                    current_token_count = 0

                recursive_chunks = self._recursive_split(split, new_separators)
                final_chunks.extend(recursive_chunks)
                continue

            if current_token_count + split_token_count > self.chunk_size:
                # Current chunk is full
                final_chunks.append(separator.join(current_chunk_parts))

                # Handle overlap
                # This is a simplified overlap: we keep some parts from the end
                overlap_parts = []
                overlap_tokens = 0
                for part in reversed(current_chunk_parts):
                    part_tokens = self._get_token_count(part)
                    if overlap_tokens + part_tokens <= self.chunk_overlap:
                        overlap_parts.insert(0, part)
                        overlap_tokens += part_tokens
                    else:
                        break

                current_chunk_parts = overlap_parts + [split]
                current_token_count = overlap_tokens + split_token_count
            else:
                current_chunk_parts.append(split)
                current_token_count += split_token_count

        if current_chunk_parts:
            final_chunks.append(separator.join(current_chunk_parts))

        return final_chunks

    def create_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        if not text:
            return []
        texts = self.split_text(text)
        return [
            Chunk(text=t, metadata=metadata, token_count=self._get_token_count(t))
            for t in texts
        ]
