import React, {useState, useEffect} from 'react'
import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import Insights from './Insights'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function Upload(){
  const [file, setFile] = useState(null)
  const [datasetId, setDatasetId] = useState(null)
  const [columns, setColumns] = useState([])
  const [message, setMessage] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [validation, setValidation] = useState(null)
  const [features, setFeatures] = useState([])
  // show charts automatically (buttons removed)
  const [showConfusionChart, setShowConfusionChart] = useState(true)
  const [showFeatureChart, setShowFeatureChart] = useState(true)

  async function downloadFile(url, filename){
    setMessage('Preparing download...')
    try{
      const res = await fetch(url)
      if(!res.ok) throw new Error('Download failed: '+res.status)
      const blob = await res.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(blobUrl)
      setMessage('Download started')
    }catch(err){
      setMessage('Error: '+err.message)
    }
  }

  async function fetchFeatureImportances(analysisId){
    try{
      const res = await fetch(`http://127.0.0.1:8000/api/analysis/${analysisId}/feature_importances`)
      if(!res.ok) return
      const data = await res.json()
      const feats = data.features || []
      setFeatures(feats)
      return feats
    }catch(e){
      // ignore
      return []
    }
  }

  function renderConfusion(){
    if(!analysis?.artifacts?.confusion_matrix) return null
    let cm = analysis.artifacts.confusion_matrix
    try{
      if(!Array.isArray(cm) || cm.length === 0) cm = [[0,0],[0,0]]
      if(cm.length === 1){ const v = cm[0][0] || 0; cm = [[v,0],[0,0]] }
      if(cm.length === 2) cm = cm.map(r => (Array.isArray(r) ? (r.concat([0,0]).slice(0,2)) : [0,0]))
    }catch(e){ cm = [[0,0],[0,0]] }
    const flatMax = Math.max(...cm.flat())
    return (
      <div style={{maxWidth:600,marginTop:10}}>
        <h4>Confusion Matrix</h4>
        <table style={{borderCollapse:'collapse'}}>
          <thead>
            <tr><th style={{border:'1px solid #ddd',padding:6}}>True \ Pred</th><th style={{border:'1px solid #ddd',padding:6}}>0</th><th style={{border:'1px solid #ddd',padding:6}}>1</th></tr>
          </thead>
          <tbody>
            {cm.map((row,i)=>(
              <tr key={i}><td style={{border:'1px solid #ddd',padding:6}}>True {i}</td>{row.map((cell,j)=>{const intensity=flatMax>0?Math.round((cell/flatMax)*220):0;const bg=`rgb(${255-intensity},${255-intensity},255)`;return <td key={j} style={{border:'1px solid #ddd',padding:8,background:bg,textAlign:'center'}}>{cell}</td>})}</tr>
            ))}
          </tbody>
        </table>
        {showConfusionChart && (
          <div style={{marginTop:8}}>
            <Bar data={{ labels:['Pred:0','Pred:1'], datasets:[{ label:'True 0', data: cm[0], backgroundColor:'rgba(75,192,192,0.6)' },{ label:'True 1', data: cm[1], backgroundColor:'rgba(255,99,132,0.6)' }] }} options={{ plugins:{ legend:{ display:true } }, scales:{ y:{ beginAtZero:true }, x:{ beginAtZero:true } } }} />
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
    const data = { labels, datasets:[{ label:'Importance (abs coef)', data: values, backgroundColor:'rgba(54,162,235,0.6)' }] }
    return (
      <div style={{maxWidth:800,marginTop:10}}>
        <h4>Feature Importances</h4>
        {showFeatureChart ? <Bar data={data} options={{ indexAxis:'y', plugins:{ legend:{ display:false } }, scales:{ x:{ beginAtZero:true } } }} /> : <div style={{marginBottom:8}}>Click "Show Feature Chart" to view bar chart.</div>}
        <div style={{marginTop:8}}>
          <table style={{width:'100%',borderCollapse:'collapse'}}><thead><tr><th style={{border:'1px solid #ddd',padding:6,textAlign:'left'}}>Feature</th><th style={{border:'1px solid #ddd',padding:6}}>Coef</th><th style={{border:'1px solid #ddd',padding:6}}>Abs</th></tr></thead><tbody>{top.map((f,i)=>(<tr key={i}><td style={{border:'1px solid #eee',padding:6}}>{f.feature}</td><td style={{border:'1px solid #eee',padding:6,textAlign:'right'}}>{f.coef.toFixed?f.coef.toFixed(4):f.coef}</td><td style={{border:'1px solid #eee',padding:6,textAlign:'right'}}>{f.abs.toFixed?f.abs.toFixed(4):f.abs}</td></tr>))}</tbody></table>
        </div>
      </div>
    )
  }

  async function handleUpload(e){
    e.preventDefault()
    if(!file) return setMessage('Choose a CSV file first')
    const fd = new FormData()
    fd.append('file', file)

    setMessage('Uploading...')
    try{
      const res = await fetch('http://127.0.0.1:8000/api/upload', { method: 'POST', body: fd })
      let data = null
      try {
        data = await res.json()
      } catch (parseErr) {
        // non-JSON response
        throw new Error(`Upload failed (status ${res.status})`)
      }
      if(!res.ok) throw new Error(data.detail || `Upload failed (status ${res.status})`)
      setDatasetId(data.dataset_id)
      setColumns(data.columns)
      setMessage('Upload successful')
      if(data.validation) setValidation(data.validation)
    }catch(err){
      setMessage('Error: '+err.message)
    }
  }

  async function runAnalysis(){
    if(!datasetId) return setMessage('Upload a dataset first')
    setMessage('Training...')
    try{
      // allow user to select a target column if Attrition not present
      let target = 'Attrition'
      if(!columns.includes('Attrition') && columns.length>0){
        // ask user to confirm choice via prompt (simple fallback)
        const chosen = window.prompt('Target column not found. Enter target column name from: ' + columns.join(', '), columns[0])
        if(!chosen) {
          setMessage('Analysis cancelled: no target selected')
          return
        }
        target = chosen
      }
      const res = await fetch(`http://127.0.0.1:8000/api/analyze?dataset_id=${datasetId}&target_column=${encodeURIComponent(target)}` , { method: 'POST' })
      let data = null
      try { data = await res.json() } catch(e){ throw new Error(`Analysis failed (status ${res.status})`) }
      if(!res.ok) throw new Error(data.detail || `Analysis failed (status ${res.status})`)
      setMessage('Analysis complete. Analysis ID: '+data.analysis_id)
      setAnalysis({ id: data.analysis_id, metrics: data.metrics, artifacts: data.artifacts })
      // fetch feature importances for this analysis so UI can show chart
      fetchFeatureImportances(data.analysis_id)
    }catch(err){
      setMessage('Error: '+err.message)
    }
  }

  async function fetchAnalysis(){
    if(!analysis?.id) return setMessage('No analysis to fetch')
    setMessage('Fetching analysis...')
    try{
      const res = await fetch(`http://127.0.0.1:8000/api/analysis/${analysis.id}`)
      const data = await res.json()
      if(!res.ok) throw new Error(data.detail || 'Fetch failed')
      // server returns metrics_json and artifacts_json keys
      const metrics = data.metrics_json || data.metrics || analysis.metrics
      const artifacts = data.artifacts_json || data.artifacts || analysis.artifacts
      setAnalysis({ id: data.id || analysis.id, metrics, artifacts })
      // refresh features as well
      fetchFeatureImportances(data.id || analysis.id)
      setMessage('Analysis fetched')
    }catch(err){
      setMessage('Error: '+err.message)
    }
  }

  return (
    <div className="layout">
      <div className="card">
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div>
            <h2 className="title">Upload Dataset</h2>
            <div className="small">Upload a CSV to train and analyze attrition</div>
          </div>
        </div>

        <div style={{marginTop:12}}>
          <form onSubmit={handleUpload} className="metadata">
            <input type="file" accept=".csv" onChange={e=>setFile(e.target.files[0])} />
            <div className="controls">
              <button type="submit" className="btn btn-primary">Upload CSV</button>
              {datasetId && <div className="small">Dataset ID: {datasetId}</div>}
            </div>
          </form>
        </div>

        {datasetId && (
          <div style={{marginTop:16}}>
            <div className="card" style={{marginBottom:12}}>
              <h3 className="title">Dataset Details</h3>
              <div className="small">Columns:</div>
              <div className="small" style={{marginTop:6}}>{columns.join(', ')}</div>
              <div style={{marginTop:10}}>
                <button onClick={runAnalysis} className="btn btn-primary">Run Analysis</button>
              </div>
            </div>

            {validation && (
              <div className="card" style={{background:'#fff8e1'}}>
                <h4>Validation Summary</h4>
                <div>Records: {validation.record_count}</div>
                <div>Missing expected fields: {validation.missing_expected_fields.join(', ') || 'None'}</div>
                <div>Invalid rows: {validation.invalid_rows_count}</div>
                <div>Duplicate rows: {validation.duplicate_count}</div>
                {validation.invalid_row_samples && validation.invalid_row_samples.length>0 && (
                  <div>
                    <div>Invalid row samples:</div>
                    <pre>{JSON.stringify(validation.invalid_row_samples, null, 2)}</pre>
                  </div>
                )}
                <div style={{marginTop:8}}>
                  <button onClick={runAnalysis} className="btn">Proceed to Prediction</button>
                </div>
              </div>
            )}

            {analysis && (
              <div className="card" style={{marginTop:12}}>
                <h3 className="title">Analysis</h3>
                <div>Analysis ID: {analysis.id}</div>
                <div style={{marginTop:8}}>
                  <div className="small">Metrics:</div>
                  <pre>{JSON.stringify(analysis.metrics, null, 2)}</pre>
                </div>
                <div style={{marginTop:8}}>
                  <div className="small">Artifacts:</div>
                  <pre>{JSON.stringify(analysis.artifacts, null, 2)}</pre>
                </div>
                <Insights analysis={analysis} features={features} dataset={{columns}} />
                <div className="chart-wrap">
                  {renderConfusion()}
                  {renderFeatureImportance()}
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      <aside className="sidebar">
        <div className="card sidebar-card">
          <h4 className="title">Controls</h4>
          <div className="section small">Refresh & Downloads</div>
          <div className="controls">
            <button onClick={fetchAnalysis} className="btn">Refresh / View full analysis</button>
          </div>
          <div style={{marginTop:12}}>
            <button disabled={!analysis} className="btn btn-primary" onClick={async ()=>{
              if(!analysis) return setMessage('No analysis to download. Run analysis first.')
                  const url = `http://127.0.0.1:8000/api/download/analysis/${analysis.id}/pdf`
              await downloadFile(url, `analysis_${analysis.id}.pdf`)
            }}>Download analysis (PDF)</button>
          </div>
          <div style={{marginTop:8}}>
            <button disabled={!analysis} className="btn" onClick={async ()=>{
              if(!analysis) return setMessage('No analysis to download. Run analysis first.')
                  const url = `http://127.0.0.1:8000/api/download/model/${analysis.id}`
              await downloadFile(url, `model_${analysis.id}.pkl`)
            }}>Download trained model (.pkl)</button>
          </div>
          <div style={{marginTop:8}}>
            <button disabled={!analysis} className="btn" onClick={async ()=>{
              if(!analysis) return setMessage('No analysis to download. Run analysis first.')
                  const url = `http://127.0.0.1:8000/api/download/predictions/${analysis.id}`
              await downloadFile(url, `predictions_${analysis.id}.csv`)
            }}>Download prediction results (.csv)</button>
          </div>
          <div style={{marginTop:16}} className="small">{message}</div>
        </div>
      </aside>
    </div>
  )
}
