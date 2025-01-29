import os
from flask import Flask, render_template, request, redirect, url_for
from google.cloud import storage

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "images"
BUCKET_NAME = "images-uploads-bucket"  # Replace with your GCP bucket name

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize GCP Storage Client
storage_client = storage.Client()

@app.route("/")
def index():
    """Render the homepage with upload and list options."""
    try:
        blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix="images/"))
        images = [
            {"filename": blob.name, "url": blob.public_url}
            for blob in blobs
            if not blob.name.endswith("/")  # Exclude subdirectories
        ]
        return render_template("index.html", images=images)
    except Exception as e:
        print("Error listing blobs:", str(e))
        return "An error occurred while listing images.", 500

@app.route("/upload", methods=["POST"])
def upload():
    """Handle image upload and store it in GCP Cloud Storage."""
    try:
        if "file" not in request.files:
            return "No file part in the request", 400

        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400

        if file:
            # Save file locally
            local_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            print("Saving file locally to:", local_path)
            file.save(local_path)

            # Upload file to Cloud Storage
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(f"images/{file.filename}")
            print("Uploading file to GCS:", blob)
            blob.upload_from_filename(local_path)

            # Make file publicly accessible
            print("Making file public...")
            blob.make_public()
            print("File is now public at:", blob.public_url)

            # Remove local copy
            os.remove(local_path)
            print("Removed local file:", local_path)

            return redirect("/")
    except Exception as e:
        print("Error during file upload:", str(e))
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
