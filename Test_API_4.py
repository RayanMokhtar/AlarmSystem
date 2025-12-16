import requests

url = "http://127.0.0.1:8000/upload-video"

with open("video_test.mp4", "rb") as f:
    response = requests.post(
        url,
        files={"file": ("video_test.mp4", f, "video/mp4")}
    )

print(response.status_code)
print(response.json())
