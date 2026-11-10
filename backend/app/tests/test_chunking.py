
import unittest

from app.ai.chunking import create_chunks, validate_chunks


class TestChunking(unittest.TestCase):

    def setUp(self):
        # A sufficiently long document for multiple chunks
        self.sample_text = (
            "The insurance policy provides medical coverage. "
            "The policyholder can claim eligible hospital expenses. "
            "The policy remains valid until December 2027. "
            "Renewal must be completed before the expiry date. "
        ) * 100

    def test_multiple_chunks_are_created(self):
        chunks = create_chunks(
            self.sample_text,
            document_id=102,
            source_type="txt"
        )

        self.assertGreater(len(chunks), 1)

    def test_chunk_metadata_exists(self):
        chunks = create_chunks(
            self.sample_text,
            document_id=102,
            source_type="txt"
        )

        required_fields = [
            "document_id",
            "chunk_id",
            "chunk_index",
            "source_type",
            "start_token",
            "end_token",
            "token_count",
            "model_input_token_count",
            "chunk_text"
        ]

        for chunk in chunks:
            for field in required_fields:
                self.assertIn(field, chunk)

    def test_chunk_token_limit(self):
        chunks = create_chunks(
            self.sample_text,
            document_id=102,
            source_type="txt"
        )

        for chunk in chunks:
            self.assertLessEqual(chunk["token_count"], 180)
            self.assertLessEqual(chunk["model_input_token_count"], 256)

    def test_overlap_is_correct(self):
        chunks = create_chunks(
            self.sample_text,
            document_id=102,
            source_type="txt"
        )

        for previous, current in zip(chunks, chunks[1:]):
            actual_overlap = (
                previous["end_token"] - current["start_token"]
            )

            self.assertEqual(actual_overlap, 30)

    def test_chunk_validation(self):
        chunks = create_chunks(
            self.sample_text,
            document_id=102,
            source_type="txt"
        )

        self.assertTrue(validate_chunks(chunks))

    def test_empty_document(self):
        chunks = create_chunks(
            "",
            document_id=102,
            source_type="txt"
        )

        self.assertEqual(chunks, [])

    def test_short_document(self):
        chunks = create_chunks(
            "This is a short insurance document.",
            document_id=102,
            source_type="txt"
        )

        self.assertEqual(len(chunks), 1)

    def test_invalid_overlap(self):
        with self.assertRaises(ValueError):
            create_chunks(
                self.sample_text,
                document_id=102,
                source_type="txt",
                chunk_size=100,
                overlap=100
            )

    def test_invalid_document_id(self):
        with self.assertRaises(ValueError):
            create_chunks(
                self.sample_text,
                document_id=0,
                source_type="txt"
            )


if __name__ == "__main__":
    unittest.main()
