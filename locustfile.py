import asyncio
import httpx
import os

# --- Test Configuration ---
API_URL = "http://localhost:8000/api/v1/conversations/stream"
NUM_CONCURRENT_USERS = 5
IMAGE_PATH = "test_image.png"  # We need a placeholder image for this test
PROMPT_TEXT = "Please analyze this circuit diagram."

async def run_user_simulation(client: httpx.AsyncClient, user_id: int):
    """Simulates a single user uploading an image and prompt."""
    print(f"[User {user_id}] Starting request...")
    
    try:
        # Prepare the multipart form data
        with open(IMAGE_PATH, "rb") as f:
            files = {"image": (os.path.basename(IMAGE_PATH), f, "image/png")}
            data = {"text_input": PROMPT_TEXT}
            
            response = await client.post(API_URL, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                print(f"[User {user_id}] Request successful (200 OK). Backend is handling the stream.")
                # In a real test, we might process the stream, but for a simple load test,
                # just confirming the connection is established is enough.
                # We'll read a small part of the stream to ensure it's working.
                async for _ in response.aiter_bytes(chunk_size=1024):
                    print(f"[User {user_id}] Receiving stream data...")
                    break # Break after the first chunk for this test
            else:
                print(f"[User {user_id}] Request failed with status: {response.status_code}")
                print(f"[User {user_id}] Response: {response.text}")

    except Exception as e:
        print(f"[User {user_id}] An error occurred: {e}")

async def main():
    """Main function to run the concurrency test."""
    # Create a placeholder image file for the test
    try:
        with open(IMAGE_PATH, "wb") as f:
            f.write(os.urandom(1024)) # Create a dummy 1KB PNG-like file
        print(f"Created a dummy test image: {IMAGE_PATH}")
    except Exception as e:
        print(f"Could not create dummy test image: {e}")
        return

    async with httpx.AsyncClient() as client:
        tasks = [run_user_simulation(client, i + 1) for i in range(NUM_CONCURRENT_USERS)]
        await asyncio.gather(*tasks)

    # Clean up the placeholder image
    if os.path.exists(IMAGE_PATH):
        os.remove(IMAGE_PATH)
        print(f"Cleaned up dummy test image: {IMAGE_PATH}")

if __name__ == "__main__":
    print(f"Starting concurrency test with {NUM_CONCURRENT_USERS} simultaneous users...")
    print("Ensure your backend server is running.")
    asyncio.run(main())
