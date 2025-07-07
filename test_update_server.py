"""
Minimal test server for update endpoints
"""
from flask import Flask, jsonify
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.modules.update import create_update_endpoints

app = Flask(__name__)

# Register update endpoints
print("Registering update endpoints...")
create_update_endpoints(app)

@app.route('/')
def index():
    return "Update Test Server - Try /api/update/check"

@app.route('/api/test')
def test():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} {list(rule.methods)}")
    
    print("\nStarting test server on http://localhost:5555")
    app.run(port=5555, debug=True)
