import { useParams } from 'react-router-dom'

export default function CompanyPage() {
  const { companyId } = useParams<{ companyId: string }>()

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Company: {companyId}</h1>
      <p className="text-gray-600">Company details and analysis</p>
    </div>
  )
}
