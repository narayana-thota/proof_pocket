
import unittest

from app.ai.pipeline import process_document


class TestDocumentPipeline(unittest.TestCase):

    def setUp(self):
        self.document_id = 101
        self.source_type = "pdf"

        self.sample_text = """
        This insurance policy provides coverage for accidental damage.
        The policy is valid from January 2026 to December 2027.
        The customer must renew the policy before the expiry date.
        The insurance company will process eligible claims within 30 days.
        """ * 30

    def test_pipeline_creates_chunks(self):
        results = process_document(
            extracted_text=self.sample_text,
            document_id=self.document_id,
            source_type=self.source_type
        )

        self.assertGreater(len(results), 0)

    def test_every_chunk_has_embedding(self):
        results = process_document(
            self.sample_text,
            self.document_id,
            self.source_type
        )

        for chunk in results:
            self.assertIn("embedding", chunk)

    def test_embedding_dimension(self):
        results = process_document(
            self.sample_text,
            self.document_id,
            self.source_type
        )

        for chunk in results:
            self.assertEqual(len(chunk["embedding"]), 384)

    def test_chunk_metadata_is_preserved(self):
        results = process_document(
            self.sample_text,
            self.document_id,
            self.source_type
        )

        for index, chunk in enumerate(results):
            self.assertEqual(chunk["document_id"], self.document_id)
            self.assertEqual(chunk["source_type"], self.source_type)
            self.assertEqual(chunk["chunk_index"], index)
            self.assertIn("chunk_text", chunk)
            self.assertIn("chunk_id", chunk)

    def test_empty_document_is_rejected(self):
        with self.assertRaises(ValueError):
            process_document(
                extracted_text="",
                document_id=self.document_id,
                source_type=self.source_type
            )

    def test_invalid_text_type_is_rejected(self):
        with self.assertRaises(TypeError):
            process_document(
                extracted_text=None,
                document_id=self.document_id,
                source_type=self.source_type
            )


if __name__ == "__main__":
    unittest.main()
