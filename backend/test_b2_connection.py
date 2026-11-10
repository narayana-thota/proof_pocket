
from app.storage.b2_storage import check_bucket_connection

result = check_bucket_connection()

print(result)

from io import BytesIO

from app.storage.b2_storage import (
    upload_file,
    download_file,
    delete_file,
    generate_presigned_url
)

# Create a sample file in memory
sample_content = b"ProofPocket Backblaze storage test."

file_obj = BytesIO(sample_content)

object_key = "test/proofpocket-test.txt"

try:
    # 1. Upload
    result = upload_file(
        file_obj,
        object_key,
        "text/plain"
    )
    print("UPLOAD:", result)

    # 2. Generate temporary access URL
    url = generate_presigned_url(object_key)
    print("PRESIGNED URL:", url)

    # 3. Download
    download_file(
        object_key,
        "/tmp/proofpocket-test.txt"
    )
    print("DOWNLOAD: Successful")

    # 4. Delete test file
    result = delete_file(object_key)
    print("DELETE:", result)

except Exception as error:
    print("Storage test failed:", error)
