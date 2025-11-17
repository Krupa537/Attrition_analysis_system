import React, { useState } from 'react'

export default function Insights({ analysis, features, dataset }) {
  const [hoveredCard, setHoveredCard] = useState(null)
  const [expandedFactors, setExpandedFactors] = useState(false)

  if (!analysis || !features || features.length === 0) return null

  // Extract key insights from feature importances and metrics
  const topFeatures = features.slice(0, 5)
  
  // Calculate attrition statistics
  const calculateAttritionStats = () => {
    // Extract metrics to estimate attrition percentage
    const metrics = analysis.metrics || {}
    const confusionMatrix = analysis.artifacts?.confusion_matrix || []
    
    let totalEmployees = 0
    let attritionCount = 0
    
    // Try to estimate from confusion matrix
    if (Array.isArray(confusionMatrix) && confusionMatrix.length > 0) {
      if (confusionMatrix[0]?.length === 2) {
        // Standard 2x2 confusion matrix: [[TN, FP], [FN, TP]]
        const tn = confusionMatrix[0][0] || 0
        const fp = confusionMatrix[0][1] || 0
        const fn = confusionMatrix[1]?.[0] || 0
        const tp = confusionMatrix[1]?.[1] || 0
        
        totalEmployees = tn + fp + fn + tp
        attritionCount = tp + fn // Actual positive cases
      } else if (confusionMatrix.length === 1 && confusionMatrix[0]?.length === 1) {
        // Single value matrix
        totalEmployees = confusionMatrix[0][0] || 0
        attritionCount = 0
      }
    }
    
    const attritionPercentage = totalEmployees > 0 ? (attritionCount / totalEmployees * 100) : 0
    
    return {
      attritionPercentage: attritionPercentage.toFixed(1),
      totalEmployees,
      attritionCount
    }
  }

  // Calculate overtime impact
  const calculateOvertimeImpact = () => {
    const featureMap = {}
    features.forEach(f => {
      featureMap[f.feature.toLowerCase()] = f
    })
    
    const overtimeFeature = featureMap['overtime_yes'] || featureMap['overtime']
    if (!overtimeFeature) return 0
    
    // Logistic regression coefficient to percentage impact
    // e^coefficient gives odds ratio
    const oddsRatio = Math.exp(overtimeFeature.coef)
    const percentageIncrease = ((oddsRatio - 1) * 100)
    
    return percentageIncrease.toFixed(1)
  }
  
  const attritionStats = calculateAttritionStats()
  const overtimeImpact = calculateOvertimeImpact()
  
  // Color gradients for different insight types
  const gradients = {
    overtime: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    satisfaction: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    role: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    tenure: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    compensation: 'linear-gradient(135deg, #ff9a56 0%, #ff6a88 100%)',
    performance: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }

  // Generate insights based on top features
  const generateInsights = () => {
    const insights = []
    
    // Look for key features and generate human-readable insights
    const featureMap = {}
    features.forEach(f => {
      featureMap[f.feature.toLowerCase()] = f
    })

    // 1. Overall attrition percentage insight
    if (attritionStats.totalEmployees > 0) {
      insights.push({
        icon: '📊',
        title: 'Overall Attrition Rate',
        text: `${attritionStats.attritionPercentage}% of employees have left the organization`,
        subtext: `${attritionStats.attritionCount} out of ${attritionStats.totalEmployees} employees`,
        type: 'attrition',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        severity: attritionStats.attritionPercentage > 20 ? 'critical' : attritionStats.attritionPercentage > 10 ? 'high' : 'medium'
      })
    }

    // 2. Overtime impact insight
    if (featureMap['overtime_yes'] || featureMap['overtime']) {
      const overtimeCoef = featureMap['overtime_yes']?.coef || featureMap['overtime']?.coef || 0
      if (Math.abs(overtimeCoef) > 0.3) {
        insights.push({
          icon: '⏰',
          title: 'Overtime Impact on Attrition',
          text: `Employees working overtime have ${overtimeImpact}% higher attrition risk compared to those without overtime`,
          subtext: `Overtime workers are ${(Math.exp(overtimeCoef)).toFixed(2)}x more likely to leave`,
          type: 'overtime',
          gradient: gradients.overtime,
          severity: 'high'
        })
      }
    }

    // Check for satisfaction
    const satisfactionFeatures = features.filter(f => f.feature.toLowerCase().includes('satisf'))
    if (satisfactionFeatures.length > 0) {
      const avgSatisfactionCoef = satisfactionFeatures.reduce((acc, f) => acc + f.coef, 0) / satisfactionFeatures.length
      if (Math.abs(avgSatisfactionCoef) > 0.3) {
        insights.push({
          icon: '😟',
          title: 'Job Satisfaction Critical',
          text: 'Low job satisfaction is a strong predictor of employee attrition',
          type: 'satisfaction',
          gradient: gradients.satisfaction,
          severity: 'critical',
          details: `${satisfactionFeatures.length} satisfaction-related factors detected`
        })
      }
    }

    // Check for department/role
    const roleFeatures = features.filter(f => f.feature.toLowerCase().includes('role') || f.feature.toLowerCase().includes('job'))
    if (roleFeatures.length > 0) {
      insights.push({
        icon: '💼',
        title: 'Job Role Matters',
        text: 'Certain job roles show higher attrition rates than others',
        type: 'role',
        gradient: gradients.role,
        severity: 'medium',
        details: `${roleFeatures.length} role-related factors detected`
      })
    }

    // Check for years/tenure
    const tenureFeatures = features.filter(f => f.feature.toLowerCase().includes('year'))
    if (tenureFeatures.length > 0) {
      const avgTenureCoef = tenureFeatures.reduce((acc, f) => acc + Math.abs(f.coef), 0) / tenureFeatures.length
      if (avgTenureCoef > 0.2) {
        insights.push({
          icon: '📅',
          title: 'Tenure Correlation',
          text: 'Years with company is a significant factor in predicting attrition',
          type: 'tenure',
          gradient: gradients.tenure,
          severity: 'high',
          details: `${tenureFeatures.length} tenure-related factors detected`
        })
      }
    }

    // Check for monthly income
    if (featureMap['monthlyincome'] || featureMap['monthly_income']) {
      const incomeCoef = featureMap['monthlyincome']?.coef || featureMap['monthly_income']?.coef || 0
      if (Math.abs(incomeCoef) > 0.3) {
        insights.push({
          icon: '💰',
          title: 'Compensation Impact',
          text: 'Monthly income has a notable relationship with employee attrition',
          type: 'compensation',
          gradient: gradients.compensation,
          severity: 'medium'
        })
      }
    }

    // Add general metrics insight
    if (analysis.metrics) {
      const accuracy = analysis.metrics.accuracy || 0
      const precision = analysis.metrics.precision || 0
      const f1 = analysis.metrics.f1 || 0
      insights.push({
        icon: '🎯',
        title: 'Model Performance',
        text: `Predictions are ${(accuracy * 100).toFixed(1)}% accurate with ${(precision * 100).toFixed(1)}% precision`,
        type: 'performance',
        gradient: gradients.performance,
        severity: 'info',
        details: `F1-Score: ${(f1 * 100).toFixed(1)}%`
      })
    }

    return insights.length > 0 ? insights : [{
      icon: '🔍',
      title: 'Analysis Summary',
      text: 'Review the feature importances above to understand key attrition drivers',
      type: 'default',
      gradient: gradients.default,
      severity: 'info'
    }]
  }

  const insights = generateInsights()

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'critical': return '#ff4757'
      case 'high': return '#ffa502'
      case 'medium': return '#ffd93d'
      case 'low': return '#6bcf7f'
      default: return '#667eea'
    }
  }

  return (
    <div style={{marginTop: 30, marginBottom: 30}}>
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes liftUp {
          to { transform: translateY(-8px); }
        }
        @keyframes shimmer {
          0%, 100% { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
          50% { box-shadow: 0 12px 20px rgba(0,0,0,0.25); }
        }
        .insight-card {
          animation: slideIn 0.5s ease-out forwards;
        }
        .insight-card:hover {
          animation: liftUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
      `}</style>

      <h2 style={{fontSize: '28px', fontWeight: 'bold', marginBottom: 24, color: '#1a1a1a', display: 'flex', alignItems: 'center', gap: '10px'}}>
        📈 Attrition Insights
        <span style={{fontSize: '14px', fontWeight: 'normal', color: '#666', background: '#f0f0f0', padding: '4px 12px', borderRadius: '20px'}}>
          {insights.length} insights
        </span>
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: 20,
        marginBottom: 30
      }}>
        {insights.map((insight, idx) => (
          <div
            key={idx}
            className="insight-card"
            onMouseEnter={() => setHoveredCard(idx)}
            onMouseLeave={() => setHoveredCard(null)}
            style={{
              background: insight.gradient,
              color: 'white',
              padding: 24,
              borderRadius: 16,
              boxShadow: hoveredCard === idx ? '0 12px 24px rgba(0,0,0,0.2)' : '0 4px 12px rgba(0,0,0,0.1)',
              transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'hidden',
              borderLeft: `4px solid ${getSeverityColor(insight.severity)}`,
              transform: hoveredCard === idx ? 'translateY(-8px) scale(1.02)' : 'translateY(0) scale(1)'
            }}
          >
            {/* Background accent */}
            <div style={{
              position: 'absolute',
              top: '-50%',
              right: '-50%',
              width: '200px',
              height: '200px',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '50%',
              transition: 'all 0.6s ease'
            }} />

            {/* Severity badge */}
            <div style={{
              position: 'absolute',
              top: 12,
              right: 12,
              background: getSeverityColor(insight.severity),
              color: 'white',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '11px',
              fontWeight: 'bold',
              textTransform: 'uppercase',
              zIndex: 1
            }}>
              {insight.severity}
            </div>

            <div style={{position: 'relative', zIndex: 2}}>
              <div style={{
                fontSize: '48px',
                marginBottom: 16,
                filter: hoveredCard === idx ? 'scale(1.2)' : 'scale(1)',
                transition: 'filter 0.3s ease',
                display: 'inline-block'
              }}>
                {insight.icon}
              </div>
              <h3 style={{
                fontSize: '18px',
                fontWeight: 'bold',
                marginBottom: 10,
                marginTop: 0
              }}>
                {insight.title}
              </h3>
              <p style={{
                fontSize: '14px',
                lineHeight: '1.6',
                margin: '0 0 12px 0',
                opacity: 0.95
              }}>
                {insight.text}
              </p>
              {insight.details && (
                <p style={{
                  fontSize: '12px',
                  lineHeight: '1.4',
                  margin: 0,
                  opacity: 0.85,
                  fontStyle: 'italic',
                  borderTop: '1px solid rgba(255,255,255,0.3)',
                  paddingTop: 10
                }}>
                  💡 {insight.details}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Top Contributing Factors Section */}
      <div style={{
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        padding: 24,
        borderRadius: 16,
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        transition: 'all 0.3s ease'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
          cursor: 'pointer'
        }} onClick={() => setExpandedFactors(!expandedFactors)}>
          <h3 style={{marginTop: 0, marginBottom: 0, fontSize: '20px', fontWeight: 'bold', color: '#1a1a1a'}}>
            🎯 Top Contributing Factors
          </h3>
          <span style={{
            fontSize: '20px',
            transition: 'transform 0.3s ease',
            transform: expandedFactors ? 'rotate(180deg)' : 'rotate(0)'
          }}>
            ▼
          </span>
        </div>

        {expandedFactors && (
          <ol style={{
            marginLeft: 24,
            marginTop: 16,
            marginBottom: 0
          }}>
            {topFeatures.map((feat, idx) => (
              <li
                key={idx}
                style={{
                  marginBottom: 16,
                  paddingBottom: 12,
                  borderBottom: idx < topFeatures.length - 1 ? '1px solid rgba(0,0,0,0.1)' : 'none',
                  animation: `slideIn 0.5s ease-out ${idx * 0.1}s both`
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 6
                }}>
                  <strong style={{fontSize: '15px', color: '#1a1a1a'}}>
                    {idx + 1}. {feat.feature}
                  </strong>
                  <span style={{
                    background: getSeverityColor('high'),
                    color: 'white',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {feat.abs.toFixed(4)}
                  </span>
                </div>
                <div style={{
                  background: 'rgba(0,0,0,0.05)',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#555'
                }}>
                  Coefficient: <strong>{feat.coef.toFixed(4)}</strong> | Impact: <strong>{feat.abs.toFixed(4)}</strong>
                </div>
              </li>
            ))}
          </ol>
        )}

        {!expandedFactors && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12
          }}>
            {topFeatures.slice(0, 3).map((feat, idx) => (
              <div
                key={idx}
                style={{
                  background: 'white',
                  padding: 12,
                  borderRadius: 8,
                  textAlign: 'center',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                }}
              >
                <div style={{fontSize: '12px', color: '#666', marginBottom: 4}}>{feat.feature}</div>
                <div style={{fontSize: '18px', fontWeight: 'bold', color: getSeverityColor('high')}}>
                  {feat.abs.toFixed(4)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
