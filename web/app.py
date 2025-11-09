"""
Flask Web Application for West Bengal Electoral Data
"""

import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import DataStorage
from src.validator import DataValidator
from src.utils import load_config, setup_logging


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
config = load_config('config/config.yaml')
setup_logging(config)
logger = logging.getLogger(__name__)

# Initialize components
storage = DataStorage(config)
validator = DataValidator(config)

# Configure app
web_config = config.get('web', {})
app.config['SECRET_KEY'] = web_config.get('secret_key', 'dev-secret-key')


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/api/districts')
def get_districts():
    """Get list of districts"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        districts_file = output_dir / 'districts.json'
        
        if districts_file.exists():
            with open(districts_file, 'r') as f:
                districts = json.load(f)
            return jsonify({'success': True, 'data': districts})
        else:
            return jsonify({'success': False, 'error': 'Districts data not found'})
    
    except Exception as e:
        logger.error(f"Error fetching districts: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/assemblies')
def get_assemblies():
    """Get list of assemblies"""
    try:
        district_no = request.args.get('district')
        output_dir = Path(config['directories']['output_dir'])
        assemblies_file = output_dir / 'assemblies.json'
        
        if not assemblies_file.exists():
            return jsonify({'success': False, 'error': 'Assemblies data not found'})
        
        with open(assemblies_file, 'r') as f:
            assemblies = json.load(f)
        
        # Filter by district if specified
        if district_no:
            assemblies = [a for a in assemblies if a.get('distNo') == int(district_no)]
        
        return jsonify({'success': True, 'data': assemblies})
    
    except Exception as e:
        logger.error(f"Error fetching assemblies: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/parts/<int:ac_number>')
def get_parts(ac_number):
    """Get parts for an AC"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        parts_file = output_dir / f'AC_{ac_number:03d}_parts.json'
        
        if parts_file.exists():
            with open(parts_file, 'r') as f:
                parts = json.load(f)
            return jsonify({'success': True, 'data': parts})
        else:
            return jsonify({'success': False, 'error': f'Parts data not found for AC {ac_number}'})
    
    except Exception as e:
        logger.error(f"Error fetching parts: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/voters/<int:ac_number>/<int:part_number>')
def get_voters(ac_number, part_number):
    """Get voters for an AC and part"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        data_file = output_dir / f'AC_{ac_number:03d}_Part_{part_number:03d}.json'
        
        if not data_file.exists():
            return jsonify({'success': False, 'error': 'Voter data not found'})
        
        data = storage.load_voters(data_file)
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        voters = data['voters']
        total = len(voters)
        start = (page - 1) * per_page
        end = start + per_page
        
        return jsonify({
            'success': True,
            'data': {
                'metadata': data['metadata'],
                'voters': voters[start:end],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error fetching voters: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search')
def search_voters():
    """Search for voters"""
    try:
        query = request.args.get('q', '').strip()
        ac_number = request.args.get('ac')
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'})
        
        output_dir = Path(config['directories']['output_dir'])
        results = []
        
        # Search in specified AC or all
        if ac_number:
            pattern = f'AC_{int(ac_number):03d}_Part_*.json'
        else:
            pattern = 'AC_*_Part_*.json'
        
        data_files = output_dir.glob(pattern)
        
        for data_file in data_files:
            data = storage.load_voters(data_file)
            voters = data['voters']
            
            # Search in voters
            for voter in voters:
                if (query.lower() in voter.get('name', '').lower() or
                    query.upper() in voter.get('epic_no', '').upper()):
                    results.append({
                        'voter': voter,
                        'ac_number': data['metadata']['ac_number'],
                        'part_number': data['metadata']['part_number']
                    })
        
        return jsonify({'success': True, 'data': results[:100]})  # Limit to 100 results
    
    except Exception as e:
        logger.error(f"Error searching voters: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/validate/<int:ac_number>/<int:part_number>')
def validate_part(ac_number, part_number):
    """Validate voters for a part"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        data_file = output_dir / f'AC_{ac_number:03d}_Part_{part_number:03d}.json'
        
        if not data_file.exists():
            return jsonify({'success': False, 'error': 'Voter data not found'})
        
        data = storage.load_voters(data_file)
        voters = data['voters']
        
        # Perform validation
        sample_size = int(request.args.get('sample', 10))
        report = validator.validate_batch(voters, ac_number, part_number, sample_size)
        
        return jsonify({'success': True, 'data': report})
    
    except Exception as e:
        logger.error(f"Error validating: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/<int:ac_number>/<int:part_number>')
def export_data(ac_number, part_number):
    """Export voter data"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        data_file = output_dir / f'AC_{ac_number:03d}_Part_{part_number:03d}.json'
        
        if not data_file.exists():
            return jsonify({'success': False, 'error': 'Voter data not found'})
        
        format_type = request.args.get('format', 'json')
        
        if format_type == 'csv':
            data = storage.load_voters(data_file)
            voters = data['voters']
            
            # Export to CSV
            csv_file = output_dir / f'AC_{ac_number:03d}_Part_{part_number:03d}.csv'
            storage.export_to_csv(voters, csv_file)
            
            return send_file(csv_file, as_attachment=True)
        
        else:
            return send_file(data_file, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error exporting: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    try:
        output_dir = Path(config['directories']['output_dir'])
        
        # Create or load index
        index = storage.create_index(output_dir)
        
        return jsonify({'success': True, 'data': index})
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'success': False, 'error': str(e)})


def main():
    """Run the Flask app"""
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug', False)
    
    logger.info(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
