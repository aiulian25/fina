"""
Add route to serve service worker from root
"""
from flask import send_from_directory
import os

def register_pwa_routes(app):
    @app.route('/service-worker.js')
    def service_worker():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'js'),
            'service-worker.js',
            mimetype='application/javascript'
        )
    
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'manifest.json',
            mimetype='application/json'
        )
