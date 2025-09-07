import React from 'react'
import { companies } from '@/lib/api'

function App() {
  const [companiesData, setCompaniesData] = React.useState([])

  React.useEffect(() => {
    // Example API usage
    companies()
      .then(setCompaniesData)
      .catch(console.error)
  }, [])

  return (
    <div className="App">
      <header>
        <h1>Auralis - Competitor Analysis</h1>
      </header>
      <main>
        <p>Companies loaded: {companiesData.length}</p>
      </main>
    </div>
  )
}

export default App
