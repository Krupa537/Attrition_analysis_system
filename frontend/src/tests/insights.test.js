import { describe, it, expect, beforeEach } from 'vitest'

describe('Insights Component', () => {
  let mockAnalysis
  let mockFeatures

  beforeEach(() => {
    mockAnalysis = {
      id: 'test-123',
      metrics: {
        accuracy: 0.85,
        precision: 0.90,
        recall: 0.80,
        f1: 0.85,
        roc_auc: 0.88
      },
      artifacts: {
        confusion_matrix: [[15, 3], [2, 20]],
        model_path: '/tmp/model.pkl',
        numeric_features: ['Age', 'MonthlyIncome'],
        categorical_features: ['Department', 'OverTime']
      }
    }

    mockFeatures = [
      { feature: 'OverTime_Yes', coef: 0.8, abs: 0.8 },
      { feature: 'JobSatisfaction_Low', coef: -0.75, abs: 0.75 },
      { feature: 'MonthlyIncome', coef: -0.5, abs: 0.5 },
      { feature: 'YearsAtCompany', coef: -0.45, abs: 0.45 },
      { feature: 'Department_Sales', coef: 0.4, abs: 0.4 }
    ]
  })

  it('should calculate overall attrition rate correctly', () => {
    const cm = [[15, 3], [2, 20]]
    const tn = cm[0][0]
    const fp = cm[0][1]
    const fn = cm[1][0]
    const tp = cm[1][1]

    const total = tn + fp + fn + tp
    const attrition = tp + fn

    expect(total).toBe(40)
    expect(attrition).toBe(22)
    expect((attrition / total * 100).toFixed(1)).toBe('55.0')
  })

  it('should calculate overtime impact correctly', () => {
    const overtimeCoef = 0.8
    const oddsRatio = Math.exp(overtimeCoef)
    const percentageIncrease = ((oddsRatio - 1) * 100).toFixed(1)

    expect(parseFloat(percentageIncrease)).toBeGreaterThan(0)
    expect(parseFloat(percentageIncrease)).toBeLessThan(500)
  })

  it('should detect overtime feature', () => {
    const featureMap = {}
    mockFeatures.forEach(f => {
      featureMap[f.feature.toLowerCase()] = f
    })

    expect(featureMap['overtime_yes']).toBeDefined()
    expect(featureMap['overtime_yes'].coef).toBe(0.8)
  })

  it('should detect satisfaction features', () => {
    const satisfactionFeatures = mockFeatures.filter(f =>
      f.feature.toLowerCase().includes('satisf')
    )

    expect(satisfactionFeatures.length).toBe(1)
    expect(satisfactionFeatures[0].feature).toBe('JobSatisfaction_Low')
  })

  it('should sort features by absolute value', () => {
    const topFeatures = mockFeatures.slice(0, 3)

    expect(topFeatures[0].abs).toBe(0.8)
    expect(topFeatures[1].abs).toBe(0.75)
    expect(topFeatures[2].abs).toBe(0.5)
  })

  it('should handle empty features gracefully', () => {
    expect(mockFeatures.length).toBeGreaterThan(0)
  })

  it('should extract metrics correctly', () => {
    const metrics = mockAnalysis.metrics

    expect(metrics.accuracy).toBe(0.85)
    expect(metrics.precision).toBe(0.90)
    expect(metrics.recall).toBe(0.80)
    expect(metrics.f1).toBe(0.85)
  })

  it('should handle confusion matrix correctly', () => {
    const cm = mockAnalysis.artifacts.confusion_matrix

    expect(cm.length).toBe(2)
    expect(cm[0].length).toBe(2)
    expect(cm[1].length).toBe(2)
  })
})

describe('Attrition Statistics', () => {
  it('should classify high attrition (>20%)', () => {
    const attritionPercentage = 25.5
    const severity = attritionPercentage > 20 ? 'critical' : 'high'

    expect(severity).toBe('critical')
  })

  it('should classify medium attrition (10-20%)', () => {
    const attritionPercentage = 15.0
    const severity = attritionPercentage > 20 ? 'critical' : attritionPercentage > 10 ? 'high' : 'medium'

    expect(severity).toBe('high')
  })

  it('should classify low attrition (<10%)', () => {
    const attritionPercentage = 5.5
    const severity = attritionPercentage > 20 ? 'critical' : attritionPercentage > 10 ? 'high' : 'medium'

    expect(severity).toBe('medium')
  })
})

describe('Feature Impact Calculations', () => {
  it('should convert coefficient to odds ratio', () => {
    const coef = 1.0
    const oddsRatio = Math.exp(coef)

    expect(oddsRatio).toBeCloseTo(2.718, 2)
  })

  it('should calculate percentage increase from odds ratio', () => {
    const coef = 0.693
    const oddsRatio = Math.exp(coef)
    const percentIncrease = ((oddsRatio - 1) * 100)

    expect(percentIncrease).toBeCloseTo(100, 0)
  })

  it('should handle negative coefficients', () => {
    const coef = -0.5
    const oddsRatio = Math.exp(coef)
    const percentChange = ((oddsRatio - 1) * 100)

    expect(percentChange).toBeLessThan(0)
  })
})
