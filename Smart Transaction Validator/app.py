from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import re
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -----------------------------
# CONFIG: COUNTRY PHONE RULES
# -----------------------------
PHONE_RULES = {
    "IN": 10,
    "SG": 8
}

# -----------------------------
# VALIDATION FUNCTIONS
# -----------------------------
def validate_phone(phone, country):
    if pd.isna(phone):
        return False
    phone = str(phone)
    return phone.isdigit() and len(phone) == PHONE_RULES.get(country, 10)

def validate_date(date_str):
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            datetime.strptime(str(date_str), fmt)
            return True
        except:
            pass
    return False

def clean_data(df):
    df["phone_valid"] = df.apply(lambda x: validate_phone(x["phone"], x["country"]), axis=1)
    df["date_valid"] = df["order_date"].apply(validate_date)

    # keep only valid rows
    cleaned = df[(df["phone_valid"] == True) & (df["date_valid"] == True)]

    return cleaned

# -----------------------------
# SPLIT FILE INTO CHUNKS
# -----------------------------
def split_file(df, chunk_size=100):
    files = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        file_path = os.path.join(OUTPUT_FOLDER, f"cleaned_part_{i}.csv")
        chunk.to_csv(file_path, index=False)
        files.append(file_path)
    return files

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df = pd.read_csv(filepath)

    cleaned = clean_data(df)

    output_file = os.path.join(OUTPUT_FOLDER, "cleaned_data.csv")
    cleaned.to_csv(output_file, index=False)

    split_file(cleaned, 50)

    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)