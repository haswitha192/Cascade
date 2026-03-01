import requests

url = "http://localhost:7071/api/processResume"

with open("resume.pdf", "rb") as f:
    response = requests.post(
        url,
        data=f,
        headers={"Content-Type": "application/pdf"}
    )

print(response.status_code)
print(response.text)