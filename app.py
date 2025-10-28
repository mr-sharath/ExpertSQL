from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import openai
import json
from neon_db import get_schema, execute_query, validate_sql as validate_neon_sql

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Verify Neon DB connection
if not os.getenv('NEON_DB_URL'):
    raise ValueError("NEON_DB_URL not found in environment variables")

# Get database schema for context
def get_database_schema():
    return get_schema()

# Validate SQL query using Neon's validation
def validate_sql(query):
    return validate_neon_sql(query)

def generate_natural_language_summary(query, results):
    """Generate a natural language summary of query results"""
    if not results:
        return "No results found for your query."
    
    # Get column names from the first result
    sample_result = results[0]
    columns = list(sample_result.keys())
    
    # Count the number of results
    result_count = len(results)
    
    # Prepare data for the prompt (handle non-serializable types)
    def safe_serialize(obj):
        try:
            if hasattr(obj, 'hex'):  # Handle UUID
                return str(obj)
            return str(obj)  # Fallback to string representation
        except:
            return "[complex data]"
    
    # Create a safe version of results for the prompt
    safe_results = []
    for row in results[:5]:  # Only use first 5 rows for the prompt
        safe_row = {}
        for k, v in row.items():
            try:
                # Skip vector and binary data from the prompt
                if 'vector' in str(k).lower() or 'embedding' in str(k).lower():
                    continue
                safe_row[k] = safe_serialize(v)
            except:
                continue
        safe_results.append(safe_row)
    
    # Create a prompt for the LLM to generate a summary
    prompt = f"""
    You are a data analyst. Given the following query and its results, provide a concise, 
    natural language summary of what the data shows. Be specific about the numbers and 
    any important patterns or insights. Keep it to 2-3 sentences maximum.
    
    Query: {query}
    
    Results (showing {len(safe_results)} of {result_count} rows):
    {json.dumps(safe_results, indent=2, default=str)}
    """
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst that explains query results in clear, concise natural language. Focus on the key insights and patterns in the data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        # Fallback to a simple summary if LLM call fails
        return f"Found {result_count} results with columns: {', '.join(str(col) for col in columns)}."

# Generate SQL from natural language
def generate_sql(natural_language):
    schema = get_database_schema()
    
    prompt = f"""
    You are a SQL expert. Given the following database schema:
    {json.dumps(schema, indent=2)}
    
    Convert the following natural language query into a SQL query:
    "{natural_language}"
    
    Return ONLY the SQL query, nothing else. The query should be compatible with PostgreSQL.
    """
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that converts natural language to SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        # Clean up the SQL query (remove code blocks if present)
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    except Exception as e:
        raise Exception(f"Error generating SQL: {str(e)}")

# API endpoint for processing queries
@app.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        natural_language = data.get('query')
        
        if not natural_language:
            return jsonify({"error": "No query provided"}), 400
        
        # Generate SQL from natural language
        sql_query = generate_sql(natural_language)
        
        # Validate the generated SQL
        is_valid, error_message = validate_sql(sql_query)
        if not is_valid:
            return jsonify({
                "error": f"Invalid SQL query: {error_message}",
                "generated_sql": sql_query
            }), 400
        
        # Execute the query
        try:
            # Execute the query using Neon DB
            results = execute_query(sql_query)
            
            # Generate natural language summary
            summary = generate_natural_language_summary(natural_language, results)
            
            return jsonify({
                "success": True,
                "query": natural_language,
                "sql": sql_query,
                "results": results,
                "summary": summary
            })
        except Exception as e:
            return jsonify({
                "error": f"Error executing query: {str(e)}",
                "generated_sql": sql_query
            }), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve the frontend
@app.route('/')
def index():
    return render_template('index.html')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Run the app
    app.run(debug=True, port=5000)
