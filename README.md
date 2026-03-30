# Sales App (MongoDB + Flask)

This project is a full-stack sales tracker with:

- Flask backend API
- MongoDB storage
- Browser frontend (HTML, CSS, JavaScript)

## Features

- Create, list, update, and delete sales
- Automatic total calculation (`quantity * price`)
- Real-time table updates in the UI

## Project Structure

```text
sales_app/
	app.py
	requirements.txt
	.env.example
	templates/
		index.html
	static/
		styles.css
		app.js
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment values:

```bash
copy .env.example .env
```

4. Edit `.env` and set your MongoDB URI.

## Run

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## API Endpoints

- `GET /api/health`
- `GET /api/sales`
- `POST /api/sales`
- `PUT /api/sales/<sale_id>`
- `DELETE /api/sales/<sale_id>`

