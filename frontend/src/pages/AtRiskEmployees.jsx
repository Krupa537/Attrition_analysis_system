import React, { useState, useEffect } from 'react';
import API from '../api';

export default function AtRiskEmployees({ analysis }) {
  const [atRiskData, setAtRiskData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('risk');
  const [filterLevel, setFilterLevel] = useState('all');

  useEffect(() => {
    if (analysis?.id) {
      fetchAtRiskEmployees();
    }
  }, [analysis?.id]);

  const fetchAtRiskEmployees = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(API.getAtRiskEmployees(analysis.id));
      if (!res.ok) throw new Error('Failed to fetch at-risk employees');
      const data = await res.json();
      setAtRiskData(data);

      // Show notification if critical employees at risk
      if (data.critical_count > 0) {
        showNotification(`⚠️ ALERT: ${data.critical_count} employees are at critical risk of leaving!`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message) => {
    if (Notification.permission === 'granted') {
      new Notification('Employee Attrition Alert', {
        body: message,
        icon: '⚠️',
        tag: 'attrition-alert'
      });
    }
  };

  if (!atRiskData) return null;

  const { total_employees, at_risk_count, risk_percentage, at_risk_employees } = atRiskData;

  // Filter employees
  let filtered = at_risk_employees;
  if (filterLevel !== 'all') {
    filtered = at_risk_employees.filter(emp => emp.risk_level === filterLevel || (filterLevel === 'high' && (emp.risk_level === 'High' || emp.risk_level === 'Critical')));
  }

  // Sort employees
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'risk') {
      return b.attrition_probability - a.attrition_probability;
    }
    return a.index - b.index;
  });

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'Critical':
        return '#ff4444';
      case 'High':
        return '#ff9800';
      case 'Moderate':
        return '#ffc107';
      default:
        return '#666';
    }
  };

  const getRetentionStrategies = (employee) => {
    const strategies = [];
    const data = employee.employee_data || {};

    // Check various factors
    if (data.Overtime === 'Yes') {
      strategies.push('💼 Reduce overtime and workload');
    }
    if (data['Job Satisfaction'] && data['Job Satisfaction'] < 3) {
      strategies.push('😊 Improve job satisfaction - conduct engagement surveys');
    }
    if (data['Job Involvement'] && data['Job Involvement'] < 3) {
      strategies.push('🎯 Increase job involvement - assign meaningful projects');
    }
    if (data['Years Since Last Promotion'] && data['Years Since Last Promotion'] > 5) {
      strategies.push('📈 Consider promotion or career advancement');
    }
    if (data['Monthly Income'] && data['Monthly Income'] < 3000) {
      strategies.push('💰 Review and adjust salary');
    }
    if (data['Years At Company'] && data['Years At Company'] < 2) {
      strategies.push('👥 Provide better onboarding and mentorship');
    }
    if (data['Work Life Balance'] && data['Work Life Balance'] < 3) {
      strategies.push('⏰ Improve work-life balance initiatives');
    }

    return strategies.length > 0 ? strategies : ['💬 Schedule one-on-one meeting to understand concerns'];
  };

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '20px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h2 style={{ margin: 0, marginBottom: 10 }}>⚠️ Employee Attrition Alert</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{at_risk_count}</div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>Employees at Risk</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{total_employees}</div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>Total Employees</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{risk_percentage.toFixed(1)}%</div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>Attrition Risk Rate</div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <div>
          <label style={{ fontSize: '12px' }}>Sort By:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ padding: '5px' }}>
            <option value="risk">Risk Level (Highest First)</option>
            <option value="index">Employee Index</option>
          </select>
        </div>
        <div>
          <label style={{ fontSize: '12px' }}>Filter Risk Level:</label>
          <select value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)} style={{ padding: '5px' }}>
            <option value="all">All Levels ({at_risk_employees.length})</option>
            <option value="Critical">Critical ({at_risk_employees.filter(e => e.risk_level === 'Critical').length})</option>
            <option value="High">High ({at_risk_employees.filter(e => e.risk_level === 'High').length})</option>
            <option value="Moderate">Moderate ({at_risk_employees.filter(e => e.risk_level === 'Moderate').length})</option>
          </select>
        </div>
      </div>

      {/* Employees List */}
      <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {sorted.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            No employees in this risk category
          </div>
        ) : (
          sorted.map((employee, idx) => (
            <div key={idx} style={{
              background: 'white',
              border: `2px solid ${getRiskColor(employee.risk_level)}`,
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '12px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                    Employee #{employee.index}
                  </div>
                  <div style={{
                    display: 'inline-block',
                    background: getRiskColor(employee.risk_level),
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    marginTop: '5px'
                  }}>
                    {employee.risk_level} RISK
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '20px', fontWeight: 'bold', color: getRiskColor(employee.risk_level) }}>
                    {(employee.attrition_probability * 100).toFixed(1)}%
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Attrition Probability</div>
                </div>
              </div>

              {/* Employee Details */}
              <div style={{
                background: '#f5f5f5',
                padding: '10px',
                borderRadius: '4px',
                marginBottom: '10px',
                fontSize: '13px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  {employee.employee_data.Age && (
                    <div>
                      <strong>Age:</strong> {employee.employee_data.Age}
                    </div>
                  )}
                  {employee.employee_data.Department && (
                    <div>
                      <strong>Department:</strong> {employee.employee_data.Department}
                    </div>
                  )}
                  {employee.employee_data.JobRole && (
                    <div>
                      <strong>Job Role:</strong> {employee.employee_data.JobRole}
                    </div>
                  )}
                  {employee.employee_data.MonthlyIncome && (
                    <div>
                      <strong>Monthly Income:</strong> ${employee.employee_data.MonthlyIncome}
                    </div>
                  )}
                  {employee.employee_data['Years At Company'] && (
                    <div>
                      <strong>Tenure:</strong> {employee.employee_data['Years At Company']} years
                    </div>
                  )}
                  {employee.employee_data.OverTime && (
                    <div>
                      <strong>Overtime:</strong> {employee.employee_data.OverTime}
                    </div>
                  )}
                </div>
              </div>

              {/* Retention Strategies */}
              <div style={{ marginTop: '10px' }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '13px' }}>
                  💡 Recommended Retention Strategies:
                </div>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
                  {getRetentionStrategies(employee).map((strategy, i) => (
                    <li key={i} style={{ marginBottom: '4px', color: '#333' }}>
                      {strategy}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Summary Statistics */}
      <div style={{
        marginTop: '20px',
        background: '#f9f9f9',
        padding: '15px',
        borderRadius: '8px',
        borderLeft: '4px solid #667eea'
      }}>
        <h3 style={{ margin: 0, marginBottom: 10 }}>📊 Key Insights</h3>
        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
          <li>Focus retention efforts on {at_risk_count} identified at-risk employees</li>
          <li>Priority: Address critical risk employees immediately</li>
          <li>Consider implementing mentorship programs and career development plans</li>
          <li>Review compensation and work-life balance policies</li>
          <li>Schedule regular check-ins to monitor employee satisfaction</li>
        </ul>
      </div>
    </div>
  );
}
