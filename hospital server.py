#!/usr/bin/env python3
"""
Flask web server for Saskatoon Hospital Capacity Tracker
Serves the React frontend and provides API endpoints for hospital data
"""

from flask import Flask, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = 'hospital_data.json'
BACKUP_FILE = 'hospital_data_backup.json'

def load_hospital_data():
    """Load hospital data from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info("Loaded current hospital data")
                return data
        elif os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'r') as f:
                data = json.load(f)
                logger.warning("Loaded backup hospital data")
                return data
        else:
            logger.error("No data files found")
            return None
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

@app.route('/')
def index():
    """Serve the main hospital tracker page"""
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Saskatoon Hospital Capacity Tracker</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
    </style>
</head>
<body>
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect } = React;
        const { AlertTriangle, Clock, Users, Bed, Activity } = lucide;

        const SaskatoonHospitalTracker = () => {
            const [hospitalData, setHospitalData] = useState(null);
            const [loading, setLoading] = useState(true);
            const [error, setError] = useState(null);
            const [lastUpdated, setLastUpdated] = useState(new Date());

            // Fetch data from API
            const fetchData = async () => {
                try {
                    const response = await fetch('/api/hospitals');
                    if (!response.ok) throw new Error('Failed to fetch data');
                    const data = await response.json();
                    setHospitalData(data);
                    setError(null);
                    setLastUpdated(new Date());
                } catch (err) {
                    setError(err.message);
                    console.error('Error fetching data:', err);
                }
                setLoading(false);
            };

            useEffect(() => {
                fetchData();
                // Refresh data every 15 minutes
                const interval = setInterval(fetchData, 15 * 60 * 1000);
                return () => clearInterval(interval);
            }, []);

            // Calculate capacity percentage and status
            const getCapacityInfo = (hospital) => {
                const percentage = ((hospital.totalOccupied / hospital.totalPlanned) * 100).toFixed(1);
                let status = 'normal';
                let statusText = 'Normal';
                
                if (hospital.totalOvercapacity > 0) {
                    status = 'overcapacity';
                    statusText = 'Over Capacity';
                } else if (percentage >= 95) {
                    status = 'high';
                    statusText = 'High Capacity';
                } else if (percentage >= 85) {
                    status = 'moderate';
                    statusText = 'Moderate';
                }
                
                return { percentage, status, statusText };
            };

            const getStatusColor = (status) => {
                switch (status) {
                    case 'overcapacity': return 'bg-red-500';
                    case 'high': return 'bg-orange-500';
                    case 'moderate': return 'bg-yellow-500';
                    default: return 'bg-green-500';
                }
            };

            if (loading) {
                return (
                    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                            <p className="mt-4 text-gray-600">Loading hospital data...</p>
                        </div>
                    </div>
                );
            }

            if (error || !hospitalData) {
                return (
                    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                        <div className="text-center">
                            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                            <h2 className="text-xl font-semibold text-gray-900 mb-2">Data Unavailable</h2>
                            <p className="text-gray-600 mb-4">{error || 'Unable to load hospital data'}</p>
                            <button 
                                onClick={fetchData}
                                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                );
            }

            const hospitals = hospitalData.hospitals || {};
            const totalAdmittedInED = Object.values(hospitals).reduce((sum, h) => sum + (h.admittedInED || 0), 0);
            const totalActiveConsults = Object.values(hospitals).reduce((sum, h) => sum + (h.activeConsults || 0), 0);

            return (
                <div className="min-h-screen bg-gray-50">
                    {/* Header */}
                    <header className="bg-white shadow-sm border-b">
                        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <h1 className="text-2xl font-bold text-gray-900">Saskatoon Hospital Capacity</h1>
                                    <p className="text-sm text-gray-600 mt-1">Real-time emergency department status</p>
                                </div>
                                <div className="flex items-center text-sm text-gray-500 mt-2 sm:mt-0">
                                    <Clock className="w-4 h-4 mr-1" />
                                    <span>Updated: {hospitalData.timestamp || 'Unknown'}</span>
                                </div>
                            </div>
                        </div>
                    </header>

                    {/* Emergency Summary */}
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                <Activity className="w-5 h-5 mr-2 text-red-500" />
                                Emergency Department Summary
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="bg-red-50 p-4 rounded-lg">
                                    <div className="flex items-center">
                                        <Users className="w-6 h-6 text-red-600 mr-3" />
                                        <div>
                                            <p className="text-sm text-red-600 font-medium">Admitted Patients in ED</p>
                                            <p className="text-2xl font-bold text-red-700">{totalAdmittedInED}</p>
                                            <p className="text-xs text-red-500">Patients admitted but no bed available</p>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-amber-50 p-4 rounded-lg">
                                    <div className="flex items-center">
                                        <AlertTriangle className="w-6 h-6 text-amber-600 mr-3" />
                                        <div>
                                            <p className="text-sm text-amber-600 font-medium">Active Consults</p>
                                            <p className="text-2xl font-bold text-amber-700">{totalActiveConsults}</p>
                                            <p className="text-xs text-amber-500">Specialist consultations in progress</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Hospital Cards */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {Object.entries(hospitals).map(([hospitalName, hospital]) => {
                                const capacityInfo = getCapacityInfo(hospital);
                                
                                return (
                                    <div key={hospitalName} className="bg-white rounded-lg shadow-sm border overflow-hidden">
                                        <div className="p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <div>
                                                    <h3 className="text-lg font-semibold text-gray-900">{hospital.shortName || hospitalName}</h3>
                                                    <p className="text-sm text-gray-600">{hospitalName}</p>
                                                </div>
                                                <div className="text-right">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getStatusColor(capacityInfo.status)}`}>
                                                        {capacityInfo.statusText}
                                                    </span>
                                                    <p className="text-sm text-gray-500 mt-1">{capacityInfo.percentage}% occupied</p>
                                                </div>
                                            </div>

                                            {/* Capacity Bar */}
                                            <div className="mb-6">
                                                <div className="flex justify-between text-sm text-gray-600 mb-1">
                                                    <span>Capacity</span>
                                                    <span>{hospital.totalOccupied} / {hospital.totalPlanned} beds</span>
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2">
                                                    <div 
                                                        className={`h-2 rounded-full ${getStatusColor(capacityInfo.status)}`}
                                                        style={{ width: `${Math.min(capacityInfo.percentage, 100)}%` }}
                                                    ></div>
                                                </div>
                                                {hospital.totalOvercapacity > 0 && (
                                                    <p className="text-xs text-red-600 mt-1 font-medium">
                                                        +{hospital.totalOvercapacity} patients over capacity
                                                    </p>
                                                )}
                                            </div>

                                            {/* Emergency Department Data */}
                                            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                                                <div className="text-center">
                                                    <div className="flex items-center justify-center mb-1">
                                                        <Users className="w-4 h-4 text-red-500 mr-1" />
                                                        <span className="text-sm font-medium text-gray-700">Admitted in ED</span>
                                                    </div>
                                                    <p className="text-xl font-bold text-red-600">{hospital.admittedInED !== null ? hospital.admittedInED : '—'}</p>
                                                    {hospital.admittedInED === null && (
                                                        <p className="text-xs text-gray-400">Data not available</p>
                                                    )}
                                                </div>
                                                <div className="text-center">
                                                    <div className="flex items-center justify-center mb-1">
                                                        <AlertTriangle className="w-4 h-4 text-amber-500 mr-1" />
                                                        <span className="text-sm font-medium text-gray-700">Active Consults</span>
                                                    </div>
                                                    <p className="text-xl font-bold text-amber-600">{hospital.activeConsults !== null ? hospital.activeConsults : '—'}</p>
                                                    {hospital.activeConsults === null && (
                                                        <p className="text-xs text-gray-400">Data not available</p>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Additional Stats */}
                                            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
                                                <div className="text-center">
                                                    <p className="text-xs text-gray-500">Vacant</p>
                                                    <p className="text-sm font-semibold text-green-600">{hospital.totalVacant}</p>
                                                </div>
                                                <div className="text-center">
                                                    <p className="text-xs text-gray-500">ALC Patients</p>
                                                    <p className="text-sm font-semibold text-blue-600">{hospital.totalALC}</p>
                                                </div>
                                                <div className="text-center">
                                                    <p className="text-xs text-gray-500">Overcapacity</p>
                                                    <p className="text-sm font-semibold text-red-600">{hospital.totalOvercapacity}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Disclaimer */}
                        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex">
                                <AlertTriangle className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                                <div className="text-sm text-blue-800">
                                    <p className="font-medium mb-2">Important Disclaimer</p>
                                    <p className="mb-2">
                                        This information is updated every 15 minutes and represents a point in time. It is not a complete picture of Saskatoon hospital capacity or occupancy. Hospital occupancy levels change continuously throughout the day and night as patients are admitted and discharged.
                                    </p>
                                    <p className="mb-2">
                                        The report includes vacant beds but does not show when a vacant bed has been reserved for the next incoming patient from other areas or those unoccupied due to temporary bed closures.
                                    </p>
                                    <p>
                                        <strong>Alternate Level of Care (ALC)</strong> patients are assessed by the care team as needing to remain in hospital but no longer need the specialty care of that unit. Caution should be taken when using this data as there are known data quality issues associated with ALC data collection.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Data Source */}
                        <div className="mt-4 text-center text-xs text-gray-500">
                            Data source: <a href="https://www.ehealthsask.ca/reporting/Documents/SaskatoonHospitalBedCapacity.pdf" 
                                         className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                                Saskatchewan Health Authority Hospital Occupancy Report
                            </a>
                        </div>
                    </div>
                </div>
            );
        };

        ReactDOM.render(<SaskatoonHospitalTracker />, document.getElementById('root'));
    </script>
</body>
</html>
    """
    return render_template_string(html_template)

@app.route('/api/hospitals')
def api_hospitals():
    """API endpoint to get hospital data"""
    data = load_hospital_data()
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Hospital data not available'}), 503

@app.route('/api/status')
def api_status():
    """API endpoint to check system status"""
    data = load_hospital_data()
    
    status = {
        'status': 'ok' if data else 'error',
        'dataAvailable': data is not None,
        'lastCheck': datetime.now().isoformat(),
        'dataFile': os.path.exists(DATA_FILE),
        'backupFile': os.path.exists(BACKUP_FILE)
    }
    
    if data:
        status['dataTimestamp'] = data.get('timestamp')
        status['lastUpdated'] = data.get('lastUpdated')
        status['hospitalCount'] = len(data.get('hospitals', {}))
    
    return jsonify(status)

@app.route('/api/hospitals/<hospital_code>')
def api_hospital_detail(hospital_code):
    """API endpoint to get specific hospital data"""
    data = load_hospital_data()
    if not data:
        return jsonify
