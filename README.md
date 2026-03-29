# Simple MongoDB Python App

This is a small command-line application that stores sales records in MongoDB.

## Features

- Create sale records
- Read/list sales
- Update sale price
- Delete sales

## Requirements

- Python 3.10+
- MongoDB running locally or a MongoDB Atlas connection string

## Setup

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set your MongoDB connection string:
   ```powershell
   copy .env.example .env
   ```
3. Run the app:
   ```powershell
   python app.py
   ```

If `MONGODB_URI` is not set, the app defaults to `mongodb://localhost:27017`.
