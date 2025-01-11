
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# ... your routes and other code ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    try:
        data = request.get_json()
        record_id = data['id']
        url = data['fields'].get('Background Video URL')

        if url:
            print(f"Received URL for record {record_id}: {url}")
            # Add your video processing logic here

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
