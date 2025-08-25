# Infinite SQL - Natural Language to SQL Query Tool

Infinite SQL is a web application that allows users to query an e-commerce database using natural language. It leverages OpenAI's API to translate natural language queries into SQL, making database interaction more accessible to non-technical users.

## Features

- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **E-commerce Focus**: Pre-configured with an e-commerce database schema
- **Web Interface**: Simple and intuitive web interface for running queries
- **Secure**: Built-in protection against SQL injection
- **RESTful API**: Programmatic access to the query functionality

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd infinite_SQL
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

## Usage

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. Enter your natural language query in the input field and click "Run Query"

## API Endpoints

- `POST /api/query` - Process a natural language query
  - Request body: `{"query": "your natural language query"}`
  - Response: `{"sql": "generated SQL query", "results": [query results]}`

- `GET /health` - Health check endpoint

## Project Structure

```
infinite_SQL/
├── app.py              # Main application file
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not in version control)
├── ecommerce.db        # SQLite database file
├── static/             # Static files (CSS, JS)
│   └── styles.css
├── templates/          # HTML templates
│   └── index.html
└── README.md           # This file
```

## Security Notes

- Always keep your `.env` file secure and never commit it to version control
- The application includes basic SQL injection protection
- For production use, consider implementing additional security measures like:
  - User authentication
  - Rate limiting
  - Input validation
  - HTTPS

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and SQLAlchemy
- Uses OpenAI's API for natural language processing
- Inspired by the need for more accessible database querying tools
