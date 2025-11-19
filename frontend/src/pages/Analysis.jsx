import React, {useEffect, useState} from 'react'
import { useParams } from 'react-router-dom'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import Insights from './Insights'
import API from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function Analysis(){
  const { id } = useParams()
  const [analysis, setAnalysis] = useState(null)
  const [message, setMessage] = useState('')
  const [features, setFeatures] = useState([])
  // hide charts by default; user can click the buttons to display them
  // show charts automatically (buttons removed)
  const [showConfusionChart, setShowConfusionChart] = useState(true)
  const [showFeatureChart, setShowFeatureChart] = useState(true)

  useEffect(()=>{
    if(id) fetchAnalysis(id)
  },[id])

  async function fetchAnalysis(fetchId){
    setMessage('Loading...')
    try{
      const res = await fetch(API.getAnalysis(fetchId))
      const data = await res.json()
      if(!res.ok) throw new Error(data.detail || 'Fetch failed')
      const metrics = data.metrics_json || data.metrics
      const artifacts = data.artifacts_json || data.artifacts
      setAnalysis({ id: data.id, metrics, artifacts })
      setMessage('')
      // fetch feature importances if available
      fetchFeatureImportances(data.id)
      return { id: data.id, metrics, artifacts }
    }catch(err){
      setMessage('Error: '+err.message)
      return null
    }
  }

  async function fetchFeatureImportances(analysisId){
    try{
      const res = await fetch(API.getFeatureImportances(analysisId))
      if(!res.ok) return
      const data = await res.json()
      const feats = data.features || []
      setFeatures(feats)
      return feats
    }catch(e){
      // ignore silently; feature importances are optional
      return []
    }
  }

  function renderConfusion(){
    if(!analysis?.artifacts?.confusion_matrix) return null
    const cm = analysis.artifacts.confusion_matrix
    // normalize to 2x2 shape for charting (fill missing with zeros)
    let chartCm = cm
    try{
      if(!Array.isArray(chartCm) || chartCm.length === 0) chartCm = [[0,0],[0,0]]
      if(chartCm.length === 1){
        const v = chartCm[0][0] || 0
        chartCm = [[v,0],[0,0]]
      }
      if(chartCm.length === 2){
        chartCm = chartCm.map(r => (Array.isArray(r) ? (r.concat([0,0]).slice(0,2)) : [0,0]))
      }
    }catch(e){
      chartCm = [[0,0],[0,0]]
    }
    // render as a small table with intensity
    const flatMax = Math.max(...chartCm.flat())
    return (
      <div style={{maxWidth:400}}>
        <h4>Confusion Matrix</h4>
        <table style={{borderCollapse:'collapse'}}>
          <thead>
            <tr>
              <th style={{border:'1px solid #ddd',padding:6}}>True \ Pred</th>
              <th style={{border:'1px solid #ddd',padding:6}}>0</th>
              <th style={{border:'1px solid #ddd',padding:6}}>1</th>
            </tr>
          </thead>
          <tbody>
            {chartCm.map((row, i)=> (
              <tr key={i}>
                <td style={{border:'1px solid #ddd',padding:6}}>True {i}</td>
                {row.map((cell,j)=>{
                  const intensity = flatMax>0 ? Math.round((cell/flatMax)*220) : 0
                  const bg = `rgb(${255-intensity},${255-intensity},255)`
                  return (<td key={j} style={{border:'1px solid #ddd',padding:8,background:bg,textAlign:'center'}}>{cell}</td>)
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {showConfusionChart && (
          <div style={{maxWidth:600,marginTop:12}}>
            <Bar
              data={{
                labels: ['Pred:0','Pred:1'],
                datasets: [
                  { label: 'True 0', data: chartCm[0], backgroundColor: 'rgba(75,192,192,0.6)' },
                  { label: 'True 1', data: chartCm[1], backgroundColor: 'rgba(255,99,132,0.6)' }
                ]
              }}
              options={{
                plugins: { legend: { display: true } },
                scales: { y: { beginAtZero: true }, x: { beginAtZero: true } }
              }}
            />
          </div>
        )}
      </div>
    )
  }

  function renderFeatureImportance(){
    if(!features || features.length===0) return null
    const top = features.slice(0,30)
    const labels = top.map(f=>f.feature)
    const values = top.map(f=>f.abs)
    const data = { labels, datasets: [{ label: 'Importance (abs coef)', data: values, backgroundColor: 'rgba(54,162,235,0.6)' }] }
    return (
      <div style={{maxWidth:800,marginTop:12}}>
        <h4>Feature Importances</h4>
        {showFeatureChart
          ? (
            <Bar
              data={data}
              options={{
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
              }}
            />
          )
          : <div style={{marginBottom:8}}>Click "Show Feature Chart" to view bar chart.</div>
        }
        <div style={{marginTop:8}}>
          <table style={{width:'100%',borderCollapse:'collapse'}}>
            <thead>
              <tr>
                <th style={{border:'1px solid #ddd',padding:6,textAlign:'left'}}>Feature</th>
                <th style={{border:'1px solid #ddd',padding:6}}>Coef</th>
                <th style={{border:'1px solid #ddd',padding:6}}>Abs</th>
              </tr>
            </thead>
            <tbody>
              {top.map((f,i)=>(
                <tr key={i}>
                  <td style={{border:'1px solid #eee',padding:6}}>{f.feature}</td>
                  <td style={{border:'1px solid #eee',padding:6,textAlign:'right'}}>{f.coef.toFixed ? f.coef.toFixed(4) : f.coef}</td>
                  <td style={{border:'1px solid #eee',padding:6,textAlign:'right'}}>{f.abs.toFixed ? f.abs.toFixed(4) : f.abs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="title">Analysis Viewer</h2>
      {id ? <div className="small">Showing analysis {id}</div> : <div className="small">Enter an analysis ID in the URL or run analysis from Home.</div>}
      <div style={{marginTop:10}} className="small">{message}</div>
      {analysis && (
        <div style={{marginTop:12}}>
          <div className="card">
            <h3 className="title">Metrics</h3>
            <pre>{JSON.stringify(analysis.metrics, null, 2)}</pre>
          </div>
          <Insights analysis={analysis} features={features} />
          <div className="chart-wrap">
            {renderConfusion()}
            {renderFeatureImportance()}
          </div>
        </div>
      )}
    </div>
  )
}
