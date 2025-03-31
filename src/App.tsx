import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Power, DollarSign, Activity, Clock } from 'lucide-react';
import { format } from 'date-fns';
interface LoadStatus {
  status: Record<string, string>;
  power: Record<string, number>;
  cost: number;
}

interface HistoryData {
  timestamp: string;
  cost: number;
  [key: string]: any;
}

function App() {
  const [currentStatus, setCurrentStatus] = useState<LoadStatus | null>(null);
  const [history, setHistory] = useState<HistoryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, historyRes] = await Promise.all([
          axios.get('http://localhost:5000/api/status'),
          axios.get('http://localhost:5000/api/history')
        ]);
        setCurrentStatus(statusRes.data);
        console.log(statusRes.data);
        
        setHistory(historyRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
  }, []);

  const handleToggle = async (load: string) => {
    if (!currentStatus) return;
    
    setUpdating(load);
    const newStatus = currentStatus.status[load] === 'ON' ? 'OFF' : 'ON';
    
    try {
      await axios.post('http://localhost:5000/api/toggle', {
        load,
        status: newStatus
      });
      
      // Update local state
      setCurrentStatus(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          status: {
            ...prev.status,
            [load]: newStatus
          }
        };
      });
    } catch (error) {
      console.error('Error toggling load:', error);
      // Revert the toggle if there's an error
      alert('Failed to toggle load. Please try again.');
    } finally {
      setUpdating(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-500" />
              <span className="ml-2 text-xl font-semibold text-gray-900">Blitz⚡</span>
            </div>
            <div className="flex items-center">
              <Clock className="h-5 w-5 text-gray-500" />
              <span className="ml-2 text-gray-600">{format(new Date(), 'PPpp')}</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Current Status */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {currentStatus && Object.entries(currentStatus.status).map(([load, status]) => (
              <div key={load} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Power className={`h-5 w-5 ${status === 'ON' ? 'text-green-500' : 'text-red-500'}`} />
                    <span className="ml-2 font-medium">{load}</span>
                  </div>
                  <button
                    onClick={() => handleToggle(load)}
                    disabled={updating === load}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      status === 'ON' ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        status === 'ON' ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
                <div className="mt-2">
                  <span className="text-sm text-gray-500">Power Consumption:</span>
                  <span className="ml-2 font-medium">{Math.round(currentStatus.power[`${load}_Power`])} W</span>
                </div>
              </div>
            ))}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center">
                <DollarSign className="h-5 w-5 text-blue-500" />
                <span className="ml-2 font-medium">Current Cost</span>
              </div>
              <div className="mt-2">
                <span className="text-2xl font-bold text-blue-600">
                  ${currentStatus?.cost.toFixed(2)}
                </span>
                <span className="ml-1 text-sm text-gray-500">/hour</span>
              </div>
            </div>
          </div>
        </div>

        {/* Historical Data */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">24-Hour Cost History</h2>
          <div className="w-full h-[400px]">
            <LineChart
              width={1000}
              height={400}
              data={history}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => format(new Date(value), 'HH:mm')}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => format(new Date(value), 'PPpp')}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cost']}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;